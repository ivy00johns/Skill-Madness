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
  4. Score it: the positive prompt must load the skill; the near-miss must not.

Each probe emits one JSONL record. `--telemetry` additionally writes
skill-health-shaped lines that `scripts/gauntlet/trace-merge.py` can consume, so
a probe result can stand in for the run telemetry that was never produced.

Caveats, stated rather than buried:

* Moving `HERMES_HOME` makes the host re-bootstrap its runtime and rewrite its
  own launcher against the scratch profile. This probe snapshots that launcher
  and restores it afterwards, but a crash (SIGKILL) can still leave it pointing
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

Usage:
  trigger-probe.py --model deepseek-v4-flash [--limit N] [--only NAME]
                   [--repeat N] [--out probe.jsonl] [--summary probe.md]
                   [--telemetry telemetry.jsonl] [--timeout SECS] [--quiet]
                   [--seed-config config.yaml] [--env-file .env]

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


@dataclass
class Row:
    skill: str
    phase: str
    trigger: str
    must_fire: bool
    near_miss: str


def strip_quotes(value: str) -> str:
    value = value.strip()
    if len(value) >= 2 and value[0] == '"' and value[-1] == '"':
        value = value[1:-1]
    return value.replace('\\"', '"').strip()


def parse_matrix(path: Path) -> list[Row]:
    """Read coverage-matrix.md into rows. Skips header and separator lines."""
    rows: list[Row] = []
    for line in path.read_text(encoding="utf-8").splitlines():
        match = MATRIX_ROW.match(line)
        if not match:
            continue
        skill, phase, trigger, must_fire, near_miss = (c.strip() for c in match.groups())
        if skill.lower() in {"skill", "trap"} or set(skill) <= {"-", " "}:
            continue
        rows.append(
            Row(
                skill=skill,
                phase=phase,
                trigger=strip_quotes(trigger),
                must_fire=must_fire.lower().startswith("yes"),
                near_miss=strip_quotes(near_miss),
            )
        )
    return rows


def host_launchers(host: str) -> list[Path]:
    """Every file the host may rewrite to re-point itself.

    `host` on PATH is often a tiny shim; the launcher that actually carries the
    interpreter path lives deeper in the profile. Snapshot all candidates, or
    the repair silently misses the file that matters.
    """
    candidates: list[Path] = []
    found = shutil.which(host)
    if found:
        candidates.append(Path(found))
    candidates.append(Path.home() / ".hermes" / "hermes-agent" / ".hermes" / "bin" / host)
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
) -> tuple[set[str], int, str]:
    """Ask the host one query; return (loaded skills, exit code, note)."""
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
        return set(), 124, "host timeout"
    except OSError as exc:
        return set(), 127, f"host not runnable: {exc}"
    loaded = parse_loads(proc.stdout)
    if proc.returncode:
        tail = [ln for ln in (proc.stderr or "").strip().splitlines() if ln.strip()]
        detail = " | ".join(tail[-3:])[:500] or "no stderr"
        return loaded, proc.returncode, f"host exited {proc.returncode}: {detail}"
    return loaded, 0, ""


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
    """Skills the host actually loaded, paired use->result.

    A `skill_view` call is only a load when its result did not report the skill
    missing: a lookup the model attempted and lost is not a firing.
    """
    pending: list[str] = []
    loaded: set[str] = set()
    for line in stream.splitlines():
        line = line.strip()
        if not line.startswith("{"):
            continue
        try:
            event = json.loads(line)
        except json.JSONDecodeError:
            continue
        kind = event.get("type")
        if kind == "tool_use" and event.get("name") == SKILL_LOAD:
            name = (event.get("input") or {}).get("name")
            pending.append(name.strip() if isinstance(name, str) else "")
        elif kind == "tool_result" and event.get("name") == SKILL_LOAD:
            name = pending.pop(0) if pending else ""
            if name and not _failed_result(event):
                loaded.add(name)
    return loaded


def _group_verdict(kind: str, verdicts: list[str]) -> str:
    """Collapse repeated probes of one prompt into a single verdict.

    Selection is stochastic, so one call is not evidence. For a must-fire row,
firing in every rep is PASS, in some reps is FLAKY, and in none is MISS. For a
near-miss row, never loading the skill is PASS. BLOCKED requires every rep to
have been blocked -- a row that ran and failed must not hide behind one crash.
    """
    if all(v == "BLOCKED" for v in verdicts):
        return "BLOCKED"
    if kind == "positive":
        passed = sum(1 for v in verdicts if v == "PASS")
        if passed == len(verdicts):
            return "PASS"
        return "FLAKY" if passed else "MISS"
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
    args = parser.parse_args()

    if not args.matrix.is_file():
        print(f"error: matrix not found: {args.matrix}", file=sys.stderr)
        return 2
    if shutil.which(args.host) is None:
        print(f"error: host '{args.host}' is not on PATH", file=sys.stderr)
        return 2

    rows = [r for r in parse_matrix(args.matrix) if r.must_fire]
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

    # The host rewrites its own launcher when HERMES_HOME moves. Snapshot every
    # candidate so the run cannot leave the user's install pointing at a deleted
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
                    loaded, code, note = run_probe(
                        query, args.model, home, work, args.timeout, environ
                    )
                    seconds = round(time.time() - started, 2)

                    if code != 0 and not loaded:
                        verdict = "BLOCKED"
                    elif kind == "positive":
                        verdict = "PASS" if row.skill in loaded else "MISS"
                    else:
                        verdict = "FALSE_POSITIVE" if row.skill in loaded else "PASS"
                    verdicts.append(verdict)

                    record = {
                        "run_id": run_id,
                        "ts": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
                        "layer": "trigger_selection",
                        "skill": row.skill,
                        "phase": row.phase,
                        "prompt_kind": kind,
                        "prompt": query,
                        "expected": "fire" if kind == "positive" else "no-fire",
                        "loaded": sorted(loaded),
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
                        extra = "" if row.skill in loaded else f" (loaded: {sorted(loaded) or 'none'})"
                        print(f"[{verdict}] {row.skill:<28} {kind:<8} rep {rep}/{reps}{extra}", file=sys.stderr)

                group = _group_verdict(kind, verdicts)
                if group in {"MISS", "FALSE_POSITIVE", "FLAKY"}:
                    findings += 1
                groups.append({"skill": row.skill, "kind": kind, "group": group, "verdicts": verdicts})
                for record in records[-reps:]:
                    record["group_verdict"] = group
                    telemetry.append(
                        {
                            "ts": record["ts"],
                            "skill": row.skill,
                            "outcome": "success" if group == "PASS" else "failure",
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
    blocked = sum(1 for g in groups if g["group"] == "BLOCKED")
    flaky = sum(1 for g in groups if g["group"] == "FLAKY")
    misses = sum(1 for g in groups if g["group"] == "MISS")
    false_pos = sum(1 for g in groups if g["group"] == "FALSE_POSITIVE")

    summary = [
        f"# Trigger probe — {args.host} / {args.model}",
        "",
        f"- run: `{run_id}`",
        f"- prompts: **{len(groups)}** across **{len(rows)}** always-fire skills"
        f", {reps} rep(s) each = **{len(records)}** host calls",
        f"- PASS {passed} · MISS {misses} · FLAKY {flaky} · FALSE_POSITIVE {false_pos} · BLOCKED {blocked}",
        "",
        "A MISS is a must-fire skill the model never loaded on its legitimate",
        "trigger across every rep; FLAKY means it loaded in some reps but not all.",
        "A FALSE_POSITIVE is a skill loaded on its near-miss control.",
        "",
    ]
    if misses or flaky:
        summary.append("## Missed must-fire prompts")
        summary.append("")
        for g in groups:
            if g["group"] in {"MISS", "FLAKY"}:
                summary.append(f"- `{g['group']}` {g['skill']} ({g['kind']}): {g['verdicts']}")
        summary.append("")
    if args.summary:
        args.summary.write_text("\n".join(summary) + "\n", encoding="utf-8")

    print("", file=sys.stderr)
    print(f"prompts: {len(groups)}  PASS {passed}  MISS {misses}  FLAKY {flaky}  "
          f"FALSE_POSITIVE {false_pos}  BLOCKED {blocked}", file=sys.stderr)

    if blocked and passed + misses + false_pos + flaky == 0:
        return 2
    return 1 if findings else 0


if __name__ == "__main__":
    raise SystemExit(main())
