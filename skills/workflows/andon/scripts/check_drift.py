#!/usr/bin/env python3
"""Report how far Andon has moved since this skill was last checked against it. Read-only.

It compares three things with references/andon-pin.json:
  1. commits on the Andon checkout's origin/main since the pinned commit that touch the watched files;
  2. the CLI's usage lines (from apps/agent/src/cli.ts) at the pin and now;
  3. the installed agent (`andon --version`) and the `andon <command>`s this skill names that its help lacks.

Exit 0: nothing moved. Exit 1: drift to review (see references/refresh.md). Exit 2: couldn't check.

Usage: check_drift.py [--andon-repo ~/Work/andon] [--no-fetch]
"""
import argparse
import json
import os
import re
import subprocess
import sys
from pathlib import Path

SKILL = Path(__file__).resolve().parents[1]
PIN = SKILL / "references" / "andon-pin.json"
USAGE_RE = re.compile(r"^\s*andon ([a-z][a-z-]*)\b.*$")


def git(repo: Path, *args: str) -> str:
    r = subprocess.run(["git", "-C", str(repo), *args], capture_output=True, text=True)
    if r.returncode:
        raise RuntimeError(r.stderr.strip() or f"git {' '.join(args)} failed")
    return r.stdout


def usage_lines(text: str) -> list:
    """The `andon …` lines of the CLI's usage block, normalised."""
    out = []
    for line in text.splitlines():
        s = line.strip().strip("`'\",")
        if s.startswith("andon ") and USAGE_RE.match(s) and "${" not in s:
            out.append(re.sub(r"\s{2,}", "  ", s))
    return sorted(set(out))


def commands(lines: list) -> set:
    """Top-level command names; `andon list | status | version` names three."""
    out = set()
    for l in lines:
        m = re.match(r"andon ([a-z][a-z-]*(?: \| [a-z][a-z-]*)*)(?:\s|$)", l)
        if m:
            out.update(m.group(1).split(" | "))
    return out


def skill_commands() -> dict:
    """`andon <command>` mentions in this skill's markdown, with the files they are in."""
    found = {}
    for md in [SKILL / "SKILL.md", *sorted((SKILL / "references").glob("*.md"))]:
        for m in re.finditer(r"`andon ([a-z][a-z-]+)", md.read_text()):
            found.setdefault(m.group(1), set()).add(md.name)
    return found


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--andon-repo", default=os.environ.get("ANDON_REPO", "~/Work/andon"))
    ap.add_argument("--no-fetch", action="store_true")
    a = ap.parse_args()

    pin = json.loads(PIN.read_text())
    repo = Path(a.andon_repo).expanduser()
    drift = False
    print(f"pinned: Andon {pin['commit']} ({pin['date']}), installed agent {pin['installed_agent']}")

    if not (repo / ".git").exists():
        print(f"no Andon checkout at {repo}; pass --andon-repo. Only the installed CLI is checked.")
        head = None
    else:
        if not a.no_fetch:
            subprocess.run(["git", "-C", str(repo), "fetch", "-q", "origin"], capture_output=True)
        try:
            head = git(repo, "rev-parse", "--short=8", "origin/main").strip()
            log = git(repo, "log", "--oneline", f"{pin['commit']}..origin/main", "--", *pin["watched"]).strip()
        except RuntimeError as e:
            print(f"can't read the Andon checkout: {e}", file=sys.stderr)
            sys.exit(2)
        print(f"Andon origin/main: {head}")
        if log:
            drift = True
            n = len(log.splitlines())
            print(f"\n{n} commit(s) since the pin touch the watched files:")
            print("\n".join(f"  {l}" for l in log.splitlines()[:40]) + ("\n  …" if n > 40 else ""))
            changed = git(repo, "diff", "--stat", f"{pin['commit']}..origin/main", "--", *pin["watched"]).strip()
            print("\n" + changed)
        old = usage_lines(git(repo, "show", f"{pin['commit']}:apps/agent/src/cli.ts"))
        new = usage_lines(git(repo, "show", "origin/main:apps/agent/src/cli.ts"))
        gone, added = [l for l in old if l not in new], [l for l in new if l not in old]
        if gone or added:
            drift = True
            print("\nCLI usage changed in the source:")
            for l in gone:
                print(f"  - {l}")
            for l in added:
                print(f"  + {l}")
        source_cmds = commands(new)

    env = dict(os.environ)
    if "ANDON_CONFIG_DIR" not in env and Path("~/.andon/agent/config.json").expanduser().is_file():
        env["ANDON_CONFIG_DIR"] = str(Path("~/.andon/agent").expanduser())
    try:
        ver = subprocess.run(["andon", "version"], capture_output=True, text=True, env=env).stdout.strip().split()[0]
        helptext = subprocess.run(["andon", "--help"], capture_output=True, text=True, env=env).stdout
    except (FileNotFoundError, IndexError):
        ver, helptext = None, ""
    if ver is None:
        print("\nno `andon` on PATH; the installed-agent checks were skipped")
    else:
        if ver != pin["installed_agent"]:
            drift = True
            print(f"\ninstalled agent is {ver}, the pin says {pin['installed_agent']}")
        installed = commands(usage_lines(helptext))
        mentioned = skill_commands()
        missing = {c: f for c, f in mentioned.items() if c not in installed}
        if missing:
            print("\ncommands this skill names that the installed `andon --help` lacks"
                  + (" (in the source; an `andon update` brings them)" if head else "") + ":")
            for c, files in sorted(missing.items()):
                where = "in source" if head and c in source_cmds else "NOT in source either"
                if where != "in source":
                    drift = True
                print(f"  andon {c:10} {where:22} {', '.join(sorted(files))}")

    print("\nresult: " + ("drift; follow references/refresh.md" if drift else "nothing moved"))
    sys.exit(1 if drift else 0)


if __name__ == "__main__":
    main()
