# Build Results — AllTheSkills P0 + P1 + P2

**Date:** 2026-05-24 · **Orchestrated build** · **Status: P0 + P1 + P2 COMPLETE (all QA gates PASS), uncommitted**
**Plan:** `DeepResearch/The-Hive/ecc_deepdive/source-material/14-alltheskills-frontier.md` → P0
**Contract:** `contracts/hooks/hooks-layer.md` v1.0.0

> ⚠️ **Nothing is committed.** The user was remote and could not approve Touch ID / GitHub commit-or-branch signing, so the build ran with a hard "no git writes" constraint. All changes are uncommitted working-tree edits on `main`. Review and commit when ready.

## What shipped (P0)

A complete hooks layer — the runtime-enforcement gap the ECC research identified as AllTheSkills' #1 missing capability. It turns the orchestrator's QA-gate doctrine into something actually enforced.

### New files
| Path | Role |
|------|------|
| `contracts/hooks/hooks-layer.md` | The binding interface spec (v1.0.0) |
| `hooks/hooks.manifest.json` | Canonical registry: 4 hooks (id/event/script/profiles/blocking) |
| `hooks/run-with-flags.sh` | Sole entrypoint; profile/disable gating + stdin pass-through dispatch |
| `hooks/lib/hook-flags.sh` | `ATS_HOOK_PROFILE` + `ATS_DISABLED_HOOKS` parsing; `is_enabled <id>` |
| `hooks/scripts/qa-gate.sh` + `qa-gate-validate.py` | **Marquee** Stop hook: validates `qa-report.json`, blocks on gate failure |
| `hooks/scripts/post-edit-format.sh` | PostToolUse: format edited file if a formatter is present |
| `hooks/scripts/session-start-profile.sh` | SessionStart: inject CLAUDE.md / profile.yaml (≤8 KB) |
| `hooks/scripts/pre-commit-lint.sh` | PreToolUse(git commit): warn-only skills lint |
| `scripts/lint-hooks.sh` | Lint gate for the hooks tree (mirrors `lint-skills.sh`) |
| `tests/hooks/` | bats suite (45 tests) + fixtures + runner |
| `coordination/hooks-p0-qa-report.json` | QE agent's schema-conformant QA report |

### Edited files (additive only — no restructuring)
- `scripts/convert.sh` — `convert_hooks_claude_code()` emits `integrations/claude-code/hooks/` + `hooks.json`; logs `unsupported` for the other 10 harnesses.
- `scripts/install.sh` — `install_hooks_claude_code()` installs to namespaced `~/.claude/ats-hooks/` (never merges user `settings.json`; prints the merge snippet). Also fixed a skill-walk bug that misclassified `hooks/` subdirs.
- `.github/workflows/lint-skills.yml` — added a `hooks-ubuntu` job (`lint-hooks.sh` + hooks bats); existing jobs untouched.
- `README.md` — added a `## 🪝 Hooks` section.

## QA gate

```json
{ "proceed": true,
  "reason": "No CRITICAL blockers; contract_conformance=5 (>=3); security=5 (>=3); status PASS." }
```
Scores: correctness/completeness/code_quality/contract_conformance/security all ≥4 (gate-relevant two = 5). Full report: `coordination/hooks-p0-qa-report.json`.

### Verification (independently re-run at the wave gate)
- `bash -n` clean on all 7 new/edited scripts; `py_compile` clean on the validator.
- qa-gate validator: PASS fixture → allow; 4 FAIL fixtures → block w/ correct reason; malformed/missing → exit 2. QE added **10 adversarial cases** (OR-semantics, `score==3` boundary, HIGH≠CRITICAL, type-confusion) — all correct.
- `scripts/lint-hooks.sh` → 0 errors. **hooks bats: 45/45.** **installer regression: 172/172 (no regression).**
- convert emits hooks for claude-code, `unsupported` for others; **no `integrations/` changes left in the tree.**
- Verified on real **bash 3.2.57**; no `eval`, no injection surface, `mktemp` temp dirs.

## Open issues (LOW/INFO — non-gating)
- ISS-001 — contract §1 ASCII tree draws the validator as nested under `qa-gate.sh`; it's correctly a sibling. Cosmetic doc fix.
- ISS-002 — `is_enabled` spawns python3 per call to read the manifest. Fine at P0 scale; revisit if hook latency matters.
- ISS-003 — `post-edit-format.sh` header comment omits `yaml/yml`, which it actually handles.

---

# P1 — Install discipline + catalog invariants

**Status: COMPLETE (QA gate PASS), uncommitted.** Built as two parallel workstreams (non-overlapping ownership), QA-verified independently, wave-gated.
**Contracts:** `contracts/installer/catalog-invariant.md` (A), `contracts/installer/plan-apply.md` (B).

## P1-A — Catalog-as-CI-invariant
- `scripts/catalog.sh` — `--check` (exit 1 on drift), `--sync`, `--text`. Source of truth = `skills/` minus `archive/` + `in-progress/`. **Authoritative count: 47** (orchestrator 1 · roles 10 · contracts 2 · meta 4 · git 4 · workflows 26).
- **Resolved real drift:** README was already correct at 47; `--sync` fixed `.claude-plugin/plugin.json` (46→47) and `.claude-plugin/marketplace.json` (41→47). Per-category mermaid labels are synced too, and the `| 47 |` table-row index is protected from clobbering.
- `tests/catalog/` — 8 bats (incl. an adversarial per-category-label-drift case). 8/8 pass.

## P1-B — Plan/apply install + install-state + profiles
- New, **alongside the untouched `install.sh`** (legacy path preserved, ECC-style): `scripts/install-plan.sh` (pure resolution → serializable JSON plan w/ sha256 per op), `scripts/install-apply.sh` (executor + idempotent `<root>/.claude/.ats-install-state.json`), `scripts/install-state.sh` (`list`/`drift`/`uninstall`/`repair`), `scripts/lib/install-state.sh`, `manifests/profiles.json` (5 profiles).
- **Content-hash install-state is the provenance ECC itself lacks** — drift detection and repair fall out of it.
- `tests/install-plan/` — 21 bats (full lifecycle + create/skip/overwrite + profile resolution). 21/21 pass.

## CI (orchestrator-wired)
Added an additive `installer-ubuntu` job to `.github/workflows/lint-skills.yml`: `catalog.sh --check` + `bats tests/catalog` + `bats tests/install-plan`. Existing jobs intact (`lint-ubuntu`, `hooks-ubuntu`, `installer-ubuntu`, `lint-macos`).

## P1 QA gate
`proceed=true` — correctness 5 · completeness 5 · code_quality 4 · contract_conformance 5 · security 5; no blockers. Report: `coordination/p1-qa-report.json`. Independently wave-gated (catalog clean, 8/8 + 21/21 bats, workflow parses, install.sh/convert.sh carry only P0 hooks changes). Composition check: P0's `qa-gate-validate.py` validates the P1 report → allow.

### P1 open issues (LOW/INFO — non-gating)
- ISS-P1-001 — `coordination/*qa-report.json` uses `schema_version: 1` (int) vs the repo's string-semver convention. Cosmetic.
- ISS-P1-002 — add a codified archive-exclusion regression test (nice-to-have).

### P1 handoff additions
- New scripts are **not yet wired into `install.sh`** by design — plan/apply is the new disciplined path beside the legacy installer. Decide later whether `install.sh` should delegate to it.
- `manifests/profiles.json` is new; review the 5 profile definitions.
- The count sync touched `plugin.json` + `marketplace.json` — verify those reads correctly before committing.

---

---

# P2 — Runtime feedback + safety

**Status: COMPLETE (QA gate PASS), uncommitted.** Two parallel workstreams, independently QE-verified, wave-gated.
**Contracts:** `contracts/installer/skill-health.md` (C), `contracts/installer/skill-scan.md` (D).

## P2-C — Skill-health telemetry
- `scripts/skill-health.sh` — `report` / `record` / `drift`. **Deterministic math in code** (named threshold/window constants), the explicit refusal of ECC's prompt-scoring anti-pattern: per-skill 7d/30d success rate, `declining` flag, and version-drift (recorded vs current frontmatter `version`).
- `hooks/scripts/skill-usage.sh` (+ manifest entry, profiles standard+strict, non-blocking) — coarse best-effort emitter.
- Additive "## Data source" pointers in `skills/meta/skill-review/SKILL.md` + `skills/meta/skill-update/SKILL.md`.
- `tests/skill-health/` — 17 bats. **Honest limitation:** Claude Code emits no clean "skill invoked → outcome" signal, so the emitter only attributes `Skill`-tool calls and records `outcome:unknown` (excluded from the success-rate denominator — tested). Version-drift needs no runtime signal and is the most reliable piece. The deterministic engine is ready for a richer host signal when one exists.

## P2-D — Skill supply-chain / injection scanner
- `scripts/scan-skills.sh` — `--check`/`--text`/`--json`; deterministic, LLM-free. Rules: secrets / private-keys / zero-width-unicode (HIGH), prompt-injection phrases / untrusted `composes_with` (MEDIUM), mcp-ref / long-base64 (LOW). Secret excerpts **redacted** (`AKIA****`). Inline `# scan-skills:ignore` + `.scan-skills-ignore` supported.
- **Real-tree scan is genuinely CLEAN: 0 HIGH, no ignore file needed.** The 12 MEDIUM are legit external cross-plugin `composes_with` refs (brainstorming, frontend-design, writing-plans, …); 13 LOW are mcp-ref inventory. No genuine secret anywhere.
- Additive "## Automated pre-scan" pointer in `skills/roles/security-agent/SKILL.md` (it consumes the scanner's findings rather than freelance-auditing).
- `tests/scan-skills/` — 15 bats + 6 QE-added adversarial = 21.

## CI (orchestrator-wired)
Added an additive blocking `security-ubuntu` job (`scan-skills.sh --check skills/` + `bats tests/scan-skills`). Workflow now has 5 jobs: `lint-ubuntu`, `hooks-ubuntu`, `installer-ubuntu`, `security-ubuntu`, `lint-macos`.

## P2 QA gate
`proceed=true` — correctness 5 · completeness 5 · code_quality 4 · contract_conformance 4 · security 5; 0 blockers. Report: `coordination/p2-qa-report.json`. Wave-gated (scanner clean on real tree, 17/17 + 21/21 bats, hooks regression 45/45 intact, 5 jobs parse, redaction leak count 0). Composition check: P0's `qa-gate-validate.py` validates the P2 report → allow.

### P2 issues (LOW/INFO — non-gating, addressed)
- ISS-P2-001 (LOW) — contract named non-existent `skill-audit`/`skill-improvement-plan`; the agent correctly used `skill-review`/`skill-update`, and **the contract has been corrected** to match reality.
- ISS-P2-002 (INFO) — the 12 legit MEDIUM `untrusted-composes` add triage noise; consider an external-skill allowlist later.
- ISS-P2-003 (INFO) — pre-existing frontmatter WARNs on the edited skills (not introduced by the additive prose).

### P2 handoff additions
- The skill-health emitter is **coarse by design** (host signal gap) — don't read empty/sparse health data as "skills are failing"; it means "no telemetry yet." Version-drift is the trustworthy signal today.
- The scanner is wired as a **blocking** CI gate. It's green now; if a future skill legitimately needs an injection-defense example, use the documented ignore mechanism (don't weaken the rule).

---

## Deferred (P3 — not built this session)
- **P3** — publish the AllTheSkills frontmatter spec (`skills/meta/skill-writer/references/frontmatter-spec.md`) as a named standard with the lint rules as its reference validator, so other collections (incl. ECC) can converge on it.

## Handoff for the user (when home)
1. **Review the diff, then commit** (signing will prompt Touch ID): the additive edits to `convert.sh`/`install.sh`/`lint-skills.yml`/`README.md` + the new `hooks/`, `scripts/lint-hooks.sh`, `tests/hooks/`, `contracts/hooks/`, `coordination/`. Your earlier `skills/workflows/repo-deep-dive/` changes are also still uncommitted and unrelated — commit separately if you like.
2. **markdownlint not run** (no `markdownlint-cli` locally; `npx` broken by nvm noise in the sandbox). Run `npx markdownlint-cli 'README.md' --ignore node_modules` before committing.
3. **`.claude-plugin/plugin.json` left unchanged** — it enumerates skills only, not scripts/hooks; the hooks ship via the installer's `~/.claude/ats-hooks/` path. Decide if you also want plugin-level hook registration.
4. **Project not configured for Skill-Madness conventions** — `docs/agents/` is absent; this build used defaults (single-context, format-by-detection, local `contracts/`). Run `/setup-project-skills` to make those sticky.
5. To actually enable the hooks in Claude Code: run `scripts/convert.sh --tool claude-code` then `scripts/install.sh --tool claude-code`, and merge the printed snippet into `~/.claude/settings.json`. (I did **not** run the installer — it writes into `~/.claude/`, which symlinks to this repo.)

## Mission skill manifest
- `qe-agent` — ✅ invoked (independent QE pass + `coordination/hooks-p0-qa-report.json`).
- `nano-banana` / `ui-ux-pro-max` / `frontend-design` / `ux-review` / `render-sanity` — N/A (no UI surface in this build).
- `code-review` / `security-review` — folded into the QE pass (no-eval/injection/portability spot-check); a dedicated pass is available on request.
