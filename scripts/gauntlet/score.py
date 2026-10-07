#!/usr/bin/env python3
"""Grade Gauntlet v2 selection/invocation proof, never artifact-name counts.

Exit 0: recorded-case gate passed (fixtures are labelled FIXTURE_PASS).
Exit 1: missing/failed/blocked/error cases or insufficient live trials.
Exit 2: malformed, stale, forged, mixed-cell or legacy evidence.
Efficacy and behavioral safety require separate experiments and stay UNVERIFIED.
"""
import argparse
import json
from pathlib import Path
import sys

from pipeline import EvidenceError, grade, load_manifest, read_jsonl, report, write_new


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('trace', type=Path)
    parser.add_argument('--manifest', type=Path, required=True)
    parser.add_argument('--out', type=Path, help='new Markdown report path; never overwrite evidence')
    parser.add_argument('--json-out', type=Path, help='new machine-readable report path')
    args = parser.parse_args()
    try:
        manifest = load_manifest(args.manifest)
        summary = grade(read_jsonl(args.trace), manifest)
        # Validate output paths before producing either report.
        for path in (args.out, args.json_out):
            if path and (path.exists() or path.is_symlink()):
                raise EvidenceError('refusing to overwrite evidence: ' + str(path))
        if args.out and args.json_out and args.out.resolve() == args.json_out.resolve():
            raise EvidenceError('output paths must differ')
        if args.out:
            write_new(args.out, report(summary))
        else:
            print(report(summary), end='')
        if args.json_out:
            write_new(args.json_out, json.dumps(summary, indent=2) + '\n')
        return 1 if summary['findings'] else 0
    except (EvidenceError, OSError, TypeError, KeyError) as exc:
        print('grading blocked: ' + str(exc), file=sys.stderr)
        return 2


if __name__ == '__main__':
    raise SystemExit(main())
