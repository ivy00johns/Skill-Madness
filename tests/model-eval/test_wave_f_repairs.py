"""Regression tests for scoped audit repairs, no remote mutations or model calls."""
import copy
import json
from pathlib import Path
import subprocess
import sys

import jsonschema
import pytest
import yaml

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / 'scripts/lib'))
sys.path.insert(0, str(ROOT / 'skills/workflows/skill-creator'))
from standard_export import export, load
from scripts.check_matrix import check_cell
from resource_delivery import source_diagnostics


def test_standard_export_preserves_native_source_and_body():
    original = '---\nname: test-skill\nversion: 1.0.0\ndescription: Use this test.\nallowed-tools: [Read, Bash]\nmetadata: {flag: true, tags: [one]}\nfuture-field: {x: 1}\n---\n# Body\nexact bytes\n'
    native, body = load(original)
    data, exported_body = load(export(original))
    assert native['allowed-tools'] == ['Read', 'Bash']
    assert data['allowed-tools'] == 'Read Bash'
    assert all(isinstance(v, str) for v in data['metadata'].values())
    assert json.loads(data['metadata']['psfs.future-field']) == {'x': 1}
    assert exported_body == body
    assert load(original)[0] == native


@pytest.mark.parametrize('name', ['trailing-', 'double--dash', 'Upper', '-first'])
def test_invalid_names_block_export_and_author_schema(name):
    data = {'name': name, 'description': 'Use test.', 'version': '1.0.0'}
    with pytest.raises(ValueError): export('---\n' + yaml.safe_dump(data) + '---\nbody')
    with pytest.raises(jsonschema.ValidationError): jsonschema.validate(data, json.loads((ROOT / 'spec/frontmatter.schema.json').read_text()))


def cell():
    return {'run_id': 'offline', 'task_id': 'load-fixture', 'layer': 'load',
            'skill_hash': '1'*64, 'baseline_hash': '2'*64, 'verifier_hash': '3'*64,
            'host': {'name': 'gemini-cli', 'version': 'fixture'}, 'model': {'id': None},
            'split': 'dev', 'falsifier': 'missing installed helper',
            'limits': {'max_calls': 1, 'max_seconds': 120, 'max_cost_usd': 0},
            'trajectory': {'calls': 0, 'seconds': 1, 'cost_usd': 0},
            'outcome': 'pass', 'proof': 'pass', 'architecture': 'pass',
            'status': 'success', 'evidence_kind': 'offline-fixture'}


def test_matrix_cli_and_no_universal_claim(tmp_path):
    record = cell()
    result = check_cell(record)
    assert result['accepted'] and not result['capability_claim']
    filename = tmp_path / 'cells.json'
    filename.write_text(json.dumps([record]))
    command = [sys.executable, '-m', 'scripts.check_matrix', str(filename)]
    run = subprocess.run(command, cwd=ROOT / 'skills/workflows/skill-creator', capture_output=True, text=True)
    assert run.returncode == 0 and json.loads(run.stdout)[0]['accepted']
    record['trajectory']['seconds'] = 121
    filename.write_text(json.dumps([record]))
    run = subprocess.run(command, cwd=ROOT / 'skills/workflows/skill-creator', capture_output=True, text=True)
    assert run.returncode == 2


@pytest.mark.parametrize('mutation', ['error', 'forced', 'no-proof', 'holdout', 'worker', 'cost', 'trial'])
def test_matrix_disqualifiers(mutation):
    r = cell()
    r.update(layer='efficacy', split='held_out_test', retrieval_proof='trace-hash',
             test_touches=1, trials=3, baseline_host=r['host'], baseline_model=r['model'])
    if mutation == 'error': r['status'] = 'timeout'
    if mutation == 'forced': r['forced'] = True
    if mutation == 'no-proof': r['retrieval_proof'] = None
    if mutation == 'holdout': r['test_touches'] = 2
    if mutation == 'worker': r['baseline_model'] = {'id': 'changed'}
    if mutation == 'cost': r['trajectory']['cost_usd'] = None
    if mutation == 'trial': r['trials'] = 1
    assert not check_cell(r)['accepted']


@pytest.mark.parametrize('mutation', ['shape', 'limits', 'usage', 'nan', 'infinity', 'boolean-cost', 'unknown-layer', 'unknown-kind', 'trials', 'live-model'])
def test_matrix_malformed_receipts_fail_closed(mutation):
    r = cell()
    if mutation == 'shape': r = []
    if mutation == 'limits': r['limits'] = 'no limits'
    if mutation == 'usage': r['trajectory'] = []
    if mutation == 'nan': r['trajectory']['seconds'] = float('nan')
    if mutation == 'infinity': r['limits']['max_seconds'] = float('inf')
    if mutation == 'boolean-cost': r['trajectory']['cost_usd'] = False
    if mutation == 'unknown-layer': r['layer'] = 'universal'
    if mutation == 'unknown-kind': r['evidence_kind'] = 'imagined'
    if mutation == 'trials': r.update(layer='efficacy', trials='many')
    if mutation == 'live-model': r['evidence_kind'] = 'live-host'
    assert not check_cell(r)['accepted']


def test_matrix_cli_invalid_container_and_negative_trigger(tmp_path):
    filename = tmp_path / 'cells.json'
    for invalid in ('{}', '[]', 'invalid JSON'):
        filename.write_text(invalid)
        run = subprocess.run([sys.executable, '-m', 'scripts.check_matrix', str(filename)],
                             cwd=ROOT / 'skills/workflows/skill-creator', capture_output=True, text=True)
        assert run.returncode == 2 and not json.loads(run.stdout)['accepted']
        assert 'Traceback' not in run.stderr
    r = cell()
    r.update(layer='trigger', should_trigger=False, forced=False)
    assert check_cell(r)['accepted']
    r['forced'] = True
    assert not check_cell(r)['accepted']


def test_resource_closure_lint_through_cli(tmp_path):
    skill = tmp_path / 'test-skill'
    skill.mkdir()
    md = skill / 'SKILL.md'
    md.write_text('---\nname: test-skill\nversion: 1.0.0\ndescription: Use when testing.\n---\n# Test\nRun `scripts/check.py` and read `references/missing.md`.\n')
    (skill / 'scripts').mkdir()
    (skill / 'scripts/check.py').write_text('print("local")\n')
    assert source_diagnostics(md)['missing'] == ['references/missing.md']
    command = ['bash', str(ROOT / 'scripts/lint-skills.sh'), '--verbose', str(md)]
    run = subprocess.run(command, capture_output=True, text=True)
    assert run.returncode == 1 and 'missing literal local resource' in run.stdout
    (skill / 'references').mkdir()
    (skill / 'references/missing.md').write_text('# Real reference\n')
    run = subprocess.run(command, capture_output=True, text=True)
    assert run.returncode == 0 and 'source resource closure' in run.stdout
    assert 'physical lines' in run.stdout and 'nonblank lines' in run.stdout
    (skill / 'scripts/check.py').unlink()
    (skill / 'scripts/check.py').symlink_to(md)
    run = subprocess.run(command, capture_output=True, text=True)
    assert run.returncode == 1 and 'resource inspection blocked' in run.stdout


def test_capture_limits_through_real_node_interface(tmp_path):
    script = ROOT / 'skills/workflows/website-walkthrough-video/scripts/capture.mjs'
    code = f"import {{checkCaptureBounds}} from {json.dumps(script.as_uri())}; checkCaptureBounds(1440,8000); for(const dims of [[1440,8001],[1440,4001,2],[100000,8000]]){{let refused=false;try{{checkCaptureBounds(...dims)}}catch{{refused=true}}if(!refused)process.exit(2)}}"
    result = subprocess.run(['node', '--input-type=module', '-e', code], capture_output=True, text=True)
    assert result.returncode == 0, result.stderr
    config = tmp_path / 'site.json'
    config.write_text(json.dumps({'baseUrl': 'http://127.0.0.1:1', 'outDir': str(tmp_path / 'out'), 'routes': ['/']*21}))
    result = subprocess.run(['node', str(script), '--config', str(config)], capture_output=True, text=True)
    assert result.returncode != 0 and '1–20 routes' in result.stderr
    assert not (tmp_path / 'out/manifest.json').exists()


def test_consent_freshness_and_native_sequential_contracts():
    read = lambda p: (ROOT / p).read_text()
    assert 'Author replies are context only' in read('skills/git/git-pr-feedback/SKILL.md')
    assert 'default scan and `--dry-run` are read-only' in read('skills/git/git-post-merge-cleanup/SKILL.md')
    assert 'Missing answer means BLOCKED' in read('skills/workflows/maintain-context/SKILL.md')
    assert 'source commit/hash' in read('skills/workflows/llm-wiki/SKILL.md')
    assert 'Skill activation' in read('skills/workflows/artifact-publish/SKILL.md')
    assert 'BUILD_SLICE role packet authorizes implementation' in read('skills/orchestrator/SKILL.md')
