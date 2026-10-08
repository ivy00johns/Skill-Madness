#!/usr/bin/env python3
"""Claude Code trigger probe: for each coverage-matrix row, ask `claude -p` the
positive trigger and the near-miss control, and read the host's own Skill tool
calls from stream-json. A load = a Skill tool_use whose `skill` input names the
row (bare or plugin-prefixed). Stops a run as soon as the first Skill call lands."""
import argparse, json, os, re, subprocess, sys, time
from concurrent.futures import ThreadPoolExecutor

def rows(matrix):
    out = []
    for l in open(matrix):
        c = [x.strip() for x in l.strip().strip('|').split('|')]
        if l.startswith('|') and len(c) >= 5 and re.fullmatch(r'[a-z0-9-]+', c[0]):
            out.append(dict(skill=c[0], mode=c[3].split()[0].lower(),
                            pos=c[2].strip('"“” '), neg=re.sub(r'\s*\(.*\)$', '', c[4]).strip('"“” ')))
    return out

def run(skill, prompt, kind, model, cwd, timeout):
    t0 = time.time()
    cmd = ["claude", "-p", prompt, "--model", model, "--output-format", "stream-json",
           "--verbose", "--max-turns", "6"]
    p = subprocess.Popen(cmd, cwd=cwd, stdout=subprocess.PIPE, stderr=subprocess.DEVNULL, text=True)
    loads, first_tool, err = [], None, None
    try:
        deadline = t0 + timeout
        for line in p.stdout:
            if time.time() > deadline:
                err = "timeout"; break
            if re.search(r"<command-name>/?(?:[\w-]+:)?%s</command-name>|Base directory for this skill: \S*/%s\b" % (re.escape(skill), re.escape(skill)), line):
                loads.append(skill + " (slash/expanded)"); break
            try: ev = json.loads(line)
            except ValueError: continue
            if ev.get("type") == "result" and ev.get("is_error"):
                err = (ev.get("result") or ev.get("subtype") or "error")[:120]
            if ev.get("type") != "assistant": continue
            for blk in ev.get("message", {}).get("content", []):
                if blk.get("type") != "tool_use": continue
                first_tool = first_tool or blk.get("name")
                if blk.get("name") == "Skill":
                    loads.append(str(blk.get("input", {}).get("skill", "")))
            if loads:  # first skill decision observed; that's the selection signal
                break
    finally:
        p.kill(); p.wait()
    hit = any(l.split(" ")[0] == skill or l.split(" ")[0].endswith(":" + skill) for l in loads)
    return dict(skill=skill, kind=kind, prompt=prompt, loads=loads, first_tool=first_tool,
                hit=hit, error=err, secs=round(time.time() - t0, 1))

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--matrix", required=True); ap.add_argument("--out", required=True)
    ap.add_argument("--cwd", required=True); ap.add_argument("--model", default="claude-opus-5-5")
    ap.add_argument("--only", default=""); ap.add_argument("--kind", default="all")
    ap.add_argument("--jobs", type=int, default=8); ap.add_argument("--timeout", type=int, default=240)
    a = ap.parse_args()
    only = set(filter(None, a.only.split(",")))
    jobs = []
    for r in rows(a.matrix):
        if r["mode"] != "yes" or (only and r["skill"] not in only): continue
        f = next((os.path.join(d, "SKILL.md") for d, _, fs in os.walk("skills") if os.path.basename(d) == r["skill"] and "SKILL.md" in fs), None)
        if not f or not os.path.exists(os.path.expanduser("~/.claude/skills/" + r["skill"])):
            print(f"skip {r['skill']}: not installed for Claude Code", file=sys.stderr); continue
        if re.search(r"^disable-model-invocation:\s*true", open(f).read(), re.M):
            print(f"skip {r['skill']}: user-invoke-only", file=sys.stderr); continue
        if a.kind in ("all", "positive"): jobs.append((r["skill"], r["pos"], "positive"))
        if a.kind in ("all", "negative"): jobs.append((r["skill"], r["neg"], "negative"))
    print(f"{len(jobs)} probes", file=sys.stderr)
    with open(a.out, "a") as fh, ThreadPoolExecutor(a.jobs) as ex:
        for res in ex.map(lambda j: run(*j, a.model, a.cwd, a.timeout), jobs):
            fh.write(json.dumps(res) + "\n"); fh.flush()
            v = ("PASS" if res["hit"] else "MISS") if res["kind"] == "positive" else ("FALSE_POS" if res["hit"] else "ok")
            print(f"{v:9} {res['kind']:8} {res['skill']:28} loads={res['loads']} err={res['error']}", file=sys.stderr)

if __name__ == "__main__":
    main()
