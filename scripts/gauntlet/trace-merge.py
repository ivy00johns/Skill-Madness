#!/usr/bin/env python3
"""Merge validated Gauntlet v2 receipts; legacy/coarse telemetry is not proof."""
import argparse
import json
from pathlib import Path
import sys

from pipeline import EvidenceError, grade, load_manifest, read_jsonl, write_new


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('telemetry', type=Path, nargs='+', help='v2 receipt JSONL files, not prose/coarse hook events')
    parser.add_argument('--manifest', type=Path, required=True)
    parser.add_argument('--out', type=Path)
    parser.add_argument('--strict', action='store_true', help='exit 1 for failed, blocked or missing planned cases')
    args = parser.parse_args()
    try:
        manifest = load_manifest(args.manifest)
        records = [r for path in args.telemetry for r in read_jsonl(path)]
        summary = grade(records, manifest)
        merged = ''.join(json.dumps(r, sort_keys=True) + '\n' for r in sorted(records, key=lambda r: r['case_id']))
        if args.out:
            write_new(args.out, merged)
        else:
            sys.stdout.write(merged)
        print(json.dumps(summary, sort_keys=True), file=sys.stderr)
        return 1 if args.strict and summary['findings'] else 0
    except (EvidenceError, OSError, TypeError, KeyError) as exc:
        print('trace merge blocked: ' + str(exc), file=sys.stderr)
        return 2


if __name__ == '__main__':
    raise SystemExit(main())
