"""Freebuff host for skill-creator trigger evals: offline, no provider calls.

The live path (bun + Codebuff checkout + endpoint) runs only when
ATS_CODEBUFF_DIR and ATS_FREEBUFF_MOCK_URL point at a checkout and a fake
OpenAI-compatible server; CI exercises the trace scorer and the guards.
"""
import json
import os
from pathlib import Path
import sys

import pytest

ROOT = Path(__file__).resolve().parents[2]
SKILL = ROOT / 'skills/workflows/skill-creator'
sys.path.insert(0, str(SKILL))
from scripts.run_eval import observe_freebuff_trace, run_eval, run_single_query_freebuff


def trace(*events, model='pinned', result=None):
    head = dict(type='init', model=model, agent='freebuff-root-eval', snapshot_commit='abc123')
    tail = result or dict(type='result', exit_code=0, error=None)
    return '\n'.join(json.dumps(e) for e in [head, *events, tail])


def load(name='candidate', content='---\nname: candidate\n---\nbody', description='Use it.', call_id='c1'):
    return [dict(type='tool_call', toolCallId=call_id, toolName='skill', input={'name': name}),
            dict(type='tool_result', toolCallId=call_id, toolName='skill',
                 output=[{'type': 'json', 'value': {'name': name, 'description': description, 'content': content}}])]


def test_loaded_candidate_counts_as_trigger():
    result = observe_freebuff_trace(trace(*load()), 'candidate', 'pinned')
    assert result['status'] == 'success' and result['triggered'] is True
    assert result['retrieval_evidence'][0]['tool_call_id'] == 'c1'
    assert result['snapshot_commit'] == 'abc123'


@pytest.mark.parametrize('events', [
    [],
    load(name='other-skill'),
    [dict(type='tool_call', toolCallId='r1', toolName='read_files', input={'paths': ['SKILL.md']}),
     dict(type='tool_result', toolCallId='r1', toolName='read_files', output=[])],
    [dict(type='text', text='I will use the candidate skill now')],
])
def test_mentions_reads_and_other_skills_are_not_triggers(events):
    result = observe_freebuff_trace(trace(*events), 'candidate', 'pinned')
    assert result['status'] == 'success' and result['triggered'] is False


def test_freebuff_refusal_is_an_error_not_a_trigger():
    refused = load(description='', content="Error: Skill 'candidate' can only be invoked by the user.")
    result = observe_freebuff_trace(trace(*refused), 'candidate', 'pinned')
    assert result['triggered'] is None and 'refused' in result['error_message']


@pytest.mark.parametrize('raw,needle', [
    ('', 'empty'),
    (trace(*load(), model='other'), 'model'),
    (trace(*load(), result=dict(type='result', exit_code=1, error='timeout')), 'timeout'),
    (trace(dict(type='error', message='provider down')), 'execution error'),
    (trace(load()[0]), 'unfinished'),
    (trace(load()[1]), 'Uncorrelated'),
    (json.dumps(dict(type='result', exit_code=1, error='MOCK_KEY is too short')), 'before starting'),
])
def test_broken_traces_never_score(raw, needle):
    result = observe_freebuff_trace(raw, 'candidate', 'pinned')
    assert result['triggered'] is None and needle in result['error_message']


def test_recoverable_stream_error_does_not_void_the_run():
    retry = dict(type='error', message='stream cut', source='stream-interrupted')
    result = observe_freebuff_trace(trace(retry, *load()), 'candidate', 'pinned')
    assert result['status'] == 'success' and result['triggered'] is True


def write_skill(root, extra=''):
    folder = root / 'candidate'
    folder.mkdir()
    (folder / 'SKILL.md').write_text('---\nname: candidate\ndescription: Use it.\n%s---\nbody\n' % extra)
    return folder


def test_user_only_candidate_is_refused_before_any_run(tmp_path):
    folder = write_skill(tmp_path, 'disable-model-invocation: true\n')
    result = run_single_query_freebuff('q', 'candidate', str(folder), 'Use it.', 30, 'pinned', {})
    assert result['triggered'] is None and 'disable-model-invocation' in result['error_message']


def test_missing_checkout_or_endpoint_blocks(tmp_path):
    folder = write_skill(tmp_path)
    result = run_single_query_freebuff('q', 'candidate', str(folder), 'Use it.', 30, 'pinned', {'codebuff_dir': str(tmp_path)})
    assert result['triggered'] is None and 'Codebuff checkout' in result['error_message']


def test_unknown_host_is_rejected(tmp_path):
    folder = write_skill(tmp_path)
    with pytest.raises(ValueError, match='host'):
        run_eval([{'query': 'q', 'should_trigger': True}], 'candidate', 'Use it.', str(folder), 1, 30, 1, 0.5, 'pinned', host='other')


def test_snapshot_is_freebuff_root_with_skill_tool():
    snapshot = json.loads((SKILL / 'assets/freebuff-root-agent.json').read_text())
    definition = snapshot['definition']
    assert snapshot['license'] == 'Apache-2.0' and len(snapshot['source_commit']) == 40
    assert 'skill' in definition['toolNames'] and 'ask_user' not in definition['toolNames']
    assert 'Freebuff' in definition['systemPrompt']


@pytest.mark.skipif(not (os.environ.get('ATS_CODEBUFF_DIR') and os.environ.get('ATS_FREEBUFF_MOCK_URL')),
                    reason='live Freebuff engine check needs ATS_CODEBUFF_DIR and a fake endpoint')
def test_live_engine_against_fake_endpoint(tmp_path, monkeypatch):
    monkeypatch.setenv('ATS_MOCK_KEY', 'mock-key-0123456789abcdef')
    folder = tmp_path / 'demo-skill'
    folder.mkdir()
    (folder / 'SKILL.md').write_text('---\nname: demo-skill\ndescription: Demo skill.\n---\nSay hi.\n')
    config = {'codebuff_dir': os.environ['ATS_CODEBUFF_DIR'], 'base_url': os.environ['ATS_FREEBUFF_MOCK_URL'],
              'provider': 'openai-compatible', 'api_key_env': 'ATS_MOCK_KEY'}
    result = run_single_query_freebuff('use the demo skill', 'demo-skill', str(folder), 'Demo skill.', 90, 'mock-model', config)
    assert result['status'] == 'success' and result['triggered'] is True, result
    assert result['tools'] == ['skill']


def test_optimizer_endpoint_posts_one_chat_completion(monkeypatch):
    """The Freebuff host's optimizer needs no Hermes: one local HTTP round trip."""
    import http.server
    import threading
    from scripts.improve_description import _call_openai_compatible

    seen = {}

    class Handler(http.server.BaseHTTPRequestHandler):
        def do_POST(self):
            seen['path'] = self.path
            seen['auth'] = self.headers.get('Authorization')
            seen['body'] = json.loads(self.rfile.read(int(self.headers['Content-Length'])))
            payload = json.dumps({'choices': [{'message': {'content': '<new_description>Better.</new_description>'}}]}).encode()
            self.send_response(200)
            self.send_header('Content-Type', 'application/json')
            self.send_header('Content-Length', str(len(payload)))
            self.end_headers()
            self.wfile.write(payload)

        def log_message(self, *args):
            pass

    server = http.server.HTTPServer(('127.0.0.1', 0), Handler)
    threading.Thread(target=server.serve_forever, daemon=True).start()
    try:
        monkeypatch.setenv('ATS_OPT_KEY', 'opt-key-0123456789')
        endpoint = {'base_url': 'http://127.0.0.1:%d/v1/' % server.server_port, 'api_key_env': 'ATS_OPT_KEY'}
        text = _call_openai_compatible('improve this', 'pinned-model', endpoint, timeout=10)
    finally:
        server.shutdown()
    assert text == '<new_description>Better.</new_description>'
    assert seen['path'] == '/v1/chat/completions' and seen['auth'] == 'Bearer opt-key-0123456789'
    assert seen['body']['model'] == 'pinned-model' and seen['body']['messages'][0]['content'] == 'improve this'


def test_optimizer_endpoint_requires_key(monkeypatch):
    from scripts.improve_description import _call_openai_compatible
    monkeypatch.delenv('ATS_MISSING_KEY', raising=False)
    with pytest.raises(ValueError, match='api_key_env'):
        _call_openai_compatible('p', 'm', {'base_url': 'http://127.0.0.1:9/v1', 'api_key_env': 'ATS_MISSING_KEY'})


def test_agent_process_gets_only_allowlisted_env(tmp_path, monkeypatch):
    """No inherited secrets: PATH/locale/temp plus the one endpoint key."""
    import subprocess as sp
    from scripts import run_eval as module

    checkout = tmp_path / 'codebuff'
    (checkout / 'sdk/src').mkdir(parents=True)
    (checkout / 'sdk/src/index.ts').write_text('')
    (checkout / 'node_modules').mkdir()
    folder = write_skill(tmp_path)
    monkeypatch.setenv('ATS_ENDPOINT_KEY', 'endpoint-key-0123456789')
    monkeypatch.setenv('GITHUB_TOKEN', 'must-not-leak')
    monkeypatch.setenv('NEXT_PUBLIC_CB_ENVIRONMENT', 'dev')
    monkeypatch.setattr(module.shutil, 'which', lambda name: '/usr/bin/' + name)
    captured = {}

    def fake_run(cmd, **kwargs):
        captured.update(kwargs)
        return sp.CompletedProcess(cmd, 0, stdout=trace(*load(), model='pinned'), stderr='')

    monkeypatch.setattr(module.subprocess, 'run', fake_run)
    config = {'codebuff_dir': str(checkout), 'base_url': 'http://127.0.0.1:9/v1',
              'provider': 'openai-compatible', 'api_key_env': 'ATS_ENDPOINT_KEY'}
    result = run_single_query_freebuff('q', 'candidate', str(folder), 'Use it.', 30, 'pinned', config)
    env = captured['env']
    assert result['status'] == 'success'
    assert env['ATS_ENDPOINT_KEY'] == 'endpoint-key-0123456789'
    assert 'GITHUB_TOKEN' not in env and 'NEXT_PUBLIC_CB_ENVIRONMENT' not in env
    assert env['HOME'] != os.environ.get('HOME') and env['HOME'] == env['USERPROFILE']
    assert set(env) <= {'PATH', 'LANG', 'LC_ALL', 'TMPDIR', 'SYSTEMROOT', 'ATS_ENDPOINT_KEY', 'HOME',
                        'USERPROFILE', 'XDG_CONFIG_HOME', 'XDG_CACHE_HOME', 'AI_SDK_LOG_WARNINGS'}
