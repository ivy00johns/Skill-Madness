#!/usr/bin/env python3
"""Plan a local frontend gate bundle; --apply is the explicit write opt-in.

No dependency installs, global configuration, Git hooksPath mutation or overwrite.
Existing hook managers should invoke scripts/frontend-guards/run.py themselves.
"""
import argparse
import json
import os
from pathlib import Path
import sys

RUNNER = '''#!/usr/bin/env python3
"""Run every frontend source guard; errors and blocked inspection fail the gate."""
from pathlib import Path
import subprocess
import sys
root = Path(__file__).resolve().parents[2]
folder = Path(__file__).resolve().parent
failed = False
for script, flags in (
    ("check_design_tokens.py", ["--profile", "layout"]),
    ("check_class_extraction.py", []),
    ("check_shared_layout.py", []),
):
    rc = subprocess.call([sys.executable, str(folder / script), "--root", str(root), *flags])
    failed = failed or rc != 0
sys.exit(1 if failed else 0)
'''
WORKFLOW = '''name: Frontend Source Guards
on: [push, pull_request]
permissions:
  contents: read
jobs:
  frontend-source:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v5
      - uses: actions/setup-python@v6
        with:
          python-version: '3.x'
      - run: python3 scripts/frontend-guards/run.py
'''
HOOK = '''#!/usr/bin/env sh
# Merge this invocation into your existing hook manager; do not replace hooks.
exec python3 scripts/frontend-guards/run.py
'''


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", default=".")
    parser.add_argument("--class-guard-dir", help="class-extraction-guard skill root when not in a canonical checkout")
    parser.add_argument("--apply", action="store_true", help="explicit consent to create the listed project files")
    parser.add_argument("--wire-precommit", action="store_true", help="also create a plain project Git hook only when no existing hook/manager/path override exists")
    args = parser.parse_args()
    root = Path(args.root).resolve()
    if not root.is_dir():
        raise ValueError("project root does not exist")
    folder = Path(__file__).resolve().parent
    class_root = Path(args.class_guard_dir).resolve() if args.class_guard_dir else folder.parents[1] / "class-extraction-guard"
    files = {"scripts/frontend-guards/run.py": RUNNER,
             ".github/workflows/frontend-source-guards.yml": WORKFLOW,
             ".githooks/frontend-source-guards": HOOK,
             ".design-guard.json": json.dumps({"inlineStyleMode": "layout", "rules": {"no-inline-style": "error"}}, indent=2) + "\n",
             ".class-guard.json": json.dumps({"rules": {"repeated-class-string": "error", "duplicate-css-block": "error"}}, indent=2) + "\n"}
    for script in ("check_class_extraction.py", "check_shared_layout.py", "frontend_source.py"):
        files["scripts/frontend-guards/" + script] = (class_root / "scripts" / script).read_text()
    files["scripts/frontend-guards/check_design_tokens.py"] = (folder / "check_design_tokens.py").read_text()
    if args.wire_precommit:
        import subprocess
        if not (root / ".git").is_dir():
            raise ValueError("plain hook wiring requires project-local .git directory; worktrees must merge into their existing hook setup explicitly")
        override = subprocess.run(["git", "-C", str(root), "config", "--get", "core.hooksPath"], capture_output=True, text=True)
        if override.returncode not in (0, 1):
            raise ValueError("cannot inspect Git hook configuration")
        if override.returncode == 0 or (root / ".husky").exists() or (root / "lefthook.yml").exists():
            raise ValueError("existing hook manager/path: merge the runner explicitly; never replace it")
        files[".git/hooks/pre-commit"] = HOOK
    # Validate all sources/destinations before the first write, never overwrite.
    planned = []
    for relative, content in files.items():
        target = root / relative
        if target.is_symlink() or not target.parent.resolve().is_relative_to(root):
            raise ValueError("unsafe destination: %s" % relative)
        if target.exists() and (not target.is_file() or target.read_text() != content):
            raise ValueError("existing file differs; merge explicitly before bootstrap: %s" % relative)
        planned.append({"path": relative, "action": "keep" if target.exists() else "create"})
    if args.apply:
        for relative, content in files.items():
            target = root / relative
            if not target.exists():
                target.parent.mkdir(parents=True, exist_ok=True)
                with target.open("x") as out:
                    out.write(content)
                if relative.endswith(".py") or relative.startswith((".githooks/", ".git/hooks/")):
                    target.chmod(0o755)
    print(json.dumps({"applied": args.apply, "files": planned,
                      "hook_activation": "plain project hook requested" if args.wire_precommit else "NOT ACTIVATED: after approval, merge python3 scripts/frontend-guards/run.py into Husky/lefthook/existing pre-commit; no hooksPath or global settings changed",
                      "boundary": "full source-tree checks; generated output must remain in ignored directories; visible two-width render proof is still required"}, indent=2))
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except (OSError, ValueError) as exc:
        print("frontend bootstrap blocked: %s" % exc, file=sys.stderr)
        sys.exit(2)
