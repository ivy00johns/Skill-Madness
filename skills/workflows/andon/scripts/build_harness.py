#!/usr/bin/env python3
"""Assemble a chosen set of Skill-Madness skills into an Andon harness bundle and check it the way Andon will.

Andon imports a harness with `andon harness add <dir>`: it hashes every file, reads every SKILL.md it finds, and
refuses a bundle over 600 files or 8 MB, with duplicate skill names, a missing entry skill, or a bad stage outline.
The whole repo is far over those limits, so this copies only the named skills (symlinks skipped, as Andon skips them),
writes harness.json, and runs the same checks before Andon ever sees it. Nothing is imported or approved here.

Rules mirror the Andon commit in references/andon-pin.json (rechecked 8d64fa04): packages/shared/src/harness.ts (validateHarness, harnessManifestSchema) and
apps/agent/src/harness.ts (readBundle).

Usage:
  build_harness.py --skills madness,plan-builder,git-pr [--entry madness] [--slug madness] [--out DIR]
  build_harness.py --preset core --dry-run
  build_harness.py --skills ... --outline stages.json      # a JSON list of stages, or a full harness.json
"""
import argparse
import json
import re
import shutil
import subprocess
import sys
from pathlib import Path

MAX_FILES = 600
MAX_BYTES = 8 * 1024 * 1024
MAX_SKILLS = 200
MAX_STAGES = 12
RESERVED_STAGES = {"review", "ci", "merge"}
SLUG_RE = re.compile(r"^[a-z0-9][a-z0-9-]{0,39}$")
SKIP_DIRS = {".git", "node_modules", "dist", "build", ".next", ".turbo", "target", "vendor", "__pycache__"}

PRESETS = {
    # The router plus what it most often hands a single run: plan, commit, PR, fix the gate, debug.
    "core": ["madness", "plan-builder", "git-commit", "git-pr", "git-pr-feedback", "fix-until-green", "diagnose-loop"],
}

DEFAULT_STAGES = [
    {"key": "plan", "label": "Plan", "actor": "agent", "gate": {"requires": ["a plan a person approved"], "max_rounds": 1},
     "produces": ["plan.md"]},
    {"key": "build", "label": "Build", "actor": "agent", "depends_on": ["plan"]},
    {"key": "verify", "label": "Verify", "actor": "agent", "depends_on": ["build"],
     "gate": {"requires": ["typecheck, lint and tests pass"]}},
]


def repo_root() -> Path:
    return Path(__file__).resolve().parents[4]


def frontmatter(text: str) -> dict:
    """The keys this script needs (name, version, description), from the same YAML subset Andon parses."""
    m = re.match(r"^---\r?\n(.*?)\r?\n---(?:\r?\n|$)", text, re.S)
    if not m:
        return {}
    out, lines, i = {}, m.group(1).splitlines(), 0
    while i < len(lines):
        line = lines[i]
        i += 1
        if not line.strip() or line[0].isspace() or ":" not in line:
            continue
        key, raw = line.split(":", 1)
        raw = raw.strip()
        if raw in ("|", ">", "|-", ">-"):
            block = []
            while i < len(lines) and (not lines[i].strip() or lines[i][0].isspace()):
                block.append(lines[i].strip())
                i += 1
            joiner = "\n" if raw.startswith("|") else " "
            out[key.strip()] = joiner.join(block).strip()
        else:
            out[key.strip()] = raw.strip("'\"")
    return out


def find_skills(root: Path) -> dict:
    """name -> skill directory, for every live skill (archive/ is left out unless named by path)."""
    found = {}
    for skill_md in sorted((root / "skills").rglob("SKILL.md")):
        rel = skill_md.relative_to(root / "skills")
        if rel.parts[0] == "archive":
            continue
        name = frontmatter(skill_md.read_text(encoding="utf-8")).get("name") or skill_md.parent.name
        found[name] = skill_md.parent
    return found


def tracked_files(root: Path):
    """The repo's committed files, so eval workspaces, node_modules and other local leftovers stay out. None when
    the checkout isn't a git repo (then everything on disk counts)."""
    try:
        out = subprocess.run(["git", "-C", str(root), "ls-files", "-z", "skills"], capture_output=True, check=True)
    except (OSError, subprocess.CalledProcessError):
        return None
    return {(root / p).resolve() for p in out.stdout.decode().split("\0") if p}


def bundle_files(base: Path, tracked):
    """Every regular file under base the way Andon walks it (sorted, symlinks skipped, SKIP_DIRS pruned), limited
    to tracked files when there is a git index."""
    files, skipped = [], []
    for entry in sorted(base.iterdir(), key=lambda p: p.name):
        if entry.is_symlink():
            skipped.append(entry)
        elif entry.is_dir():
            if entry.name not in SKIP_DIRS:
                sub_files, sub_skipped = bundle_files(entry, tracked)
                files += sub_files
                skipped += sub_skipped
        elif entry.is_file() and (tracked is None or entry.resolve() in tracked):
            files.append(entry)
    return files, skipped


def load_outline(path: str | None) -> dict:
    if not path:
        return {"stages": DEFAULT_STAGES}
    data = json.loads(Path(path).read_text(encoding="utf-8"))
    return {"stages": data} if isinstance(data, list) else data


def depends_on_itself(key: str, stages: dict, seen=None) -> bool:
    seen = seen or set()
    for dep in stages.get(key, {}).get("depends_on", []):
        if dep == key or dep in seen:
            return True
        if dep in stages and depends_on_itself(dep, stages, seen | {dep}):
            return True
    return False


def validate(slug, manifest, skills, file_count, total_bytes):
    """Andon's validateHarness, in the same order and wording where it can be. (Its points-outside-the-bundle check
    can't fire on a copy made here, so it is left out.)"""
    errors, warnings = [], []
    if not SLUG_RE.match(slug):
        errors.append(f'"{slug}" is not a usable harness name (letters, digits and dashes, at most 40)')
    if file_count > MAX_FILES:
        errors.append(f"the bundle has {file_count} files (at most {MAX_FILES})")
    if total_bytes > MAX_BYTES:
        errors.append(f"the bundle is {round(total_bytes / 1024)} KB (at most {MAX_BYTES // 1024} KB)")
    if len(skills) > MAX_SKILLS:
        errors.append(f"the bundle has {len(skills)} skills (at most {MAX_SKILLS})")
    seen = {}
    for name, path, desc in skills:
        if name in seen:
            errors.append(f'two skills are called "{name}" ({seen[name]} and {path})')
        seen[name] = path
        if not desc:
            warnings.append(f'"{name}" has no description, so it will rarely be picked up')
        elif len(desc) > 1024:
            errors.append(f'"{name}"\'s description is over 1024 characters')
    entry = manifest.get("entry")
    if entry and entry not in seen:
        errors.append(f'the entry skill "{entry}" is not in the bundle')
    stages = manifest.get("stages", [])
    if len(stages) > MAX_STAGES:
        errors.append(f"the outline has {len(stages)} stages (at most {MAX_STAGES})")
    keys = {}
    for st in stages:
        key = st.get("key")
        if key in RESERVED_STAGES:
            errors.append(f'"{key}" is Andon\'s own stage and cannot be redefined')
        if key in keys:
            errors.append(f'two stages are called "{key}"')
        keys[key] = st
    for st in stages:
        for dep in st.get("depends_on", []):
            if dep not in keys:
                errors.append(f'stage "{st.get("key")}" depends on "{dep}", which the outline doesn\'t declare')
        if depends_on_itself(st.get("key"), keys):
            errors.append(f'stage "{st.get("key")}" depends on itself')
    return errors, warnings


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    pick = ap.add_mutually_exclusive_group(required=True)
    pick.add_argument("--skills", help="comma-separated skill names")
    pick.add_argument("--preset", choices=sorted(PRESETS), help="a named skill set")
    ap.add_argument("--slug", default="madness", help="harness name Andon registers (default: madness)")
    ap.add_argument("--name", default="Skill Madness", help="display name (default: Skill Madness)")
    ap.add_argument("--entry", default=None, help="skill to open first (default: madness when bundled)")
    ap.add_argument("--outline", help="JSON file: a list of stages, or a whole harness.json")
    ap.add_argument("--out", help="output directory (default: integrations/andon-harness/<slug>)")
    ap.add_argument("--dry-run", action="store_true", help="check only; write nothing")
    args = ap.parse_args()

    root = repo_root()
    available = find_skills(root)
    tracked = tracked_files(root)
    wanted = PRESETS[args.preset] if args.preset else [s.strip() for s in args.skills.split(",") if s.strip()]
    missing = [w for w in wanted if w not in available]
    if missing:
        print(f"unknown skill(s): {', '.join(missing)}", file=sys.stderr)
        return 2

    # Size and skills come from the sources; the copy below is byte-for-byte, so the numbers hold for the bundle.
    skills, files, skipped, total, sources = [], [], [], 0, []
    for name in wanted:
        src = available[name]
        sub_files, sub_skipped = bundle_files(src, tracked)
        sources += [(name, src, f) for f in sub_files]
        skipped += sub_skipped
        files += sub_files
        total += sum(f.stat().st_size for f in sub_files)
        for f in sub_files:
            if f.name.upper() == "SKILL.MD":
                fm = frontmatter(f.read_text(encoding="utf-8"))
                skills.append((fm.get("name") or f.parent.name, f"{name}/{f.relative_to(src).as_posix()}", fm.get("description", "")))

    version = json.loads((root / ".claude-plugin/plugin.json").read_text(encoding="utf-8")).get("version")
    outline = load_outline(args.outline)
    entry = args.entry or outline.get("entry") or ("madness" if "madness" in wanted else None)
    manifest = {
        "harness": args.slug,
        "name": outline.get("name", args.name),
        **({"version": version} if version else {}),
        "description": outline.get("description", f"Skill-Madness skills: {', '.join(wanted)}")[:400],
        **({"entry": entry} if entry else {}),
        "stages": outline.get("stages", []),
        "source": "https://github.com/ivy00johns/Skill-Madness",
    }
    manifest_bytes = len(json.dumps(manifest, indent=2).encode()) + 1
    # harness.json is part of the bundle Andon hashes and counts.
    errors, warnings = validate(args.slug, manifest, skills, len(files) + 1, total + manifest_bytes)
    warnings += [f"{p.relative_to(root)} is a symlink, so it is not part of the bundle" for p in skipped[:5]]
    nested = [p for _, p, _ in skills if p.count("/") > 1]
    if nested:
        errors.append(f"nested SKILL.md files would import as extra skills: {', '.join(nested)}")
    out = Path(args.out) if args.out else root / "integrations" / "andon-harness" / args.slug

    print(f"harness  {args.slug}  ({manifest['name']} {version or ''})".rstrip())
    print(f"skills   {len(skills)}: {', '.join(s[0] for s in skills)}")
    print(f"files    {len(files) + 1} of {MAX_FILES}   size {round((total + manifest_bytes) / 1024)} KB of {MAX_BYTES // 1024} KB")
    print(f"entry    {entry or '(none)'}   stages {', '.join(s['key'] for s in manifest['stages']) or '(Andon default)'}")
    for w in warnings:
        print(f"warning  {w}")
    for e in errors:
        print(f"ERROR    {e}", file=sys.stderr)
    if errors:
        return 1
    if args.dry_run:
        print("dry run: nothing written")
        return 0

    if out.exists():
        if not (out / "harness.json").is_file():
            print(f"{out} exists and is not a harness bundle this script wrote; pick another --out", file=sys.stderr)
            return 1
        shutil.rmtree(out)
    out.mkdir(parents=True)
    # Exactly the files counted above, nothing else from the working tree.
    for name, src, f in sources:
        dest = out / name / f.relative_to(src)
        dest.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(f, dest)
    (out / "harness.json").write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    print(f"wrote    {out}")
    print(f"next     andon harness add {out}        (then the person runs: andon harness approve {args.slug})")
    return 0


if __name__ == "__main__":
    sys.exit(main())
