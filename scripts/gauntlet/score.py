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


def parse_matrix(matrix_path: Path) -> tuple[dict[str, str], set[str], set[str]]:
    """Return (skill -> category, must_fire, explicit) from coverage-matrix.md.

    `must_fire` holds the `yes` rows the report scores for selection; `explicit`
    holds the `disable-model-invocation` rows, which are graded on reachability
    and never reported as missed must-fire skills.
    """
    categories: dict[str, str] = {}
    must: set[str] = set()
    explicit: set[str] = set()
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
                flag = cells[3].lower()
                if flag.startswith("yes"):
                    must.add(cells[0])
                elif flag.startswith("explicit"):
                    explicit.add(cells[0])
    return categories, must, explicit


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("trace", type=Path, help="merged trace JSONL")
    parser.add_argument("--matrix", type=Path, default=Path("docs/gauntlet/coverage-matrix.md"))
    parser.add_argument("--out", type=Path, help="write the report Markdown here (default: stdout)")
    args = parser.parse_args()

    if not args.trace.is_file():
        raise SystemExit(f"error: trace not found: {args.trace}")

    if args.matrix.is_file():
        categories, must, explicit = parse_matrix(args.matrix)
    else:
        categories, must, explicit = {}, set(), set()
    records = load_jsonl(args.trace)

    # A record proves firing only when it passed with a retrieval proof. A
    # blocked/skipped/errored record, or one whose proof says it was never
    # retrieved, is recorded but not fired — counting it would certify a run
    # where nothing loaded.
    by_skill: dict[str, list[dict]] = {}
    not_fired: dict[str, list[dict]] = {}
    for record in records:
        skill = str(record.get("skill", "")).strip()
        if not skill:
            continue
        proof = str(record.get("retrieval_proof", "")).strip()
        fired = (record.get("outcome") == "pass" and proof
                 and proof.upper() != "NOT RETRIEVED")
        (by_skill if fired else not_fired).setdefault(skill, []).append(record)

    counted = Counter(categories.get(skill, "unknown") for skill in must & set(by_skill))
    total_by_cat = Counter(categories.get(skill, "unknown") for skill in must)

    lines: list[str] = []
    lines.append("# Gauntlet II — scored coverage")
    lines.append("")
    lines.append(
        f"Trace records: {len(records)} · distinct skills fired: {len(by_skill)}"
        f" · recorded but not fired (blocked/error/unproven): {len(set(not_fired) - set(by_skill))}"
    )
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

    missed_skills = sorted(must - set(by_skill))
    unreached_explicit = sorted(explicit - set(by_skill))
    unexpected = sorted(set(by_skill) - must - explicit)
    if missed_skills:
        lines.append("## Missed must-fire skills")
        lines.append("")
        for skill in missed_skills:
            lines.append(f"- {skill}")
        lines.append("")
    if unreached_explicit:
        lines.append("## Explicit-invocation skills not reached")
        lines.append("")
        lines.append("These ship `disable-model-invocation: true`; not reaching them is a")
        lines.append("reachability finding, not a model-selection miss.")
        lines.append("")
        for skill in unreached_explicit:
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
    for skill in unreached_explicit:
        lines.append(
            f"| G2-{idx:02d} | | {skill} was never reached on its explicit-invocation path "
            f"| explicit-invocation skill unreachable in this run "
            f"| document a dispatch/entry point for {skill} | coverage-matrix.md | S |"
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
