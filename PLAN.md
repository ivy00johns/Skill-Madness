# Skill-Madness — Plan

> **Created:** 2026-05-26
> **Last updated:** 2026-05-31
> **Companions:** [`docs/REMAINING-WORK.md`](docs/REMAINING-WORK.md) (tactical ledger), [`docs/FUTURE.md`](docs/FUTURE.md) (frontier, out of scope)

> **Editing this doc?**
> 1. If you closed an item, also update the partner doc (closure log here, status in `docs/REMAINING-WORK.md`).
> 2. If you changed a phase claim or milestone, update [`START-HERE.md`](START-HERE.md)'s status table to match.

---

## Where we are

Skill-Madness is a mature **58-skill** library — a contract-first multi-agent orchestrator (14 phases), 10 role agents with exclusive file ownership, contract/meta/git/workflow skills — with a runtime + install layer on top. Two large efforts and two audits have landed; the latest audit's P0+P1 remediation has now merged, with a P2 fidelity backlog filed:

1. **Skill curation** (from `DeepResearch/skills-comparative_deepdive/PLAN-skill-creator.md`): authored 8 new skills, migrated 6, merged 3 pairs into 3 unified skills, and applied 8 categories of bulk in-place edits. Fully executed.
2. **Ecosystem audit — surface pass** (`audit/MASTER_AUDIT_PLAN.md`, 7-dimension rubric, avg 4.49/5): all critical findings closed — 5 broken `composes_with` cross-references fixed, 7 oversized descriptions trimmed under the 1024-char ceiling, 2 missing frontmatter blocks restored. This was the *style / compliance / cross-ref* layer; its per-skill reports now live in `audit/reports-v1-sufrace/`.
3. **Runtime + install layer** (`BUILD_RESULTS.md`, shipped PR #8): hooks layer (qa-gate, post-edit-format, session-start-profile, pre-commit-lint), catalog-as-CI-invariant, plan/apply installer with profiles, skill-health telemetry, supply-chain skill-scan, and the **PSFS** frontmatter standard (`spec/PSFS.md` v1.1.0 + JSON Schema validator).
4. **Functional audit + remediation** (`audit/reports-v2/`, 2026-05-28): a deeper, second audit of all **49** skills on *function / triggerability / completeness / real bugs* (distinct from effort 2's surface pass). Verdict: 14 working, 35 partial-gaps, 0 broken; 4 P0 blockers plus a wiring/ownership/namespace integrity layer. **P0 + P1 remediation shipped** (PRs #15 and #16, both merged); the **plan ledger was reconciled** (PR #17); the **P2 fidelity backlog is filed** in the ledger (FA1–FA5).

**What's left** falls in two buckets: (1) the original *documentation-polish* backlog — reference files and "thinking-move" docs from `IMPROVEMENT_PLAN.md` Phases 2–4 (mostly shipped; PR1 + CL1/CL2 remain); and (2) the *functional-fidelity* backlog from the reports-v2 audit — P2 script/doc truth-ups (FA1–FA5), the 5 namespace refs awaiting confirmation (FA6), and two open design decisions (FA7–FA8). See [`docs/REMAINING-WORK.md`](docs/REMAINING-WORK.md).

## Milestones

- ✅ **M1 — Skill curation pass** (2026-05-17 era): catalog reshaped to 47 skills across 6 categories, `archive/` + `in-progress/` staging dirs established.
- ✅ **M2 — Ecosystem audit + fixes** (2026-05-20): 48 per-skill reports; all C1–C4 critical findings resolved.
- ✅ **M3 — Runtime + install layer** (2026-05-24, PR #8): hooks, installer discipline, telemetry, scanner, PSFS standard.
- 🟡 **M4 — Doc-polish (IMPROVEMENT_PLAN Phases 2–4)**: reference files + thinking-move docs shipped (RF1–RF5, TM1–TM3). 3 items left in the ledger (PR1 verify + CL1/CL2 cleanup). **Nearly done.**
- 🟡 **M5 — Functional audit (reports-v2) + remediation** (audit 2026-05-28; remediation 2026-05-30/31): P0 blockers (PR #15) and P1 wiring/ownership/namespace (PR #16) **both merged**; plan ledger reconciled (PR #17). P2 fidelity backlog filed (FA1–FA5); FA6 namespaces resolved (2026-06-01); 2 open design decisions remain (FA7–FA8). **Remediation landed; P2 + 2 decisions open.**

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

---

## Frontier (out of scope)

Multi-host installer reach (the 184-agent / 11-tool agency-agents "convergence frontier"), a skill marketplace/registry, and per-host CI smoke tests are explicitly out of scope for now. See [`docs/FUTURE.md`](docs/FUTURE.md).
