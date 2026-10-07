#!/usr/bin/env python3
"""Plan and record Gauntlet cases offline; never launch a model or install hooks."""
import argparse
import json
from pathlib import Path
import sys

from pipeline import EvidenceError, ROOT, load_manifest, native_capture, prepare, read_jsonl, record, write_new


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest='command', required=True)
    plan = commands.add_parser('prepare', help='freeze catalog, eligibility, positive/negative cases and pipeline hashes')
    plan.add_argument('--repo', type=Path, default=ROOT)
    plan.add_argument('--matrix', type=Path, default=ROOT / 'docs/gauntlet/coverage-matrix.md')
    for name in ('run-id', 'cell-id', 'host', 'model', 'revision'):
        plan.add_argument('--' + name, required=True)
    plan.add_argument('--evidence-kind', choices=('offline-fixture', 'host-capture'), required=True)
    plan.add_argument('--trials', type=int, default=3)
    plan.add_argument('--skill', action='append', help='explicit subset; omitted means entire catalog')
    plan.add_argument('--out', type=Path, required=True)
    capture = commands.add_parser('capture', help='correlate observer event envelopes into versioned receipts')
    capture.add_argument('events', type=Path, nargs='+')
    capture.add_argument('--manifest', type=Path, required=True)
    capture.add_argument('--out', type=Path, required=True)
    native = commands.add_parser('import-host', help='normalize one recorded Freebuff SDK or Hermes case, retaining raw events')
    native.add_argument('events', type=Path)
    native.add_argument('--protocol', choices=('freebuff-sdk', 'hermes-stream'), required=True)
    native.add_argument('--case-id', required=True)
    native.add_argument('--manifest', type=Path, required=True)
    native.add_argument('--out', type=Path, required=True)
    args = parser.parse_args()
    try:
        if args.command == 'prepare':
            manifest = prepare(args.repo.resolve(), args.matrix.resolve(), args.run_id, args.cell_id,
                               args.host, args.model, args.revision, args.evidence_kind, args.trials, args.skill)
            write_new(args.out, json.dumps(manifest, indent=2) + '\n')
            print(f"Planned {len(manifest['cases'])} cases; {len(manifest['exclusions'])} skills excluded. No model calls.")
        else:
            manifest = load_manifest(args.manifest)
            if args.command == 'import-host':
                captures = [native_capture(args.protocol, read_jsonl(args.events), args.case_id, manifest)]
            else:
                captures = [r for path in args.events for r in read_jsonl(path)]
            receipts = record(captures, manifest)
            write_new(args.out, ''.join(json.dumps(r, sort_keys=True) + '\n' for r in receipts))
            print(f'Recorded {len(receipts)} correlated case receipts; use strict grading before acceptance.')
        return 0
    except (EvidenceError, OSError, TypeError, KeyError) as exc:
        print('record blocked: ' + str(exc), file=sys.stderr)
        return 2


if __name__ == '__main__':
    raise SystemExit(main())
