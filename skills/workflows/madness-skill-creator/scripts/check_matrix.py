#!/usr/bin/env python3
"""Validate frozen F3/F5 cell receipts; never dispatch models or spend money."""
import argparse
import json
import math
from pathlib import Path
import re
import sys


def number(value, minimum=0):
    return type(value) in (int, float) and math.isfinite(value) and value >= minimum


def check_cell(record):
    reasons = []
    required = ('run_id', 'task_id', 'layer', 'skill_hash', 'baseline_hash', 'verifier_hash',
                'host', 'model', 'split', 'falsifier', 'limits', 'trajectory',
                'outcome', 'proof', 'architecture', 'status', 'evidence_kind')
    if not isinstance(record, dict) or any(not record.get(key) for key in required):
        return {'accepted': False, 'capability_claim': False,
                'reasons': ['missing frozen identity, criteria or evidence fields']}
    for key in ('run_id', 'task_id', 'falsifier'):
        if not isinstance(record[key], str) or not record[key].strip():
            reasons.append('invalid ' + key)
    for key in ('skill_hash', 'baseline_hash', 'verifier_hash'):
        if not isinstance(record[key], str) or not re.fullmatch('[0-9a-f]{64}', record[key]):
            reasons.append('invalid ' + key)
    if record['layer'] not in ('load', 'trigger', 'efficacy'):
        reasons.append('unknown evidence layer')
    if record['split'] not in ('train', 'dev', 'held_out_test'):
        reasons.append('unknown split')
    kind = record['evidence_kind']
    if kind not in ('offline-fixture', 'live-host'):
        reasons.append('unknown evidence kind')
    host, model = record['host'], record['model']
    if not isinstance(host, dict) or any(not isinstance(host.get(k), str) or not host[k].strip() for k in ('name', 'version')):
        reasons.append('unidentified host/version')
    if not isinstance(model, dict) or (kind == 'live-host' and
            (not isinstance(model.get('id'), str) or not model['id'].strip())):
        reasons.append('unidentified worker model')
    if record['status'] != 'success':
        reasons.append('execution not successful')
    if any(record[k] != 'pass' for k in ('outcome', 'proof', 'architecture')):
        reasons.append('acceptance dimensions failed')
    limits, usage = record['limits'], record['trajectory']
    if not isinstance(limits, dict) or not isinstance(usage, dict):
        return {'accepted': False, 'capability_claim': False,
                'reasons': reasons + ['limits/trajectory must be objects']}
    for field in ('calls', 'seconds'):
        actual, ceiling = usage.get(field), limits.get('max_' + field)
        if not number(actual) or not number(ceiling) or ceiling <= 0 or actual > ceiling:
            reasons.append('missing/exceeded ' + field + ' cap')
        if field == 'calls' and (type(actual) is not int or type(ceiling) is not int):
            reasons.append('call counts must be integers')
    cost, cap = usage.get('cost_usd'), limits.get('max_cost_usd')
    if not number(cost) or not number(cap) or cost > cap:
        reasons.append('unknown/exceeded monetary liability')
    if kind == 'offline-fixture' and (cost != 0 or usage.get('calls') != 0):
        reasons.append('offline fixture cannot claim model calls/spend')
    if 'forced' in record and type(record['forced']) is not bool:
        reasons.append('forced must be boolean')
    if record['layer'] in ('trigger', 'efficacy'):
        if record['layer'] == 'trigger' and type(record.get('should_trigger')) is not bool:
            reasons.append('trigger label must be boolean')
        requires_retrieval = record['layer'] == 'efficacy' or record.get('should_trigger') is True
        proof = record.get('retrieval_proof')
        if record.get('forced') or (requires_retrieval and (not isinstance(proof, str) or not proof.strip())):
            reasons.append('missing unforced retrieval')
    if record['layer'] == 'efficacy':
        if record['split'] != 'held_out_test' or type(record.get('test_touches')) is not int or record['test_touches'] != 1:
            reasons.append('invalid final holdout')
        if record.get('baseline_model') != model or record.get('baseline_host') != host:
            reasons.append('changed worker/host')
        if type(record.get('trials')) is not int or record['trials'] < 2:
            reasons.append('single rollout cannot establish efficacy')
    capability_claim = kind == 'live-host' and record['layer'] == 'efficacy'
    return {'accepted': not reasons, 'capability_claim': capability_claim and not reasons,
            'reasons': reasons, 'evidence_kind': kind}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('records', type=Path)
    args = parser.parse_args()
    try:
        records = json.loads(args.records.read_text())
        if not isinstance(records, list) or not records:
            raise ValueError('records must be a nonempty list of cell receipts')
        results = [check_cell(record) for record in records]
    except (OSError, ValueError, TypeError) as exc:
        print(json.dumps({'accepted': False, 'reasons': [str(exc)]}))
        return 2
    print(json.dumps(results, indent=2))
    return 0 if all(r['accepted'] for r in results) else 2


if __name__ == '__main__':
    sys.exit(main())
