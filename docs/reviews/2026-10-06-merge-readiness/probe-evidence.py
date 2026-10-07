#!/usr/bin/env python3
"""Offline audit probes; all outputs stay in the specified evidence directory."""
import argparse
from collections import Counter
import hashlib
import importlib.util
import json
from pathlib import Path
import subprocess
import sys

import jsonschema

parser = argparse.ArgumentParser()
parser.add_argument('--candidate', type=Path, required=True)
parser.add_argument('--product', type=Path, required=True)
parser.add_argument('--evidence', type=Path, required=True)
args = parser.parse_args()
candidate = args.candidate.resolve()
evidence = args.evidence.resolve()
product = args.product.resolve()
records = [json.loads(line) for line in (evidence / 'bazaar-run-trace.jsonl').read_text().splitlines() if line.strip()]
schema = json.loads((candidate / 'docs/gauntlet/trace-schema.json').read_text())
validator = jsonschema.Draft202012Validator(schema, format_checker=jsonschema.FormatChecker())
invalid = [{'record': n, 'errors': [err.message for err in validator.iter_errors(record)]}
           for n, record in enumerate(records, 1)]
invalid = [r for r in invalid if r['errors']]
active = {p.parent.name for p in (candidate / 'skills').rglob('SKILL.md') if 'archive' not in p.parts}
names = {r['skill'] for r in records}
near = [r for r in records if r.get('expected') == 'near-miss-control']
summary = {
    'trace_records': len(records),
    'schema_invalid': invalid,
    'active_skills': len(active),
    'active_skills_named_in_trace': len(active & names),
    'active_skills_without_any_record': sorted(active - names),
    'unknown_trace_names': sorted(names - active),
    'outcomes': dict(Counter(r['outcome'] for r in records)),
    'proofs': dict(Counter(r.get('proof') for r in records)),
    'hosts': sorted({r['host']['name'] for r in records}),
    'near_miss_records': len(near),
    'unforced_retrieval_certification': 'UNVERIFIED: no correlated host tool-call receipt in the trace; prose and artifact paths do not establish retrieval',
}
spec = importlib.util.spec_from_file_location('guarded', candidate / 'skills/loops/loop-controller/scripts/run_guarded.py')
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)
frozen = json.loads((evidence / 'bazaar-frozen.json').read_text())
try:
    current = module.frozen_digest(frozen['paths'])
    summary['frozen_boundary'] = {'recorded': frozen['sha256'], 'current': current, 'matches': current == frozen['sha256'], 'paths': frozen['paths']}
except (OSError, ValueError) as exc:
    summary['frozen_boundary'] = {'error': str(exc)}

# A schema-valid negative rollout must never certify any skill as fired.
negative = []
for name in sorted(active):
    record = dict(records[0])
    record.update(skill=name, outcome='blocked', proof='blocked', retrieval_proof='NOT RETRIEVED', gate_results=['blocked'])
    negative.append(record)
path = evidence / 'synthetic-all-blocked.jsonl'
path.write_text(''.join(json.dumps(r) + '\n' for r in negative))
score = subprocess.run([sys.executable, str(candidate / 'scripts/gauntlet/score.py'), str(path), '--matrix', str(candidate / 'docs/gauntlet/coverage-matrix.md'), '--out', str(evidence / 'synthetic-all-blocked-score.md')], capture_output=True, text=True)
merge = subprocess.run([sys.executable, str(candidate / 'scripts/gauntlet/trace-merge.py'), str(path), '--matrix', str(candidate / 'docs/gauntlet/coverage-matrix.md'), '--strict', '--out', str(evidence / 'synthetic-all-blocked-merged.jsonl')], capture_output=True, text=True)
(evidence / 'synthetic-all-blocked-merge.log').write_text(merge.stdout + merge.stderr)
summary['negative_control'] = {'schema_valid_records': len(negative), 'score_exit': score.returncode, 'strict_trace_merge_exit': merge.returncode, 'expected': 'must not certify retrieval; every record explicitly BLOCKED'}
(evidence / 'trace-audit.json').write_text(json.dumps(summary, indent=2) + '\n')
print(json.dumps(summary, indent=2))
