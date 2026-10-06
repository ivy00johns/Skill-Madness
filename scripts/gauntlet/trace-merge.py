#!/usr/bin/env python3
"""Merge Gauntlet II skill-usage telemetry into one trace and report misses.

Reads the JSONL telemetry written by the host's skill-usage hook (one record per
skill invocation), normalizes it against the pre-registered expectations from
coverage-matrix.md, and reports every must-fire skill that produced no record.

This tool is authored for the Gauntlet II run. It is deterministic and offline;
it never calls a model, never writes outside the paths given, and never touches
the real home directory.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

MATRIX_ROW = re.compile(r"^\|\s*(.+?)\s*\|\s*(.+?)\s*\|\s*(.+?)\s*\|\s*(.+?)\s*\|\s*(.+?)\s*\|")


def load_jsonl(path: Path) -> list[dict]:
    records: list[dict] = []
    with path.open(encoding="utf-8") as fh:
        for lineno, line in enumerate(fh, 1):
            line = line.strip()
            if not line:
                continue
            try:
                value = json.loads(line)
            except json.JSONDecodeError as exc:
                print(f"warn: {path}:{lineno}: {exc}", file=sys.stderr)
                continue
            if isinstance(value, dict):
                records.append(value)
            else:
                print(f"warn: {path}:{lineno}: not an object", file=sys.stderr)
    return records


def derive_expectations(matrix_path: Path) -> tuple[set[str], set[str], set[str]]:
    """Return (must_fire, near_miss, explicit) skill names from coverage-matrix.md.

    `explicit` rows ship `disable-model-invocation: true`: they are deliberately
    not model-selectable, so a firing is welcome but never a false positive, and
    a non-firing is only reported as unreached, not as a missed must-fire.
    """
    must: set[str] = set()
    near: set[str] = set()
    explicit: set[str] = set()
    for line in matrix_path.read_text(encoding="utf-8").splitlines():
        match = MATRIX_ROW.match(line)
        if not match:
            continue
        skill, _phase, _trigger, must_fire, near_miss = (c.strip() for c in match.groups())
        if skill.lower() in {"skill", "trap"} or set(skill) <= {"-", " "}:
            continue
        if must_fire.lower().startswith("yes"):
            must.add(skill)
            if near_miss:
                near.add(skill)
        elif must_fire.lower().startswith("explicit"):
            explicit.add(skill)
    return must, near, explicit


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("telemetry", type=Path, help="JSONL telemetry from the skill-usage hook")
    parser.add_argument("--matrix", type=Path, default=Path("docs/gauntlet/coverage-matrix.md"))
    parser.add_argument("--out", type=Path, help="write merged trace JSONL here (default: stdout)")
    parser.add_argument("--strict", action="store_true", help="exit non-zero when a must-fire is missed")
    args = parser.parse_args()

    if not args.telemetry.is_file():
        print(f"error: telemetry not found: {args.telemetry}", file=sys.stderr)
        return 2

    records = load_jsonl(args.telemetry)
    fired = {str(r.get("skill", "")).strip() for r in records if r.get("skill")}

    must: set[str] = set()
    explicit: set[str] = set()
    if args.matrix.is_file():
        must, _near, explicit = derive_expectations(args.matrix)
    else:
        print(f"warn: matrix not found, no expectations derived: {args.matrix}", file=sys.stderr)

    missed = sorted(must - fired)
    unreached_explicit = sorted(explicit - fired)
    false_positives = sorted(fired - must - explicit) if must else []

    merged = "\n".join(json.dumps(r, sort_keys=True) for r in records)
    if args.out:
        args.out.write_text(merged + ("\n" if merged else ""), encoding="utf-8")
    else:
        sys.stdout.write(merged + ("\n" if merged else ""))

    print(f"\n# trace-merge summary", file=sys.stderr)
    print(f"records: {len(records)}", file=sys.stderr)
    print(f"must-fire skills: {len(must)}", file=sys.stderr)
    if missed:
        print(f"missed must-fire ({len(missed)}):", file=sys.stderr)
        for skill in missed:
            print(f"  - {skill}", file=sys.stderr)
    if unreached_explicit:
        print(f"explicit skills not reached ({len(unreached_explicit)}):", file=sys.stderr)
        for skill in unreached_explicit:
            print(f"  - {skill}", file=sys.stderr)
    if false_positives:
        print(f"unexpected firings ({len(false_positives)}):", file=sys.stderr)
        for skill in false_positives:
            print(f"  - {skill}", file=sys.stderr)

    if args.strict and missed:
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
