#!/usr/bin/env python3
"""Fail-closed Gauntlet evidence pipeline. Never invokes models or host commands.

YAML is used only to read the repository's established frontmatter format.
JSON Schema validation is mandatory, not advisory. Raw observer captures are
retained in receipts so grading replays evidence instead of trusting counters.
"""
from __future__ import annotations

import hashlib
import json
from pathlib import Path
import re
from collections import Counter

VERSION = 2
MODES = {'automatic', 'explicit', 'dispatch'}
STATUSES = {'pass', 'fail', 'blocked', 'execution-error'}
ROOT = Path(__file__).resolve().parents[2]
SCHEMA = ROOT / 'docs/gauntlet/trace-schema.json'


class EvidenceError(ValueError):
    """Missing, invalid, or incompatible evidence (CLI exit 2)."""


def digest(value):
    return hashlib.sha256(value).hexdigest()


def json_hash(value):
    return digest(json.dumps(value, sort_keys=True, separators=(',', ':'), allow_nan=False).encode())


def object_pairs(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise EvidenceError('duplicate JSON key: ' + key)
        result[key] = value
    return result


def decode(text):
    try:
        return json.loads(text, object_pairs_hook=object_pairs,
                          parse_constant=lambda v: (_ for _ in ()).throw(EvidenceError('non-finite JSON: ' + v)))
    except (json.JSONDecodeError, UnicodeError) as exc:
        raise EvidenceError('invalid JSON: ' + str(exc)) from exc


def read_json(path):
    return decode(Path(path).read_text(encoding='utf-8'))


def read_jsonl(path):
    records = []
    for number, line in enumerate(Path(path).read_text(encoding='utf-8').splitlines(), 1):
        if not line.strip():
            continue
        try:
            value = decode(line)
            if not isinstance(value, dict):
                raise EvidenceError('record must be an object')
            records.append(value)
        except EvidenceError as exc:
            raise EvidenceError(f'{path}:{number}: {exc}') from exc
    if not records:
        raise EvidenceError('empty evidence: ' + str(path))
    return records


def exact(value, keys, label):
    if not isinstance(value, dict) or set(value) != set(keys):
        raise EvidenceError(label + ' requires exactly: ' + ', '.join(sorted(keys)))


def nonempty(value, label):
    if not isinstance(value, str) or not value.strip():
        raise EvidenceError(label + ' must be a nonempty string')


def sha(value, label):
    if not isinstance(value, str) or not re.fullmatch('[0-9a-f]{64}', value):
        raise EvidenceError(label + ' must be SHA-256')


def safe_file(repo, relative):
    if not isinstance(relative, str) or Path(relative).is_absolute() or '..' in Path(relative).parts:
        raise EvidenceError('unsafe resource path: ' + str(relative))
    path = repo / relative
    if path.is_symlink() or not path.resolve().is_relative_to(repo.resolve()) or not path.is_file():
        raise EvidenceError('missing/symlinked resource: ' + relative)
    return path


def catalog(repo):
    try:
        import yaml
    except ImportError as exc:
        raise EvidenceError('PyYAML is required; use the project-local Python environment') from exc
    inventory = {}
    for path in sorted((repo / 'skills').rglob('SKILL.md')):
        relative = path.relative_to(repo)
        if set(relative.parts) & {'archive', 'in-progress', 'node_modules', '.workspaces'}:
            continue
        path = safe_file(repo, str(relative))
        text = path.read_text(encoding='utf-8')
        match = re.match(r'\A---\r?\n(.*?)\r?\n---(?:\r?\n|\Z)(.*)', text, re.S)
        if not match:
            raise EvidenceError('missing frontmatter: ' + str(relative))
        try:
            metadata = yaml.safe_load(match[1])
        except yaml.YAMLError as exc:
            raise EvidenceError('invalid frontmatter: ' + str(relative)) from exc
        if not isinstance(metadata, dict):
            raise EvidenceError('frontmatter must be a mapping')
        name = metadata.get('name')
        if name != path.parent.name or name in inventory:
            raise EvidenceError('duplicate/mismatched skill name: ' + str(name))
        for key in ('disable-model-invocation', 'user-invocable', 'requires_claude_code'):
            if key in metadata and type(metadata[key]) is not bool:
                raise EvidenceError('invalid boolean: ' + key)
        mode = ('dispatch' if metadata.get('user-invocable') is False else 'explicit') if metadata.get('disable-model-invocation') else 'automatic'
        if relative.parts[1] == 'roles' and metadata.get('disable-model-invocation'):
            mode = 'dispatch'
        resources = {}
        for resource in sorted(path.parent.rglob('*')):
            resource_relative = resource.relative_to(path.parent)
            if set(resource_relative.parts) & {'__pycache__', 'node_modules', '.git', '.workspaces'}:
                continue
            if resource.is_symlink():
                raise EvidenceError('symlinked skill resource: ' + str(resource))
            if resource.is_file() and resource.name not in {'.env', '.DS_Store'}:
                resources[str(resource_relative)] = {'sha256': digest(resource.read_bytes()),
                                                     'mode': resource.stat().st_mode & 0o777}
        inventory[name] = {'path': str(relative), 'category': relative.parts[1],
                           'sha256': digest(path.read_bytes()), 'body_sha256': digest(match[2].encode()),
                           'resources': resources, 'mode': mode,
                           'claude_only': metadata.get('requires_claude_code', False)}
    if not inventory:
        raise EvidenceError('empty skill catalog')
    return inventory


def matrix(path, inventory):
    rows = {}
    for line in Path(path).read_text(encoding='utf-8').splitlines():
        if not line.startswith('|'):
            continue
        cells = [cell.strip() for cell in line.strip().strip('|').split('|')]
        if len(cells) != 5 or cells[0] == 'Skill' or set(cells[0]) <= {'-', ' '}:
            continue
        name, phase, positive, required, negative = cells
        if name not in inventory or name in rows:
            raise EvidenceError('unknown/duplicate matrix skill: ' + name)
        if required.lower() not in {'yes', 'yes (optional)', 'no'} or not positive or not negative:
            raise EvidenceError('invalid matrix row: ' + name)
        rows[name] = {'phase': phase, 'positive': positive.strip('"'), 'negative': negative.strip('"'),
                      'required': required.lower() == 'yes'}
    if set(rows) != set(inventory):
        raise EvidenceError('matrix/catalog mismatch: ' + ', '.join(sorted(set(rows) ^ set(inventory))))
    return rows


def pipeline_hashes():
    paths = sorted(Path(__file__).parent.glob('*.py')) + [SCHEMA]
    return {str(p.relative_to(ROOT)): digest(p.read_bytes()) for p in paths}


def prepare(repo, matrix_path, run_id, cell_id, host, model, revision, evidence_kind, trials=3, selection=None):
    for label, value in [('run_id', run_id), ('cell_id', cell_id), ('host', host), ('model', model)]:
        nonempty(value, label)
    if not re.fullmatch('[0-9a-f]{40}', revision):
        raise EvidenceError('revision must be a full observed Git SHA')
    if evidence_kind not in {'offline-fixture', 'host-capture'} or type(trials) is not int or trials < 1:
        raise EvidenceError('invalid evidence kind/trial count')
    inventory = catalog(repo)
    rows = matrix(matrix_path, inventory)
    selected = sorted(selection if selection is not None else inventory)
    if not selected or len(set(selected)) != len(selected) or set(selected) - set(inventory):
        raise EvidenceError('unknown/duplicate/empty skill selection')
    excluded, cases = {}, []
    for name in selected:
        if not rows[name]['required'] and selection is None:
            excluded[name] = 'optional/not must-fire; explicitly select this skill to test it'
            continue
        if inventory[name]['claude_only'] and host != 'claude-code':
            excluded[name] = 'requires_claude_code: true; not a portable skill'
            continue
        for expected in ('positive', 'negative'):
            for trial in range(1, trials + 1):
                cases.append({'case_id': f'{name}:{expected}:{trial}', 'skill': name,
                              'expected': expected, 'trial': trial,
                              'mode': inventory[name]['mode'] if expected == 'positive' else 'automatic',
                              'query': rows[name][expected], 'phase': rows[name]['phase']})
    if not cases:
        raise EvidenceError('no eligible cases on this host')
    return {'schema_version': VERSION, 'binding': {'run_id': run_id, 'cell_id': cell_id,
            'host': host, 'model': model, 'revision': revision, 'evidence_kind': evidence_kind},
            'repo': str(repo.resolve()), 'matrix': str(matrix_path.resolve()),
            'matrix_sha256': digest(matrix_path.read_bytes()), 'catalog': inventory,
            'pipeline': pipeline_hashes(), 'selection': selected if selection is not None else None, 'exclusions': excluded,
            'trials': trials, 'cases': cases}


def validate_manifest(manifest):
    exact(manifest, {'schema_version', 'binding', 'repo', 'matrix', 'matrix_sha256', 'catalog',
                     'pipeline', 'selection', 'exclusions', 'trials', 'cases'}, 'manifest')
    if manifest['schema_version'] != VERSION:
        raise EvidenceError('unsupported manifest version')
    exact(manifest['binding'], {'run_id', 'cell_id', 'host', 'model', 'revision', 'evidence_kind'}, 'binding')
    # Re-derive every case and eligibility from frozen inputs, not mutable assertions.
    repo, matrix_path = Path(manifest['repo']), Path(manifest['matrix'])
    expected = prepare(repo, matrix_path, **manifest['binding'], trials=manifest['trials'], selection=manifest['selection'])
    if expected != manifest:
        raise EvidenceError('manifest drift: catalog, matrix, pipeline or planned cases changed')
    return manifest


def load_manifest(path):
    return validate_manifest(read_json(path))


def case_map(manifest):
    return {case['case_id']: case for case in manifest['cases']}


def normalize_native(protocol, raw, case, manifest):
    from adapters import normalize
    return normalize(protocol, raw, case, manifest, EvidenceError)


def native_capture(protocol, raw, case_id, manifest):
    case = case_map(manifest).get(case_id)
    if not case:
        raise EvidenceError('unplanned native case: ' + case_id)
    capture = {'binding': manifest['binding'], 'manifest_sha256': json_hash(manifest),
               'case_id': case_id, 'events': normalize_native(protocol, raw, case, manifest),
               'source': {'protocol': protocol, 'events': raw, 'sha256': json_hash(raw)}}
    return capture


def observe(capture, manifest):
    """Correlate exact call/result receipts; prose and coarse telemetry cannot pass."""
    keys = {'binding', 'manifest_sha256', 'case_id', 'events'}
    if isinstance(capture, dict) and 'source' in capture:
        keys.add('source')
    exact(capture, keys, 'capture')
    if capture['binding'] != manifest['binding'] or capture['manifest_sha256'] != json_hash(manifest):
        raise EvidenceError('capture is from another run/cell/model/revision/manifest')
    case = case_map(manifest).get(capture['case_id'])
    if not case:
        raise EvidenceError('unplanned case: ' + str(capture['case_id']))
    events = capture['events']
    if 'source' in capture:
        source = capture['source']
        exact(source, {'protocol', 'events', 'sha256'}, 'raw source')
        if source['sha256'] != json_hash(source['events']):
            raise EvidenceError('raw observer capture hash mismatch')
        if events != normalize_native(source['protocol'], source['events'], case, manifest):
            raise EvidenceError('normalized events disagree with retained host capture')
    if not isinstance(events, list) or len(events) < 2:
        raise EvidenceError('capture requires init and terminal events')
    exact(events[0], {'type', 'query', 'mode', 'tools'}, 'init')
    if (events[0]['type'] != 'init' or events[0]['query'] != case['query'] or events[0]['mode'] != case['mode']
            or not isinstance(events[0]['tools'], list) or not events[0]['tools']
            or any(not isinstance(t, str) or not t for t in events[0]['tools'])
            or len(set(events[0]['tools'])) != len(events[0]['tools'])):
        raise EvidenceError('init does not match planned query/mode/tool surface')
    tools = events[0]['tools']
    required_tool = 'skill' if case['mode'] in {'automatic', 'explicit'} else 'role_load'
    if required_tool not in tools:
        raise EvidenceError('required retrieval tool unavailable: ' + required_tool)
    exact(events[-1], {'type', 'status'}, 'terminal')
    if events[-1]['type'] != 'terminal' or events[-1]['status'] not in {'completed', 'blocked', 'error', 'timeout'}:
        raise EvidenceError('invalid terminal event')
    pending, used, retrieved, failed, errors = {}, set(), [], False, False
    for event in events[1:-1]:
        if not isinstance(event, dict):
            raise EvidenceError('event must be an object')
        event_type = event.get('type')
        if event_type == 'text':
            exact(event, {'type', 'text'}, 'text')
            if not isinstance(event['text'], str):
                raise EvidenceError('text must be a string')
            continue
        if event_type == 'error':
            exact(event, {'type', 'message'}, 'error')
            nonempty(event['message'], 'error message')
            errors = True
            continue
        if event_type == 'tool_call':
            exact(event, {'type', 'call_id', 'tool', 'skill', 'origin'}, 'tool_call')
            nonempty(event['call_id'], 'call_id')
            if event['call_id'] in used or event['tool'] not in tools:
                raise EvidenceError('duplicate call ID or unavailable tool')
            if event['skill'] not in manifest['catalog'] or event['skill'] in manifest['exclusions']:
                raise EvidenceError('unknown/ineligible retrieved skill')
            if event['tool'] not in {'skill', 'role_load', 'read_file'}:
                raise EvidenceError('unsupported retrieval tool')
            if event['origin'] not in {'model', 'user', 'orchestrator'}:
                raise EvidenceError('missing invocation origin')
            used.add(event['call_id'])
            pending[event['call_id']] = event
        elif event_type == 'tool_result':
            exact(event, {'type', 'call_id', 'tool', 'skill', 'status', 'content'}, 'tool_result')
            call = pending.pop(event['call_id'], None)
            if not call or (call['tool'], call['skill']) != (event['tool'], event['skill']):
                raise EvidenceError('uncorrelated tool result')
            if event['status'] not in {'success', 'refused', 'error'} or not isinstance(event['content'], str):
                raise EvidenceError('invalid retrieval result')
            if event['status'] != 'success':
                failed = True
                errors |= event['status'] == 'error'
                continue
            info = manifest['catalog'][event['skill']]
            if digest(event['content'].encode()) not in {info['sha256'], info['body_sha256']}:
                raise EvidenceError('retrieved content does not match frozen candidate bytes')
            # Direct file reads are recorded, but never count as automatic selection.
            valid_mode = (case['mode'] == 'automatic' and call['tool'] == 'skill' and call['origin'] == 'model'
                          or case['mode'] == 'explicit' and call['tool'] == 'skill' and call['origin'] == 'user'
                          or case['mode'] == 'dispatch' and call['tool'] == 'role_load' and call['origin'] == 'orchestrator')
            retrieved.append({'skill': call['skill'], 'call_id': call['call_id'], 'tool': call['tool'],
                              'origin': call['origin'], 'counts_for_mode': bool(valid_mode)})
        else:
            raise EvidenceError('unsupported/interior terminal event: ' + str(event_type))
    if pending:
        raise EvidenceError('unfinished tool calls')
    status = events[-1]['status']
    if status in {'error', 'timeout'} or errors:
        outcome = 'execution-error'
    elif status == 'blocked' or failed:
        outcome = 'blocked'
    else:
        target = [r for r in retrieved if r['skill'] == case['skill']]
        success = (any(r['counts_for_mode'] for r in target) if case['expected'] == 'positive' else not target)
        outcome = 'pass' if success else 'fail'
    return {'schema_version': VERSION, 'manifest_sha256': json_hash(manifest),
            'case_id': case['case_id'], 'skill': case['skill'], 'expected': case['expected'],
            'mode': case['mode'], 'outcome': outcome, 'retrievals': retrieved,
            'capture_sha256': json_hash(capture), 'capture': capture}


def validate_receipt(receipt, manifest):
    try:
        import jsonschema
    except ImportError as exc:
        raise EvidenceError('jsonschema is required; refusing an advisory-only check') from exc
    try:
        jsonschema.Draft202012Validator(read_json(SCHEMA)).validate(receipt)
    except jsonschema.ValidationError as exc:
        raise EvidenceError('invalid v2 receipt: ' + exc.message) from exc
    expected = observe(receipt['capture'], manifest)
    if receipt != expected:
        raise EvidenceError('receipt counters/proof modified; replay does not agree')
    return receipt


def record(captures, manifest):
    results, seen = [], set()
    for capture in captures:
        receipt = observe(capture, manifest)
        if receipt['case_id'] in seen:
            raise EvidenceError('duplicate case receipt: ' + receipt['case_id'])
        seen.add(receipt['case_id'])
        validate_receipt(receipt, manifest)
        results.append(receipt)
    return sorted(results, key=lambda r: r['case_id'])


def grade(receipts, manifest):
    seen, tools = {}, set()
    for receipt in receipts:
        validate_receipt(receipt, manifest)
        if receipt['case_id'] in seen:
            raise EvidenceError('duplicate case receipt: ' + receipt['case_id'])
        seen[receipt['case_id']] = receipt
        tools.add(tuple(sorted(receipt['capture']['events'][0]['tools'])))
    if len(tools) > 1:
        raise EvidenceError('tool surface changed mid-cell')
    missing = sorted(set(case_map(manifest)) - set(seen))
    findings = [{'case_id': case, 'status': 'missing'} for case in missing]
    findings += [{'case_id': case, 'status': r['outcome']} for case, r in sorted(seen.items()) if r['outcome'] != 'pass']
    verdict = 'FAIL' if findings else 'FIXTURE_PASS' if manifest['binding']['evidence_kind'] == 'offline-fixture' else 'RECORDED_CASES_PASS'
    if verdict == 'RECORDED_CASES_PASS' and manifest['trials'] < 3:
        verdict = 'INSUFFICIENT_TRIALS'
        findings.append({'case_id': '*', 'status': 'fewer than three trials; smoke only'})
    counts = Counter(r['outcome'] for r in seen.values())
    modes = {}
    for mode in sorted(MODES):
        positives = [case for case in manifest['cases'] if case['expected'] == 'positive' and case['mode'] == mode]
        skills = sorted({case['skill'] for case in positives})
        covered = [name for name in skills if all(seen.get(case['case_id'], {}).get('outcome') == 'pass' for case in positives if case['skill'] == name)]
        modes[mode] = {'planned_skills': len(skills), 'proven_skills': len(covered), 'skills': covered}
    return {'schema_version': VERSION, 'binding': manifest['binding'], 'manifest_sha256': json_hash(manifest),
            'scope': 'full-catalog' if manifest['selection'] is None or set(manifest['selection']) == set(manifest['catalog']) else 'selected-subset',
            'planned_cases': len(manifest['cases']), 'recorded_cases': len(seen), 'outcomes': dict(counts),
            'invocation_modes': modes, 'negative_controls_passed': sum(r['expected'] == 'negative' and r['outcome'] == 'pass' for r in seen.values()),
            'excluded_skills': manifest['exclusions'], 'verdict': verdict, 'findings': findings,
            'live_model_capability': 'NOT_ESTABLISHED' if manifest['binding']['evidence_kind'] == 'offline-fixture' else 'observed cases only; not efficacy or universal cross-model certification',
            'observer_trust': 'raw captures must come from a trusted host observer; hashes detect drift, not fabricated source events',
            'efficacy': 'UNVERIFIED', 'safety_and_degradation': 'UNVERIFIED', 'trajectory': 'not used for acceptance'}


def report(summary):
    lines = ['# Gauntlet II — evidence-bound coverage', '', f"**Verdict: {summary['verdict']}**", '',
             f"Scope: {summary['scope']} · recorded cases: {summary['recorded_cases']}/{summary['planned_cases']}", '',
             f"Live model capability: {summary['live_model_capability']}", '',
             'Efficacy and safety/degradation are UNVERIFIED by this selection grader.', '',
             '| Invocation mode | Planned skills | Proven across positive trials |', '|---|---|---|']
    for mode, values in summary['invocation_modes'].items():
        lines.append(f"| {mode} | {values['planned_skills']} | {values['proven_skills']} |")
    lines += ['', f"Negative controls passed: {summary['negative_controls_passed']}", '',
              '## Findings and proposed intake', '', '| Case | Status |', '|---|---|']
    for finding in summary['findings']:
        # Input-derived text cannot inject table rows/HTML into the report.
        case = json.dumps(finding['case_id']).replace('|', '&#124;').replace('<', '&lt;').replace('>', '&gt;')
        lines.append(f"| `{case}` | {finding['status']} |")
    if not summary['findings']:
        lines.append('| — | no case failures; scope and evidence-kind limitations still apply |')
    return '\n'.join(lines) + '\n'


def write_new(path, text):
    """Never overwrite earlier evidence, a frozen plan, or a symlink."""
    with Path(path).open('x', encoding='utf-8') as handle:
        handle.write(text)
