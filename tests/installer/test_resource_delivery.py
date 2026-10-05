"""Offline delivery regressions; never mutate real HOME or call providers."""
import importlib.util
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO / 'scripts/lib'))
import resource_delivery as delivery


class ResourceDelivery(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix='ats delivery ')
        self.root = Path(self.temp.name)
        self.repo = self.root / 'repo with spaces'
        shutil.copytree(REPO / 'scripts', self.repo / 'scripts')
        shutil.copytree(REPO / 'manifests', self.repo / 'manifests')
        self.skill = self.repo / 'skills/workflows/fixture'
        self.skill.mkdir(parents=True)
        self.write(self.skill / 'SKILL.md', '---\nname: fixture\nversion: 1.0.0\ndescription: Test resource delivery.\n---\n# Fixture\nRead references/guide.md and run scripts/helper.py.\n')
        for relative, text in {
            'scripts/helper.py': "from pathlib import Path\nroot=Path(__file__).resolve().parents[1]\nprint((root/'template/start.txt').read_text())\n",
            'template/start.txt': 'installed template', 'assets/config.json': '{}',
            'agents/grader.md': '# Grader', 'eval-viewer/view.html': '<html>viewer</html>',
            'references/guide.md': '# Guide', 'references/nested/more.md': '# Nested',
            'scripts/__pycache__/no.pyc': 'cache', 'scripts/node_modules/no.js': 'junk',
            'assets/.env': 'private value must never ship',
        }.items():
            self.write(self.skill / relative, text)
        (self.skill / 'scripts/helper.py').chmod(0o755)
        self.home = self.root / 'home'
        self.home.mkdir()
        self.project = self.root / 'project'
        self.project.mkdir()
        self.out = self.repo / 'integrations'

    def tearDown(self):
        self.temp.cleanup()

    def write(self, path, text):
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text)

    def run_cli(self, script, *args, env=None):
        environment = dict(os.environ, HOME=str(self.home), GIT_CONFIG_GLOBAL='/dev/null')
        if env:
            environment.update(env)
        return subprocess.run(['bash', str(self.repo / 'scripts' / script), *map(str, args)],
                              cwd=self.project, env=environment, capture_output=True, text=True, timeout=90)

    def convert(self, *args):
        result = self.run_cli('convert.sh', '--out', self.out, *args)
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        return result

    def plan(self, tool='claude-code', root=None):
        self.convert('--tool', tool)
        return delivery.make_plan(self.out, [tool], root or self.home, {'workflows'}, 'full', 'test')

    def test_all_formats_ship_declared_resources_and_exclude_debris_secrets(self):
        self.convert()
        for tool in delivery.TOOLS:
            data = delivery.inventory(self.out / tool, tool)
            root = self.out / tool / data['skills'][0]['root']
            for rel in ('scripts/helper.py', 'template/start.txt', 'assets/config.json', 'agents/grader.md', 'eval-viewer/view.html', 'references/nested/more.md'):
                self.assertTrue((root / rel).is_file(), str(root / rel))
            self.assertFalse((root / 'assets/.env').exists())
            self.assertFalse((root / 'scripts/__pycache__').exists())
            self.assertFalse((root / 'scripts/node_modules').exists())
            self.assertEqual((root / 'scripts/helper.py').stat().st_mode & 0o777, 0o755)

    def test_serial_parallel_bytes_and_totals_equal(self):
        first = self.convert()
        original = {str(p.relative_to(self.out)): p.read_bytes() for p in self.out.rglob('*') if p.is_file()}
        shutil.rmtree(self.out)
        second = self.convert('--parallel', '--jobs', '3')
        parallel = {str(p.relative_to(self.out)): p.read_bytes() for p in self.out.rglob('*') if p.is_file()}
        self.assertEqual(original, parallel)
        self.assertEqual(first.stderr.split('[convert] processed')[-1], second.stderr.split('[convert] processed')[-1])
        self.assertTrue((self.out / 'gemini-cli/gemini-extension.json').is_file())

    def test_native_hook_manifest_is_optional_and_never_activates_settings(self):
        shutil.copytree(REPO / 'hooks', self.repo / 'hooks')
        self.convert('--tool', 'claude-code')
        ordinary = delivery.make_plan(self.out, ['claude-code'], self.home, {'workflows'}, 'full', 'test')
        hooked = delivery.make_plan(self.out, ['claude-code'], self.home, {'workflows'}, 'full', 'test', True)
        self.assertFalse(any('/.claude/ats-hooks/' in op['dest'] for op in ordinary['operations']))
        self.assertTrue(any('/.claude/ats-hooks/' in op['dest'] for op in hooked['operations']))
        delivery.apply_plan(hooked, self.home)
        self.assertTrue((self.home / '.claude/ats-hooks/run-with-flags.sh').stat().st_mode & 0o111)
        self.assertFalse((self.home / '.claude/settings.json').exists())

    def test_classic_parallel_preview_and_manifest_tampering_fail_closed(self):
        self.convert()
        before = {str(p): p.read_bytes() for base in (self.home, self.project) for p in base.rglob('*') if p.is_file()}
        result = self.run_cli('install.sh', '--all', '--parallel', '--jobs', '2', '--dry-run', '--no-interactive')
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertEqual(before, {str(p): p.read_bytes() for base in (self.home, self.project) for p in base.rglob('*') if p.is_file()})
        helper = self.out / 'cursor/rules/fixture-resources/scripts/helper.py'
        helper.write_text('tamper')
        result = self.run_cli('install.sh', '--tool', 'cursor', '--no-interactive')
        self.assertNotEqual(result.returncode, 0)
        self.assertFalse((self.project / '.cursor').exists())

    def test_invalid_plan_schema_hash_mode_missing_source_and_prior_state_block(self):
        import copy
        original = self.plan()
        for mutation in ('schema', 'hash', 'mode', 'relative-dest', 'missing'):
            plan = copy.deepcopy(original)
            if mutation == 'schema': plan['schema_version'] = 1
            if mutation == 'hash': plan['operations'][0]['sha256'] = 'bogus'
            if mutation == 'mode': plan['operations'][0]['mode'] = True
            if mutation == 'relative-dest': plan['operations'][0]['dest'] = 'relative'
            if mutation == 'missing': plan['operations'][0]['source'] = str(self.root / 'missing')
            with self.assertRaises((ValueError, OSError)): delivery.apply_plan(plan, self.home)
            self.assertFalse((self.home / '.claude').exists())
        state = self.home / '.claude/.ats-install-state.json'
        self.write(state, json.dumps({'schema_version': 2, 'root': str(self.home), 'files': [{'dest': str(self.root / 'escaped')}]}))
        with self.assertRaises(ValueError): delivery.apply_plan(original, self.home)

    def test_direct_worker_parses_out_and_rejects_mismatched_context(self):
        result = self.run_cli('convert.sh', '--tool', 'cursor', '--out', self.out,
                              env={'ATS_CONVERT_WORKER': '1', 'ATS_CONVERT_TOOL': 'cursor'})
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertTrue((self.out / 'cursor/rules/fixture.mdc').exists())
        result = self.run_cli('convert.sh', '--tool', 'qwen', '--out', self.out,
                              env={'ATS_CONVERT_WORKER': '1', 'ATS_CONVERT_TOOL': 'cursor'})
        self.assertEqual(result.returncode, 2)
        self.assertFalse((self.out / 'qwen').exists())

    def test_converter_resource_failure_is_error_in_both_modes(self):
        (self.skill / 'assets/link').symlink_to(self.root / 'outside')
        for flags in ((), ('--parallel', '--jobs', '2')):
            result = self.run_cli('convert.sh', '--out', self.out, *flags)
            self.assertNotEqual(result.returncode, 0)
            self.assertNotIn('(0 skipped, 0 errors)', result.stderr)

    def test_classic_installed_helpers_run_without_checkout_all_tools(self):
        self.convert()
        result = self.run_cli('install.sh', '--all', '--no-interactive')
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        for tool in delivery.TOOLS:
            data = delivery.inventory(self.out / tool, tool)
            rel = data['skills'][0]['root'] + '/scripts/helper.py'
            for script in delivery.destinations(tool, rel, self.home, self.project):
                result = subprocess.run([sys.executable, str(script)], cwd=self.project, capture_output=True, text=True)
                self.assertEqual(result.returncode, 0, str(script) + result.stderr)
                self.assertIn('installed template', result.stdout)
                self.assertEqual(script.stat().st_mode & 0o777, 0o755)
        self.assertTrue((self.home / '.gemini/extensions/alltheskills/gemini-extension.json').exists())

    def test_plan_installs_flat_resources_and_gemini_extension_paths(self):
        self.convert()
        tools = ['copilot', 'cursor', 'qwen', 'opencode', 'gemini-cli', 'aider', 'windsurf']
        plan = delivery.make_plan(self.out, tools, self.home, {'workflows'}, 'full', 'test')
        delivery.apply_plan(plan, self.home)
        for tool in tools:
            data = delivery.inventory(self.out / tool, tool)
            for script in delivery.destinations(tool, data['skills'][0]['root'] + '/scripts/helper.py', self.home, self.home):
                self.assertTrue(script.exists(), str(script))
                result = subprocess.run([sys.executable, str(script)], capture_output=True, text=True)
                self.assertEqual(result.returncode, 0, result.stderr)
        self.assertTrue((self.home / '.gemini/extensions/alltheskills/skills/fixture/SKILL.md').exists())
        self.assertTrue((self.home / '.gemini/extensions/alltheskills/gemini-extension.json').exists())

    def test_stale_source_hash_or_mode_blocks_all_writes(self):
        for change in ('bytes', 'mode'):
            plan = self.plan()
            src = Path(plan['operations'][-1]['source'])
            if change == 'bytes':
                src.write_text('changed')
            else:
                src.chmod(0o600 if plan['operations'][-1]['mode'] != 0o600 else 0o644)
            with self.assertRaises(ValueError):
                delivery.apply_plan(plan, self.home)
            self.assertFalse((self.home / '.claude').exists())

    def test_root_escape_symlink_and_duplicate_destinations_block(self):
        import copy
        original = self.plan()
        for mutation in ('root', 'escape', 'duplicate', 'symlink'):
            plan = copy.deepcopy(original)
            if mutation == 'root': plan['root'] = str(self.root)
            if mutation == 'escape': plan['operations'][0]['dest'] = str(self.root / 'outside')
            if mutation == 'duplicate': plan['operations'].append(plan['operations'][0])
            if mutation == 'symlink': (self.home / '.claude').symlink_to(self.project, target_is_directory=True)
            with self.assertRaises(ValueError): delivery.apply_plan(plan, self.home)
            self.assertFalse((self.root / 'outside').exists())
            if mutation == 'symlink': (self.home / '.claude').unlink()
            self.assertEqual(list(self.project.iterdir()), [])

    def test_intervening_destination_edit_blocks_but_reapply_is_idempotent(self):
        plan = self.plan()
        delivery.apply_plan(plan, self.home)
        self.assertIn('created=0 updated=0', delivery.apply_plan(plan, self.home))
        dest = Path(plan['operations'][0]['dest'])
        dest.write_text('user edit')
        with self.assertRaises(ValueError): delivery.apply_plan(plan, self.home)
        self.assertEqual(dest.read_text(), 'user edit')

    def test_apply_dry_run_zero_writes_and_partial_state_merges(self):
        plan = self.plan()
        before_files = {str(p): p.read_bytes() for p in self.home.rglob('*') if p.is_file()}
        delivery.apply_plan(plan, self.home, True)
        self.assertEqual(before_files, {str(p): p.read_bytes() for p in self.home.rglob('*') if p.is_file()})
        delivery.apply_plan(plan, self.home)
        before = delivery.read_json(self.home / '.claude/.ats-install-state.json')
        plan2 = self.plan('cursor')
        delivery.apply_plan(plan2, self.home)
        after = delivery.read_json(self.home / '.claude/.ats-install-state.json')
        self.assertTrue({f['dest'] for f in before['files']} <= {f['dest'] for f in after['files']})

    def test_real_guard_creator_and_living_plan_resources_after_install(self):
        # No evaluator/provider process: only offline help/static viewer rendering.
        for name in ('design-token-guard', 'class-extraction-guard', 'skill-creator', 'living-plan'):
            shutil.copytree(REPO / 'skills/workflows' / name, self.repo / 'skills/workflows' / name,
                            ignore=shutil.ignore_patterns('__pycache__', 'node_modules'))
        self.convert('--tool', 'cursor')
        result = self.run_cli('install.sh', '--tool', 'cursor', '--no-interactive')
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        base = self.project / '.cursor/rules'
        creator = base / 'skill-creator-resources'
        self.assertTrue((creator / 'agents/grader.md').exists())
        self.assertTrue((creator / 'assets/eval_review.html').exists())
        # Viewer annotations require the skill's existing Python 3.10+ runtime;
        # load under 3.9 with postponed annotations for this dependency-free smoke.
        namespace = {'__file__': str(creator / 'eval-viewer/generate_review.py'), '__name__': 'delivery_viewer'}
        source = (creator / 'eval-viewer/generate_review.py').read_text()
        exec(compile('from __future__ import annotations\n' + source, namespace['__file__'], 'exec'), namespace)
        self.assertIn('EMBEDDED_DATA', namespace['generate_html']([], 'offline delivery'))
        self.assertTrue((base / 'living-plan-resources/template/START-HERE.template.md').exists())
        bootstrap = base / 'design-token-guard-resources/scripts/bootstrap_frontend_guards.py'
        target = self.root / 'guarded-project'
        target.mkdir()
        result = subprocess.run([sys.executable, '-B', str(bootstrap), '--root', str(target),
                                 '--class-guard-dir', str(base / 'class-extraction-guard-resources'), '--apply'], capture_output=True, text=True)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.write(target / 'page.html', '<main style="display:grid"></main>')
        result = subprocess.run([sys.executable, '-B', str(target / 'scripts/frontend-guards/run.py')], capture_output=True, text=True)
        self.assertEqual(result.returncode, 1)

    def test_explicit_secret_injection_without_ancestor_credentials(self):
        copied = self.root / 'installed/nano/scripts/generate_image.py'
        self.write(copied, (REPO / 'skills/workflows/nano-banana/scripts/generate_image.py').read_text())
        self.write(self.root / '.env', 'GEMINI_API_KEY=must-not-discover\n')
        source = 'from __future__ import annotations\n' + copied.read_text()
        from unittest.mock import patch
        with patch.dict(os.environ, {}, clear=True):
            namespace = {'__file__': str(copied), '__name__': 'offline_nano'}
            exec(compile(source, str(copied), 'exec'), namespace)
            self.assertNotIn('GEMINI_API_KEY', os.environ)
        approved = self.root / 'approved.env'
        self.write(approved, 'GEMINI_API_KEY=fixture-only-value\n')
        with patch.dict(os.environ, {'ATS_ENV_FILE': str(approved)}, clear=True):
            namespace = {'__file__': str(copied), '__name__': 'offline_nano'}
            exec(compile(source, str(copied), 'exec'), namespace)
            self.assertEqual(os.environ.get('GEMINI_API_KEY'), 'fixture-only-value')
        with patch.dict(os.environ, {'ATS_ENV_FILE': str(approved), 'GEMINI_API_KEY': 'export-wins'}, clear=True):
            namespace = {'__file__': str(copied), '__name__': 'offline_nano'}
            exec(compile(source, str(copied), 'exec'), namespace)
            self.assertEqual(os.environ['GEMINI_API_KEY'], 'export-wins')

    def test_state_mode_drift_repair_stale_source_and_edited_uninstall(self):
        plan = self.plan()
        delivery.apply_plan(plan, self.home)
        helper = next(Path(op['dest']) for op in plan['operations'] if op['dest'].endswith('scripts/helper.py'))
        helper.chmod(0o600)
        self.assertEqual(delivery.manage_state('drift', self.home), 1)
        delivery.manage_state('repair', self.home)
        self.assertEqual(helper.stat().st_mode & 0o777, 0o755)
        helper.write_text('edited')
        with self.assertRaises(ValueError): delivery.manage_state('uninstall', self.home)
        source = next(Path(op['source']) for op in plan['operations'] if op['dest'] == str(helper))
        source.write_text('source changed')
        with self.assertRaises(ValueError): delivery.manage_state('repair', self.home)
        self.assertEqual(helper.read_text(), 'edited')

    def test_reconversion_removes_only_previously_owned_outputs(self):
        self.convert('--tool', 'cursor')
        self.write(self.out / 'cursor/rules/unrelated.txt', 'keep me')
        (self.skill / 'template/start.txt').unlink()
        self.convert('--tool', 'cursor')
        self.assertFalse((self.out / 'cursor/rules/fixture-resources/template/start.txt').exists())
        self.assertEqual((self.out / 'cursor/rules/unrelated.txt').read_text(), 'keep me')

    def sync(self, *args):
        return subprocess.run([sys.executable, str(self.repo / 'scripts/lib/sync_delivery.py'), '--repo', str(self.repo), *args],
                              env=dict(os.environ, HOME=str(self.home)), capture_output=True, text=True, timeout=30)

    def test_sync_subset_collision_backup_and_owned_only_cleanup(self):
        second = self.repo / 'skills/workflows/second/SKILL.md'
        self.write(second, (self.skill / 'SKILL.md').read_text().replace('fixture', 'second'))
        base = self.home / '.claude/skills'
        self.write(base / 'fixture/user.txt', 'precious local copy')
        unrelated = base / 'unrelated'
        unrelated.symlink_to(self.root / 'absent')
        result = self.sync('--to-claude', 'fixture')
        self.assertEqual(result.returncode, 2, result.stdout + result.stderr)
        self.assertFalse((base / 'second').exists())
        self.assertEqual((base / 'fixture/user.txt').read_text(), 'precious local copy')
        result = self.sync('--to-claude', '--replace-with-backup', '--dry-run', 'fixture')
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertFalse((base / '.ats-sync-owned.json').exists())
        result = self.sync('--to-claude', '--replace-with-backup', 'fixture')
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertTrue((base / 'fixture').is_symlink())
        self.assertEqual(next(base.glob('fixture.ats-backup-*/user.txt')).read_text(), 'precious local copy')
        shutil.rmtree(self.skill)
        result = self.sync('--clean')
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertFalse((base / 'fixture').is_symlink())
        self.assertTrue(unrelated.is_symlink())

    def test_sync_lists_every_collision_and_previews_each_backup(self):
        second = self.repo / 'skills/workflows/second/SKILL.md'
        self.write(second, (self.skill / 'SKILL.md').read_text().replace('fixture', 'second'))
        base = self.home / '.claude/skills'
        self.write(base / 'fixture/user.txt', 'local copy')
        base.joinpath('second').symlink_to(self.root / 'elsewhere')
        result = self.sync('--to-claude', '--dry-run')
        self.assertEqual(result.returncode, 2)
        self.assertIn('collision: %s (existing directory)' % (base / 'fixture'), result.stderr)
        self.assertIn('collision: %s (existing link -> %s)' % (base / 'second', self.root / 'elsewhere'), result.stderr)
        self.assertIn('2 unowned/edited collision(s)', result.stderr)
        result = self.sync('--to-claude', '--dry-run', '--replace-with-backup')
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn('link: %s (backs up existing directory)' % (base / 'fixture'), result.stdout)
        self.assertIn('link: %s (backs up existing link -> %s)' % (base / 'second', self.root / 'elsewhere'), result.stdout)
        self.assertEqual((base / 'fixture/user.txt').read_text(), 'local copy')

    def test_cursor_sync_filters_native_only_and_copies_template(self):
        native = self.repo / 'skills/meta/native/SKILL.md'
        self.write(native, '---\nname: native\nversion: 1.0.0\ndescription: native only\nrequires_claude_code: true\n---\n# Native\n')
        result = self.sync('--copy', '--to-cursor', 'workflows')
        self.assertEqual(result.returncode, 0, result.stderr)
        base = self.home / '.cursor/skills-cursor'
        self.assertTrue((base / 'fixture/template/start.txt').exists())
        self.assertFalse((base / 'native').exists())
        result = self.sync('--copy', '--to-cursor')
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertFalse((base / 'native').exists())
        self.write(base / 'fixture/user.txt', 'edited')
        result = self.sync('--copy', '--to-cursor', 'fixture')
        self.assertEqual(result.returncode, 2)
        self.assertEqual((base / 'fixture/user.txt').read_text(), 'edited')

    def test_apply_rolls_back_prior_writes_on_io_failure(self):
        from unittest.mock import patch
        plan = self.plan()
        before_files = {str(p): p.read_bytes() for p in self.home.rglob('*') if p.is_file()}
        original = delivery.replace_bytes
        calls = []
        def failing(path, data, mode):
            calls.append(path)
            if len(calls) == 2: raise OSError('simulated disk failure')
            return original(path, data, mode)
        with patch.object(delivery, 'replace_bytes', side_effect=failing):
            with self.assertRaises(OSError): delivery.apply_plan(plan, self.home)
        self.assertFalse((self.home / '.claude/.ats-install-state.json').exists())
        self.assertEqual(before_files, {str(p): p.read_bytes() for p in self.home.rglob('*') if p.is_file()})


if __name__ == '__main__':
    unittest.main()
