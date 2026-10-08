"""Offline Wave E behavioral regressions: no provider calls or real-HOME writes."""
import json
import os
from pathlib import Path
import subprocess
import sys
from unittest.mock import patch

import pytest
import yaml

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / 'skills/workflows/skill-creator'))
from scripts.run_eval import observe_trace, run_single_query, run_eval
from scripts.run_loop import split_eval_set_hygiene, run_loop, claim_holdout
from scripts.utils import update_skill_description
from scripts.generate_report import generate_html


def trace(*events, model='pinned'):
    return '\n'.join(json.dumps(e) for e in [dict(type='system', subtype='init', model=model), *events, dict(type='result', exit_code=0)])


def retrieval(name='candidate', success=True):
    return [dict(type='tool_use', name='skill_view', tool_call_id='c1', input={'name': name}),
            dict(type='tool_result', name='skill_view', tool_call_id='c1', output=json.dumps({'success': success, 'name': name}), is_error=False)]


@pytest.mark.parametrize('events,expected', [
    (retrieval(), True),
    ([dict(type='text', text='candidate')], False),
    ([dict(type='tool_use', name='skills_list', input={}), dict(type='tool_result', name='skills_list', output='candidate')], False),
    (retrieval('candidate-other'), False),
])
def test_exact_successful_retrieval_only(events, expected):
    result = observe_trace(trace(*events), 'candidate', 'pinned')
    assert result['status'] == 'success'
    assert result['triggered'] is expected


@pytest.mark.parametrize('raw', [
    'candidate', '{}', trace(*retrieval(success=False)), trace(model='changed'),
    trace(dict(type='tool_use', name='skill_view', input={'name': 'candidate'})),
    trace(*retrieval()) + '\n' + json.dumps(dict(type='result', exit_code=1)),
])
def test_invalid_trace_is_error(raw):
    assert observe_trace(raw, 'candidate', 'pinned')['triggered'] is None


def test_snapshot_subprocess_boundary(tmp_path, monkeypatch):
    source = tmp_path / 'candidate'
    source.mkdir()
    original = '---\nname: candidate\ndescription: old\nversion: 1.0.0\n---\n# Body\n'
    (source / 'SKILL.md').write_text(original)
    monkeypatch.setenv('HERMES_HOME', '/do-not-touch')
    seen = []
    def worker(cmd, **kwargs):
        env = kwargs['env']
        home = Path(env['HERMES_HOME'])
        content = (home / 'skills/candidate/SKILL.md').read_text()
        candidate = yaml.safe_load(content.split('---')[1])['description']
        seen.append((candidate, str(home)))
        assert '-s' not in cmd and '-m' in cmd
        assert kwargs['input'] == 'query'
        assert str(tmp_path) not in str(kwargs['cwd'])
        assert home != Path('/do-not-touch')
        assert (home / '.no-bundled-skills').exists()
        return subprocess.CompletedProcess(cmd, 0, trace(*retrieval()), '')
    with patch('scripts.run_eval.subprocess.run', side_effect=worker):
        for candidate in ('first: "quoted"', 'second \\ candidate'):
            assert run_single_query('query', 'candidate', str(source), candidate, 10, 'pinned')['triggered'] is True
    assert seen[0][0] != seen[1][0] and seen[0][1] != seen[1][1]
    assert all(not Path(home).exists() for _, home in seen)
    assert (source / 'SKILL.md').read_text() == original


def test_errors_never_become_passing_negatives():
    with patch('scripts.run_eval.run_single_query', return_value={'status': 'timeout', 'triggered': None}):
        result = run_eval([{'query': 'negative', 'should_trigger': False}], 'candidate', 'description', '.', 1, 1, model='pinned')
    assert result['summary'] == {'total': 1, 'passed': 0, 'failed': 0, 'errored': 1}
    assert result['results'][0]['pass'] is None


def items():
    return [{'query': f'real task {i}', 'should_trigger': i % 2 == 0, 'provenance': 'real'} for i in range(60)]


def test_splits_stable_across_order_subsets_and_synthetic():
    tasks = items()
    original = split_eval_set_hygiene(tasks, .3)
    reverse = split_eval_set_hygiene(list(reversed(tasks)), .3)
    assert [{i['query'] for i in s} for s in original] == [{i['query'] for i in s} for s in reverse]
    for item in tasks:
        assigned = split_eval_set_hygiene([item], .3)
        assert next(j for j,s in enumerate(assigned) if s) == next(j for j,s in enumerate(original) if item in s)
    synthetic = [{'query': 'generated', 'should_trigger': True}]
    assert split_eval_set_hygiene(synthetic, .3) == (synthetic, [], [])


def test_loop_selects_dev_then_burns_holdout_once(tmp_path):
    source = tmp_path / 'candidate'
    source.mkdir()
    (source / 'SKILL.md').write_text('---\nname: candidate\ndescription: original\n---\n# Body\n')
    train, dev, test = split_eval_set_hygiene(items(), .3)
    calls = []
    def evaluate(tasks, name, description, *args):
        calls.append((tasks, description))
        passed = tasks == test or (tasks == dev and description == 'better')
        results = [dict(i, pass_=passed, triggers=0, runs=1, valid_runs=1, errors=0) for i in tasks]
        for result in results: result['pass'] = result.pop('pass_')
        return {'results': results, 'summary': {'passed': len(tasks) if passed else 0, 'failed': 0 if passed else len(tasks), 'total': len(tasks), 'errored': 0}}
    def improve(*args, **kwargs):
        assert all(json.dumps(i['query']) not in json.dumps(args) for i in test + dev)
        return 'better'
    state = tmp_path / 'consumed'
    with patch('scripts.run_loop.run_eval', side_effect=evaluate), patch('scripts.run_loop.improve_description', side_effect=improve):
        output = run_loop(items(), source, None, 1, 10, 2, 1, .5, .3, 'pinned', False, holdout_state_dir=state)
        assert output['best_description'] == 'better'
        assert [tasks for tasks, _ in calls].count(test) == 1
        assert calls[-1] == (test, 'better')
        with pytest.raises(ValueError, match='already consumed'):
            claim_holdout(test[:1], state, 'third')
    page = generate_html(output, skill_name='candidate')
    assert 'Dev' in page and 'Final held-out test' in page and 'better' in page


def test_loop_stops_on_execution_error_without_optimizing(tmp_path):
    source = tmp_path / 'candidate'
    source.mkdir()
    (source / 'SKILL.md').write_text('---\nname: candidate\ndescription: old\n---\nbody')
    with patch('scripts.run_loop.run_eval', return_value={'summary': {'errored': 1}}), patch('scripts.run_loop.improve_description') as improve:
        out = run_loop(items(), source, None, 1, 1, 2, 1, .5, .3, 'pinned', False, holdout_state_dir=tmp_path / 'state')
    improve.assert_not_called()
    assert out['exit_reason'] == 'execution_error' and not out['test_touched_once']


def test_train_only_calibration_cannot_reuse_frozen_test(tmp_path):
    from scripts.run_loop import freeze_splits
    source = tmp_path / 'candidate'
    source.mkdir()
    (source / 'SKILL.md').write_text('---\nname: candidate\ndescription: old\n---\nbody')
    train, dev, test = split_eval_set_hygiene(items(), .3)
    state = tmp_path / '.workspaces/candidate/heldout-consumed'
    freeze_splits(train, dev, test, state)
    with patch('scripts.run_loop.Path.cwd', return_value=tmp_path), patch('scripts.run_loop.run_eval') as evaluator:
        with pytest.raises(ValueError, match='Frozen split'):
            run_loop(items(), source, None, 1, 1, 1, 1, .5, 0, 'pinned', False)
    evaluator.assert_not_called()


def test_corrupt_exact_session_database_is_operational_error(tmp_path):
    database = tmp_path / 'state.db'
    database.write_bytes(b'not SQLite')
    events = retrieval()
    events[1]['output'] = '{truncated'
    records = [json.loads(line) for line in trace(*events).splitlines()]
    records[-1]['session_id'] = 'session'
    result = observe_trace('\n'.join(json.dumps(r) for r in records), 'candidate', 'pinned', database)
    assert result['status'] == 'error' and result['triggered'] is None


def test_description_yaml_roundtrip():
    original = '---\nname: candidate\ndescription: old\n---\nBODY\n'
    for value in ('quote " slash \\ colon: yes', 'line one\nline two'):
        output = update_skill_description(original, value)
        assert yaml.safe_load(output.split('---')[1])['description'] == value
        assert output.endswith('BODY\n')


def test_frozen_splits_prevent_ratio_or_provenance_leak(tmp_path):
    from scripts.run_loop import freeze_splits
    train, dev, test = split_eval_set_hygiene(items(), .3)
    freeze_splits(train, dev, test, tmp_path)
    with pytest.raises(ValueError, match='Frozen split'):
        freeze_splits(train + test[:1], dev, test[1:], tmp_path)


def test_truncated_trace_uses_exact_session_tool_result_only(tmp_path):
    import sqlite3
    database = tmp_path / 'state.db'
    with sqlite3.connect(database) as db:
        db.execute('CREATE TABLE messages(session_id TEXT,role TEXT,tool_call_id TEXT,tool_name TEXT,content TEXT)')
        db.execute('INSERT INTO messages VALUES(?,?,?,?,?)', ('session', 'tool', 'c1', 'skill_view', json.dumps({'success': True, 'name': 'candidate'})))
    events = retrieval()
    events[1]['output'] = '{truncated...'
    raw = trace(*events)
    records = [json.loads(line) for line in raw.splitlines()]
    records[-1]['session_id'] = 'session'
    raw = '\n'.join(json.dumps(r) for r in records)
    assert observe_trace(raw, 'candidate', 'pinned', database)['triggered'] is True
    records[-1]['session_id'] = 'wrong-session'
    raw = '\n'.join(json.dumps(r) for r in records)
    assert observe_trace(raw, 'candidate', 'pinned', database)['triggered'] is None
