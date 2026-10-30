#!/usr/bin/env python3
"""skill_eval.py — cost-capped `claude plugin eval` suites for single skills.

`claude plugin eval` (Claude Code >= 2.1.269) runs each eval case in an
isolated session WITH the skill loaded and again WITHOUT it, and reports the
difference (delta) — what the skill actually contributed. Every case run is a
full Claude session on your credential, so this wrapper keeps the free parts
free and the paid part capped:

  convert  skill-creator evals/evals.json -> plugin-eval case dirs     (free)
  lint     check suites against the runner's floor rules + count cost  (free)
  run      lint, then `claude plugin eval` with a REQUIRED --max-cost-usd,
           local-only report, with/without ablation                     (paid)
  report   delta, pass rate and real cost from the latest run           (free)

Usage:
  skill_eval.py convert skills/meta/madness [--negative "near-miss prompt" ...]
  skill_eval.py lint skills/meta/madness [skills/... ...]
  skill_eval.py run skills/meta/madness --max-cost-usd 0.50 [--case 01-*]
                [--runs 1] [--model haiku] [--allow-tools Write ...] [--trust]
  skill_eval.py report skills/meta/madness [--json]

A case is a directory under <skill>/evals/ holding prompt.md (frontmatter:
max_turns, timeout_seconds, allowed_tools, runs) and graders/*.md. Grader types:
regex, file_exists, tool_used, tool_order (free) and llm, baseline (bill a judge
model). convert never overwrites an existing case directory.

Pure python3 stdlib. Exit codes: 0 ok, 1 lint failure or a case below
--threshold, 2 argument error, 3 `claude` CLI missing or too old, 5 stopped at
the --max-cost-usd cap (partial results kept).
"""

import argparse
import glob
import json
import os
import re
import shutil
import subprocess
import sys

FREE_GRADERS = {"regex", "file_exists", "tool_used", "tool_order"}
PAID_GRADERS = {"llm", "baseline"}
MIN_RUNS = 3
DEFAULT_RUNS = 3
DEFAULT_TIMEOUT = 600
DEFAULT_MAX_TURNS = 20
DEFAULT_TOOLS = ["Skill", "Read", "Glob", "Grep"]
# The runner refuses a case whose prompt still holds its blank `init` template.
INIT_TODO = "TODO: describe what the agent should do"
SANDBOX_PATH = re.compile(r"(^|[\s'\"(`])(/Users/|/home/|~/)")
WRITES = re.compile(r"\b(write|writes|wrote|create[sd]?|generate[sd]?|save[sd]?|produce[sd]?|output)\b"
                    r".{0,40}\b(files?|docs?|documents?|report|series|folder|directory)\b", re.I)
# A filename in the EXPECTED result means the skill makes it; in the prompt it's often just context.
OUTPUT_FILE = re.compile(r"\b[\w-]+\.(md|json|csv|html|py|ts|yaml)\b")
OVER_BUDGET = 5
NO_CLI = 3


def die(msg, code=2):
    print(f"skill_eval: {msg}", file=sys.stderr)
    sys.exit(code)


# ---------- tiny frontmatter (the subset prompt.md / graders use) ----------

def parse_md(path):
    """Return (frontmatter dict, body) for a case/grader markdown file."""
    text = open(path, encoding="utf-8").read()
    m = re.match(r"---\n(.*?)\n---\n?(.*)", text, re.S)
    if not m:
        return {}, text
    fm = {}
    for line in m.group(1).splitlines():
        if ":" not in line or line.lstrip().startswith("#"):
            continue
        key, val = line.split(":", 1)
        val = val.strip()
        if val.startswith("[") and val.endswith("]"):
            val = [v.strip().strip("'\"") for v in val[1:-1].split(",") if v.strip()]
        elif re.fullmatch(r"-?\d+", val):
            val = int(val)
        elif val in ("true", "false"):
            val = val == "true"
        else:
            val = val.strip("'\"")
        fm[key.strip()] = val
    return fm, m.group(2)


def write_md(path, fm, body):
    lines = ["---"]
    for k, v in fm.items():
        if isinstance(v, list):
            v = "[" + ", ".join(v) + "]"
        elif isinstance(v, bool):
            v = "true" if v else "false"
        lines.append(f"{k}: {v}")
    lines += ["---", "", body.rstrip() + "\n"]
    with open(path, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))


# ---------- skill + case discovery ----------

def skill_name(skill_dir):
    path = os.path.join(skill_dir, "SKILL.md")
    if not os.path.isfile(path):
        die(f"{skill_dir}: no SKILL.md (pass a skill directory)")
    fm, _ = parse_md(path)
    return fm.get("name") or os.path.basename(os.path.normpath(skill_dir))


def case_dirs(skill_dir):
    root = os.path.join(skill_dir, "evals")
    out = []
    for d in sorted(glob.glob(os.path.join(root, "*"))):
        if os.path.basename(d) in ("results", "mocks") or not os.path.isdir(d):
            continue
        if os.path.isfile(os.path.join(d, "prompt.md")) or os.path.isfile(os.path.join(d, "case.yaml")):
            out.append(d)
    return out


def slugify(text, limit=40):
    s = re.sub(r"[^a-z0-9]+", "-", text.lower()).strip("-")
    return s[:limit].rstrip("-") or "case"


# ---------- convert ----------

def fires_grader(name):
    # Display-only under ablation: it shows the skill fired but never moves delta.
    return {"type": "tool_used", "tool": "Skill", "input_match": name}, ""


def not_fired_grader(name):
    # Scored in both arms: the skill must NOT load on a near-miss prompt.
    return {"type": "tool_used", "tool": "Skill", "input_match": name,
            "min": 0, "max": 0, "arm": "both"}, ""


def outcome_grader(ev):
    claims = [a.get("text", a) if isinstance(a, dict) else str(a)
              for a in ev.get("assertions") or ev.get("expectations") or []]
    if not claims and ev.get("expected_output"):
        claims = [ev["expected_output"]]
    if not claims:
        return None
    body = "The response satisfies every one of these checkable claims:\n\n" + \
        "\n".join(f"- {c}" for c in claims)
    return {"type": "llm", "weight": 1}, body


def write_case(root, slug, prompt, graders):
    case = os.path.join(root, slug)
    if os.path.exists(case):
        return None
    os.makedirs(os.path.join(case, "graders"))
    write_md(os.path.join(case, "prompt.md"),
             {"max_turns": DEFAULT_MAX_TURNS, "timeout_seconds": DEFAULT_TIMEOUT,
              "allowed_tools": DEFAULT_TOOLS, "runs": DEFAULT_RUNS}, prompt)
    for gname, (fm, body) in graders.items():
        write_md(os.path.join(case, "graders", f"{gname}.md"), fm, body)
    return case


def cmd_convert(args):
    skill_dir = args.skill
    name = skill_name(skill_dir)
    root = os.path.join(skill_dir, "evals")
    src = os.path.join(root, "evals.json")
    evals = []
    if os.path.isfile(src):
        evals = json.load(open(src, encoding="utf-8")).get("evals", [])
    elif not args.negative:
        die(f"{src} not found and no --negative given; nothing to convert")
    made, skipped, notes = [], [], []
    for i, ev in enumerate(evals):
        prompt = (ev.get("prompt") or "").strip()
        if not prompt:
            notes.append(f"eval {ev.get('id', i)}: empty prompt, skipped")
            continue
        slug = f"{int(ev.get('id', i)):02d}-{slugify(ev.get('name') or prompt)}"
        graders = {"fires": fires_grader(name)}
        outcome = outcome_grader(ev)
        if outcome:
            graders["outcome"] = outcome
        else:
            notes.append(f"{slug}: no assertions or expected_output — add an outcome grader")
        if ev.get("files"):
            notes.append(f"{slug}: input files {ev['files']} not copied — cases run in a sandbox cwd; "
                         "inline the content or add a case.yaml scaffold")
        if SANDBOX_PATH.search(prompt):
            notes.append(f"{slug}: prompt names an absolute or ~/ path — it won't exist in the sandbox; "
                         "rewrite it relative and supply the content as a fixture")
        expected = " ".join([ev.get("expected_output") or "", json.dumps(ev.get("assertions") or [])])
        if WRITES.search(prompt + " " + expected) or OUTPUT_FILE.search(expected):
            notes.append(f"{slug}: looks like the skill writes files — raise max_turns/timeout_seconds, add "
                         "Write to allowed_tools (run with --allow-tools Write), and point the rubric at the "
                         "file with focus: {source: file, path: ...}; the judge only sees the last message")
        (made if write_case(root, slug, prompt, graders) else skipped).append(slug)
    for j, neg in enumerate(args.negative or [], 1):
        slug = f"neg-{j:02d}-{slugify(neg)}"
        (made if write_case(root, slug, neg, {"not-fired": not_fired_grader(name)}) else skipped).append(slug)
    for s in made:
        print(f"  wrote   {os.path.join(root, s)}")
    for s in skipped:
        print(f"  kept    {os.path.join(root, s)} (exists; never overwritten)")
    for n in notes:
        print(f"  note    {n}")
    print(f"{len(made)} case(s) written for {name}. Next: skill_eval.py lint {skill_dir}")
    return 0


# ---------- lint ----------

def lint_case(case, name):
    errs, warns, paid = [], [], 0
    prompt_path = os.path.join(case, "prompt.md")
    if not os.path.isfile(prompt_path):
        warns.append("case.yaml case — only graders/ are linted")
        fm, body = {}, ""
    else:
        fm, body = parse_md(prompt_path)
        if not body.strip() or INIT_TODO in body:
            errs.append("prompt body is empty or still the blank init template")
        runs = fm.get("runs", DEFAULT_RUNS)
        if isinstance(runs, int) and runs < MIN_RUNS:
            errs.append(f"runs: {runs} — the runner's floor is {MIN_RUNS} (override with --runs for a pilot instead)")
        for key in ("timeout_seconds", "allowed_tools"):
            if key not in fm:
                warns.append(f"prompt.md has no {key} — an under-set timeout scores as 0, not as a timeout")
    graders = sorted(glob.glob(os.path.join(case, "graders", "*.md")))
    if not graders:
        errs.append("no graders/*.md")
    scored, negative = 0, False
    texts = [body]
    for g in graders:
        gfm, gbody = parse_md(g)
        texts.append(gbody)
        gtype = gfm.get("type")
        gname = os.path.basename(g)
        if gtype not in FREE_GRADERS | PAID_GRADERS:
            errs.append(f"{gname}: unknown type {gtype!r}")
            continue
        if gtype in PAID_GRADERS:
            paid += 1
        if gtype == "tool_used" and gfm.get("tool") == "Skill":
            if gfm.get("max") == 0:
                negative = True
                if gfm.get("min", 1) != 0 or gfm.get("arm") != "both":
                    errs.append(f"{gname}: a must-not-fire check needs min: 0, max: 0 AND arm: both")
                else:
                    scored += 1
            continue  # a plain fired-check is display-only under ablation
        scored += 1
    if graders and not scored:
        errs.append("only a skill-fired check — it never moves delta; add an outcome grader")
    for t in texts:
        if SANDBOX_PATH.search(t):
            errs.append("absolute or ~/ path in prompt or grader — cases run in a sandbox cwd")
            break
    return errs, warns, paid, negative


def suites_under(root):
    """Skill dirs under root that have plugin-eval cases (evals.json-only skills are skipped)."""
    return sorted(os.path.dirname(p) for p in glob.glob(os.path.join(root, "**", "SKILL.md"), recursive=True)
                  if "-workspace" not in p and case_dirs(os.path.dirname(p)))


def cmd_lint(args):
    failed = False
    skills = args.skills
    if getattr(args, "all", None):
        skills = suites_under(args.all)
        print(f"{len(skills)} skill(s) with plugin-eval cases under {args.all}")
    for skill_dir in skills:
        name = skill_name(skill_dir)
        cases = case_dirs(skill_dir)
        print(f"{name}: {len(cases)} case(s)")
        if not cases:
            print("  ERROR no cases under evals/ — run convert first")
            failed = True
            continue
        negatives, paid_total, runs_total = 0, 0, 0
        for case in cases:
            errs, warns, paid, negative = lint_case(case, name)
            fm, _ = parse_md(os.path.join(case, "prompt.md")) if os.path.isfile(os.path.join(case, "prompt.md")) else ({}, "")
            runs_total += fm.get("runs", DEFAULT_RUNS) if isinstance(fm.get("runs", DEFAULT_RUNS), int) else DEFAULT_RUNS
            negatives += negative
            paid_total += paid
            tag = os.path.basename(case)
            for e in errs:
                print(f"  ERROR {tag}: {e}")
            for w in warns:
                print(f"  warn  {tag}: {w}")
            failed |= bool(errs)
        if not negatives:
            print(f"  ERROR no must-not-fire case — add one with: convert {skill_dir} --negative \"<near-miss prompt>\"")
            failed = True
        print(f"  full suite = {runs_total} runs x 2 arms = {runs_total * 2} Claude sessions; "
              f"{paid_total} paid judge grader(s). Pilot with: skill_eval.py run {skill_dir} --runs 1 --case <one> --max-cost-usd 0.25")
    return 1 if failed else 0


# ---------- run ----------

def cmd_run(args):
    if not shutil.which("claude"):
        die("`claude` CLI not found on PATH", NO_CLI)
    probe = subprocess.run(["claude", "plugin", "eval", "--help"], capture_output=True, text=True)
    if probe.returncode != 0:
        die("`claude plugin eval` unavailable — needs Claude Code >= 2.1.269", NO_CLI)
    if args.max_cost_usd <= 0:
        die("--max-cost-usd must be > 0")
    lint_rc = cmd_lint(argparse.Namespace(skills=[args.skill]))
    if lint_rc and not args.case:
        die("lint failed — fix the suite before paying for a run", 1)
    estimate = last_cost_per_run(args.skill)
    if estimate:
        print(f"last run averaged ${estimate:.4f} per session")
    cmd = ["claude", "plugin", "eval", args.skill, "--ablation", "with-without",
           "--max-cost-usd", f"{args.max_cost_usd}", "--no-publish"]
    if args.publish:
        cmd.remove("--no-publish")
    for flag, val in (("--case", args.case), ("--runs", args.runs), ("--model", args.model),
                      ("--judge-model", args.judge_model), ("--threshold", args.threshold)):
        if val is not None:
            cmd += [flag, str(val)]
    if args.allow_tools:
        cmd += ["--allow-tools", *args.allow_tools]
    if args.scaffold:
        cmd.append("--scaffold")
    if args.trust:
        cmd.append("--trust-plugin")
    print("+ " + " ".join(cmd), flush=True)
    rc = subprocess.run(cmd).returncode
    if rc == 2:
        print(f"stopped at the ${args.max_cost_usd} cap — partial results kept; "
              "raising the cap is the owner's call", file=sys.stderr)
        return OVER_BUDGET
    return rc


# ---------- report ----------

def latest_result(skill_dir):
    hits = glob.glob(os.path.join(skill_dir, "evals", "results", "*", "aggregate-result.json"))
    return max(hits, key=os.path.getmtime) if hits else None


def _sessions(data):
    # aggregate-result.json schemaVersion 1: cases[].arms.{with,without} = [run, ...]
    return sum(len(runs) for c in data.get("cases") or []
               for runs in (c.get("arms") or {}).values() if isinstance(runs, list))


def last_cost_per_run(skill_dir):
    path = latest_result(skill_dir)
    if not path:
        return None
    data = json.load(open(path, encoding="utf-8"))
    n = _sessions(data)
    cost = data.get("costUsd")
    return cost / n if cost and n else None


def cmd_report(args):
    path = latest_result(args.skill)
    if not path:
        die(f"no results under {args.skill}/evals/results/ — nothing has run yet", 1)
    data = json.load(open(path, encoding="utf-8"))
    if args.json:
        print(json.dumps(data, indent=2))
        return 0
    print(f"{path}")
    for p in (data.get("suite") or {}).get("plugins") or []:
        if p.get("problem"):
            print(f"  WARNING plugin {p.get('name')}: {p['problem']} — the with-arm ran without the skill; "
                  "the scores below mean nothing")
    if data.get("schemaVersion") != 1:
        print(f"  note: schemaVersion {data.get('schemaVersion')!r} (written for 1) — fields may be missing")
    for c in data.get("cases") or []:
        a = c.get("aggregates") or {}
        errors = [r["error"] for runs in (c.get("arms") or {}).values() if isinstance(runs, list)
                  for r in runs if r.get("error")]
        print(f"  {c.get('name', '?')}  with={a.get('score', '-')}  without={a.get('scoreWithout', '-')}  "
              f"delta={a.get('delta', '-')}" + (f"  errors={len(errors)}" if errors else ""))
    top = data.get("aggregates") or {}
    n = _sessions(data)
    cost = data.get("costUsd") or 0
    print(f"suite: {top.get('casesPassed', '?')}/{top.get('casesTotal', '?')} cases passed  "
          f"mean delta={top.get('meanDelta', '-')}  cost=${cost:.4f} over {n} session(s)"
          + (f" (${cost / n:.4f} each)" if n else "")
          + ("  PARTIAL — stopped at the cap" if data.get("partial") else ""))
    return 0


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="mode", required=True)
    c = sub.add_parser("convert", help="evals.json -> plugin-eval cases (free)")
    c.add_argument("skill")
    c.add_argument("--negative", action="append", help="a near-miss prompt the skill must NOT fire on")
    l = sub.add_parser("lint", help="check suites, count cost (free)")
    l.add_argument("skills", nargs="*")
    l.add_argument("--all", metavar="ROOT", help="lint every skill under ROOT that has plugin-eval cases (CI)")
    r = sub.add_parser("run", help="claude plugin eval with a required cost cap (paid)")
    r.add_argument("skill")
    r.add_argument("--max-cost-usd", type=float, required=True)
    r.add_argument("--case")
    r.add_argument("--runs", type=int)
    r.add_argument("--model")
    r.add_argument("--judge-model")
    r.add_argument("--threshold", type=float)
    r.add_argument("--allow-tools", nargs="+")
    r.add_argument("--trust", action="store_true", help="pass --trust-plugin (only after the owner says yes)")
    r.add_argument("--scaffold", action="store_true",
                   help="run each case.yaml scaffold_script (author-supplied bash; only on cases you wrote)")
    r.add_argument("--publish", action="store_true", help="also publish the HTML report to claude.ai")
    p = sub.add_parser("report", help="delta + cost from the latest run (free)")
    p.add_argument("skill")
    p.add_argument("--json", action="store_true")
    args = ap.parse_args()
    if args.mode == "lint" and not (args.skills or args.all):
        ap.error("lint needs a skill directory or --all ROOT")
    return {"convert": cmd_convert, "lint": cmd_lint, "run": cmd_run, "report": cmd_report}[args.mode](args)


if __name__ == "__main__":
    sys.exit(main())
