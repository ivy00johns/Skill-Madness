"""No model calls or real HOME mutation: all generated projects are temporary."""
import importlib.util
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

REPO = Path(__file__).resolve().parents[2]
DTG = REPO / "skills/workflows/design-token-guard/scripts"
CEG = REPO / "skills/workflows/class-extraction-guard/scripts"


class FrontendWave(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)

    def tearDown(self):
        self.temp.cleanup()

    def write(self, name, content):
        path = self.root / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content)
        return path

    def cli(self, script, *args):
        folder = DTG if script in ("check_design_tokens.py", "bootstrap_frontend_guards.py") else CEG
        return subprocess.run([sys.executable, str(folder / script), "--root", str(self.root), *args], capture_output=True, text=True)

    def design(self, text, *args, suffix="html"):
        self.write("page." + suffix, text)
        result = self.cli("check_design_tokens.py", "--json", *args)
        return result, json.loads(result.stdout)

    def css(self, text):
        self.write("styles.css", text)
        self.write(".class-guard.json", json.dumps({"rules": {"duplicate-css-block": "error"}}))
        result = self.cli("check_class_extraction.py", "--json")
        return result, json.loads(result.stdout)

    def test_html_literal_dimension_is_reported(self):
        result, data = self.design('<main style="display:grid;grid-template-columns:60% 40%;width:1200px"></main>')
        self.assertEqual(result.returncode, 0) # legacy warn policy
        self.assertEqual(data["summary"]["warnings"], 1)

    def test_html_layout_profile_blocks_grid(self):
        result, _ = self.design('<main style="display:grid;grid-template-columns:60% 40%"></main>', "--profile", "layout")
        self.assertEqual(result.returncode, 1)

    def test_jsx_layout_profile_blocks(self):
        result, _ = self.design('export const P = () => <main style={{display: "grid", width: "1200px"}}/>;', "--profile", "layout", suffix="tsx")
        self.assertEqual(result.returncode, 1)

    def test_custom_property_inputs_allowed_html_and_jsx(self):
        for suffix, text in (("html", '<main style="--progress:72%;--size:var(--space)"></main>'),
                             ("tsx", "export const P = () => <main style={{'--progress': progress}}/>;")):
            with self.subTest(suffix=suffix):
                result, _ = self.design(text, "--profile", "layout", suffix=suffix)
                self.assertEqual(result.returncode, 0, result.stderr)

    def test_custom_property_plus_layout_cannot_escape(self):
        result, _ = self.design("<main style={{'--progress': progress, width: width}}/>", "--profile", "layout", suffix="tsx")
        self.assertEqual(result.returncode, 1)

    def test_multiple_custom_properties_and_string_braces_are_safe(self):
        result, _ = self.design("<main style={{'--progress': progress, '--label': 'a{b}', '--color': getColor(a, b)}}/>", "--profile", "layout", suffix="tsx")
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        result, _ = self.design("<main style={{'--progress': progress, '--color': getColor(a, b)}}/>", "--profile", "layout", suffix="tsx")
        self.assertEqual(result.returncode, 0)

    def test_spaced_jsx_style_objects_cannot_escape_layout_policy(self):
        for text, expected in (
            ('<main style={ {width: "1200px"} }/>', 1),
            ("<main style={ {'--label': 'a{b}', '--color': getColor(a, b)} }/>", 0),
            ("<main style={ {'--value': value, ...styles} }/>", 1),
        ):
            result, _ = self.design(text, "--profile", "layout", suffix="tsx")
            self.assertEqual(result.returncode, expected, result.stdout + result.stderr)

    def test_uppercase_and_unquoted_html_inline_layout_block(self):
        for text in ('<main STYLE="display:grid"></main>', '<main style=display:grid></main>'):
            result, _ = self.design(text, "--profile", "layout")
            self.assertEqual(result.returncode, 1)

    def test_invalid_source_encoding_is_blocked(self):
        (self.root / "page.html").write_bytes(b"\xff")
        for script in ("check_design_tokens.py", "check_class_extraction.py", "check_shared_layout.py"):
            self.assertEqual(self.cli(script, "--json").returncode, 2)

    def test_unreadable_source_mock_fails_instead_of_clean(self):
        from unittest.mock import patch
        spec = importlib.util.spec_from_file_location("test_dtg", DTG / "check_design_tokens.py")
        module = importlib.util.module_from_spec(spec)
        sys.modules[spec.name] = module
        spec.loader.exec_module(module)
        with patch.object(module, "_read", side_effect=PermissionError("unreadable")):
            with self.assertRaises(ValueError):
                module.run(str(self.root), module.DEFAULT_CONFIG, [str(self.root / "a.html")], module.TokenIndex())

    def test_staged_design_subroot_and_newline_filename(self):
        subprocess.run(["git", "init", "-q", str(self.root)], check=True)
        self.write("web/a\nb.html", '<main style="display:grid"></main>')
        self.write("other.html", '<main style="display:grid"></main>')
        subprocess.run(["git", "-C", str(self.root), "add", "."], check=True)
        result = subprocess.run([sys.executable, str(DTG / "check_design_tokens.py"), "--root", str(self.root / "web"), "--staged", "--profile", "layout", "--json"], capture_output=True, text=True)
        self.assertEqual(result.returncode, 1, result.stdout + result.stderr)
        self.assertEqual(json.loads(result.stdout)["summary"]["files_scanned"], 1)

    def test_opaque_object_and_spread_block(self):
        for style in ("{styles}", "{{...styles}}", "{{width: width}}"):
            result, _ = self.design("<main style=" + style + "/>", "--profile", "layout", suffix="tsx")
            self.assertEqual(result.returncode, 1)

    def test_scan_counts_clean_files_not_only_findings(self):
        self.write("second.html", "<main>clean</main>")
        result, data = self.design("<main>clean</main>")
        self.assertEqual(result.returncode, 0)
        self.assertEqual(data["summary"]["files_scanned"], 2)
        self.assertEqual(data["summary"]["files_with_findings"], 0)

    def test_staged_non_git_is_blocked_for_both_guards(self):
        for script in ("check_design_tokens.py", "check_class_extraction.py"):
            result = self.cli(script, "--staged", "--json")
            self.assertEqual(result.returncode, 2)
            self.assertEqual(json.loads(result.stdout)["status"], "blocked")

    def test_missing_explicit_path_and_config_are_blocked(self):
        for script in ("check_design_tokens.py", "check_class_extraction.py"):
            for args in (("absent.html",), ("--config", str(self.root / "missing.json"))):
                self.assertEqual(self.cli(script, "--json", *args).returncode, 2)

    def test_bad_severity_is_blocked(self):
        for script, config, rule in (("check_design_tokens.py", ".design-guard.json", "no-inline-style"),
                                     ("check_class_extraction.py", ".class-guard.json", "duplicate-css-block")):
            self.write(config, json.dumps({"rules": {rule: "erorr"}}))
            self.assertEqual(self.cli(script, "--json").returncode, 2)

    def test_four_unique_hash_classes_do_not_hide_duplicate_css(self):
        result, data = self.css("\n".join(".hash%d {display:grid; gap:var(--space); padding:var(--pad)}" % n for n in range(4)))
        self.assertEqual(result.returncode, 1, result.stderr)
        self.assertEqual(data["findings"][0]["count"], 4)

    def test_css_scope_specificity_and_importance_are_not_collapsed(self):
        cases = (
            ".a {display:grid;gap:1rem;padding:2rem} @media (min-width:20em){.b {display:grid;gap:1rem;padding:2rem}} @layer x{.c {display:grid;gap:1rem;padding:2rem}}",
            ".a {display:grid;gap:1rem;padding:2rem} .b:hover {display:grid;gap:1rem;padding:2rem} #x .c {display:grid;gap:1rem;padding:2rem}",
            ".a {display:grid;gap:1rem;padding:2rem} .b {display:grid!important;gap:1rem;padding:2rem} .c {padding:2rem;gap:1rem;display:grid}",
        )
        for text in cases:
            result, data = self.css(text)
            self.assertEqual(result.returncode, 0, data)

    def test_duplicate_css_exception_requires_reason(self):
        text = " ".join(".x%d {display:grid;gap:1rem;padding:2rem}" % n for n in range(3))
        _, data = self.css(text)
        key = data["findings"][0]["string"]
        self.write(".class-guard.json", json.dumps({"rules": {"duplicate-css-block": "error"}, "cssAllowlist": [{"fingerprint": key, "reason": "owner-approved independent modules"}]}))
        self.assertEqual(self.cli("check_class_extraction.py", "--json").returncode, 0)
        self.write(".class-guard.json", json.dumps({"cssAllowlist": [{"fingerprint": key}]}))
        self.assertEqual(self.cli("check_class_extraction.py", "--json").returncode, 2)

    def test_copied_source_header_footer_block(self):
        for n in range(4):
            self.write("pages/%d.html" % n, '<header><nav><a href="/">Home</a></nav></header><main>%d</main><footer><p>Copyright</p></footer>' % n)
        result = self.cli("check_shared_layout.py", "--json")
        self.assertEqual(result.returncode, 1)
        self.assertEqual(len(json.loads(result.stdout)["findings"]), 3)

    def test_copied_nav_with_per_page_active_state_still_blocks(self):
        pages = ("home", "about", "contact")
        for page in pages:
            links = "".join('<li><a href="/%s"%s>%s</a></li>' % (
                p, ' aria-current="page" class="link active"' if p == page else ' class="link"', p) for p in pages)
            self.write("pages/%s.html" % page, "<header><nav><ul>%s</ul></nav></header><main>%s</main>" % (links, page))
        result = self.cli("check_shared_layout.py", "--json")
        self.assertEqual(result.returncode, 1, result.stdout)
        tags = sorted(f["tag"] for f in json.loads(result.stdout)["findings"])
        self.assertEqual(tags, ["header", "nav"])

    def test_different_nav_links_are_not_collapsed(self):
        for n in range(3):
            self.write("p%d.html" % n, '<nav><a href="/x%d" class="active">Section %d</a></nav>' % (n, n))
        self.assertEqual(self.cli("check_shared_layout.py", "--json").returncode, 0)

    def test_duplicate_css_sites_report_each_selector_line(self):
        text = "\n\n".join(".x%d {display:grid;\n  gap:1rem;\n  padding:2rem}" % n for n in range(3))
        _, data = self.css(text)
        self.assertEqual(data["findings"][0]["occurrences"], ["styles.css:1 .x0", "styles.css:5 .x1", "styles.css:9 .x2"])
        _, data = self.css("\n".join(".y%d {display:grid;gap:1rem;padding:2rem}" % n for n in range(3)))
        self.assertEqual(data["findings"][0]["occurrences"], ["styles.css:1 .y0", "styles.css:2 .y1", "styles.css:3 .y2"])

    def test_shared_partial_and_generated_output_do_not_block(self):
        chrome = '<header><a href="/">Home</a></header>'
        self.write("templates/header.html", chrome)
        for n in range(4):
            self.write("templates/p%d.html" % n, '{% include "header.html" %}<main>' + str(n) + '</main>')
            self.write("dist/p%d.html" % n, chrome)
        self.assertEqual(self.cli("check_shared_layout.py", "--json").returncode, 0)

    def test_html_comments_and_script_markup_are_not_chrome(self):
        for n in range(3):
            self.write("p%d.html" % n, '<!-- <header><a>Home</a></header> --><script>const x="<header><a>Home</a></header>";</script>')
        self.assertEqual(self.cli("check_shared_layout.py", "--json").returncode, 0)

    def test_preview_zero_writes_apply_idempotent_runner_blocks_escape(self):
        before = list(self.root.rglob("*"))
        result = self.cli("bootstrap_frontend_guards.py", "--class-guard-dir", str(CEG.parent))
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(before, list(self.root.rglob("*")))
        args = ("--class-guard-dir", str(CEG.parent), "--apply")
        self.assertEqual(self.cli("bootstrap_frontend_guards.py", *args).returncode, 0)
        contents = {str(p): (p.read_bytes(), p.stat().st_mtime_ns) for p in self.root.rglob("*") if p.is_file()}
        self.assertEqual(self.cli("bootstrap_frontend_guards.py", *args).returncode, 0)
        self.assertEqual(contents, {str(p): (p.read_bytes(), p.stat().st_mtime_ns) for p in self.root.rglob("*") if p.is_file()})
        self.write("pages/a.html", '<main style="display:grid"></main>')
        result = subprocess.run([sys.executable, str(self.root / "scripts/frontend-guards/run.py")], capture_output=True, text=True)
        self.assertEqual(result.returncode, 1)
        self.assertFalse((self.root / ".git/hooks/pre-commit").exists())

    def test_conflicting_bootstrap_config_prevents_all_writes(self):
        self.write(".class-guard.json", "{}")
        result = self.cli("bootstrap_frontend_guards.py", "--class-guard-dir", str(CEG.parent), "--apply")
        self.assertEqual(result.returncode, 2)
        self.assertFalse((self.root / "scripts").exists())

    def test_missing_bundle_resource_and_symlink_parent_block_without_writes(self):
        result = self.cli("bootstrap_frontend_guards.py", "--class-guard-dir", str(self.root / "absent"), "--apply")
        self.assertEqual(result.returncode, 2)
        self.assertFalse((self.root / "scripts").exists())
        with tempfile.TemporaryDirectory() as external:
            (self.root / "scripts").symlink_to(external, target_is_directory=True)
            result = self.cli("bootstrap_frontend_guards.py", "--apply")
            self.assertEqual(result.returncode, 2)
            self.assertEqual(list(Path(external).iterdir()), [])
            self.assertFalse((self.root / ".class-guard.json").exists())

    def test_existing_hook_is_never_overwritten(self):
        subprocess.run(["git", "init", "-q", str(self.root)], check=True)
        hook = self.write(".git/hooks/pre-commit", "#!/bin/sh\necho user hook\n")
        result = self.cli("bootstrap_frontend_guards.py", "--class-guard-dir", str(CEG.parent), "--apply", "--wire-precommit")
        self.assertEqual(result.returncode, 2)
        self.assertIn("user hook", hook.read_text())
        self.assertFalse((self.root / "scripts").exists())

    def test_plain_project_hook_wires_only_on_explicit_opt_in(self):
        subprocess.run(["git", "init", "-q", str(self.root)], check=True)
        result = self.cli("bootstrap_frontend_guards.py", "--class-guard-dir", str(CEG.parent), "--apply", "--wire-precommit")
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertTrue((self.root / ".git/hooks/pre-commit").is_file())
        self.assertTrue((self.root / ".git/hooks/pre-commit").stat().st_mode & 0o111)

    def test_css_whitespace_normalized_and_strings_kept_distinct(self):
        result, _ = self.css('.a {display:grid;gap: var(--gap);padding:2rem} .b { display : grid; gap:var( --gap );padding : 2rem;} .c{display:grid;gap:var(--gap);padding:2rem}')
        self.assertEqual(result.returncode, 1)
        result, _ = self.css('.a{content:"a b";display:grid;gap:1rem} .b{content:"ab";display:grid;gap:1rem} .c{content:"a b";display:grid;gap:1rem}')
        self.assertEqual(result.returncode, 0)

    def test_scoped_styles_and_css_modules_are_not_cross_file_equivalence(self):
        self.write(".class-guard.json", json.dumps({"rules": {"duplicate-css-block": "error"}}))
        for n in range(3):
            self.write("x%d.module.css" % n, '.card{display:grid;gap:1rem;padding:2rem}')
            self.write("x%d.vue" % n, '<style scoped>.card{display:grid;gap:1rem;padding:2rem}</style>')
        result = self.cli("check_class_extraction.py", "--json")
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)

    def test_bundle_catches_combined_four_page_escape(self):
        result = self.cli("bootstrap_frontend_guards.py", "--class-guard-dir", str(CEG.parent), "--apply")
        self.assertEqual(result.returncode, 0, result.stderr)
        for n in range(4):
            self.write("pages/%d.html" % n, '<header><a href="/">Home</a></header><main style="display:grid;width:1200px">%d</main><footer><p>Copyright</p></footer>' % n)
            self.write("styles/%d.css" % n, '.hash%d{display:grid;gap:var(--gap);padding:var(--pad)}' % n)
        result = subprocess.run([sys.executable, str(self.root / "scripts/frontend-guards/run.py")], capture_output=True, text=True)
        self.assertEqual(result.returncode, 1)
        for signal in ("no-inline-style", "duplicate-css-block", "shared-layout"):
            self.assertIn(signal, result.stdout)

    def test_shared_layout_exception_requires_reason(self):
        for n in range(2):
            self.write("p%d.html" % n, '<header><a>Home</a></header>')
        result = self.cli("check_shared_layout.py", "--json")
        key = json.loads(result.stdout)["findings"][0]["fingerprint"]
        self.write(".class-guard.json", json.dumps({"sharedLayout": {"allowlist": [{"fingerprint": key, "reason": "owner-approved independent demos"}]}}))
        self.assertEqual(self.cli("check_shared_layout.py", "--json").returncode, 0)
        self.write(".class-guard.json", json.dumps({"sharedLayout": {"allowlist": [{"fingerprint": key}]}}))
        self.assertEqual(self.cli("check_shared_layout.py", "--json").returncode, 2)

    def test_converter_preserves_native_metadata_and_exports_solo_roles(self):
        import shutil
        fake = self.root / "repo"
        shutil.copytree(REPO / "scripts", fake / "scripts")
        for path in list((REPO / "skills/roles").glob("*/SKILL.md")) + [REPO / "skills/contracts/contract-auditor/SKILL.md"]:
            target = fake / path.relative_to(REPO)
            target.parent.parent.mkdir(parents=True, exist_ok=True)
            shutil.copytree(path.parent, target.parent)
        for tool in ("claude-code", "gemini-cli"):
            result = subprocess.run(["bash", str(fake / "scripts/convert.sh"), "--tool", tool], capture_output=True, text=True)
            self.assertEqual(result.returncode, 0, result.stderr)
        native = fake / "integrations/claude-code/roles/frontend-agent/SKILL.md"
        self.assertIn('spawned_by: ["orchestrator"]', native.read_text())
        self.assertIn("disable-model-invocation: true", native.read_text())
        portable = fake / "integrations/gemini-cli/skills"
        self.assertEqual(len(list(portable.glob("*/SKILL.md"))), 11)
        self.assertIn("Explicit solo mode", (portable / "frontend-agent/SKILL.md").read_text())

    def test_native_and_solo_role_contracts(self):
        paths = list((REPO / "skills/roles").glob("*/SKILL.md")) + [REPO / "skills/contracts/contract-auditor/SKILL.md"]
        self.assertEqual(len(paths), 11)
        for path in paths:
            text = path.read_text()
            self.assertIn("requires_claude_code: false", text, str(path))
            self.assertIn("disable-model-invocation: true", text)
            self.assertIn("solo", text.lower())
            self.assertIn("UNVERIFIED", text)
            self.assertNotIn("For single-agent or ad-hoc work, this skill is not the right tool.", text)


if __name__ == "__main__":
    unittest.main()
