# Skill-Madness — Plan

> **Created:** 2026-05-26
> **Last updated:** 2026-06-23
> **Companions:** [`docs/REMAINING-WORK.md`](docs/REMAINING-WORK.md) (tactical ledger), [`docs/FUTURE.md`](docs/FUTURE.md) (frontier, out of scope)

> **Editing this doc?**
> 1. If you closed an item, also update the partner doc (closure log here, status in `docs/REMAINING-WORK.md`).
> 2. If you changed a phase claim or milestone, update [`START-HERE.md`](START-HERE.md)'s status table to match.

---

## Where we are

Skill-Madness is a mature **68-skill** library across **seven categories** — a contract-first multi-agent orchestrator (14 phases), 10 role agents with exclusive file ownership, contract/meta/git/workflow skills, and a **13-skill autonomous-loop library** — with a runtime + install layer on top. Several large efforts and two audits have landed; most recently the **entire autonomous-loop backlog** (`docs/research/DEEP-RESEARCH-LOOPS.md` §10) shipped across PRs #24–#30, taking the catalog 50 → 67:

1. **Skill curation** (from `DeepResearch/skills-comparative_deepdive/PLAN-skill-creator.md`): authored 8 new skills, migrated 6, merged 3 pairs into 3 unified skills, and applied 8 categories of bulk in-place edits. Fully executed.
2. **Ecosystem audit — surface pass** (`audit/MASTER_AUDIT_PLAN.md`, 7-dimension rubric, avg 4.49/5): all critical findings closed — 5 broken `composes_with` cross-references fixed, 7 oversized descriptions trimmed under the 1024-char ceiling, 2 missing frontmatter blocks restored. This was the *style / compliance / cross-ref* layer; its per-skill reports now live in `audit/reports-v1-sufrace/`.
3. **Runtime + install layer** (`BUILD_RESULTS.md`, shipped PR #8): hooks layer (qa-gate, post-edit-format, session-start-profile, pre-commit-lint), catalog-as-CI-invariant, plan/apply installer with profiles, skill-health telemetry, supply-chain skill-scan, and the **PSFS** frontmatter standard (`spec/PSFS.md` v1.1.0 + JSON Schema validator).
4. **Functional audit + remediation** (`audit/reports-v2/`, 2026-05-28): a deeper, second audit of all **49** skills on *function / triggerability / completeness / real bugs* (distinct from effort 2's surface pass). Verdict: 14 working, 35 partial-gaps, 0 broken; 4 P0 blockers plus a wiring/ownership/namespace integrity layer. **P0 + P1 remediation shipped** (PRs #15 and #16, both merged); the **plan ledger was reconciled** (PR #17); the **P2 fidelity backlog is filed** in the ledger (FA1–FA5).
5. **Catalog self-maintaining** (#23, 2026-06-02): the filesystem is now the single source of truth for the skill count — `catalog.sh --check`/`--sync` reconciles `plugin.json` plus the count phrasings in README/CLAUDE/PLAN/START-HERE, a pre-commit `catalog-sync` hook blocks drift before commit, and bundled `node_modules` SKILL.md scaffolds no longer inflate the count. This **closed FA3**.
6. **Autonomous-loop library + front door** (#24–#30, 2026-06-19 → 06-22): a new `skills/loops/` category (13 skills) plus the `madness` front-door router, built from the `DEEP-RESEARCH-LOOPS.md` §10 backlog. Every loop is a configuration of one `loop-controller` guardrail harness (iteration cap, token budget, no-progress breaker, fresh-context stop evaluator). Catalog 50 → 67, all CI green.

**What's left** is the *pre-loops* backlog (the loop library itself is fully shipped — see M6). Two buckets: (1) the original *documentation-polish* / process backlog — reference files and "thinking-move" docs from `IMPROVEMENT_PLAN.md` Phases 2–4 (mostly shipped; PR1 + PR2 + CL1/CL2/CL3 remain); and (2) the *functional-fidelity* backlog from the reports-v2 audit — P2 script/frontmatter/description truth-ups (FA1, FA2, FA4; FA5 cosmetic) and two open design decisions (FA7–FA8). FA3 (count drift) closed via #23 and FA6 (namespaces) closed 2026-06-01. See [`docs/REMAINING-WORK.md`](docs/REMAINING-WORK.md) — **11 items open** (incl. the new CL3 catalog-coverage gap).

## Milestones

- ✅ **M1 — Skill curation pass** (2026-05-17 era): catalog reshaped to 47 skills across 6 categories, `archive/` + `in-progress/` staging dirs established.
- ✅ **M2 — Ecosystem audit + fixes** (2026-05-20): 48 per-skill reports; all C1–C4 critical findings resolved.
- ✅ **M3 — Runtime + install layer** (2026-05-24, PR #8): hooks, installer discipline, telemetry, scanner, PSFS standard.
- 🟡 **M4 — Doc-polish / process (IMPROVEMENT_PLAN Phases 2–4 + later additions)**: reference files + thinking-move docs shipped (RF1–RF5, TM1–TM3). 5 items left in the ledger: PR1 (verify) + CL1/CL2 (cleanup) from the original plan, plus PR2 (changelog discipline, user report) and CL3 (catalog-coverage gap, FA3 residual) filed later. **Nearly done.**
- 🟡 **M5 — Functional audit (reports-v2) + remediation** (audit 2026-05-28; remediation 2026-05-30/31): P0 blockers (PR #15) and P1 wiring/ownership/namespace (PR #16) **both merged**; plan ledger reconciled (PR #17). FA6 namespaces resolved (2026-06-01); FA3 count-drift closed by #23 (2026-06-02). P2 truth-ups (FA1/FA2/FA4, FA5 cosmetic) + 2 design decisions (FA7–FA8) remain. **Remediation landed; P2 + 2 decisions open.**
- ✅ **M6 — Autonomous-loop library + front-door router** (#24–#30, 2026-06-19 → 06-22): the `DEEP-RESEARCH-LOOPS.md` §10 backlog **fully built** — a 13-skill `loops/` category (loop-controller + 12 concrete loops) wired into the orchestrator, plus the `madness` router (meta); catalog made self-maintaining (#23). Catalog 50 → 67; all CI green (lint matrix + `catalog.sh --check` + bats). **Backlog cleared.**

## Closure log

Items move here on ship. Format: `<ref> (date) — <one-line summary>`.

- **PLAN-skill-creator Phase 0** (2026-05-17) — `skills/archive/` (6 retired skills + README) and `skills/in-progress/` (empty, sync-excluded) established.
- **PLAN-skill-creator Phase 1** (2026-05-17) — 6 migrations: fly-hermes → `hermes-agent/.claude/skills/`; wiki-research, project-profiler → workflows; code-reviewer → `roles/code-review-agent`; dependency-coordinator contracts→workflows; interactive-doc → workflows (old `skills/docs/` removed).
- **PLAN-skill-creator Phase 2** (2026-05-17) — 3 merges: skill-improvement-plan + skill-updater → `meta/skill-update`; git-branch-cleanup + git-clean-worktrees → `git/git-post-merge-cleanup`; skill-audit + skill-deep-review → `meta/skill-review` (originals in `skills/archive/`).
- **PLAN-skill-creator Phase 3** (2026-05-17) — 8 new skills: diagnose-loop, grill-me, maintain-context, architecture-rescue, caveman, zoom-out, work-item-brief (perfect 5.00 audit), setup-project-skills.
- **PLAN-skill-creator Phase 4** (2026-05-17) — 8 bulk-edit categories applied: `disable-model-invocation` + rewritten descriptions on 12 orchestrator-internal skills; trigger phrases on 5 weak descriptions; length rule on 10 long skills; tradeoff caveats on 6; Anti-Pattern sections on 6; pipeline-position callouts on 11; "When this skill applies" on 14; XML→H2 heading conversion (WI-408 later reversed for plan-builder by audit finding I14).
- **MASTER_AUDIT C1–C4** (2026-05-20) — 5 broken cross-refs fixed (git-commit, skill-explorer ×2, sync-skills ×2); 7 oversized descriptions trimmed; 2 missing frontmatter blocks restored (dependency-coordinator, interactive-doc).
- **IMPROVEMENT_PLAN Phase 1** (spec alignment, A1–A6 + B10) — `frontmatter-spec.md` documents `allowed-tools` (hyphen canonical), `compatibility`, `argument-hint`, `disable-model-invocation`, angle-bracket prohibition, and the `[What]+[When]+[Key capabilities]` description anatomy; A4 enforced by the PSFS schema/lint.
- **IMPROVEMENT_PLAN Phase 5** (the compliance sweep) — satisfied by the MASTER_AUDIT campaign + PSFS schema validating all 47 skills clean (the catalog count at that time; now 49).
- **Runtime/install build P0–P3** (2026-05-24, PR #8) — hooks layer, catalog invariant, plan/apply install, skill-health, skill-scan, and PSFS v1.1.0 standard. Contracts in `contracts/`.
- **RF1–RF5** (2026-05-26, 515a172) — IMPROVEMENT_PLAN Phase 2 reference files authored: `patterns.md`, `quick-checklist.md`, `performance-notes.md`, `validation-script-pattern.md` (skill-writer) + `troubleshooting.md` (skill-explorer).
- **TM1–TM3** (2026-05-26, 8127c7c) — IMPROVEMENT_PLAN Phase 3 thinking moves authored + wired: `contradiction-finding` (wiki-research), `assumption-audit` (deployment-checklist + orchestrator phase-guide Phase 3), `second-order-effects` (plan-builder).
- **Functional audit** (2026-05-28, `audit/reports-v2/`) — second-layer audit of all 49 skills on function / triggerability / completeness / real-bugs (distinct from M2's surface pass). Verdict: 14 working, 35 partial-gaps, 0 broken; 4 P0 blockers plus wiring/ownership/namespace integrity issues. Rendered companion at `audit/reports-v2/00-MASTER-AUDIT.html`. Findings intaken to the ledger as FA1–FA8. *(Note: `audit/` is now gitignored — the reports live in the working tree, not version control.)*
- **FA-P0 — functional-audit blockers** (2026-05-30, PR #15, c2d10af) — `plugin.json` 46→49 (added `living-plan`, `plan-intake`, `render-sanity`); qe-agent schema prose reconciled to the canonical `qa-report-schema.json`; observability/performance/docs agents stop claiming a phantom QE gate score; setup-project-skills broken contract-template path fixed.
- **FA-P1 — wiring & integrity** (2026-05-30, PR #16, merged 2026-05-31) — 6 dead `spawned_by` edges trimmed; contract types standardized on flat `contracts/types.<ext>`; wiki layout canonicalized to root `index.md` + `wiki/`; `file-ownership.md` rebuilt canonical (no path owned twice; `.env.example`→infra; `docs/agents`→setup-project-skills; `docs/adr`→maintain-context); known plugin refs namespaced (5 left pending human confirm → FA6); `audit/` + `node_modules/` gitignored.
- **Living-plan reconciliation** (2026-05-31, PR #17) — re-synced PLAN / START-HERE / REMAINING-WORK / FUTURE / CLAUDE to reality (count 47→49), intaken the reports-v2 functional audit as ledger entries FA1–FA8, and untracked the 96 superseded v1 audit reports.
- **website-walkthrough-video skill** (2026-05-31) — added the 50th skill: a smooth full-site scrolling walkthrough-video generator (Playwright full-page capture + ffmpeg pan/render → desktop + mobile mp4s). Catalog 49→50.
- **FA6 — external namespace correctness** (2026-06-01) — corrected refs wrongly prefixed `superpowers:` on non-superpowers skills (`superpowers:ux-review`→`ux-review`, `superpowers:ui-ux-pro-max`→`ui-ux-pro-max`, `superpowers:frontend-design`→`frontend-design:frontend-design`) in render-sanity / ui-brief / claude-design-brief / frontmatter-spec; added a known-bare-externals whitelist to `lint-skills.sh`. The 5 "bare" refs the audit flagged were already correct (built-in commands + a global skill, not superpowers).
- **FA3 — doc-count single source of truth** (2026-06-02, PR #23, 4cf6e99) — made the filesystem the sole source of truth for the skill count: `catalog.sh` gained `--check`/`--sync` (CI-wired in `lint-skills.yml`), `-maxdepth` immunity to bundled `node_modules` SKILL.md scaffolds, and coverage of the count phrasings in README/CLAUDE/PLAN/START-HERE; `sync-catalog-skills.py` reconciles the `plugin.json` skills array with disk; a PreToolUse `catalog-sync` hook re-stages drift before commit; +5 bats; catalog contract → v1.1.0. Residual gap tracked as **CL3** (the README skill-table + architecture-diagram counts aren't covered by `--check`).
- **design-token-guard + use-freellmapi** (2026-06-19, PR #24, 98fd7e1) — two new workflow skills. Catalog 50 → 52 (self-reconciled by #23's tooling).
- **Loops category — foundation** (2026-06-21, PRs #25/#26/#27, b84e4fc/feaa582/ec43f09) — new `skills/loops/` category: `loop-controller` (the guardrail harness) + `fix-until-green`, wired into the orchestrator, plus `orchestrator-task-loop`. (#22 stopped the orchestrator dispatching role labels as subagent types; #28 aligned `primitives.md` with the ultracode rename.)
- **Autonomous-loop library complete + madness router** (2026-06-22, PR #30, d646b00) — the remaining 10 loops (contract-conformance, babysit, coverage, perf, self-healing, migration, nightly-docs-and-changelog, dependency-health, codebase-exploration, repo-cleanup) bringing `loops/` to 13, plus the `madness` front-door router (meta). The whole `DEEP-RESEARCH-LOOPS.md` §10 backlog is now built. Catalog → **67**; all CI green. (#29 excluded gitignored junk from the install-plan per-category disk count.)

---

## Frontier (out of scope)

Multi-host installer reach (the 184-agent / 11-tool agency-agents "convergence frontier"), a skill marketplace/registry, and per-host CI smoke tests are explicitly out of scope for now. See [`docs/FUTURE.md`](docs/FUTURE.md).
