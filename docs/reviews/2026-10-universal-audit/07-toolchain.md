# Toolchain, tests and hygiene — W7

## Snapshot and read-only procedure

Audited worktree HEAD `51106e1762205ab5a0b06b0d77ad8c69e8e33aba`; user's main worktree HEAD `d06cc28…` is different. [Baseline commands](evidence/baseline.txt) establish identity, no tracked integration files, ignored integrations, counts and absent root environment. Never merge statements about current main into baseline findings. In particular `cloudflare-pages-deploy` is not an active skill in this baseline, so its omission from generated baseline output is not a freshness defect.

Canonical source was read. Tests ran from a **new audit-local copy**, because tests and converters create temporary/generated output and the owner permits writes only in this report folder. [audit_checks.py](evidence/audit_checks.py) copies source and redirects `TMPDIR`, `BATS_TMPDIR` and hardcoded `/tmp` mktemp templates through an audit-local shim. This is not a skill-creator workspace or paid eval run. Environment had Bats and Python/PyYAML; jsonschema unavailable. No installs or credential import were needed; root environment values never printed/copied into reports.

The copy originally omitted tracked `.scan-skills-ignore`. That was this auditor's setup error. [final_checks.py](evidence/final_checks.py) restored it **in the audit copy only**, then reran scanner and supervised full tests with [rerun_tests.py](evidence/rerun_tests.py). No canonical ignore/script/skill file was changed. Logs preserve both the failure and correction. Audit-only copied trees/generated install scratch can be removed after receipts/manifests are retained; no preexisting file is eligible for cleanup.

## Real command results

| Command / execution context | Actual result | Receipt |
|---|---|---|
| `bash scripts/lint-skills.sh` / source snapshot | Exit 0; **0 errors, 120 warnings across 82** (76 active, six archives); schema check advisory without jsonschema | [full lint](evidence/lint-skills.txt) |
| `bash scripts/catalog.sh --check` / source snapshot | Exit 0; plugin listing/counts **76**, clean | [catalog](evidence/catalog-check.txt) |
| `bash tests/run-all.sh --tap` / first source snapshot | TAP 346: 345 ok including seven skips, **one fail at 306**; detached exit status UNVERIFIED | [original TAP](evidence/tests-run-all.txt), [honest first summary](evidence/test-summary.json) |
| `bats --tap tests/scan-skills/01-scan-skills.bats` / corrected snapshot | **15/15, exit 0** after restoring tracked ignore input | [correction:2](evidence/refutation-checks.txt#L2) |
| `bash scripts/scan-skills.sh --check skills/` / canonical tree | Exit 0; HIGH 0, MEDIUM 24, LOW 18 | [scan receipt:23](evidence/refutation-checks.txt#L23) |
| `bash tests/run-all.sh --tap` / corrected source snapshot | **346 planned = 339 passed + seven skipped; zero failed; exit 0** | [corrected full TAP](evidence/tests-run-all-corrected.txt), [summary](evidence/corrected-test-summary.json) |
| `bash scripts/convert.sh --out AUDIT/evidence/generated-sequential` / canonical source, audit output | **466 processed across 11 targets, 370 skipped, 0 errors; exit 0** | [full sequential output](evidence/convert-sequential.txt) |
| `bash scripts/convert.sh --parallel --jobs 3 --out AUDIT/evidence/generated-parallel` | **Exit 1:** macOS `xargs: command line cannot be assembled, too long`; worker path independently checked in audit snapshot | [parallel output](evidence/convert-parallel.txt) |
| Fresh plan for `copilot,gemini-cli,claude-code` with audit `--integrations`/`--root` | Exit 0; **741 operations**; zero Copilot script / Gemini manifest / Claude hook operations | [plan](evidence/fresh-install-plan.json), [compact counts](evidence/resource-delivery-summary.json) |

Selected exact excerpts:

```text
Results: 0 error(s), 120 warning(s) across 82 skills.
PASSED
EXIT_CODE=0

[OK]  plugin.json skills array matches disk (76 skills)
[OK]  catalog clean: counts + plugin.json listing all match disk (total = 76)
EXIT_CODE=0

[convert] processed 466 skills across 11 tools (370 skipped, 0 errors)
EXIT_CODE=0

xargs: command line cannot be assembled, too long
EXIT_CODE=1
```

Corrected full suite skipped these **seven**, not passed them:

```text
ok 336 schema passes Draft202012Validator.check_schema # skip python3 jsonschema not installed
ok 337 GATE: every real SKILL.md validates against the schema # skip python3 jsonschema not installed — cannot run real-tree schema gate
ok 338 fixture: minimal Core-valid frontmatter PASSES # skip python3 jsonschema not installed
ok 339 fixture: bad-semver version FAILS # skip python3 jsonschema not installed
ok 340 fixture: non-kebab name FAILS # skip python3 jsonschema not installed
ok 341 fixture: '<' in description FAILS # skip python3 jsonschema not installed
ok 342 fixture: bad min_plan enum FAILS # skip python3 jsonschema not installed
```

Source [CI:130](../../../.github/workflows/lint-skills.yml#L130) installs jsonschema/PyYAML; no evidence of missing CI schema enforcement. Linux CI was inspected, not executed in this session. The canonical scanner's MEDIUM review-language/external-composition warnings are not all security defects; HIGH 0 does not certify safety against every malicious skill.

## Generation freshness and targets — starting claims corrected

- **Absent/ignored, not stale tracked artifacts.** `git ls-files integrations` returned empty; canonical integrations were absent, and check-ignore confirmed the generated path. [generation comparison](evidence/generation-comparison.json) uses `committed_count` as a helper label, but all old counts are zero because there is no materialized baseline tree. Its `missing_names` means old-absent/fresh-present, **not skills omitted by fresh conversion**.
- Fresh Claude output has 76 bodies; nine per-skill non-Claude formats have 39 bodies each; Aider/Windsurf have **39 bodies each in a consolidated file**. Their `fresh_count:0` in that set comparison is not empty generation: the helper only counted per-skill filenames. [Sequential receipt:472/539](evidence/convert-sequential.txt#L472) confirms both consolidated outputs.
- **Windsurf implemented**, not dead: [converter targets/functions](../../../scripts/convert.sh#L30), [Windsurf install](../../../scripts/install.sh#L786). **Codex/Hermes/Devin have no baseline converter targets**: [target list](../../../scripts/install-plan.sh#L44). Native docs establish possible skill loading, not shipped library adapters.
- Conversion intentionally skips `requires_claude_code:true` for every non-Claude target at [711](../../../scripts/convert.sh#L711). This accurately explains missing roles/loops, but is too coarse for hosts with equivalent capabilities.
- CI enforces recursive Bats/catalog/schema/hooks/scan and version changes: [CI:117–151](../../../.github/workflows/lint-skills.yml#L117), [version gate:69](../../../.github/workflows/lint-skills.yml#L69). Determinism fixtures compare generated sample outputs, not every actual host's installed discovery/efficacy. F3/F5 already propose that coverage. A scheduled source-vs-generated drift test is not meaningful against nonexistent committed output; resource closure/installed smoke is.

## Delivery route map at this HEAD

Actual user's installed discovery path and counts are **UNVERIFIED**; table maps code-defined routes only. Current native host installation contracts require version/capability smoke before claiming support.

| Host / format | Converter route | Classic installation / plan | Raw sync baseline | Main risk |
|---|---|---|---|---|
| Claude Code | Categorized SKILL.md + references/scripts, generated hooks | `~/.claude/skills` + `~/.claude/ats-hooks`; opt-in settings wiring. Plan enumerates skill sources only | Category links into Claude skills | Assets/helpers omitted; plan lacks hooks; actual nested discovery UNVERIFIED |
| Copilot | Flat `.agent.md`, slug-references and slug-scripts | Mirrors `~/.github/agents` / `~/.copilot/agents`; classic misses script dirs; plan resolves references but not scripts | None | Generated helper programs lost; literal relative paths need rewriting |
| Gemini CLI | `skills/<slug>/SKILL.md` + refs/scripts, extension manifest | Classic keeps extension/skills shape. Plan strips `skills/` at enumeration and omits manifest | None | Plan output is not same installed extension; worker dry-run unsafe |
| Cursor | `rules/<slug>.mdc`, top-level refs inlined, separate scripts | Flat rules; resource dirs not equivalently installed | Flat **raw source** skills into `~/.cursor/skills` | Two content sets: 39 converted vs raw gated roles/loops included; activation fidelity untested |
| OpenCode | Flat agents, refs/scripts side directories | Classic flat `.md` only; plan script slug filter loss; global `.opencode` differs from official `.config/opencode` | None | Resource and current global-location mismatch |
| Qwen | Flat agents, top-level refs inline, scripts side dirs | Classic flat output loses script dirs; plan does not recognize slug-scripts | None | Nested refs and runnable resources incomplete |
| Antigravity / OpenClaw / Kimi | Per-skill directories / native multi-file envelopes | Directory copy broadly retains generated refs/scripts | None | Generated asset/helper closure incomplete; capability core filtered |
| Aider / Windsurf | Consolidated body file, references deliberately skipped | Project-scoped conventions/rules; explicit Aider read/config still necessary | None | Copy alone not activation; resource-dependent doctrine degraded |
| Codex / Hermes / Devin / `~/.agents` | None in baseline converter | None in baseline installer | **None in baseline sync** | Supplied seven-host sync/97-Codex claim describes another installation/revision, not this source |

Sources: [output contract](../../../contracts/installer/per-tool-output-spec.md#L1), [locations](../../../contracts/installer/install-locations.md#L1), [classic installer](../../../scripts/install.sh#L1), [plan resolver:165–228](../../../scripts/install-plan.sh#L165), [sync script](../../../skills/workflows/sync-skills/scripts/sync-skills.sh#L1). Updated official [OpenCode](https://opencode.ai/docs/agents/), [Devin](https://docs.devin.ai/product-guides/skills) and [Aider](https://aider.chat/docs/usage/conventions.html) docs checked live; exact host load was not executed.

## Verified defects and proof strength

### UA-08 — P0 parallel dry-run reset

[scripts/install.sh:47](../../../scripts/install.sh#L47) initializes `DRY_RUN=false`; worker entry before `main` bypasses `--dry-run` parsing. Parent exports dry-run, but child initialization overwrites it. Direct worker call used `ATS_INSTALL_WORKER=1`, `ATS_INSTALL_TOOL=gemini-cli`, exported `DRY_RUN=true`, `--dry-run`, a snapshot with fresh manifest and **fake HOME inside audit**. Result:

```text
[OK] Gemini CLI: 39 skills -> .../adversarial-fixtures/worker-home/.gemini/extensions/alltheskills
EXIT_CODE=0
worker wrote despite dry-run: True
```

[Full repro](evidence/refutation-checks.txt#L156). This proves unsafe worker path; does not claim serial dry-run writes, or that real HOME was affected. Fix flags after parsing/immutable worker payload and test parent-parallel route on supported userlands.

### UA-09 — parallel converter context, status and manifest

[Globals:43](../../../scripts/convert.sh#L43) reset exported output context; [worker:790](../../../scripts/convert.sh#L790) enters before `main`. Safe worker fixture reports requested output absent, default snapshot integrations present, Gemini manifest absent, exit 0. [Receipt:5299](evidence/adversarial-results.txt#L5299). Parent [875–919](../../../scripts/convert.sh#L875) concatenates nine worker receipts but only adds two serial counts; counted converter errors can be hidden by worker unconditional exit 0. Shell fatal errors can still escape under `set -e`, so “all errors are swallowed” is too broad. Actual parent attempt stopped earlier at macOS xargs limit; don't claim observed incorrect parent totals from that aborted run. Require semantic serial/parallel equivalence, aggregated statuses/counts and one manifest emission.

### UA-10/11 — resource closure and installation loss

[copy_references:109](../../../scripts/convert.sh#L109) and [copy_scripts:126](../../../scripts/convert.sh#L126) exist: PF1 is not undone. Neither copies assets, creator `agents/` / `eval-viewer/`, root living-plan templates or scanner/catalog helpers. Inline reference enumeration [152](../../../scripts/convert.sh#L152) maxdepth 1 omits nested Mermaid chart types/setup templates. Resource summary `source_assets:10` counts immediate source asset entries, **not total recursive asset files**; generated asset files zero.

[plan slug:228](../../../scripts/install-plan.sh#L228) understands `-references`, not `-scripts`; [Gemini roots:165/190](../../../scripts/install-plan.sh#L165) strip source `skills` without readding destination prefix. Fresh 741-operation plan has zero Copilot script operations, zero Gemini manifest and zero CC hook operations. Classic Copilot [540](../../../scripts/install.sh#L540), OpenCode/Cursor/Qwen flat copies similarly omit relevant helper dirs; classic Gemini shape is correct. Some converter references still literally name `references/...` after flattening into slug-reference directories: a source count cannot establish runnable installed paths.

Use one resource manifest plus explicit SKILL_ROOT or reference rewrites; verify installed resource closure in isolated HOME/cwd/PATH. Root `.env` must never be shipped; runtime secret-loader contract and explicit environment injection instead (UA-26).

### UA-21 — apply trusts reviewed plan metadata

Safe fixture changed source bytes **after hashing/planning**, source mode 755. Applied copied new bytes while state recorded old digest, destination mode 644, crafted destination outside declared `--root` was created. All destinations stayed under audit.

```text
EXIT_CODE=0
source_mode: 0o755
dest_mode: 0o644
stored_hash_matches_installed_bytes: false
outside_root_destination_created: true
```

[Exact receipt:5290](evidence/adversarial-results.txt#L5290), [apply:92–147](../../../scripts/install-apply.sh#L92). `--root` is only used for state, not destination containment. Missing source warns/continues; state is rewritten for this plan, not merged. Check plan schema/digest/safe real paths and symlink parents, preserve required modes, merge owned state, use atomic apply with recovery. Crafting a plan is required for the destination escape; ordinary plan resolution is not accused of malicious destinations.

### UA-20 — raw sync projection and ownership

Baseline supports CC/Cursor only, not all hosts in prompt. [flat link:412](../../../skills/workflows/sync-skills/scripts/sync-skills.sh#L412) discovers all skills rather than using selected TARGETS. [_do_link:393](../../../skills/workflows/sync-skills/scripts/sync-skills.sh#L393) removes existing destination copies without confirmation/backup; [clean:285](../../../skills/workflows/sync-skills/scripts/sync-skills.sh#L285) removes all broken links rather than only manifest-owned ones. **Source-inspected; collision/subset fixture not run.** Existing Claude fast symlinks can remain; non-Claude projection needs same resolver as conversion, ownership manifest and explicit collision policy. Do not delete unrelated skills or stale links simply because they are in a conventional host folder.

### QA/hook deployment caveats

[Strict missing-validator receipt](evidence/adversarial-results.txt#L64) reproduces UA-12. [qa-gate:35–41](../../../hooks/scripts/qa-gate.sh#L35) drains payload but does not inspect `stop_hook_active`, unlike [safety:40](../../../skills/loops/loop-controller/references/safety.md#L40). Payload-aware bounded reentry needed without weakening final verification. This is not a reintroduced TTY hang: DV1 guard and closed stdin test runner remain.

Generated wrapper uses `$CLAUDE_PROJECT_DIR/.claude/ats-hooks/run-with-flags.sh`; classic installer places hooks under `~/.claude/ats-hooks`. **Potential path mismatch, installed runtime execution UNVERIFIED**; no separate confirmed-bug row. Native manifest contains six events, not the task-loop template's TaskCompleted/TeammateIdle events. Keep native hooks opt-in; adapters must prove actual event fired and blocking semantics, not just write a hook file. Current converter “only Claude native lifecycle hooks” [934](../../../scripts/convert.sh#L934) is refuted by live [Gemini](https://geminicli.com/docs/hooks/) / [Cursor](https://cursor.com/docs/hooks) docs; adapters absent is the real statement.

## Repo hygiene and claims

- Filesystem count: contracts 2, git 4, loops 13, meta 7, orchestrator 1, roles 10, workflows 39 = **76**. Current README/CLAUDE/START count agrees; historical 69–73 milestones are not count drift. [baseline](evidence/baseline.txt), [catalog](evidence/catalog-check.txt).
- No `*-workspace/` directories under skills in measured tree. Root `.workspaces/` convention remains for actual skill-creator evaluations; this report-local fixture copy is not an iterative skill workspace. No per-skill environment was created.
- [START-HERE:8](../../../START-HERE.md#L8) still describes full Ubuntu+macOS CI broadly; actual macOS [CI:227](../../../.github/workflows/lint-skills.yml#L227) is `continue-on-error:true`. README's DV3 correction remains good; propose residual scoped wording only (UA-30), not re-open DV3 wholesale.
- README's claimed number of unguarded workflows needs a precisely defined gate taxonomy and full count; **UNVERIFIED**, no numerical drift finding filed. Physical/nonblank lines and words/tokens are distinct measurements; current lint/catalog should not imply host efficacy.
- Git PR [90](../../../skills/git/git-pr/SKILL.md#L90) uses unsupported `gh pr view --head`; real local help supports positional branch. [Receipt:5336](evidence/adversarial-results.txt#L5336). Feedback replies not equivalent to resolved threads; tag deletion order ambiguous/unsafe before approval by prose, not observed remote mutation (UA-22/23).

## Validation boundaries

No app build/typecheck target applies to a report-only shell/docs audit. Audit-helper Python syntax and selected shell syntax, Markdownlint, matrix/ledger coverage, proposal YAML structure, local links/line ranges, source hashes and git write boundary are checked in [final receipt](evidence/report-validation.txt). Local jsonschema absence is disclosed, not fixed by out-of-folder installation.

Live host discovery, hook firing, 76-skill trigger/efficacy runs, exact installed counts, paid price/model catalogs, actual Luna incident artifacts, Linux execution and production deployments were **not performed**. Existing tests green do not refute newly reproduced uncovered worker/resource/guard/QA defects. No implementation or intake followed this report.
