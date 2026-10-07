"""Offline only: fake observer events, temporary catalogs, no provider calls."""
import copy
import importlib.util
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / 'scripts/gauntlet'))
import pipeline as p


class Pipeline(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix='gauntlet-offline-')
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.repo = self.root / 'repo'
        self.skill('alpha')
        self.skill('role', category='roles', extra='disable-model-invocation: true\nuser-invocable: false\n')
        self.skill('explicit', extra='disable-model-invocation: true\n')
        self.skill('native', extra='requires_claude_code: true\n')
        self.matrix = self.root / 'matrix.md'
        self.matrix.write_text('# Coverage\n\n| Skill | Phase | Legitimate trigger | Must-fire | Near-miss |\n|---|---|---|---|---|\n' + ''.join(
            f'| {name} | P3 | perform {name} task | yes | explain {name} concept |\n' for name in ('alpha', 'explicit', 'native', 'role')))
        self.manifest = p.prepare(self.repo, self.matrix, 'run', 'cell', 'claude-code', 'pinned', 'a' * 40, 'offline-fixture', 3)

    def skill(self, name, category='workflows', extra=''):
        path = self.repo / 'skills' / category / name / 'SKILL.md'
        path.parent.mkdir(parents=True)
        path.write_text(f'---\nname: {name}\nversion: 1.0.0\ndescription: Use for {name}.\n{extra}---\n# {name}\nInstructions.\n')
        return path

    def capture(self, case=None, retrieval=True, status='completed', result_status='success', tool=None, origin=None):
        case = case or self.manifest['cases'][0]
        mode = case['mode']
        tool = tool or ('role_load' if mode == 'dispatch' else 'skill')
        origin = origin or {'automatic': 'model', 'explicit': 'user', 'dispatch': 'orchestrator'}[mode]
        events = [{'type': 'init', 'query': case['query'], 'mode': mode, 'tools': ['skill', 'role_load', 'read_file']},
                  {'type': 'text', 'text': f"I used {case['skill']}"}]
        if retrieval:
            text = (self.repo / self.manifest['catalog'][case['skill']]['path']).read_text()
            events += [{'type': 'tool_call', 'call_id': 'c1', 'tool': tool, 'skill': case['skill'], 'origin': origin},
                       {'type': 'tool_result', 'call_id': 'c1', 'tool': tool, 'skill': case['skill'],
                        'status': result_status, 'content': text if result_status == 'success' else 'Error: refused'}]
        events.append({'type': 'terminal', 'status': status})
        return {'binding': self.manifest['binding'], 'manifest_sha256': p.json_hash(self.manifest),
                'case_id': case['case_id'], 'events': events}

    def complete(self):
        return p.record([self.capture(case, retrieval=case['expected'] == 'positive') for case in self.manifest['cases']], self.manifest)

    def cli(self, script, *args):
        return subprocess.run([sys.executable, str(ROOT / 'scripts/gauntlet' / script), *map(str, args)],
                              capture_output=True, text=True, timeout=30, env={**os.environ, 'HOME': str(self.root / 'home')})

    def save(self, name, value, lines=False):
        path = self.root / name
        path.write_text(''.join(json.dumps(r) + '\n' for r in value) if lines else json.dumps(value))
        return path

    def test_full_fixture_pass_has_separate_modes_and_no_live_claim(self):
        result = p.grade(self.complete(), self.manifest)
        self.assertEqual(result['verdict'], 'FIXTURE_PASS')
        self.assertEqual(result['planned_cases'], 24)
        self.assertEqual(result['negative_controls_passed'], 12)
        self.assertEqual(result['invocation_modes']['automatic']['proven_skills'], 2)
        self.assertEqual(result['invocation_modes']['explicit']['proven_skills'], 1)
        self.assertEqual(result['invocation_modes']['dispatch']['proven_skills'], 1)
        self.assertEqual(result['live_model_capability'], 'NOT_ESTABLISHED')
        self.assertEqual(result['efficacy'], 'UNVERIFIED')

    def test_blocked_all_never_counts_as_pass(self):
        records = p.record([self.capture(case, retrieval=False, status='blocked') for case in self.manifest['cases']], self.manifest)
        result = p.grade(records, self.manifest)
        self.assertEqual(result['verdict'], 'FAIL')
        self.assertEqual(result['outcomes'], {'blocked': 24})
        self.assertTrue(all(v['proven_skills'] == 0 for v in result['invocation_modes'].values()))

    def test_prose_mention_is_not_retrieval(self):
        self.assertEqual(p.observe(self.capture(retrieval=False), self.manifest)['outcome'], 'fail')

    def test_forced_load_and_file_read_cannot_pass_automatic(self):
        for kwargs in ({'origin': 'user'}, {'tool': 'read_file'}, {'tool': 'role_load', 'origin': 'orchestrator'}):
            with self.subTest(kwargs=kwargs):
                self.assertEqual(p.observe(self.capture(**kwargs), self.manifest)['outcome'], 'fail')

    def test_refused_error_timeout_are_not_passing_negative_controls(self):
        case = next(c for c in self.manifest['cases'] if c['expected'] == 'negative')
        for kwargs, expected in [({'result_status': 'refused'}, 'blocked'), ({'result_status': 'error'}, 'execution-error'),
                                 ({'retrieval': False, 'status': 'timeout'}, 'execution-error'), ({'retrieval': False, 'status': 'blocked'}, 'blocked')]:
            with self.subTest(kwargs=kwargs):
                self.assertEqual(p.observe(self.capture(case, **kwargs), self.manifest)['outcome'], expected)

    def test_successful_negative_retrieval_is_false_positive(self):
        case = next(c for c in self.manifest['cases'] if c['expected'] == 'negative')
        self.assertEqual(p.observe(self.capture(case), self.manifest)['outcome'], 'fail')

    def test_correlated_result_and_exact_candidate_bytes_required(self):
        for mutation in ('id', 'bytes', 'name', 'unfinished', 'duplicate'):
            capture = self.capture()
            if mutation == 'id': capture['events'][3]['call_id'] = 'wrong'
            if mutation == 'bytes': capture['events'][3]['content'] = 'I loaded alpha'
            if mutation == 'name': capture['events'][3]['skill'] = 'role'
            if mutation == 'unfinished': del capture['events'][3]
            if mutation == 'duplicate': capture['events'].insert(4, copy.deepcopy(capture['events'][2]))
            with self.subTest(mutation=mutation), self.assertRaises(p.EvidenceError):
                p.observe(capture, self.manifest)

    def test_unknown_skills_and_extra_events_rejected(self):
        capture = self.capture()
        capture['events'][2]['skill'] = 'not-a-skill'
        with self.assertRaises(p.EvidenceError): p.observe(capture, self.manifest)
        capture = self.capture()
        capture['events'].insert(1, {'type': 'terminal', 'status': 'completed'})
        with self.assertRaises(p.EvidenceError): p.observe(capture, self.manifest)

    def test_case_query_and_origin_binding(self):
        for key in ('query', 'mode', 'tools'):
            capture = self.capture()
            capture['events'][0][key] = [] if key == 'tools' else 'changed'
            with self.subTest(key=key), self.assertRaises(p.EvidenceError): p.observe(capture, self.manifest)

    def test_mixed_run_cell_model_host_revision_rejected(self):
        for key in self.manifest['binding']:
            capture = copy.deepcopy(self.capture())
            capture['binding'][key] = 'changed'
            with self.subTest(key=key), self.assertRaises(p.EvidenceError): p.observe(capture, self.manifest)

    def test_manifest_hash_and_receipt_tampering_rejected(self):
        capture = self.capture()
        capture['manifest_sha256'] = 'b' * 64
        with self.assertRaises(p.EvidenceError): p.observe(capture, self.manifest)
        receipt = p.record([self.capture(retrieval=False)], self.manifest)[0]
        for key, value in [('outcome', 'pass'), ('capture_sha256', '0' * 64), ('retrievals', [])]:
            changed = copy.deepcopy(receipt); changed[key] = value
            if changed == receipt: continue
            with self.subTest(key=key), self.assertRaises(p.EvidenceError): p.grade([changed], self.manifest)

    def test_missing_positives_and_controls_fail(self):
        records = self.complete()
        for expected in ('positive', 'negative'):
            subset = [r for r in records if r['expected'] != expected]
            with self.subTest(expected=expected):
                self.assertEqual(p.grade(subset, self.manifest)['verdict'], 'FAIL')

    def test_duplicate_receipts_rejected(self):
        records = self.complete()
        with self.assertRaises(p.EvidenceError): p.grade(records + [records[0]], self.manifest)
        with self.assertRaises(p.EvidenceError): p.record([self.capture(), self.capture()], self.manifest)

    def test_tool_surface_drift_rejected(self):
        captures = [self.capture(case, retrieval=case['expected'] == 'positive') for case in self.manifest['cases']]
        captures[-1]['events'][0]['tools'] = ['skill', 'role_load']
        with self.assertRaises(p.EvidenceError): p.grade(p.record(captures, self.manifest), self.manifest)

    def test_non_claude_eligibility_is_explicit(self):
        manifest = p.prepare(self.repo, self.matrix, 'run', 'free', 'freebuff', 'pinned', 'a' * 40, 'offline-fixture')
        self.assertIn('native', manifest['exclusions'])
        self.assertFalse(any(c['skill'] == 'native' for c in manifest['cases']))
        capture = self.capture();capture['events'][2]['skill'] = 'native'
        capture['binding'] = manifest['binding'];capture['manifest_sha256'] = p.json_hash(manifest)
        with self.assertRaises(p.EvidenceError): p.observe(capture, manifest)

    def test_catalog_matrix_and_resource_drift_rejected(self):
        manifest_path = self.save('manifest.json', self.manifest)
        path = self.repo / self.manifest['catalog']['alpha']['path']
        original = path.read_text();path.write_text(original + 'changed')
        with self.assertRaises(p.EvidenceError): p.load_manifest(manifest_path)
        path.write_text(original)
        resource = path.parent / 'reference.txt';resource.write_text('changed')
        with self.assertRaises(p.EvidenceError): p.load_manifest(manifest_path)
        resource.unlink();self.matrix.write_text(self.matrix.read_text() + '\nchanged')
        with self.assertRaises(p.EvidenceError): p.load_manifest(manifest_path)

    def test_matrix_duplicate_missing_and_unknown_rows_rejected(self):
        original = self.matrix.read_text()
        for text in (original + '| alpha | P3 | positive | yes | negative |\n',
                     original.replace('| alpha |', '| unknown |'), '\n'.join(original.splitlines()[:-1])):
            self.matrix.write_text(text)
            with self.assertRaises(p.EvidenceError): p.matrix(self.matrix, p.catalog(self.repo))
        self.matrix.write_text(original)

    def test_json_invalid_duplicate_and_nonfinite_fail_loud(self):
        for raw in ('{bad', '{"a":1,"a":2}', '{"a":NaN}', '[]', ''):
            path=self.root/'broken.jsonl';path.write_text(raw)
            with self.subTest(raw=raw), self.assertRaises(p.EvidenceError): p.read_jsonl(path)

    def test_pipeline_drift_and_symlink_resources_rejected(self):
        changed=copy.deepcopy(self.manifest);changed['pipeline']['invented.py']='0'*64
        with self.assertRaises(p.EvidenceError):p.validate_manifest(changed)
        resource=self.repo/'skills/workflows/alpha/secret-link';resource.symlink_to(self.matrix)
        with self.assertRaises(p.EvidenceError):p.catalog(self.repo)

    def test_live_single_trial_is_not_certified(self):
        self.manifest=p.prepare(self.repo,self.matrix,'run','cell','claude-code','pinned','a'*40,'host-capture',1)
        result=p.grade(self.complete(),self.manifest)
        self.assertEqual(result['verdict'],'INSUFFICIENT_TRIALS')
        self.assertTrue(result['findings'])

    def test_native_adapters_retain_raw_evidence_and_replay_it(self):
        case=self.manifest['cases'][0]
        content=(self.repo/self.manifest['catalog'][case['skill']]['path']).read_text()
        for protocol in ('freebuff-sdk','hermes-stream'):
            self.manifest=p.prepare(self.repo,self.matrix,'run','cell','freebuff' if protocol=='freebuff-sdk' else 'hermes','pinned','a'*40,'offline-fixture')
            case=self.manifest['cases'][0]
            init={'type':'init','model':'pinned','tools':['skill']} if protocol=='freebuff-sdk' else {'type':'system','subtype':'init','model':'pinned','tools':['skill_view']}
            init.update(query=case['query'],mode=case['mode'])
            value={'name':case['skill'],'content':content,'description':'demo','success':True}
            if protocol=='freebuff-sdk':
                calls=[{'type':'tool_call','toolCallId':'c1','toolName':'skill','input':{'name':case['skill']}},
                       {'type':'tool_result','toolCallId':'c1','toolName':'skill','output':[{'value':value}]}]
            else:
                calls=[{'type':'tool_use','tool_call_id':'c1','name':'skill_view','input':{'name':case['skill']}},
                       {'type':'tool_result','tool_call_id':'c1','name':'skill_view','output':json.dumps(value)}]
            raw=[init,*calls,{'type':'result','exit_code':0}]
            capture=p.native_capture(protocol,raw,case['case_id'],self.manifest)
            receipt=p.record([capture],self.manifest)[0]
            altered=copy.deepcopy(raw);altered[0]['query']='an easier undisclosed prompt'
            with self.assertRaises(p.EvidenceError):p.native_capture(protocol,altered,case['case_id'],self.manifest)
            self.assertEqual(receipt['outcome'],'pass')
            self.assertEqual(receipt['capture']['source']['events'],raw)
            receipt['capture']['source']['events'][0]['model']='wrong'
            with self.assertRaises(p.EvidenceError):p.validate_receipt(receipt,self.manifest)

    def test_native_adapter_refuses_contentless_telemetry_and_wrong_model(self):
        case=self.manifest['cases'][0]
        for raw in ([{'type':'init','model':'wrong','tools':['skill']},{'type':'result','exit_code':0}],
                    [{'type':'init','model':'pinned','tools':['skill']},
                     {'type':'tool_call','toolCallId':'c1','toolName':'skill','input':{'name':'alpha'}},
                     {'type':'tool_result','toolCallId':'c1','toolName':'skill','output':[{'value':{'name':'alpha'}}]},
                     {'type':'result','exit_code':0}]):
            with self.assertRaises(p.EvidenceError):p.native_capture('freebuff-sdk',raw,case['case_id'],self.manifest)
        with self.assertRaises(p.EvidenceError):p.native_capture('claude-hook',[{'skill':'alpha'}],case['case_id'],self.manifest)

    def test_optional_row_is_excluded_unless_explicitly_selected(self):
        self.matrix.write_text(self.matrix.read_text().replace('| perform native task | yes |','| perform native task | yes (optional) |'))
        manifest=p.prepare(self.repo,self.matrix,'run','cell','claude-code','pinned','a'*40,'offline-fixture')
        self.assertIn('native',manifest['exclusions'])
        subset=p.prepare(self.repo,self.matrix,'run','cell','claude-code','pinned','a'*40,'offline-fixture',selection=['native'])
        self.assertEqual(len(subset['cases']),6)
        self.assertNotIn('native',subset['exclusions'])

    def test_native_import_cli(self):
        self.manifest=p.prepare(self.repo,self.matrix,'run','cell','freebuff','pinned','a'*40,'offline-fixture')
        case=self.manifest['cases'][0]
        content=(self.repo/self.manifest['catalog'][case['skill']]['path']).read_text()
        raw=[{'type':'init','model':'pinned','tools':['skill'],'query':case['query'],'mode':case['mode']},
             {'type':'tool_call','toolCallId':'c1','toolName':'skill','input':{'name':case['skill']}},
             {'type':'tool_result','toolCallId':'c1','toolName':'skill','output':[{'value':{'name':case['skill'],'content':content}}]},
             {'type':'result','exit_code':0}]
        manifest=self.save('manifest.json',self.manifest);events=self.save('native.jsonl',raw,True)
        out=self.root/'imported.jsonl'
        result=self.cli('record.py','import-host',events,'--protocol','freebuff-sdk','--case-id',case['case_id'],'--manifest',manifest,'--out',out)
        self.assertEqual(result.returncode,0,result.stderr)
        receipt=p.read_jsonl(out)[0]
        self.assertEqual(p.validate_receipt(receipt,self.manifest)['outcome'],'pass')

    def test_native_refusal_is_blocked_and_negative_no_call_is_real_control(self):
        self.manifest=p.prepare(self.repo,self.matrix,'run','cell','freebuff','pinned','a'*40,'offline-fixture')
        case=next(c for c in self.manifest['cases'] if c['expected']=='negative' and c['skill']=='alpha')
        init={'type':'init','model':'pinned','tools':['skill'],'query':case['query'],'mode':case['mode']}
        final={'type':'result','exit_code':0}
        raw=[init,final]
        capture=p.native_capture('freebuff-sdk',raw,case['case_id'],self.manifest)
        self.assertEqual(p.observe(capture,self.manifest)['outcome'],'pass')
        raw=[init,{'type':'tool_call','toolCallId':'c1','toolName':'skill','input':{'name':'alpha'}},
             {'type':'tool_result','toolCallId':'c1','toolName':'skill','output':[{'value':{'name':'alpha','content':'Error: can only be invoked by the user'}}]},final]
        capture=p.native_capture('freebuff-sdk',raw,case['case_id'],self.manifest)
        self.assertEqual(p.observe(capture,self.manifest)['outcome'],'blocked')

    def test_native_protocol_cannot_claim_another_host(self):
        case=self.manifest['cases'][0]
        with self.assertRaises(p.EvidenceError):
            p.native_capture('freebuff-sdk',[{'type':'init','model':'pinned','tools':['skill']},{'type':'result','exit_code':0}],case['case_id'],self.manifest)

    def test_explicit_and_dispatch_receipts_cannot_use_model_origin(self):
        for mode in ('explicit','dispatch'):
            case=next(c for c in self.manifest['cases'] if c['expected']=='positive' and c['mode']==mode)
            self.assertEqual(p.observe(self.capture(case,origin='model'),self.manifest)['outcome'],'fail')

    def test_schema_is_authoritative_not_just_semantic_replay(self):
        receipt=self.complete()[0]
        receipt['untrusted_extra']='ignored?'
        with self.assertRaises(p.EvidenceError):p.validate_receipt(receipt,self.manifest)

    def test_cli_preflight_and_refusal_to_overwrite(self):
        parent=ROOT/'.workspaces/gauntlet-pipeline'
        parent.mkdir(parents=True,exist_ok=True)
        with tempfile.TemporaryDirectory(prefix='test-preflight-',dir=parent) as temporary:
            out=Path(temporary)/'new'
            result=self.cli('preflight.py','--repo',self.repo,'--matrix',self.matrix,'--revision','a'*40,'--out-dir',out)
            self.assertEqual(result.returncode,0,result.stderr)
            receipt=json.loads((out/'preflight.json').read_text())
            self.assertEqual(receipt['model_calls'],0)
            self.assertFalse(receipt['live_run_ready'])
            self.assertTrue(all(c['actual_exit']==c['expected_exit'] for c in receipt['checks']))
            before=(out/'preflight.json').read_bytes()
            result=self.cli('preflight.py','--repo',self.repo,'--matrix',self.matrix,'--revision','a'*40,'--out-dir',out)
            self.assertEqual(result.returncode,2)
            self.assertEqual((out/'preflight.json').read_bytes(),before)

    def test_trap_relative_target_and_checker_errors(self):
        sandbox=self.root/'trap-repo'
        verifier=sandbox/'scripts/gauntlet/trap-verify.sh';verifier.parent.mkdir(parents=True)
        verifier.write_bytes((ROOT/'scripts/gauntlet/trap-verify.sh').read_bytes())
        (sandbox/'.env.example').write_text('')
        gate=sandbox/'hooks/scripts/qa-gate.sh';gate.parent.mkdir(parents=True)
        gate.write_text('#!/usr/bin/env bash\nprintf \'{"decision":"block"}\\n\'\n')
        qa=sandbox/'tests/installer/qa-report.json';qa.parent.mkdir(parents=True);qa.write_text('{}')
        target=sandbox/'target';(target/'traps').mkdir(parents=True);(target/'traps/.seeded').write_text('seeded')
        def run(path):
            return subprocess.run(['bash',str(verifier),str(path)],cwd=sandbox,capture_output=True,text=True,timeout=10)
        absolute=run(target);relative=run('target')
        self.assertEqual(absolute.returncode,2)
        self.assertEqual(relative.returncode,2)
        a=next(line for line in absolute.stdout.splitlines() if line.startswith('T8\t'))
        b=next(line for line in relative.stdout.splitlines() if line.startswith('T8\t'))
        self.assertEqual(a,b);self.assertTrue(a.endswith('PASS'))
        gate.write_text('#!/usr/bin/env bash\nexit 127\n')
        failed=run('target')
        line=next(line for line in failed.stdout.splitlines() if line.startswith('T8\t'))
        self.assertTrue(line.endswith('BLOCKED'),line)

    def test_cli_prepare_capture_merge_score_with_fake_home(self):
        manifest=self.root/'planned.json'
        result=self.cli('record.py','prepare','--repo',self.repo,'--matrix',self.matrix,'--run-id','run','--cell-id','cell','--host','claude-code','--model','pinned','--revision','a'*40,'--evidence-kind','offline-fixture','--out',manifest)
        self.assertEqual(result.returncode,0,result.stderr)
        self.manifest=p.load_manifest(manifest)
        events=self.save('events.jsonl',[self.capture(case,retrieval=case['expected']=='positive') for case in self.manifest['cases']],True)
        receipts=self.root/'receipts.jsonl'
        result=self.cli('record.py','capture',events,'--manifest',manifest,'--out',receipts)
        self.assertEqual(result.returncode,0,result.stderr)
        merged=self.root/'merged.jsonl'
        result=self.cli('trace-merge.py',receipts,'--manifest',manifest,'--out',merged,'--strict')
        self.assertEqual(result.returncode,0,result.stderr)
        report=self.root/'report.md';summary=self.root/'summary.json'
        result=self.cli('score.py',merged,'--manifest',manifest,'--out',report,'--json-out',summary)
        self.assertEqual(result.returncode,0,result.stderr)
        self.assertIn('FIXTURE_PASS',report.read_text())
        self.assertEqual(json.loads(summary.read_text())['live_model_capability'],'NOT_ESTABLISHED')
        before=report.read_bytes()
        result=self.cli('score.py',merged,'--manifest',manifest,'--out',report)
        self.assertEqual(result.returncode,2)
        self.assertEqual(report.read_bytes(),before)

    def test_cli_blocks_legacy_trace_missing_manifest_and_bad_input(self):
        manifest=self.save('manifest.json',self.manifest)
        legacy=self.save('legacy.jsonl',[{'skill':name,'outcome':'blocked','proof':'blocked'} for name in self.manifest['catalog']],True)
        for script in ('score.py','trace-merge.py'):
            result=self.cli(script,legacy,'--manifest',manifest)
            self.assertEqual(result.returncode,2,result.stderr)
            result=self.cli(script,legacy,'--manifest',self.root/'absent.json')
            self.assertEqual(result.returncode,2,result.stderr)
        result=self.cli('record.py','capture',legacy,'--manifest',manifest,'--out',self.root/'no.jsonl')
        self.assertEqual(result.returncode,2,result.stderr)
        self.assertFalse((self.root/'no.jsonl').exists())

    def test_cli_blocked_all_and_missing_controls_exit_one(self):
        manifest=self.save('manifest.json',self.manifest)
        for kind in ('blocked','missing-negative','false-positive'):
            captures=[self.capture(case,retrieval=False,status='blocked') if kind=='blocked' else
                      self.capture(case,retrieval=case['expected']=='positive' or kind=='false-positive')
                      for case in self.manifest['cases'] if kind!='missing-negative' or case['expected']=='positive']
            trace=self.save(kind+'.jsonl',p.record(captures,self.manifest),True)
            for script in ('score.py','trace-merge.py'):
                options=['--strict'] if script=='trace-merge.py' else []
                result=self.cli(script,trace,'--manifest',manifest,*options)
                self.assertEqual(result.returncode,1,result.stderr)


if __name__ == '__main__':
    unittest.main(verbosity=2)
