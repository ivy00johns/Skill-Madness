# Remaining Work — Tactical Ledger

**Last updated:** 2026-05-31
**Companions:** [`PLAN.md`](../PLAN.md) (strategic roadmap + closure log), [`docs/FUTURE.md`](FUTURE.md) (frontier overflow)

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

---

## Cleanup (minor)

### CL1 — Stale `skill-audit` examples in sync-skills body
**P3 · Cleanup · open · Owner: —** · Source: reconciliation 2026-05-26
`skills/workflows/sync-skills/SKILL.md` lines ~77 & ~121 use `~/.claude/skills/skill-audit → repo/...` as illustrative symlink-path examples; `skill-audit` is an archived name. Swap to an active skill name. Cosmetic — not a broken `composes_with` edge.

### CL2 — Stale global `fly-hermes` symlink
**P3 · Cleanup · open · Owner: —** · Source: reconciliation 2026-05-26
A leftover global symlink `~/.claude/skills/fly-hermes → Skill-Madness/claude_docs/fly-hermes` survives the Phase-1 migration; the canonical copy now lives in `hermes-agent/.claude/skills/`. Remove the stale symlink. (Outside the repo tree — operator cleanup.)

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
**P2 · Tooling · open · Owner: —** · Source: [FAUDIT] §10 P2.11
Adopt the audit's §8 count table as the single source of truth and add `check-catalog-sync.sh` so doc/manifest skill counts can't silently drift (this very reconciliation — docs stuck at 47 while the manifest said 49 — is the symptom). Drop dead `requires_agent_teams` / `min_plan` default fields.

### FA4 — Disambiguation clauses for colliding triggers
**P2 · Descriptions · open · Owner: —** · Source: [FAUDIT] §10 P2.12
Add boundary clauses where trigger contexts overlap: ui-brief, plan-builder↔living-plan, interactive-doc tokens, skill-explorer↔find-skills, git-commit `Co-Authored-By` trailer, diagnose-loop↔systematic-debugging, qe-agent↔contract-auditor dedupe.

### FA5 — Cosmetic polish
**P3 · Cosmetic · open · Owner: —** · Source: [FAUDIT] §10 P2.13
caveman exit phrase, claude-design-brief count, render-sanity Phase label (12 vs 13), interactive-doc `conversation_search` + metadata stub, frontmatter field ordering.

### FA6 — Confirm + apply 5 bare external namespace refs
**P1 · Namespaces · open (needs human confirm) · Owner: —** · Source: [FAUDIT] §10 P1.8 (carryover from #16)
P1 namespaced the known plugin refs but left 5 bare pending confirmation of the correct prefix: `ux-review`, `ui-ux-pro-max`, `claude-api`, `loop`, `schedule` in orchestrator + frontend-agent (likely `superpowers:` / plugin prefixes). Confirm each target, then apply + add the lint that FAILs on bare known-plugin names.

### FA7 — DECISION: `metadata` block — backfill all 49 or drop
**P3 · Decision · open · Owner: —** · Source: [FAUDIT] §10 Human Decisions
Either backfill a `metadata` block across all 49 skills (discovery argument) or drop it entirely and rely on directory category + description. Pick one and apply uniformly.

### FA8 — DECISION: observability/performance scores — gate or stay advisory
**P3 · Decision · open · Owner: —** · Source: [FAUDIT] §10 Human Decisions
P0 already reworded observability/performance output to non-gating "input QE may cite." Open question: leave it advisory (close as-is) or make these gate by adding real score dimensions + rubrics to `qa-report-schema.json`. Choosing "leave advisory" closes this.

> **Already-decided human decisions** (not tracked here): code-review-agent → ceded to the external `/code-review` CLI (reframed explicit-invoke-only); context-manager → reframed user-only + deduped into `handoff-protocol.md`. Both landed in #16.
