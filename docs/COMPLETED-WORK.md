# Completed Work — Tactical Archive

**Last updated:** 2026-07-01
**Companions:** [`docs/REMAINING-WORK.md`](REMAINING-WORK.md) (open ledger — the to-do list), [`PLAN.md`](../PLAN.md) (strategic roadmap + closure log)

> **What this is.** The append-only tactical archive: every ledger item that reached
> `done`, relocated here verbatim so the open ledger stays lean and cheap to load. This
> is the *tactical* record (per-ID detail); it **complements** — does not duplicate — the
> strategic **closure log** in [`PLAN.md`](../PLAN.md) (one line per wave/milestone close).
> Rows arrive here via the **completion sweep** (see the `living-plan` skill). Never
> summarized on the way in, never deleted — trimming happens by relocation only.
>
> ID prefixes (stable, never reused): `RF` reference-file gaps · `TM` thinking-move
> additions · `PR` process additions · `CL` cleanup · `FA` functional-audit findings.

---

## Closed 2026-06-24 — pre-loops backlog clear

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

## Closed 2026-05-26 → 2026-06-01 — earlier in this backlog

Full detail in the [`PLAN.md`](../PLAN.md) closure log: **RF1–RF5** + **TM1–TM3** (reference files + thinking moves, 2026-05-26), **FA3** (catalog self-maintaining, PR #23), **FA6** (external namespace correctness, 2026-06-01).
