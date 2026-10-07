#!/usr/bin/env python3
"""Gauntlet II — trigger-selection probe.

Gauntlet II could not answer its own central question: which skills a model
loads, *unforced*. Its run trace depended on host telemetry (`skill-usage` hook
-> `$ATS_TELEMETRY_LOG`) that no host here emits, so `traces/run-trace.jsonl`
was written by the model rather than captured from the host. The scoring rubric
refuses that as evidence: "forced loading, or the skill's name appearing in
prose, is not retrieval evidence."

This probe measures selection directly, the same way on any model:

  1. Install every on-disk skill into an isolated host home.
  2. For each `coverage-matrix.md` row, ask the host the skill's legitimate
     trigger prompt, then its near-miss control prompt.
  3. Read the host's OWN skill-load events from its stream-json output. A load
     is a `skill_view` tool call by name -- the host's record, not the model's
     prose.
  4. Score it: a positive prompt passes when the skill is loaded and the answer
     does the work, or -- on an index-injecting host that already carries every
     description -- when the host demonstrably does the requested work without
     loading it. A skill that loads but then declines the work (a tool-less
     host, most often) scores `LOADED_REFUSED`, distinct from a `MISS` where
     nothing was selected at all. The near-miss control must not load the skill.

Each probe emits one JSONL record. `--telemetry` additionally writes
skill-health-shaped lines that `scripts/gauntlet/trace-merge.py` can consume, so
a probe result can stand in for the run telemetry that was never produced.

Caveats, stated rather than buried:

* Moving `HERMES_HOME` makes the host re-bootstrap its runtime and rewrite its
  own launchers against the scratch profile. It rewrites every launcher in its
  profile bin directory, so this probe snapshots each one -- `hermes` and its
  siblings like `hermes-acp`, not only the binary named on the command line --
  and restores them afterwards. A crash (SIGKILL) can still leave one pointing
  at a scratch path. Re-run the probe, or `cp` the `.bak` beside the launcher.
* The scratch profile carries a copy of the real `config.yaml` with its skills
  policy cleared (`--seed-config`). The host resolves model -> provider ->
  endpoint from that file: with no config the model lands on `provider: auto`,
  which has no endpoint, and the host exits before the model is asked anything.
* A positive MISS is strong evidence: the skill was not chosen for its own
  trigger. A near-miss "FALSE_POSITIVE" is weaker: `skill_view` is also how a
  model opens a skill to answer a direct question *about* it, which the matrix's
  near-miss controls do not distinguish from over-triggering. Read near-miss
  rows as "was opened", not "was auto-selected".
* A `WORKED` verdict is deliberately weaker than a `PASS`: the skill was not
  selected, but the requested work got done anyway. That is the expected outcome
  for skills an index-injecting host makes redundant (discovery and routing
  skills), so it is not counted as a finding. It is a heuristic -- it reads the
  host's tool activity and final text -- so it can be fooled; `--strict`
  disables it and reads `WORKED` as `MISS`.
* A `LOADED_REFUSED` verdict is the post-load counterpart to a `MISS`: the skill
  *was* selected (loaded in every rep) but the final answer declined the work --
  typically because the host lacks the tool the skill needs. It is a finding,
  but it is about the host's capability, not the description's pull. It is
  detected from refusal markers in the answer, and only when the answer carries
  no `BLOCKED` result -- a loaded skill that declines *and* hands back a folded
  degrade report has applied its fallback and scores `PASS`. The refusal check is
  still a heuristic: a skill whose answer merely mentions "I can't" mid-prose can
  be mislabeled; read it alongside the answer excerpt, not instead of it.

Usage:
  trigger-probe.py --model deepseek-v4-flash [--limit N] [--only NAME]
                   [--repeat N] [--out probe.jsonl] [--summary probe.md]
                   [--telemetry telemetry.jsonl] [--timeout SECS] [--quiet]
                   [--seed-config config.yaml] [--env-file .env]
                   [--include-explicit] [--strict]

`--repeat N` asks the same prompt N times and collapses the calls into one
verdict. Selection is stochastic, so a single call is not evidence: one rep can
miss a skill that normally fires. A positive that fires in some reps but not all
scores FLAKY, distinct from a MISS that never fired.

Exit codes: 0 = every prompt scored clean, 1 = at least one finding (miss,
false positive, or flaky), 2 = usage or environment error.
"""

from __future__ import annotations

import argparse
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
import time
from dataclasses import dataclass
from pathlib import Path

MATRIX_ROW = re.compile(r"^\|\s*(.+?)\s*\|\s*(.+?)\s*\|\s*(.+?)\s*\|\s*(.+?)\s*\|\s*(.+?)\s*\|")
SKILL_LOAD = "skill_view"
# Tool names that only consult the injected skill index. They do not count as
# doing the requested work; reading the index is what makes a skill redundant.
INDEX_TOOLS = {"skill_view", "skills_list", "skill_search"}
# Phrases that mark a final answer as a request for missing input rather than a
# deliverable: the model punted back to the user instead of doing the task.
INPUT_REQUEST_MARKERS = (
    "please paste", "please provide", "please share", "please specify",
    "please point", "point me to", "you haven't included", "you have not included",
    "can you provide", "could you provide", "can you share", "could you share",
    "i need the", "i'd need", "send me the", "which file", "which branch",
    "let me know which", "can you paste", "could you paste", "paste the",
    "can you clarify", "could you clarify", "please clarify",
)
# Phrases that mark a refusal. A refusal is not work, no matter how long it is.
REFUSAL_MARKERS = (
    "i can't", "i cannot", "i won't", "i will not", "i'm unable", "i am unable",
    "unable to help", "not able to help", "i must decline", "as an ai",
)
# A structured degraded result: the skill ran its fallback and labeled what it
# could not do. Its presence means the answer did work, not just decline.
BLOCKED_REPORT_MARKER = "blocked"
# The shortest answer still worth calling a deliverable. Routing answers are
# terse on purpose ("dependency-health-loop handles that"), so this is low; a
# request for input or a refusal is rejected before length is even considered.
MIN_ANSWER_CHARS = 40


@dataclass
class Row:
    skill: str
    phase: str
    trigger: str
    mode: str  # must_fire | explicit | optional
    near_miss: str


@dataclass
class Trace:
    loaded: set[str]
    tools: list[str]
    result_text: str


def strip_quotes(value: str) -> str:
    value = value.strip()
    if len(value) >= 2 and value[0] == '"' and value[-1] == '"':
        value = value[1:-1]
    return value.replace('\\"', '"').strip()


def parse_matrix(path: Path) -> list[Row]:
    """Read coverage-matrix.md into rows. Skips header and separator lines.

    The Must-fire cell carries the row's invocation mode: `yes` (and its
    `yes (optional)` variant) must be model-selected; `explicit` rows ship
    `disable-model-invocation: true` and are reached deliberately, never by
    unsolicited model selection; anything else is not probed.
    """
    rows: list[Row] = []
    for line in path.read_text(encoding="utf-8").splitlines():
        match = MATRIX_ROW.match(line)
        if not match:
            continue
        skill, phase, trigger, must_fire, near_miss = (c.strip() for c in match.groups())
        if skill.lower() in {"skill", "trap"} or set(skill) <= {"-", " "}:
            continue
        flag = must_fire.lower()
        if flag.startswith("explicit"):
            mode = "explicit"
        elif flag.startswith("yes"):
            mode = "optional" if "optional" in flag else "must_fire"
        else:
            continue
        rows.append(
            Row(
                skill=skill,
                phase=phase,
                trigger=strip_quotes(trigger),
                mode=mode,
                near_miss=strip_quotes(near_miss),
            )
        )
    return rows


def host_launcher_dir(host: str) -> Path:
    """The profile directory whose launcher scripts the host re-points."""
    return Path.home() / ".hermes" / "hermes-agent" / ".hermes" / "bin"


def _looks_like_launcher(path: Path) -> bool:
    """True when a file is a launcher script (it `exec`s an interpreter)."""
    try:
        return launcher_interpreter(path.read_bytes()) is not None
    except OSError:
        return False


def host_launchers(host: str) -> list[Path]:
    """Every launcher file the host may rewrite to re-point itself.

    `host` on PATH is often a tiny shim; the launcher that actually carries the
    interpreter path lives deeper in the profile. The host rewrites *every*
    launcher in its profile bin directory, not only the one matching `host` --
    a sibling such as `hermes-acp` is re-pointed too. Snapshot them all, or a
    crashed run strands one on a deleted scratch interpreter with nothing to
    restore it from.
    """
    candidates: list[Path] = []
    found = shutil.which(host)
    if found:
        candidates.append(Path(found))
    bin_dir = host_launcher_dir(host)
    try:
        entries = sorted(bin_dir.iterdir())
    except OSError:
        entries = []
    for entry in entries:
        # Only real launchers: a README or a stale `.bak` is not a file the host
        # re-points, and snapshotting it would only add restore noise.
        if entry.is_file() and _looks_like_launcher(entry):
            candidates.append(entry)
    out: list[Path] = []
    seen: set[str] = set()
    for path in candidates:
        key = str(path)
        if key in seen:
            continue
        seen.add(key)
        try:
            if path.is_file():
                out.append(path)
        except OSError:
            continue
    return out


def launcher_interpreter(content: bytes) -> Path | None:
    """The interpreter a launcher script will exec, or None when unreadable."""
    text = content.decode("utf-8", "replace")
    match = re.search(r"(?:^|\n)\s*exec\s+(\S+)", text)
    return Path(match.group(1)) if match else None


def repo_root_from(start: Path) -> Path:
    node = start
    while node != node.parent:
        if (node / ".env.example").exists():
            return node
        node = node.parent
    raise SystemExit("error: could not locate repo root (no .env.example above this script)")


def discover_skills(root: Path) -> list[Path]:
    """Every skills/**/SKILL.md outside skills/archive/."""
    found: list[Path] = []
    for path in sorted(root.glob("skills/**/SKILL.md")):
        if "archive" in path.parts:
            continue
        found.append(path.parent)
    return found


def seed_profile_config(config_path: Path, home: Path) -> str:
    """Copy the user's config into the scratch profile, minus its skills policy.

    The host resolves model -> provider -> endpoint from `config.yaml`. Ran with
    no user config, every model falls back to `provider: auto`, which has no
    endpoint, so the host dies before it is asked anything and every row reads
    BLOCKED. The scratch profile therefore carries a copy of the real config so
    the probe exercises the model the user actually runs -- while the skills
    policy (disabled lists, external dirs, trusted project dirs) is cleared, so
    the catalog this probe installed is the only one in play. Only env-var
    *names* are copied; no secret value is read or written.
    """
    if not config_path.is_file():
        return "absent"
    try:
        import yaml

        data = yaml.safe_load(config_path.read_text(encoding="utf-8")) or {}
    except Exception as exc:  # unreadable or invalid YAML -- report, do not guess
        return f"unreadable: {exc}"
    skills = data.get("skills")
    if isinstance(skills, dict):
        skills["disabled"] = []
        skills["platform_disabled"] = {}
        skills["external_dirs"] = []
        skills["trusted_project_dirs"] = []
    dest = home / ".hermes" / "config.yaml"
    try:
        dest.write_text(yaml.safe_dump(data, sort_keys=False, allow_unicode=True), encoding="utf-8")
    except Exception as exc:
        return f"unwritable: {exc}"
    return "seeded"


def install_skills(root: Path, home: Path) -> int:
    """Copy every skill into <home>/.hermes/skills and suppress bundled skills."""
    skills_dir = home / ".hermes" / "skills"
    if skills_dir.exists():
        shutil.rmtree(skills_dir)
    skills_dir.mkdir(parents=True)
    count = 0
    for src in discover_skills(root):
        dest = skills_dir / src.name
        if dest.exists():
            continue
        try:
            dest.symlink_to(src, target_is_directory=True)
        except OSError:
            shutil.copytree(src, dest)
        count += 1
    (home / ".hermes" / ".no-bundled-skills").write_text(
        "trigger probe: isolated catalog\n", encoding="utf-8"
    )
    return count


def load_env_file(path: Path, environ: dict[str, str]) -> None:
    """Add missing KEY=VALUE pairs from an env file. Never prints values."""
    if not path.is_file():
        return
    for raw in path.read_text(encoding="utf-8", errors="replace").splitlines():
        line = raw.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, _, value = line.partition("=")
        key, value = key.strip(), value.strip().strip('"').strip("'")
        if key and value and key not in environ:
            environ[key] = value


def run_probe(
    query: str, model: str, home: Path, work: Path, timeout: int, environ: dict[str, str]
) -> tuple[Trace, int, str]:
    """Ask the host one query; return (trace, exit code, note)."""
    query_file = work / "query.txt"
    query_file.write_text(query + "\n", encoding="utf-8")
    cmd = [
        "hermes", "chat", "--query-file", str(query_file), "--oneshot", "-Q",
        "--format", "stream-json", "--in", str(work), "-m", model,
        "--ignore-rules", "--max-turns", "4",
        "--run-budget", str(timeout), "-t", "skills",
    ]
    # NOTE: no --ignore-user-config. The host resolves the model's provider and
    # endpoint from config.yaml; ignoring it pins every model to `provider:
    # auto`, which has no endpoint, and the host exits 1 before the model runs.
    # The scratch profile is given a copy of the real config instead (see
    # seed_profile_config), so the isolation comes from HERMES_HOME, not a flag.
    # Isolate the skill catalog through HERMES_HOME only -- that is the profile
    # Hermes' own contract says is safe to move. HOME belongs to the OS account
    # and is where the host resolves its Python toolchain; XDG_* is where it
    # caches its install root. Overriding either makes the host re-bootstrap and
    # rewrite its launcher against a scratch path, breaking the real install
    # once the scratch dir is removed.
    env = dict(environ)
    env.update(
        HERMES_HOME=str(home / ".hermes"),
        PYTHONDONTWRITEBYTECODE="1",
    )
    for key in ("HERMES_PROFILE", "HERMES_CONFIG", "HERMES_ENV", "HERMES_YOLO_MODE"):
        env.pop(key, None)
    try:
        proc = subprocess.run(
            cmd, cwd=work, env=env, capture_output=True, text=True, timeout=timeout + 30
        )
    except subprocess.TimeoutExpired:
        return Trace(set(), [], ""), 124, "host timeout"
    except OSError as exc:
        return Trace(set(), [], ""), 127, f"host not runnable: {exc}"
    trace = parse_trace(proc.stdout)
    if proc.returncode:
        tail = [ln for ln in (proc.stderr or "").strip().splitlines() if ln.strip()]
        detail = " | ".join(tail[-3:])[:500] or "no stderr"
        return trace, proc.returncode, f"host exited {proc.returncode}: {detail}"
    return trace, 0, ""


def _failed_result(event: dict) -> bool:
    """Best-effort: did this tool_result report that no such skill exists?"""
    out = event.get("output")
    if out is None:
        out = event.get("error") or event.get("content")
    text = out if isinstance(out, str) else json.dumps(out)
    low = text.lower()
    return any(m in low for m in ("not found", "no such skill", "unknown skill",
                                  "does not exist", "not available"))


def parse_loads(stream: str) -> set[str]:
    """Skills the host actually loaded, paired use->result."""
    return parse_trace(stream).loaded


def parse_trace(stream: str) -> Trace:
    """Everything the host's stream-json reveals about one probe.

    `loaded` is the strict selection signal: a `skill_view` call is only a load
    when its result did not report the skill missing. `tools` and `result_text`
    feed the weaker work signal, so a redundant skill on an index-injecting host
    is not scored as a miss just because it was never opened.
    """
    pending: list[str] = []
    loaded: set[str] = set()
    tools: list[str] = []
    texts: list[str] = []
    result_text = ""
    for line in stream.splitlines():
        line = line.strip()
        if not line.startswith("{"):
            continue
        try:
            event = json.loads(line)
        except json.JSONDecodeError:
            continue
        kind = event.get("type")
        if kind == "tool_use":
            name = event.get("name")
            tools.append(name if isinstance(name, str) else "")
            if name == SKILL_LOAD:
                skill = (event.get("input") or {}).get("name")
                pending.append(skill.strip() if isinstance(skill, str) else "")
        elif kind == "tool_result" and event.get("name") == SKILL_LOAD:
            name = pending.pop(0) if pending else ""
            if name and not _failed_result(event):
                loaded.add(name)
        elif kind == "text":
            text = event.get("text")
            if isinstance(text, str):
                texts.append(text)
        elif kind == "result":
            text = event.get("text")
            if isinstance(text, str) and text.strip():
                result_text = text
    if not result_text:
        result_text = "".join(texts)
    return Trace(loaded=loaded, tools=tools, result_text=result_text)


def _is_input_request(text: str) -> bool:
    """Did the host ask the user to supply a missing artifact?

    Only concrete artifact requests count. A bare question is not a punt: for an
    interview skill the question IS the work, so treating every `?` as a request
    for input reads a correct interview turn as a failure.
    """
    low = text.strip().lower()
    if not low:
        return False
    return any(marker in low for marker in INPUT_REQUEST_MARKERS)


def _is_refusal(text: str) -> bool:
    """Did the host decline instead of doing the work?"""
    low = text.strip().lower()
    return bool(low) and any(marker in low for marker in REFUSAL_MARKERS)


def _reports_blocked(text: str) -> bool:
    """Did the answer hand back a structured BLOCKED result rather than punt?

    The degrade contracts (render-sanity, the source-level guards) standardize on
    the literal `BLOCKED` for a check the host could not run. An answer that
    carries it applied the skill's degraded fallback; a flat refusal did not.
    """
    return BLOCKED_REPORT_MARKER in text.lower()


def positive_verdict(skill: str, loaded: set[str], worked: bool, text: str) -> str:
    """Grade one positive probe: selection first, then whether it did the work.

    A load proves selection. When the skill loaded, the answer is `LOADED_REFUSED`
    only if it both declines *and* hands back no structured BLOCKED result -- a
    flat refusal. A refusal that still applied the skill's degraded fallback is a
    `PASS`. When the skill did not load, the weaker work signal applies: `WORKED`
    if the request was served anyway, else `MISS`.
    """
    if skill in loaded:
        if _is_refusal(text) and not _reports_blocked(text):
            return "LOADED_REFUSED"
        return "PASS"
    return "WORKED" if worked else "MISS"


def assess_work(trace: Trace) -> tuple[bool, str]:
    """Did the host do the requested work, even without loading the skill?

    An index-injecting host hands the model every skill name and description, so
    discovery and routing skills are redundant: the request is served with no
    `skill_view` call. This scores that served request. It is intentionally
    weaker than a load -- a load proves selection, work only proves the request
    was answered -- and it is never used to excuse a near-miss control.
    """
    acted = [t for t in trace.tools if t and t not in INDEX_TOOLS]
    if acted:
        return True, f"tool activity: {', '.join(sorted(set(acted)))}"
    text = trace.result_text.strip()
    if not text:
        return False, "no output"
    if _is_refusal(text):
        return False, "refused"
    if _is_input_request(text):
        return False, "asked for missing input"
    if len(text) >= MIN_ANSWER_CHARS:
        return True, f"substantive answer ({len(text)} chars)"
    return False, f"answer too thin ({len(text)} chars)"


def _group_verdict(kind: str, verdicts: list[str]) -> str:
    """Collapse repeated probes of one prompt into a single verdict.

    Selection is stochastic, so one call is not evidence. For a positive row,
    loading in every rep with the work done is PASS; loading in every rep but
    declining the work in any is LOADED_REFUSED; loading in some reps is FLAKY;
    never loading but doing the work is WORKED; never at all is MISS. For a
    near-miss row, never loading the skill is PASS. BLOCKED requires every rep to
    have been blocked -- a row that ran and failed must not hide behind one crash.
    """
    if all(v == "BLOCKED" for v in verdicts):
        return "BLOCKED"
    if kind == "positive":
        # Loading is the primary axis; the work/refusal distinction refines it.
        selected = [v for v in verdicts if v in {"PASS", "LOADED_REFUSED"}]
        if len(selected) == len(verdicts):
            # Selected in every rep -- PASS only if no rep declined the work.
            return "LOADED_REFUSED" if any(v == "LOADED_REFUSED" for v in verdicts) else "PASS"
        if selected:
            return "FLAKY"
        if any(v == "WORKED" for v in verdicts):
            return "WORKED"
        return "MISS"
    clean = sum(1 for v in verdicts if v == "PASS")
    if clean == len(verdicts):
        return "PASS"
    return "FLAKY" if clean else "FALSE_POSITIVE"


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    here = Path(__file__).resolve().parent
    root = repo_root_from(here)
    parser.add_argument("--matrix", type=Path, default=root / "docs/gauntlet/coverage-matrix.md")
    parser.add_argument("--model", default="deepseek-v4-flash")
    parser.add_argument("--host", default="hermes")
    parser.add_argument("--limit", type=int, default=0, help="probe only the first N rows")
    parser.add_argument("--only", action="append", default=[], help="probe only this skill (repeatable)")
    parser.add_argument("--kind", choices=["all", "positive", "negative"], default="all")
    parser.add_argument("--timeout", type=int, default=120, help="seconds per probe")
    parser.add_argument("--repeat", type=int, default=1, help="ask each prompt N times; verdicts collapse")
    parser.add_argument("--out", type=Path, help="results JSONL (default: stdout)")
    parser.add_argument("--summary", type=Path, help="write a markdown summary here")
    parser.add_argument("--telemetry", type=Path, help="also write trace-merge compatible telemetry")
    parser.add_argument("--env-file", type=Path, default=Path.home() / ".hermes" / ".env")
    parser.add_argument("--seed-config", type=Path, default=Path.home() / ".hermes" / "config.yaml",
                        help="config copied into the scratch profile (skills policy cleared)")
    parser.add_argument("--keep-home", action="store_true", help="keep the scratch host home")
    parser.add_argument("--quiet", action="store_true")
    parser.add_argument("--include-explicit", action="store_true",
                        help="also probe rows marked explicit (disable-model-invocation)")
    parser.add_argument("--strict", action="store_true",
                        help="require a load; read WORKED (work without a load) as MISS")
    args = parser.parse_args()

    if not args.matrix.is_file():
        print(f"error: matrix not found: {args.matrix}", file=sys.stderr)
        return 2
    if shutil.which(args.host) is None:
        print(f"error: host '{args.host}' is not on PATH", file=sys.stderr)
        return 2

    modes = {"must_fire", "optional"}
    if args.include_explicit:
        modes.add("explicit")
    rows = [r for r in parse_matrix(args.matrix) if r.mode in modes]
    if args.only:
        wanted = {n.strip() for n in args.only}
        rows = [r for r in rows if r.skill in wanted]
    if args.limit:
        rows = rows[: args.limit]
    if not rows:
        print("error: no matrix rows selected", file=sys.stderr)
        return 2

    environ = dict(os.environ)
    load_env_file(args.env_file.expanduser(), environ)

    # The host rewrites its own launchers when HERMES_HOME moves -- every script
    # in the profile bin dir, not just the one on the command line. Snapshot them
    # all so the run cannot leave the user's install pointing at a deleted
    # scratch dir.
    launcher_before: dict[Path, bytes] = {}
    for path in host_launchers(args.host):
        try:
            content = path.read_bytes()
        except OSError:
            continue
        launcher_before[path] = content
        broken = launcher_interpreter(content)
        if broken is not None and not broken.exists():
            # An earlier run (often a SIGKILLed one) already left this pointed at
            # a deleted scratch dir. Say so instead of silently snapshotting it:
            # restoring it afterwards is exactly how the damage compounds.
            print(f"warning: {path} already points at a missing interpreter ({broken}); "
                  f"this probe will not restore that state", file=sys.stderr)

    scratch = Path(tempfile.mkdtemp(prefix="gauntlet-probe-"))
    home, work = scratch / "home", scratch / "work"
    home.mkdir(), work.mkdir()
    installed = install_skills(root, home)
    config_seed = seed_profile_config(args.seed_config.expanduser(), home)
    if not args.quiet:
        print(f"installed {installed} skills; profile config: {config_seed}", file=sys.stderr)

    run_id = f"gauntlet-probe-{time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime())}"
    records: list[dict] = []
    telemetry: list[dict] = []
    groups: list[dict] = []
    findings = 0

    kinds = ["positive", "negative"] if args.kind == "all" else [args.kind]
    reps = max(1, args.repeat)

    try:
        for row in rows:
            for kind in kinds:
                if kind == "negative" and not row.near_miss:
                    continue
                query = row.trigger if kind == "positive" else row.near_miss
                verdicts: list[str] = []
                for rep in range(1, reps + 1):
                    started = time.time()
                    trace, code, note = run_probe(
                        query, args.model, home, work, args.timeout, environ
                    )
                    loaded = trace.loaded
                    worked, work_reason = (False, "") if args.strict else assess_work(trace)
                    seconds = round(time.time() - started, 2)

                    if code != 0 and not loaded:
                        verdict = "BLOCKED"
                    elif kind == "positive":
                        verdict = positive_verdict(
                            row.skill, loaded, worked, trace.result_text
                        )
                    else:
                        verdict = "FALSE_POSITIVE" if row.skill in loaded else "PASS"
                    verdicts.append(verdict)

                    record = {
                        "run_id": run_id,
                        "ts": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
                        "layer": "trigger_selection",
                        "skill": row.skill,
                        "phase": row.phase,
                        "mode": row.mode,
                        "prompt_kind": kind,
                        "prompt": query,
                        "expected": "fire" if kind == "positive" else "no-fire",
                        "loaded": sorted(loaded),
                        "worked": worked,
                        "work_reason": work_reason if (kind == "positive" and not row.skill in loaded) else "",
                        "tools": sorted({t for t in trace.tools if t}),
                        "answer": trace.result_text.strip()[:500],
                        "answer_chars": len(trace.result_text.strip()),
                        "verdict": verdict,
                        "rep": rep,
                        "reps": reps,
                        "host": {"name": args.host, "mode": "isolated-home", "skills_installed": installed,
                                 "config_seed": config_seed},
                        "model": {"id": args.model},
                        "seconds": seconds,
                        "note": note,
                    }
                    records.append(record)
                    if not args.quiet:
                        extra = "" if row.skill in loaded else f" (loaded: {sorted(loaded) or 'none'}; {work_reason or 'no work'})"
                        print(f"[{verdict}] {row.skill:<28} {kind:<8} rep {rep}/{reps}{extra}", file=sys.stderr)

                group = _group_verdict(kind, verdicts)
                if group in {"MISS", "FALSE_POSITIVE", "FLAKY", "LOADED_REFUSED"}:
                    findings += 1
                groups.append({"skill": row.skill, "kind": kind, "mode": row.mode,
                               "group": group, "verdicts": verdicts})
                for record in records[-reps:]:
                    record["group_verdict"] = group
                    telemetry.append(
                        {
                            "ts": record["ts"],
                            "skill": row.skill,
                            "outcome": "success" if group in {"PASS", "WORKED"} else "failure",
                            "session_id": run_id,
                            "source": "probe",
                            "prompt_kind": kind,
                            "verdict": group,
                        }
                    )
    finally:
        if not args.keep_home:
            shutil.rmtree(scratch, ignore_errors=True)
        for path, original in launcher_before.items():
            try:
                if path.read_bytes() == original:
                    continue
                interpreter = launcher_interpreter(original)
                if interpreter is None or not interpreter.exists():
                    # Never restore a snapshot that is itself broken -- that is how a
                    # SIGKILLed run's scratch path survives into the next generation.
                    print(f"warning: leaving {path} as the host wrote it; the snapshot "
                          f"points at a missing interpreter ({interpreter}). Run "
                          f"`hermes update`, or repoint the launcher by hand.", file=sys.stderr)
                    continue
                path.write_bytes(original)
            except OSError:
                continue

    payload = "\n".join(json.dumps(r, sort_keys=True) for r in records)
    if args.out:
        args.out.write_text(payload + "\n", encoding="utf-8")
    else:
        print(payload)
    if args.telemetry:
        args.telemetry.write_text(
            "\n".join(json.dumps(t, sort_keys=True) for t in telemetry) + "\n", encoding="utf-8"
        )

    passed = sum(1 for g in groups if g["group"] == "PASS")
    worked = sum(1 for g in groups if g["group"] == "WORKED")
    refused = sum(1 for g in groups if g["group"] == "LOADED_REFUSED")
    blocked = sum(1 for g in groups if g["group"] == "BLOCKED")
    flaky = sum(1 for g in groups if g["group"] == "FLAKY")
    misses = sum(1 for g in groups if g["group"] == "MISS")
    false_pos = sum(1 for g in groups if g["group"] == "FALSE_POSITIVE")

    summary = [
        f"# Trigger probe — {args.host} / {args.model}",
        "",
        f"- run: `{run_id}`",
        f"- prompts: **{len(groups)}** across **{len(rows)}** probed skills"
        f", {reps} rep(s) each = **{len(records)}** host calls",
        f"- PASS {passed} · WORKED {worked} · LOADED_REFUSED {refused} · "
        f"MISS {misses} · FLAKY {flaky} · FALSE_POSITIVE {false_pos} · BLOCKED {blocked}",
        "",
        "A PASS is the model loading the skill on its legitimate trigger. A MISS",
        "is a required skill the model never loaded and whose work never happened",
        "across every rep; FLAKY means it loaded in some reps but not all. WORKED",
        "means the skill was not loaded but the requested work happened anyway --",
        "the expected shape for a redundant skill on an index-injecting host, not a",
        "finding. A FALSE_POSITIVE is a skill loaded on its near-miss control.",
        "",
    ]
    if misses or flaky:
        summary.append("## Missed prompts")
        summary.append("")
        for g in groups:
            if g["group"] in {"MISS", "FLAKY"}:
                summary.append(f"- `{g['group']}` {g['skill']} ({g['mode']}, {g['kind']}): {g['verdicts']}")
        summary.append("")
    if refused:
        summary.append("## Loaded but declined the work")
        summary.append("")
        summary.append("The skill was selected in every rep, but the answer declined")
        summary.append("the work -- usually a host missing the tool the skill needs.")
        summary.append("Selection succeeded; the outcome did not.")
        summary.append("")
        for g in groups:
            if g["group"] == "LOADED_REFUSED":
                summary.append(f"- `{g['skill']}` ({g['mode']}, {g['kind']}): {g['verdicts']}")
        summary.append("")
    if worked:
        summary.append("## Worked without loading the skill")
        summary.append("")
        summary.append("The host served the request from its injected skill index;")
        summary.append("these are not failures.")
        summary.append("")
        for g in groups:
            if g["group"] == "WORKED":
                summary.append(f"- {g['skill']} ({g['kind']}): {g['verdicts']}")
        summary.append("")
    if args.summary:
        args.summary.write_text("\n".join(summary) + "\n", encoding="utf-8")

    print("", file=sys.stderr)
    print(f"prompts: {len(groups)}  PASS {passed}  WORKED {worked}  LOADED_REFUSED {refused}  "
          f"MISS {misses}  FLAKY {flaky}  FALSE_POSITIVE {false_pos}  BLOCKED {blocked}", file=sys.stderr)

    if blocked and passed + worked + refused + misses + false_pos + flaky == 0:
        return 2
    return 1 if findings else 0


if __name__ == "__main__":
    raise SystemExit(main())
