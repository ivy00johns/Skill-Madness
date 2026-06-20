#!/usr/bin/env python3
"""sync-catalog-skills.py — reconcile plugin.json's `skills` array with disk.

The filesystem is the single source of truth for which skills exist. This
script keeps the published manifest (`.claude-plugin/plugin.json` `skills`
array) in agreement with it:

  --check   exit 1 if any on-disk skill is missing from the array, or any
            array entry points at a skill that no longer exists. Prints the
            drift. (CI / pre-commit use this.)
  --sync    rewrite the array to match disk: register missing skills, drop
            stale entries, keep existing order, group by category. (Idempotent.)

A skill is a directory directly under a category (skills/<category>/<skill>/
SKILL.md) or the top-level orchestrator (skills/orchestrator/SKILL.md).
Anything under archive/, in-progress/, or node_modules/ — or nested deeper
than that (e.g. a bundled node_modules SKILL.md) — is NOT a skill.

Reconciliation preserves the existing curated order: entries already in the
array stay where they are; newly-discovered skills are appended to the end of
their category's group (sorted); entries whose directory is gone are removed.
So adding a skill directory + running --sync produces a one-line diff.

Exit codes: 0 clean / synced, 1 drift (--check), 2 usage / parse error.
"""
import json
import re
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
SKILLS = REPO / "skills"
PLUGIN_JSON = REPO / ".claude-plugin" / "plugin.json"

# Fixed category order — matches the manifest's existing grouping so a clean
# repo round-trips with a zero-line diff.
CATEGORIES = ["orchestrator", "roles", "contracts", "git", "meta", "workflows", "loops"]
EXCLUDED = {"archive", "in-progress", "node_modules"}


def discover_by_category():
    """Return {category: [./skills/<...> , ...]} of real skills found on disk."""
    by_cat = {c: [] for c in CATEGORIES}
    if not SKILLS.is_dir():
        return by_cat
    for skill_md in SKILLS.rglob("SKILL.md"):
        parts = skill_md.relative_to(SKILLS).parts  # (...,'SKILL.md')
        if any(p in EXCLUDED for p in parts):
            continue
        if len(parts) == 2:          # skills/<cat>/SKILL.md  (orchestrator)
            cat, rel = parts[0], parts[0]
        elif len(parts) == 3:        # skills/<cat>/<skill>/SKILL.md
            cat, rel = parts[0], f"{parts[0]}/{parts[1]}"
        else:                        # deeper than a skill root => not a skill
            continue
        if cat in by_cat:
            by_cat[cat].append(f"./skills/{rel}")
    return by_cat


def load_existing():
    """Return (full_text, list_of_entries) from plugin.json."""
    text = PLUGIN_JSON.read_text()
    data = json.loads(text)
    return text, list(data.get("skills", []))


def category_of(entry):
    """'./skills/<cat>/<skill>' -> '<cat>'; './skills/orchestrator' -> 'orchestrator'."""
    segs = entry.strip("./").split("/")  # ['skills','<cat>', ...]
    return segs[1] if len(segs) > 1 else None


def reconcile(existing, by_cat_disk):
    """Preserve existing order; append new (sorted) per category; drop stale.

    Returns {category: [entries]} ready to emit, grouped in CATEGORIES order.
    """
    disk_all = {e for entries in by_cat_disk.values() for e in entries}
    out = {c: [] for c in CATEGORIES}
    seen = set()
    # 1. keep existing entries that still exist on disk, in their current order
    for e in existing:
        key = e.rstrip("/")
        if key in disk_all and key not in seen:
            cat = category_of(key)
            if cat in out:
                out[cat].append(key)
                seen.add(key)
    # 2. append skills present on disk but not yet listed, sorted, to their group
    for cat in CATEGORIES:
        for e in sorted(by_cat_disk.get(cat, [])):
            if e not in seen:
                out[cat].append(e)
                seen.add(e)
    return out


def emit_array(out_by_cat):
    """Render the JSON `skills` array text, category groups separated by a blank
    line, 4-space indented entries, to match the manifest's house style."""
    groups = []
    for cat in CATEGORIES:
        entries = out_by_cat.get(cat, [])
        if entries:
            groups.append(",\n".join(f'    "{e}"' for e in entries))
    return "[\n" + ",\n\n".join(groups) + "\n  ]"


def write_array(text, array_text):
    """Replace the `skills` array block in plugin.json text, preserving the rest.

    The array contains only string entries (no nested brackets), so a non-greedy
    match from `"skills": [` to the first `]` is exact.
    """
    new_text, n = re.subn(
        r'"skills"\s*:\s*\[.*?\]',
        '"skills": ' + array_text,
        text,
        count=1,
        flags=re.DOTALL,
    )
    if n != 1:
        raise SystemExit("could not locate the `skills` array in plugin.json")
    return new_text


def main(argv):
    mode = argv[1] if len(argv) > 1 else "--check"
    if mode not in ("--check", "--sync"):
        print("usage: sync-catalog-skills.py [--check | --sync]", file=sys.stderr)
        return 2

    by_cat = discover_by_category()
    disk_set = {e for entries in by_cat.values() for e in entries}
    text, existing = load_existing()
    existing_set = {e.rstrip("/") for e in existing}

    missing = sorted(disk_set - existing_set)   # on disk, not registered
    stale = sorted(existing_set - disk_set)      # registered, gone from disk

    if mode == "--check":
        if missing or stale:
            print("[ERR] plugin.json skills array out of sync with disk:")
            for m in missing:
                print(f"  [!!]  not registered (add): {m}")
            for s in stale:
                print(f"  [!!]  stale entry (remove):  {s}")
            print("  [--]  run 'scripts/catalog.sh --sync' to reconcile")
            return 1
        print(f"[OK]  plugin.json skills array matches disk ({len(disk_set)} skills)")
        return 0

    # --sync
    reconciled = reconcile(existing, by_cat)
    new_text = write_array(text, emit_array(reconciled))
    if new_text != text:
        PLUGIN_JSON.write_text(new_text)
        added = ", ".join(missing) if missing else "none"
        removed = ", ".join(stale) if stale else "none"
        print(f"[OK]  synced plugin.json skills array (added: {added}; removed: {removed})")
    else:
        print(f"[OK]  plugin.json skills array already in sync ({len(disk_set)} skills)")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
