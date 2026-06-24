# Remaining Work — Tactical Ledger

**Last updated:** 2026-06-24
**Companions:** [`PLAN.md`](../PLAN.md) (strategic roadmap + closure log), [`docs/FUTURE.md`](FUTURE.md) (frontier overflow)

> ## ✅ Backlog clear — ready for new work (2026-06-24)
>
> Every tracked item is closed. The autonomous-loop library (DEEP-RESEARCH-LOOPS §10, 13 loops + `madness`) shipped via PRs #24–#30, and the entire **pre-loops backlog** — doc-polish/process (RF/TM/PR/CL) + the reports-v2 functional-fidelity audit (FA1–FA8) — is now resolved. Catalog is at **68 skills / 7 categories**, all gates green.
>
> **There is no open work in this ledger.** Add new items by running the `plan-intake` skill on a report (audit, deep-dive, skill-review) — don't hand-add. See the `living-plan` skill for the convention.

> **Editing this doc?**
> 1. If you closed an item, also update the partner doc (closure log in `PLAN.md`, status here).
> 2. If a finding comes from a report (audit, deep-dive, skill-review), intake it via the `plan-intake` skill — don't hand-add.

## ID convention

ID prefixes are stable and never reused: `RF` (reference-file gaps), `TM` (thinking-move additions), `PR` (process additions), `CL` (cleanup), `FA` (functional-audit findings). Source short-links: `[IP]` → `docs/archive/superseded-plans/IMPROVEMENT_PLAN.md`; `[FAUDIT]` → `audit/reports-v2/00-MASTER-AUDIT.md` (gitignored — local working tree only).

---

## Closed this cycle (2026-06-24)

The final pre-loops backlog, cleared across the FA-fidelity sweep (PR #32), the class-extraction-guard feature (PR #33), and the backlog-clear pass (PR #34):

| ID | What | Closed by |
|----|------|-----------|
| **FA1** | Doc↔script truth-up (nano-banana `.env` order, sync-skills link-replace claim, security-agent `scan-skills.sh` invocation, deployment-checklist `grep -oP`→`-oE`; mermaid/playwright/living-plan/orchestrator verified accurate) | PR #32 |
| **FA2** | `allowed-tools` + `compatibility` — repo found ~95% already backfilled; completed `design-token-guard` + `class-extraction-guard` | PR #32 / #33 |
| **FA4** | Disambiguation clauses (ui-brief, plan-builder↔living-plan, interactive-doc tokens, skill-explorer↔siblings, git-commit trailer, diagnose-loop↔systematic-debugging, qe-agent↔contract-auditor) | PR #32 |
| **FA5** | Cosmetics (caveman exit phrases, claude-design-brief 13→12, render-sanity phase wording, interactive-doc `conversation_search`) | PR #32 |
| **FA7** | **Decision: drop the `metadata:` block.** Removed from all 14 skills that carried it; routing relies on directory category + description | PR #34 |
| **FA8** | **Decision: keep observability/performance scores advisory.** P0 already reworded them to non-gating "input QE may cite"; no schema/gate change | closed as-is |
| **CL1** | Stale `skill-audit` examples in sync-skills → `skill-review` | PR #32 |
| **CL2** | **Stale-premise: closed not-actionable.** The ledger's "canonical copy moved to `hermes-agent/.claude/skills/`" never happened; the global `~/.claude/skills/fly-hermes` symlink points at a live, populated `claude_docs/fly-hermes` — removing it would orphan a live skill, not tidy. Nothing to remove in-repo | closed (decision) |
| **CL3** | `catalog.sh --check` now validates the README skill-table (one row per disk skill) + reconciled the table to 68 and the per-category prose counts | PR #34 |
| **PR1** | B2/B3/B4 process guidance — iterate-one-change-at-a-time, a required triggering-test, an optional perf-comparison — added to skill-writer + skill-review | PR #34 |
| **PR2** | Changelog discipline — guardrail in contract-author (history → `CHANGELOG.md`, one-line `// — vX.Y.Z` marker only) + `typescript-template.ts` pointer; orchestrator already carried the matching anti-pattern (from #24), cross-linked | PR #34 |

Earlier-closed in this backlog (full detail in [`PLAN.md`](../PLAN.md) closure log): **RF1–RF5** + **TM1–TM3** (reference files + thinking moves, 2026-05-26), **FA3** (catalog self-maintaining, PR #23), **FA6** (external namespace correctness, 2026-06-01).

---

## How work flows in

Reports don't rot here. A deep-dive, audit, or skill-review report becomes tracked work via the **report→ledger intake loop**: run the `plan-intake` skill on the report, approve the proposed entries, and they land here + in the [`PLAN.md`](../PLAN.md) closure log. See the `living-plan` skill for the full convention.

When the next batch of work arrives, add it below under a new dated section with fresh IDs (continuing the stable-prefix scheme).
