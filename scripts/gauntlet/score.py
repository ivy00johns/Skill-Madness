#!/usr/bin/env python3
"""Score a Gauntlet II trace into a report and a [G2] intake proposal.

Consumes the merged trace JSONL plus the pre-registered expectations from
coverage-matrix.md and emits a Markdown report with the coverage roll-up, every
missed must-fire, every unexpected firing, and a candidate intake table.

Offline and deterministic. No model calls, no writes outside the given output.
"""

from __future__ import annotations

import argparse
import json
from collections import Counter
from pathlib import Path

# Category membership is resolved from a skill's path in coverage-matrix.md order;
# for scoring we group by the known category prefixes below.
CATEGORY_ORDER = [
    "orchestrator",
    "roles",
    "contracts",
    "meta",
    "git",
    "loops",
    "workflows",
]


def load_jsonl(path: Path) -> list[dict]:
    records: list[dict] = []
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line:
            continue
        try:
            records.append(json.loads(line))
        except json.JSONDecodeError:
            continue
    return records


def parse_matrix(matrix_path: Path) -> dict[str, str]:
    """Return skill -> category, using the order of the category headings."""
    categories: dict[str, str] = {}
    current = ""
    for line in matrix_path.read_text(encoding="utf-8").splitlines():
        if line.startswith("## "):
            heading = line[3:].strip().lower()
            for name in ("orchestrator", "role", "contract", "meta", "git", "loop", "workflow"):
                if name in heading:
                    current = {
                        "role": "roles",
                        "contract": "contracts",
                        "loop": "loops",
                        "workflow": "workflows",
                    }.get(name, name)
                    break
        elif line.startswith("| ") and current:
            cells = [c.strip() for c in line.strip("|").split("|")]
            if len(cells) >= 4 and cells[0] and cells[0].lower() != "skill":
                categories.setdefault(cells[0], current)
    return categories


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("trace", type=Path, help="merged trace JSONL")
    parser.add_argument("--matrix", type=Path, default=Path("docs/gauntlet/coverage-matrix.md"))
    parser.add_argument("--out", type=Path, help="write the report Markdown here (default: stdout)")
    args = parser.parse_args()

    if not args.trace.is_file():
        raise SystemExit(f"error: trace not found: {args.trace}")

    categories = parse_matrix(args.matrix) if args.matrix.is_file() else {}
    records = load_jsonl(args.trace)

    by_skill: dict[str, list[dict]] = {}
    for record in records:
        skill = str(record.get("skill", "")).strip()
        if skill:
            by_skill.setdefault(skill, []).append(record)

    counted = Counter(categories.get(skill, "unknown") for skill in by_skill)
    total_by_cat = Counter(categories.values())

    lines: list[str] = []
    lines.append("# Gauntlet II — scored coverage")
    lines.append("")
    lines.append(f"Trace records: {len(records)} · distinct skills fired: {len(by_skill)}")
    lines.append("")
    lines.append("| Category | Expected | Fired | Missed |")
    lines.append("|---|---|---|---|")
    expected_total = fired_total = missed_total = 0
    for category in CATEGORY_ORDER:
        expected = total_by_cat.get(category, 0)
        fired = counted.get(category, 0)
        missed = max(expected - fired, 0)
        expected_total += expected
        fired_total += fired
        missed_total += missed
        lines.append(f"| {category} | {expected} | {fired} | {missed} |")
    lines.append(f"| **total** | **{expected_total}** | **{fired_total}** | **{missed_total}** |")
    lines.append("")

    missed_skills = sorted(set(categories) - set(by_skill))
    unexpected = sorted(set(by_skill) - set(categories))
    if missed_skills:
        lines.append("## Missed must-fire skills")
        lines.append("")
        for skill in missed_skills:
            lines.append(f"- {skill}")
        lines.append("")
    if unexpected:
        lines.append("## Unexpected firings (possible false positives)")
        lines.append("")
        for skill in unexpected:
            lines.append(f"- {skill}")
        lines.append("")

    lines.append("## Proposed intake (`[G2]` rows)")
    lines.append("")
    lines.append("| Proposed ID | Priority | What you would notice | One-line problem | Proposed fix | Evidence | Size |")
    lines.append("|---|---|---|---|---|---|---|")
    idx = 1
    for skill in missed_skills:
        lines.append(
            f"| G2-{idx:02d} | | {skill} did not fire on its legitimate trigger "
            f"| must-fire skill missed | review the {skill} description or trigger context "
            f"| coverage-matrix.md | S |"
        )
        idx += 1
    for skill in unexpected:
        lines.append(
            f"| G2-{idx:02d} | | {skill} fired without a must-fire context "
            f"| possible over-triggering | tighten the {skill} description "
            f"| coverage-matrix.md | S |"
        )
        idx += 1
    if idx == 1:
        lines.append("| — | — | no misses or unexpected firings | — | — | — | — |")
    lines.append("")

    report = "\n".join(lines)
    if args.out:
        args.out.write_text(report, encoding="utf-8")
    else:
        print(report)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
