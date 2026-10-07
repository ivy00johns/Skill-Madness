#!/usr/bin/env python3
"""Offline pipeline preflight: generate fixtures, run real CLIs, verify exits.

No model calls, hooks, installs or global writes. Outputs only inside --out-dir.
A fixture PASS establishes pipeline behavior, never actual model capability.
"""
import argparse
import json
from pathlib import Path
import subprocess
import sys

from pipeline import EvidenceError, ROOT, case_map, digest, json_hash, load_manifest, prepare, write_new


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--out-dir', type=Path, required=True, help='new directory inside the approved workspace')
    parser.add_argument('--repo', type=Path, default=ROOT)
    parser.add_argument('--matrix', type=Path, default=ROOT / 'docs/gauntlet/coverage-matrix.md')
    parser.add_argument('--revision', required=True, help='observed full Git revision; no automatic Git subprocess')
    args = parser.parse_args()
    try:
        out = args.out_dir.resolve()
        if not out.is_relative_to(ROOT.resolve()):
            raise EvidenceError('preflight outputs must stay inside this workspace')
        # Build/validate inputs before creating any artifacts.
        manifest = prepare(args.repo.resolve(), args.matrix.resolve(), 'offline-preflight', 'fixture-cell',
                           'claude-code', 'fixture-no-model', args.revision, 'offline-fixture')
        out.mkdir(parents=True, exist_ok=False)
        write_new(out / 'manifest.json', json.dumps(manifest, indent=2) + '\n')
        captures = []
        for case in manifest['cases']:
            events = [{'type': 'init', 'query': case['query'], 'mode': case['mode'],
                       'tools': ['skill', 'role_load', 'read_file']}]
            if case['expected'] == 'positive':
                tool = 'role_load' if case['mode'] == 'dispatch' else 'skill'
                origin = {'automatic': 'model', 'explicit': 'user', 'dispatch': 'orchestrator'}[case['mode']]
                content = (args.repo / manifest['catalog'][case['skill']]['path']).read_text()
                events += [{'type': 'tool_call', 'call_id': 'c1', 'tool': tool, 'skill': case['skill'], 'origin': origin},
                           {'type': 'tool_result', 'call_id': 'c1', 'tool': tool, 'skill': case['skill'],
                            'status': 'success', 'content': content}]
            events.append({'type': 'terminal', 'status': 'completed'})
            captures.append({'binding': manifest['binding'], 'manifest_sha256': json_hash(manifest),
                             'case_id': case['case_id'], 'events': events})
        blocked = [{**capture, 'events': [capture['events'][0], {'type': 'terminal', 'status': 'blocked'}]} for capture in captures]
        for name, values in [('events', captures), ('blocked-events', blocked)]:
            write_new(out / (name + '.jsonl'), ''.join(json.dumps(r) + '\n' for r in values))
        checks = []
        def run(label, script, *options, expected=0):
            command = [sys.executable, str(ROOT / 'scripts/gauntlet' / script), *map(str, options)]
            result = subprocess.run(command, capture_output=True, text=True, timeout=120)
            write_new(out / (label + '.log'), result.stdout + result.stderr)
            checks.append({'check': label, 'expected_exit': expected, 'actual_exit': result.returncode})
            if result.returncode != expected:
                raise EvidenceError(f'{label}: expected exit {expected}, got {result.returncode}; inspect retained log')
        plan = out / 'manifest.json'
        run('record', 'record.py', 'capture', out / 'events.jsonl', '--manifest', plan, '--out', out / 'receipts.jsonl')
        run('merge', 'trace-merge.py', out / 'receipts.jsonl', '--manifest', plan, '--strict', '--out', out / 'merged.jsonl')
        run('score', 'score.py', out / 'merged.jsonl', '--manifest', plan, '--out', out / 'report.md', '--json-out', out / 'report.json')
        run('blocked-record', 'record.py', 'capture', out / 'blocked-events.jsonl', '--manifest', plan, '--out', out / 'blocked.jsonl')
        run('blocked-merge', 'trace-merge.py', out / 'blocked.jsonl', '--manifest', plan, '--strict', expected=1)
        run('blocked-score', 'score.py', out / 'blocked.jsonl', '--manifest', plan, '--out', out / 'blocked-report.md', '--json-out', out / 'blocked-report.json', expected=1)
        summary = json.loads((out / 'report.json').read_text())
        if summary['verdict'] != 'FIXTURE_PASS' or summary['live_model_capability'] != 'NOT_ESTABLISHED':
            raise EvidenceError('fixture output misrepresents live capability')
        validate_manifest = load_manifest(plan)
        write_new(out / 'preflight.json', json.dumps({'verdict': 'OFFLINE_PIPELINE_PASS',
                  'model_calls': 0, 'checks': checks, 'manifest_sha256': json_hash(validate_manifest),
                  'artifacts': {p.name: digest(p.read_bytes()) for p in sorted(out.iterdir()) if p.is_file()},
                  'live_run_ready': False,
                  'limitation': 'a real host recording smoke with complete positive/negative event streams is still required; this command never authorizes spending'}, indent=2) + '\n')
        print(f'OFFLINE_PIPELINE_PASS: {len(checks)} CLI checks; zero model calls. Real-host recording is NOT proven.')
        return 0
    except (EvidenceError, OSError, TypeError, KeyError, subprocess.SubprocessError) as exc:
        print('preflight blocked: ' + str(exc), file=sys.stderr)
        return 2


if __name__ == '__main__':
    raise SystemExit(main())
