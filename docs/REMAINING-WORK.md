# Remaining Work — Tactical Ledger

**Last updated:** 2026-06-23
**Companions:** [`PLAN.md`](../PLAN.md) (strategic roadmap + closure log), [`docs/FUTURE.md`](FUTURE.md) (frontier overflow)

> **Status at a glance (2026-06-23):** The **autonomous-loop library is DONE** — 13 loops + the `madness` router shipped via PRs #24–#30 (`docs/research/DEEP-RESEARCH-LOOPS.md` §10 backlog fully cleared; catalog 50 → 67). That work was tracked in the research doc, not as ledger entries here, so there is nothing to close out below for it. **The 11 items still open below are the older *pre-loops* backlog** (doc-polish/process + reports-v2 functional-fidelity): PR1, PR2, CL1, CL2, CL3, FA1, FA2, FA4, FA5 (cosmetic), FA7, FA8 (decisions). FA3 (count drift) and FA6 (namespaces) are now closed.

> **Editing this doc?**
> 1. If you closed an item, also update the partner doc (closure log in `PLAN.md`, status here).
> 2. If a finding comes from a report (audit, deep-dive, skill-review), intake it via the `plan-intake` skill — don't hand-add.

## How this is organized

Every entry has **Priority** (P0–P3), **Area**, **Source**, **Status**, **Owner**, and a body. Entries are grouped by Area. ID prefixes are stable and never reused: `RF` (reference-file gaps), `TM` (thinking-move additions), `PR` (process additions), `CL` (cleanup), `FA` (functional-audit findings). The RF/TM/PR/CL items trace to `IMPROVEMENT_PLAN.md` Phases 2–4 (archived) and were verified still-open against the repo on 2026-05-26; the FA items were intaken from the reports-v2 functional audit on 2026-05-31.

Source short-links: `[IP]` → `docs/archive/superseded-plans/IMPROVEMENT_PLAN.md`; `[FAUDIT]` → `audit/reports-v2/00-MASTER-AUDIT.md` (gitignored — local working tree only). For shipped work see the closure log in [`PLAN.md`](../PLAN.md).

---

## Reference files (skill-writer / skill-explorer)

### RF1 — `patterns.md` for skill-writer (5 emergent Anthropic patterns)
**P2 · Skill-writer · closed (2026-05-26, 515a172) · Owner: —** · Source: [IP] Phase 2 / B5
Create `skills/meta/skill-writer/references/patterns.md` documenting the 5 emergent skill patterns adopted from Anthropic's May 2026 Agent Skills guide. The references dir currently holds only `frontmatter-spec.md` + `description-patterns.md`.

### RF2 — `quick-checklist.md` for skill-writer
**P3 · Skill-writer · closed (2026-05-26, 515a172) · Owner: —** · Source: [IP] Phase 2 / B6
Create `skills/meta/skill-writer/references/quick-checklist.md` — a fast pre-ship checklist for new skills.

### RF3 — `troubleshooting.md` for skill-explorer
**P3 · Skill-explorer · closed (2026-05-26, 515a172) · Owner: —** · Source: [IP] Phase 2 / B7
Create `skills/meta/skill-explorer/references/troubleshooting.md`. The references dir currently holds only `routing-table.md`.

### RF4 — `## Performance Notes` pattern doc
**P3 · Skill-writer · closed (2026-05-26, 515a172) · Owner: —** · Source: [IP] Phase 2 / B8
Document the optional `## Performance Notes` section pattern (when/how a skill records perf characteristics) as a reference for skill authors.

### RF5 — validation-script-pattern doc
**P3 · Skill-writer · closed (2026-05-26, 515a172) · Owner: —** · Source: [IP] Phase 2 / B9
Document the validation-script pattern (the *pattern doc* — actual scripts like `qa-gate-validate.py` / `scan-skills.sh` already exist from the PR #8 build, but the authoring pattern is undocumented).

---

## Thinking-move additions

### TM1 — `contradiction-finding` thinking move
**P2 · Thinking-moves · closed (2026-05-26, 8127c7c) · Owner: —** · Source: [IP] Phase 3
Create `skills/workflows/wiki-research/references/contradiction-finding.md` (the `references/` dir does not exist yet) and wire it into the SKILL.md. Surfaces contradictions between sources/claims.

### TM2 — `assumption-audit` thinking move
**P2 · Thinking-moves · closed (2026-05-26, 8127c7c) · Owner: —** · Source: [IP] Phase 3
Create `skills/workflows/deployment-checklist/references/assumption-audit.md` and wire it into deployment-checklist and the orchestrator phase-guide. Forces explicit listing + testing of assumptions before action.

### TM3 — `second-order-effects` thinking move
**P2 · Thinking-moves · closed (2026-05-26, 8127c7c) · Owner: —** · Source: [IP] Phase 3
Create `skills/workflows/plan-builder/references/second-order-effects.md` and wire it into plan-builder. (`plan-builder/references/` has `plan-format.md` + `research-extraction.md` but no second-order-effects doc.)

---

## Process additions

### PR1 — B2/B3/B4 process guidance in skill-writer / skill-review
**P3 · Process · open (verify first) · Owner: —** · Source: [IP] Phase 4
Add the three process additions: iterate-on-one-task-at-a-time (B2), a required triggering-test format (B3), and an optional perf-comparison step (B4) to the skill-writer / skill-review bodies. Partial evidence exists (skill-update mentions "diff before/after"); confirm exact B2/B3/B4 wording is present before closing — may be partly done.

### PR2 — Changelog discipline: no inline version-history in code files
**P2 · Process / contracts · open · Owner: —** · Source: user report 2026-06-02 (observed in downstream project TruthLens)
A downstream build accumulated a 21-line inline `// Changelog:` block at the top of `contracts/types.ts` — a file imported app-wide and read on nearly every task, so the history is pure read-tax for zero runtime value, and it **self-propagates** (each editor pattern-matches the block and appends to it). Root-cause check done: this is **not** prescribed by `contract-author` or its `references/typescript-template.ts` (both clean — no changelog header; the Versioning section only says "increment version + write the full contract"). It's emergent drift — a project-local "bump the `types.ts` header" convention plus the self-propagating block — that the skills don't actively **prevent**. Fix: (1) add an explicit guardrail to `contract-author` (Versioning + Output sections): the changelog lives in `CHANGELOG.md` **only**; the types file carries a one-line `// — vX.Y.Z` marker, never an inline history block ("bump the header" = the version line). (2) Model it in `references/typescript-template.ts` with a `// version history → contracts/CHANGELOG.md` pointer comment so the template demonstrates the right pattern. (3) Mirror the matching orchestrator anti-pattern (drafted 2026-06-02 in the deployed `~/.claude/skills/orchestrator` copy — **not yet committed to this repo**). (4) Sweep other code-authoring skills/templates for the same latent pattern.

---

## Cleanup (minor)

### CL1 — Stale `skill-audit` examples in sync-skills body
**P3 · Cleanup · open · Owner: —** · Source: reconciliation 2026-05-26
`skills/workflows/sync-skills/SKILL.md` lines ~77 & ~121 use `~/.claude/skills/skill-audit → repo/...` as illustrative symlink-path examples; `skill-audit` is an archived name. Swap to an active skill name. Cosmetic — not a broken `composes_with` edge.

### CL2 — Stale global `fly-hermes` symlink
**P3 · Cleanup · open · Owner: —** · Source: reconciliation 2026-05-26
A leftover global symlink `~/.claude/skills/fly-hermes → Skill-Madness/claude_docs/fly-hermes` survives the Phase-1 migration; the canonical copy now lives in `hermes-agent/.claude/skills/`. Remove the stale symlink. (Outside the repo tree — operator cleanup.)

### CL3 — `catalog --check` doesn't cover the README skill-table or architecture diagram
**P3 · Tooling · open · Owner: —** · Source: residual of FA3 (#23) + observed README drift 2026-06-23
`catalog.sh --check` (FA3) guards the skill-*count phrases* in README/CLAUDE/PLAN/START-HERE and the `plugin.json` array, but it does **not** validate the README's numbered skill-catalog table (one row per skill) or the architecture-diagram counts — those drifted silently to 60/67 before this reconciliation and had to be hand-fixed. Either extend `catalog.sh --check` to assert the README table has one row per disk skill (and the diagram totals match), or document that the table/diagram are hand-maintained and add them to a pre-ship checklist. (Local-only debris also noticed: `skills/loops/fix-until-green-workspace/` is untracked eval scaffolding sitting under the skills tree — harmless to the catalog, but tidy up.)

---

## Functional audit (reports-v2)

Findings from the second-layer *function / triggerability / completeness / real-bugs* audit (`audit/reports-v2/`, 2026-05-28). The **P0** blockers (#15, merged) and the **P1** wiring/ownership work (#16, in review) are already shipped/in-flight — see the `FA-P0` / `FA-P1` closure-log entries in [`PLAN.md`](../PLAN.md). The entries below are the **open remainder**: the P2 fidelity backlog, the namespace confirm carried over from P1, and two design decisions.

### FA1 — Script truth-up across 8 skills
**P2 · Scripts · open · Owner: —** · Source: [FAUDIT] §10 P2.9
Make documented script behavior match the actual scripts: nano-banana, sync-skills (+ README `--force`), mermaid-charts `mmdc`, playwright report authoring, security-agent secret-scan, deployment-checklist `grep -oP`, living-plan `cp`, orchestrator `skills/` path prefixes.

### FA2 — `allowed-tools` as contract + `compatibility` backfill
**P2 · Frontmatter · open · Owner: —** · Source: [FAUDIT] §10 P2.10
Add `Bash` / `WebFetch` where bodies use them, trim unused entries, standardize ordering; backfill `compatibility` on the ~15 env-dependent workflow skills.

### FA3 — Doc-count source of truth + CI guard
**P2 · Tooling · closed (2026-06-02, PR #23) · Owner: —** · Source: [FAUDIT] §10 P2.11
RESOLVED by #23 ("make the skill catalog self-maintaining"). The filesystem is now the single source of truth: `catalog.sh` gained `--check`/`--sync` (CI-wired in `lint-skills.yml`), `-maxdepth` immunity so bundled `node_modules` SKILL.md scaffolds stop inflating the count, and coverage of the count phrasings in README/CLAUDE/PLAN/START-HERE; `sync-catalog-skills.py` reconciles the `plugin.json` skills array with disk; a PreToolUse `catalog-sync` hook re-stages drift before commit; +5 bats; catalog contract → v1.1.0. **Residual gap → CL3** (the count *phrases* are guarded, but the README skill-table rows and the architecture-diagram counts are not — those still drift by hand).

### FA4 — Disambiguation clauses for colliding triggers
**P2 · Descriptions · open · Owner: —** · Source: [FAUDIT] §10 P2.12
Add boundary clauses where trigger contexts overlap: ui-brief, plan-builder↔living-plan, interactive-doc tokens, skill-explorer↔find-skills, git-commit `Co-Authored-By` trailer, diagnose-loop↔systematic-debugging, qe-agent↔contract-auditor dedupe.

### FA5 — Cosmetic polish
**P3 · Cosmetic · open · Owner: —** · Source: [FAUDIT] §10 P2.13
caveman exit phrase, claude-design-brief count, render-sanity Phase label (12 vs 13), interactive-doc `conversation_search` + metadata stub, frontmatter field ordering.

### FA6 — External skill namespace correctness
**P1 · Namespaces · closed (2026-06-01) · Owner: —** · Source: [FAUDIT] §10 P1.8 (carryover from #16)
RESOLVED. Investigation (against the live catalog) showed the 5 "bare" refs were already correct and are **not** superpowers: `ux-review` is a bare global `~/.claude/skills/` skill; `ui-ux-pro-max` is a bare-invoked plugin skill; `claude-api` / `loop` / `schedule` are Claude Code built-in commands. The real bugs were the *opposite* — wrong `superpowers:` prefixes on non-superpowers skills (`superpowers:ux-review`, `superpowers:ui-ux-pro-max`, `superpowers:frontend-design`) in render-sanity, ui-brief, claude-design-brief, and the frontmatter-spec example/convention. Fixed: corrected those to `ux-review` / `ui-ux-pro-max` / `frontend-design:frontend-design`; added a known-bare-externals whitelist to `scripts/lint-skills.sh` (so legit global/built-in refs stop warning); corrected the frontmatter-spec convention text. The 6 valid `superpowers:` refs (brainstorming, systematic-debugging, tdd, using-git-worktrees, verification-before-completion, writing-plans) were left untouched.

### FA7 — DECISION: `metadata` block — backfill all 49 or drop
**P3 · Decision · open · Owner: —** · Source: [FAUDIT] §10 Human Decisions
Either backfill a `metadata` block across all 49 skills (discovery argument) or drop it entirely and rely on directory category + description. Pick one and apply uniformly.

### FA8 — DECISION: observability/performance scores — gate or stay advisory
**P3 · Decision · open · Owner: —** · Source: [FAUDIT] §10 Human Decisions
P0 already reworded observability/performance output to non-gating "input QE may cite." Open question: leave it advisory (close as-is) or make these gate by adding real score dimensions + rubrics to `qa-report-schema.json`. Choosing "leave advisory" closes this.

> **Already-decided human decisions** (not tracked here): code-review-agent → ceded to the external `/code-review` CLI (reframed explicit-invoke-only); context-manager → reframed user-only + deduped into `handoff-protocol.md`. Both landed in #16.
