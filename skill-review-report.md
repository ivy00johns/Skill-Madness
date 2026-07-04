# Ecosystem Review Output
Reviewed: 2026-07-03T23:30:00Z
Scope: all — full-library review (bugs, inconsistencies, gaps, missing skills, fresh build ideas). Ran as five parallel review agents (cross-skill consistency, tooling/scripts/tests, docs-vs-reality, platform capability gaps, ecosystem/lifecycle scan) plus an inline frontmatter sweep. RV1–RV16, MA-1, F1–F4 and existing lint warnings were excluded as already-tracked.
Skills scanned: 71

## Executive Summary

- Total skills: 71 (7 categories; 6 archived skills excluded)
- Passing: 51 (72%) — 20 carry at least one WARN
- Issues found: 24 (0 critical, 2 high, 10 medium, 12 low)
- Ownership conflicts: 0 literal (1 semantic ambiguity noted)
- Test-suite ground truth: **317/317 bats tests pass locally** — but CI only runs ~128 of them
- Skill-health telemetry: **inert** (0 events ever recorded — emitter hook never wired)

The library itself is in good shape — frontmatter is 71/71 clean, no literal ownership overlaps, catalog counts all reconcile, and every test passes when actually run. The real defects are in the **meta-layer**: CI coverage, the portability claim, dead telemetry, and a recurring version-bump-drift pattern that this review caught three *new* instances of (the same pattern as the already-tracked RV8 — it keeps happening because nothing automates it).

The two headline items:

1. **H1 — The README's "ports cleanly to eleven hosts" story contradicts the frontmatter.** 57 of 71 skills carry `requires_claude_code: true`, and `scripts/convert.sh:664-682` skips those entirely for the 10 non-Claude-Code hosts. Only 14 skills actually convert. Every role, both contracts, all 13 loops, and the orchestrator port to zero hosts — while README:84 names "role definitions, contracts, workflows" as porting cleanly. Either the flag is over-applied (likely for many body-only skills) or the README overstates; today they simply contradict.
2. **H2 — CI never runs the two biggest test suites.** `.github/workflows/lint-skills.yml` names 6 test dirs explicitly; `tests/installer/` (172 tests — the suite that validates convert.sh output for all 11 hosts) and `tests/skill-health/` (17 tests) never gate a merge. 189 of 317 tests are dark in CI.

## Skill Inventory

| Skill | Category | Version | Desc Length | Body Lines | Refs | Status |
|-------|----------|---------|-------------|------------|------|--------|
| contract-auditor | contracts | 1.2.1 | 250 | 165 | 1 | PASS |
| contract-author | contracts | 1.4.0 | 818 | 223 | 7 | PASS |
| git-commit | git | 1.3.0 | 502 | 105 | 0 | PASS |
| git-post-merge-cleanup | git | 1.1.0 | 826 | 171 | 2 | PASS |
| git-pr | git | 1.3.0 | 553 | 114 | 0 | PASS |
| git-pr-feedback | git | 1.3.0 | 554 | 172 | 0 | PASS |
| babysit | loops | 1.0.0 | 962 | 130 | 1 | WARN |
| codebase-exploration-loop | loops | 1.0.0 | 894 | 155 | 1 | PASS |
| contract-conformance-loop | loops | 1.0.0 | 915 | 161 | 1 | PASS |
| coverage-loop | loops | 1.0.0 | 883 | 171 | 1 | PASS |
| dependency-health-loop | loops | 1.0.0 | 930 | 176 | 1 | PASS |
| fix-until-green | loops | 1.0.0 | 841 | 158 | 2 | PASS |
| loop-controller | loops | 1.1.0 | 801 | 297 | 3 | PASS |
| migration-loop | loops | 1.0.0 | 983 | 168 | 1 | WARN |
| nightly-docs-and-changelog | loops | 1.0.0 | 954 | 164 | 1 | WARN |
| orchestrator-task-loop | loops | 1.0.0 | 1017 | 215 | 2 | WARN |
| perf-loop | loops | 1.0.0 | 920 | 172 | 1 | PASS |
| repo-cleanup-loop | loops | 1.0.0 | 995 | 169 | 1 | WARN |
| self-healing-loop | loops | 1.0.0 | 909 | 154 | 1 | WARN |
| madness | meta | 1.0.0 | 910 | 157 | 0 | WARN |
| model-adaptation | meta | 1.0.0 | 987 | 167 | 2 | WARN |
| skill-catalog | meta | 1.0.0 | 772 | 132 | 0 | PASS |
| skill-explorer | meta | 1.1.0 | 752 | 139 | 2 | WARN |
| skill-review | meta | 1.2.0 | 550 | 144 | 3 | PASS |
| skill-update | meta | 1.2.0 | 502 | 139 | 2 | PASS |
| skill-writer | meta | 1.3.0 | 346 | 129 | 7 | WARN |
| orchestrator | orchestrator | 1.14.2 | 1023 | 285 | 11 | WARN |
| backend-agent | roles | 1.2.0 | 177 | 148 | 1 | PASS |
| code-review-agent | roles | 1.3.0 | 348 | 139 | 1 | PASS |
| db-migration-agent | roles | 1.2.0 | 193 | 104 | 2 | PASS |
| docs-agent | roles | 1.2.0 | 192 | 103 | 1 | PASS |
| frontend-agent | roles | 1.5.0 | 208 | 162 | 2 | PASS |
| infrastructure-agent | roles | 1.2.0 | 201 | 114 | 1 | PASS |
| observability-agent | roles | 1.2.0 | 176 | 114 | 1 | PASS |
| performance-agent | roles | 1.3.0 | 192 | 120 | 1 | PASS |
| qe-agent | roles | 1.4.0 | 232 | 109 | 5 | PASS |
| security-agent | roles | 1.2.0 | 232 | 149 | 1 | PASS |
| architecture-rescue | workflows | 1.1.0 | 595 | 51 | 2 | PASS |
| artifact-publish | workflows | 1.0.0 | 980 | 81 | 1 | WARN |
| caveman | workflows | 1.1.0 | 492 | 43 | 0 | PASS |
| class-extraction-guard | workflows | 1.0.1 | 984 | 103 | 4 | WARN |
| claude-design-brief | workflows | 1.4.0 | 786 | 104 | 6 | PASS |
| context-manager | workflows | 1.2.0 | 427 | 89 | 1 | WARN |
| dependency-coordinator | workflows | 1.1.0 | 238 | 103 | 3 | PASS |
| deployment-checklist | workflows | 1.2.0 | 372 | 65 | 2 | PASS |
| design-token-guard | workflows | 1.0.1 | 964 | 150 | 3 | WARN |
| diagnose-loop | workflows | 1.1.0 | 523 | 70 | 2 | PASS |
| find-unknowns | workflows | 1.0.0 | 1001 | 128 | 0 | WARN |
| grill-me | workflows | 1.1.1 | 528 | 12 | 0 | PASS |
| interactive-doc | workflows | 1.1.0 | 794 | 186 | 5 | WARN |
| living-plan | workflows | 1.1.0 | 456 | 148 | 0 | PASS |
| llm-wiki | workflows | 1.2.0 | 491 | 177 | 2 | PASS |
| maintain-context | workflows | 1.2.0 | 528 | 76 | 3 | PASS |
| mermaid-charts | workflows | 2.4.0 | 554 | 75 | 4 | WARN |
| nano-banana | workflows | 1.3.0 | 433 | 114 | 2 | PASS |
| plan-builder | workflows | 1.4.0 | 405 | 104 | 3 | PASS |
| plan-intake | workflows | 1.1.0 | 461 | 131 | 0 | PASS |
| playwright | workflows | 1.4.0 | 463 | 64 | 3 | PASS |
| project-profiler | workflows | 1.2.0 | 370 | 109 | 1 | PASS |
| railway-deploy | workflows | 1.3.0 | 356 | 71 | 3 | WARN |
| render-sanity | workflows | 1.1.0 | 834 | 141 | 2 | PASS |
| repo-deep-dive | workflows | 1.4.0 | 745 | 85 | 4 | PASS |
| settings-consolidator | workflows | 1.3.0 | 635 | 91 | 3 | PASS |
| setup-project-skills | workflows | 1.1.0 | 514 | 110 | 1 | PASS |
| sync-skills | workflows | 2.1.0 | 470 | 120 | 0 | PASS |
| ui-brief | workflows | 1.2.0 | 792 | 174 | 1 | PASS |
| use-freellmapi | workflows | 1.1.0 | 913 | 184 | 2 | WARN |
| website-walkthrough-video | workflows | 1.1.0 | 992 | 138 | 1 | WARN |
| wiki-research | workflows | 2.2.0 | 648 | 151 | 1 | PASS |
| work-item-brief | workflows | 1.1.0 | 576 | 76 | 3 | PASS |
| zoom-out | workflows | 1.1.0 | 445 | 14 | 0 | PASS |

## Ownership Map

No two role skills claim the same `owns.directories` or `owns.patterns` string. The canonical map in the orchestrator skill matches the role frontmatter.

### Conflicts

None literal. One **semantic** ambiguity (lint only checks string uniqueness, not glob intersection): `frontend-agent` owns `*.tsx`/`*.jsx` while `qe-agent` owns `*.test.*`/`*.spec.*` — a file like `Button.test.tsx` matches both. Worth one clarifying sentence in the ownership map (convention suggests qe wins on `.test./.spec.` infixes), and ideally a glob-intersection check in lint.

## Description Quality Ranking

| Rank | Skill | Score | Issues |
|------|-------|-------|--------|
| 1 | orchestrator | WARN | 1023/1024 chars — **1 char of headroom** before the spec's hard FAIL ceiling |
| 2 | orchestrator-task-loop | WARN | 1017/1024 chars |
| 3 | find-unknowns | WARN | 1001/1024 chars |
| 4 | repo-cleanup-loop | WARN | 995/1024 chars |
| 5 | website-walkthrough-video | WARN | 992/1024 chars |
| 6 | railway-deploy | WARN | lacks a trigger-context word (when/for/if/whenever) |
| 7 | use-freellmapi | WARN | doesn't start with an action verb |
| — | +7 more ≥950 chars | WARN | babysit, migration-loop, nightly-docs-and-changelog, model-adaptation, artifact-publish, class-extraction-guard, design-token-guard |

Systemic pattern (M10): the "pushy descriptions" convention is drifting the whole library toward the 1024 hard ceiling with **no lint warning band before the cliff** — the linter warns at 200 (soft) and fails at 1024, nothing in between. One more enthusiastic edit to the orchestrator description hard-fails the tree. Suggested fix: add a `WARN at >950` band to `lint-skills.sh`.

## Bulk Issues

### Frontmatter Violations

| Skill | Field | Issue |
|-------|-------|-------|
| (none) | — | 71/71 pass: name==dir, valid semver, required fields present, no `<`/`>` in values |
| 12 skills | description | Within ~70 chars of the 1024 hard ceiling (see ranking above) — M10 |
| artifact-publish | composes_with | References host-side skills `artifact-design`/`dataviz`; linter has no allowlist mechanism for non-namespaced external skills (colon-namespaced ones like `superpowers:*` are skipped by design, test 316) — L12 |

### Progressive Disclosure Violations

| Skill | Body Lines | Issue |
|-------|------------|-------|
| (none new) | — | No body exceeds 500 lines / 5,000 words except orchestrator (~6,110 words) — already tracked as RV16 |

### Cross-Skill Issues

| ID | Sev | Location | Description |
|----|-----|----------|-------------|
| H1 | high | README.md:9,57,84,663 + 57 skills' frontmatter | "Ports cleanly to eleven hosts" vs `requires_claude_code: true` on 57/71 skills — only 14 convert; roles/contracts/loops/orchestrator port to zero hosts. Audit the flag (likely over-applied to body-only skills) or rewrite the claim. |
| H2 | high | .github/workflows/lint-skills.yml | CI runs only ~128/317 bats tests; `tests/installer/` (172) and `tests/skill-health/` (17) never gate a merge. Add both suites (or run `bats -r tests/`) — see M2 for making that fast enough. |
| M1 | medium | scripts/skill-health.sh:60, scripts/install.sh:343-382 | Telemetry inert: the skill-usage PostToolUse hook is never merged into `~/.claude/settings.json` (installer prints a paste-snippet and stops), so `skill-events.jsonl` is never written — `report --json` returns 0 skills forever. Even wired, the emitter records only `outcome:unknown`, so success rates can never populate. Fix: opt-in installer merge step + a "telemetry inactive — hook not wired" banner in the report. |
| M2 | medium | scripts/convert.sh + scripts/lib/frontmatter.sh:30 | ~86s full run: `get_field`/`get_array` spawn a fresh python3 (importing PyYAML) per field read, × fields × 71 skills × 11 tools. Parse each SKILL.md once. This is also why `bats -r tests/` takes >10 min and why the installer suite blows its own 60s budget (100s). |
| M3 | medium | scripts/install-plan.sh:165-166 + install-apply.sh | Plan/apply path under-installs Copilot: writes only `~/.github/agents/`, never mirrors to `~/.copilot/agents/` — contradicting contracts/installer/install-locations.md:17, install.sh:403-419 (which writes both), and lib/install-state.sh:119's own comment. |
| M4 | medium | tests/ layout | `bats tests/` (non-recursive) runs **zero** tests and prints a green-looking `1..0`. Add a `tests/run-all.sh` or a Makefile target that does `bats -r tests/`, and say so in scripts/README.md. |
| M5 | medium | skills/meta/skill-explorer/SKILL.md:51 (+ evals/evals.json:15) | Skill-location map's brace list omits `loops` — an agent enumerating from it silently misses all 13 loop skills (~18% of the library). The eval fixture encodes the same omission. |
| M6 | medium | skills/meta/skill-writer/SKILL.md:88,102 | Dead link cited twice: `references/validation-checklist.md` doesn't exist (skill has quick-checklist.md / validation-script-pattern.md). |
| M7 | medium | README.md:531-663 | CLI reference documents flags that exit 2: `--only`, `--skip-claude-only`, `--verbose` (convert.sh uses `--tool`), `--skill` (lint-skills.sh takes a positional). scripts/README.md is correct — sync the root README to it. |
| M8 | medium | README.md:578-597 | "The four hooks" undercounts: hooks/hooks.manifest.json registers **six** (adds catalog-sync, skill-usage). Profile map wrong: standard fires 5, strict fires 6. |
| M9 | medium | START-HERE.md:19,21 + PLAN.md:26,67 | Narrative prose stale at catalog 69 — never records artifact-publish (#42) or find-unknowns as skills 70/71; PLAN's closure log violates its own :8-9 rule for both ships. |
| M10 | medium | scripts/lint-skills.sh | No warning band before the 1024 description hard ceiling (12 skills >950; orchestrator at 1023). |
| L1 | low | interactive-doc (1.1.0), mermaid-charts (2.4.0), model-adaptation (1.0.0) | Three NEW instances of the RV8 no-version-bump pattern: #42 added whole sections to the first two; #40 made substantive content changes to the third. The pattern now has 6 known instances — see Recommendation 4. |
| L2 | low | skills/meta/skill-writer/references/body-template.md | Orphan reference — never mentioned in skill-writer's SKILL.md (and RV14 wants README pointed at it). |
| L3 | low | skills/meta/madness/SKILL.md:135 (+ evals.json:36) | Stale count: "not all 60 skills" — reality 71. |
| L4 | low | orchestrator/SKILL.md:225; context-manager/SKILL.md:24,35,90 | Cross-skill paths drop the `skills/` prefix that every other skill uses (`roles/qe-agent/...`, `orchestrator/references/...`) — don't resolve from repo root as written. |
| L5 | low | skills/loops/self-healing-loop/SKILL.md:151 | Bare `references/primitives.md` with no `loop-controller` qualifier — reads as a missing local file; every sibling loop attributes it. |
| L6 | low | frontend-agent / qe-agent owns.patterns | Semantic glob intersection (`Button.test.tsx`) — see Ownership Conflicts. |
| L7 | low | mermaid-charts/evals/evals.json:101 | Fixture describes the library as "17 skills". |
| L8 | low | README.md:100 | "bash ≥4" prerequisite vs the bash-3.2 idioms + macOS CI job that exists specifically to keep 3.2 working — one of the two is wrong. |
| L9 | low | README.md:451-484 | Project-structure tree omits `hooks/` and `spec/`, both documented in their own README sections. |
| L10 | low | contracts/installer/plan-apply.md:21-28 | `full` profile documented with 6 categories (no loops); manifests/profiles.json correctly has 7. Contract lags code. |
| L11 | low | scripts/install-plan.sh:43 | Tools whose convert.sh sources are missing yield a silent EMPTY plan (resolver `continue`s) instead of an error. Latent — currently all 11 covered. |
| L12 | low | scripts/lint-skills.sh | No `known_external` entry mechanism for non-namespaced host skills (artifact-design, dataviz) — artifact-publish warns forever or drops accurate metadata. |

## Coverage Gaps

Platform surfaces of Claude Code (mid-2026) with **no skill coverage** (from the capability-gap agent's audited table — PARTIAL/COVERED surfaces omitted):

| Capability | Status |
|------------|--------|
| Hook **authoring** (all event types — PreToolUse/PostToolUse/Stop/SessionStart…) | NOT COVERED — the library's gates are all advisory/skippable; hooks are only consumed as Agent-Teams loop plumbing |
| Building MCP servers (vs consuming them) | NOT COVERED |
| Agent SDK / headless `claude -p` as CI/cron jobs | NOT COVERED (named as a loop primitive only) |
| Auto-memory directory curation / /remember | NOT COVERED (project-profiler writes CLAUDE.md; nothing curates memory) |
| PushNotification / notify-on-HITL-gate | NOT COVERED (zero references anywhere) |
| Measured skill-trigger evals | OUTSOURCED — skill-review punts to external /skill-creator "if available"; the library's core "pushy descriptions" value prop is never measured |
| claude-in-chrome (authed real-browser flows) | NOT COVERED (all browser skills use unauthed Playwright) |
| Prompt-caching economics | NOT COVERED |
| Scoped permission profiles for unattended loops | PARTIAL — every loop hand-waves it inline |
| Scheduled-routine management (author/list/monitor/detect-failed) | PARTIAL — each loop re-derives scheduling ad hoc |
| Checkpoints / rewind | NOT COVERED (thin; fold into loop-controller) |

Lifecycle stages with no skill (ecosystem agent): release-cutting/versioning, live-incident coordination + postmortems, WCAG/a11y auditing, license/SBOM compliance, load testing, threat modeling (pre-build), ADR authoring, feature flags, i18n readiness, synthetic seed data, human (non-agent) onboarding, contract **mocking** (author→verify exists; serve-a-fake doesn't).

## Recommendations

1. **[CI] Close the dark-test gap (H2 + M2 + M4).** Add `tests/installer` + `tests/skill-health` to lint-skills.yml (or switch to `bats -r tests/`), and make it affordable by fixing convert.sh's parse-once performance (86s → seconds). One PR, three findings.
2. **[Identity] Resolve the portability contradiction (H1).** Audit `requires_claude_code` across the 57 flagged skills — most body-only skills (roles describe capabilities, not CC tool names) can likely drop it; rewrite README:84's claim to match whatever the audit yields. This decides what the "eleven hosts" story actually is, and F1 (multi-host frontier) depends on it.
3. **[Trust] Make skill-health real or honest (M1).** Either ship the opt-in settings.json merge so telemetry actually flows, or print "inactive — hook not wired" in every report. A silent 0-row report reads as "no usage" and quietly poisons skill-review's data-source step.
4. **[Root cause] Kill the version-drift pattern with tooling, not vigilance (L1 + RV8).** Six known instances now. Per the repo's own recurring-pain rule, hand-patching is over: build the `release-cut` skill (infer bump from conventional commits, bump frontmatter + manifests, tag, notes) and/or a lint check that flags SKILL.md body diffs without a version change in the same PR.
5. **[Fix batch] One cleanup PR for the mechanical items:** M5 (add `loops` to skill-explorer's map + fixture), M6 (repoint dead link), M7/M8/L3/L4/L5/L7/L9 (doc/path/count corrections), M10 + L12 (two small lint-skills.sh additions), L10 (contract doc), M9 (narrative refresh). All are one-liners; feed this report's JSON sidecar to `/skill-update` to plan it.

## Per-Skill Scores

| Skill | Frontmatter | Description | Disclosure | Consistency | Overall |
|-------|-------------|-------------|------------|-------------|---------|
| contract-auditor | PASS | PASS | PASS | PASS | PASS |
| contract-author | PASS | PASS | PASS | PASS | PASS |
| git-commit | PASS | PASS | PASS | PASS | PASS |
| git-post-merge-cleanup | PASS | PASS | PASS | PASS | PASS |
| git-pr | PASS | PASS | PASS | PASS | PASS |
| git-pr-feedback | PASS | PASS | PASS | PASS | PASS |
| babysit | PASS | WARN | PASS | PASS | WARN |
| codebase-exploration-loop | PASS | PASS | PASS | PASS | PASS |
| contract-conformance-loop | PASS | PASS | PASS | PASS | PASS |
| coverage-loop | PASS | PASS | PASS | PASS | PASS |
| dependency-health-loop | PASS | PASS | PASS | PASS | PASS |
| fix-until-green | PASS | PASS | PASS | PASS | PASS |
| loop-controller | PASS | PASS | PASS | PASS | PASS |
| migration-loop | PASS | WARN | PASS | PASS | WARN |
| nightly-docs-and-changelog | PASS | WARN | PASS | PASS | WARN |
| orchestrator-task-loop | PASS | WARN | PASS | PASS | WARN |
| perf-loop | PASS | PASS | PASS | PASS | PASS |
| repo-cleanup-loop | PASS | WARN | PASS | PASS | WARN |
| self-healing-loop | PASS | PASS | PASS | WARN | WARN |
| madness | PASS | PASS | PASS | WARN | WARN |
| model-adaptation | PASS | WARN | PASS | WARN | WARN |
| skill-catalog | PASS | PASS | PASS | PASS | PASS |
| skill-explorer | PASS | PASS | PASS | WARN | WARN |
| skill-review | PASS | PASS | PASS | PASS | PASS |
| skill-update | PASS | PASS | PASS | PASS | PASS |
| skill-writer | PASS | PASS | PASS | WARN | WARN |
| orchestrator | PASS | WARN | PASS | WARN | WARN |
| backend-agent | PASS | PASS | PASS | PASS | PASS |
| code-review-agent | PASS | PASS | PASS | PASS | PASS |
| db-migration-agent | PASS | PASS | PASS | PASS | PASS |
| docs-agent | PASS | PASS | PASS | PASS | PASS |
| frontend-agent | PASS | PASS | PASS | PASS | PASS |
| infrastructure-agent | PASS | PASS | PASS | PASS | PASS |
| observability-agent | PASS | PASS | PASS | PASS | PASS |
| performance-agent | PASS | PASS | PASS | PASS | PASS |
| qe-agent | PASS | PASS | PASS | PASS | PASS |
| security-agent | PASS | PASS | PASS | PASS | PASS |
| architecture-rescue | PASS | PASS | PASS | PASS | PASS |
| artifact-publish | PASS | WARN | PASS | WARN | WARN |
| caveman | PASS | PASS | PASS | PASS | PASS |
| class-extraction-guard | PASS | WARN | PASS | PASS | WARN |
| claude-design-brief | PASS | PASS | PASS | PASS | PASS |
| context-manager | PASS | PASS | PASS | WARN | WARN |
| dependency-coordinator | PASS | PASS | PASS | PASS | PASS |
| deployment-checklist | PASS | PASS | PASS | PASS | PASS |
| design-token-guard | PASS | WARN | PASS | PASS | WARN |
| diagnose-loop | PASS | PASS | PASS | PASS | PASS |
| find-unknowns | PASS | WARN | PASS | PASS | WARN |
| grill-me | PASS | PASS | PASS | PASS | PASS |
| interactive-doc | PASS | PASS | PASS | WARN | WARN |
| living-plan | PASS | PASS | PASS | PASS | PASS |
| llm-wiki | PASS | PASS | PASS | PASS | PASS |
| maintain-context | PASS | PASS | PASS | PASS | PASS |
| mermaid-charts | PASS | PASS | PASS | WARN | WARN |
| nano-banana | PASS | PASS | PASS | PASS | PASS |
| plan-builder | PASS | PASS | PASS | PASS | PASS |
| plan-intake | PASS | PASS | PASS | PASS | PASS |
| playwright | PASS | PASS | PASS | PASS | PASS |
| project-profiler | PASS | PASS | PASS | PASS | PASS |
| railway-deploy | PASS | WARN | PASS | PASS | WARN |
| render-sanity | PASS | PASS | PASS | PASS | PASS |
| repo-deep-dive | PASS | PASS | PASS | PASS | PASS |
| settings-consolidator | PASS | PASS | PASS | PASS | PASS |
| setup-project-skills | PASS | PASS | PASS | PASS | PASS |
| sync-skills | PASS | PASS | PASS | PASS | PASS |
| ui-brief | PASS | PASS | PASS | PASS | PASS |
| use-freellmapi | PASS | WARN | PASS | PASS | WARN |
| website-walkthrough-video | PASS | WARN | PASS | PASS | WARN |
| wiki-research | PASS | PASS | PASS | PASS | PASS |
| work-item-brief | PASS | PASS | PASS | PASS | PASS |
| zoom-out | PASS | PASS | PASS | PASS | PASS |

Details available via `--scope=<name>` follow-up. WARN drivers: Description = near the 1024-char hard ceiling (>950) or lint-flagged phrasing; Consistency = named in a cross-skill finding (see Bulk Issues).

## Appendix — Fresh Build Ideas (new-skill backlog candidates)

Two independent ideation agents ran — one auditing the Claude Code platform surface, one scanning external ecosystems + the software-delivery lifecycle. Both were deduped against all 71 skills, FUTURE.md, and REMAINING-WORK.md. **They converged independently on the same #1.** Ranked by (identity fit × evidence × convergence); difficulty S/M/L.

### Tier 1 — build these first

1. **`skill-eval`** (meta, M/L) — *both agents' top pick, independently.* Empirical eval harness for the library's own skills: generate should-trigger / should-NOT-trigger prompt sets, run each in clean-context subagents, report trigger precision/recall + rubric-scored behavior; A/B two description versions; gate on a threshold. Today skill-review is heuristic and explicitly punts to external `/skill-creator` "if available" — so the library's central value prop ("pushy descriptions" = reliable triggering) is *never measured*, in a repo whose own memory logs repeated trigger/catalog pain. Closes the loop: skill-writer authors → skill-eval scores → skill-update fixes. DoD: reproducible JSON scorecard per skill.
2. **`mock-from-contract`** (contracts, M) — Turn an authored OpenAPI/AsyncAPI contract into a runnable, schema-faithful mock server with deterministic seeded responses, so consumer agents build against a live fake before the backend exists. Completes the contract pipeline this library already owns: contract-author → **mock-from-contract** → parallel build → contract-conformance-loop. DoD: curl-able server whose responses validate against the spec. (Would grow `contracts/` from 2 skills to 3 — its first addition since v1.)
3. **`hook-forge`** (meta, L) — Author, install, and test hooks across ALL event types: write the matcher + script, dry-run it, wire into settings.json, verify it fires. Every gate in the library today (render-sanity, design-token-guard, qa-gate…) is advisory and skippable — this is the missing deterministic-enforcement layer ("make render-sanity a non-bypassable Stop hook"; "block Edit on token files via PreToolUse"). Also directly fixes M1's class of problem (hooks that exist but never get wired).
4. **`release-cut`** (git, M) — Infer semver bump from conventional commits, bump version fields everywhere (including skill frontmatter), generate release notes, tag, open the GitHub release. *Triple-evidenced internally:* RV8 + the three new drift instances this review found (L1) + the repo's own "2nd repeat = fix the root cause" memory rule. Would take `git/` from 4 to 5 skills.
5. **`autonomy-profile`** (loops, M) — Design the scoped permission allowlist + sandbox profile a given loop needs to run unattended: enumerate exact tools/paths, generate the settings block, verify a dry pass never prompts. Every one of the 13 loops currently hand-waves this inline; it's the single biggest unblock for the loops/ category's actual promise (walk away and it keeps going).

### Tier 2 — strong, clearly-scoped

6. **`mcp-server-author`** (workflows, M/L) — Scaffold + implement + smoke-test a stdio MCP server exposing a project's own capabilities to Claude Code, then register it. The toolkit consumes a dozen MCPs and can't build one; natural companion to contract-author (a tool schema is a contract).
7. **`incident-response`** + **`postmortem`** (workflows, M + S) — The operate-end pair: HITL live-incident harness (severity, running timeline, mitigate-before-RCA, approval before prod-touching actions) and the blameless retro whose action items feed straight into plan-intake. Today the only operate-stage skill is autonomous (self-healing-loop); there's no human coordination layer and no retro artifact.
8. **`memory-curator`** (meta, M) — Set up + maintain the auto-memory convention (one-fact-per-file, MEMORY.md index, frontmatter types): dedupe, lint stale entries, verify referenced files/flags still exist. You already run exactly this workflow by hand — with zero tooling.
9. **`notify-on-event`** (workflows, S) — Wire PushNotification / SendMessage so long builds and loops ping you on completion or when they hit a HITL gate. Zero PushNotification references exist in the library, yet the whole loop identity depends on reaching you when it matters. Smallest idea on the list; arguably the best effort-to-value ratio.
10. **`worktree-fanout`** (workflows, M) — Per-agent worktree isolation on the Agent-Teams build path (+ merge-back protocol), upgrading the orchestrator's exclusive-file-ownership from convention to physical impossibility.
11. **`headless-runner`** (workflows, M/L) — Package a loop as a non-interactive job: `claude -p` streaming-JSON, exit codes, result parsing, or a thin Agent SDK app — so fix-until-green/self-healing-loop can run in GitHub Actions/cron instead of an open terminal.
12. **`routine-manager`** (loops, M) — Author/list/monitor scheduled cloud agents generally: routine catalog, "did last night's run actually fire", failure drift. nightly-docs, dependency-health, and self-healing each re-derive scheduling ad hoc; this is the shared substrate.

### Tier 3 — the quality-gates & lifecycle family (pick by appetite)

13. **`a11y-audit`** (workflows, M) — WCAG 2.2 A/AA audit + remediation (axe-core real-DOM + jsx-a11y CI). Note: ux-review/playwright *mention* "accessibility audit" as a trigger phrase but neither runs a WCAG pass — today that phrase routes to a skill that can't deliver it.
14. **`secret-scan-gate`** (workflows, S/M) — Staged-diff secret/key/.env scan as a fast pre-commit/PR gate (distinct from security-agent, a build-time role). Classic catches-what-tests-miss.
15. **`license-audit`** (workflows, M) — SBOM (Syft→CycloneDX/SPDX) + copyleft-conflict + declared-license-vs-manifests check. Internally evidenced by RV2 — this repo itself claims MIT with no LICENSE file.
16. **`flake-hunter`** (workflows/loops, M) — Re-run the suite N times under jitter/ordering to catch flaky tests before they poison a green gate. A gate that protects the gates (fix-until-green and coverage-loop currently trust a single green run).
17. **`threat-model`** (workflows, M) — Pre-build STRIDE pass feeding mitigations into contracts/work-items (security-agent audits *after* build; nothing runs design-time).
18. **`adr-author`** (workflows, S) — Write/supersede/index ADRs (setup-project-skills bootstraps the folder; zoom-out reads them; nothing writes them).
19. **`load-test`** (workflows, M) — k6/Locust script seeded from the contract; assert throughput/p95/p99 vs an SLO (perf-loop optimizes single-run metrics, never concurrency).
20. **`model-router`** (meta, S/M) — Per-role cost-optimal model assignment + enforce explicit `model:` on every spawn (operationalizes the existing subagent-model lesson in your memory).
21. Also surfaced, lower urgency: `browser-authed-flows` (claude-in-chrome for logged-in testing), `plugin-packager` (concrete packaging step under FUTURE-F2), `cache-optimizer` (prompt-cache-aware agent prompts), `feature-flag`, `seed-data-forge`, `human-onboarding`, `i18n-audit`.

### Suggested first wave

`skill-eval` + `release-cut` + `notify-on-event` (one M/L, one M, one S — and all three are self-serving: they harden this repo itself), then `mock-from-contract` + `hook-forge` + `autonomy-profile` as the identity-defining second wave. Run `plan-intake` on this appendix to turn the chosen subset into ledger entries with fresh IDs.
