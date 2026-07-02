# Remaining Work — Tactical Ledger

**Last updated:** 2026-07-01
**Companions:** [`PLAN.md`](../PLAN.md) (strategic roadmap + closure log), [`docs/COMPLETED-WORK.md`](COMPLETED-WORK.md) (completed archive — every closed item, verbatim), [`docs/FUTURE.md`](FUTURE.md) (frontier overflow)

> ## Nearly clear — one small open follow-up (as of 2026-07-01)
>
> **The pre-loops backlog is fully closed** — that detail lives in [`docs/COMPLETED-WORK.md`](COMPLETED-WORK.md) (tactical archive) with the strategic digest in the [`PLAN.md`](../PLAN.md) closure log. The autonomous-loop library (DEEP-RESEARCH-LOOPS §10, 13 loops + `madness`) shipped via PRs #24–#30; the entire **pre-loops backlog** — doc-polish/process (RF/TM/PR/CL) + the reports-v2 functional-fidelity audit (FA1–FA8) — is resolved. On 2026-07-01 the `model-adaptation` skill shipped (catalog **68 → 69**, meta 6 → 7), leaving **one small open follow-up, `MA-1`**, below. All gates green.
>
> Add new items by running the `plan-intake` skill on a report (audit, deep-dive, skill-review) — don't hand-add. See the `living-plan` skill for the convention.

> **Editing this doc?**
> 1. If you closed an item, run the **completion sweep**: move its row to [`docs/COMPLETED-WORK.md`](COMPLETED-WORK.md) (verbatim) and confirm the closure log in `PLAN.md`. Keep this file to open / in-progress items only.
> 2. If a finding comes from a report (audit, deep-dive, skill-review), intake it via the `plan-intake` skill — don't hand-add.

## ID convention

ID prefixes are stable and never reused: `RF` (reference-file gaps), `TM` (thinking-move additions), `PR` (process additions), `CL` (cleanup), `FA` (functional-audit findings), `MA` (model-adaptation follow-ups). Source short-links: `[IP]` → `docs/archive/superseded-plans/IMPROVEMENT_PLAN.md`; `[FAUDIT]` → `audit/reports-v2/00-MASTER-AUDIT.md` (gitignored — local working tree only).

---

## Open / in-progress

### 2026-07-01 — model-adaptation follow-ups (`MA`)

- **MA-1** `[open]` — **`skill-writer/references/performance-notes.md` still teaches the prior-model "anti-laziness" tactic as a broadly-recommended default.** The 2026-07-01 `model-adaptation` work added a `skill-review` anti-pattern that flags over-eager "do not truncate / produce it in full" nagging on the Claude 5 family (Fable 5 / Mythos 5), where output laziness is far less common — but `performance-notes.md` itself, a skill-writer reference, still frames the `## Performance Notes` block as a generally-good pattern. Update it to mark the tactic as prior-model / apply-sparingly (keep only where a *measured* truncation failure exists for that specific skill), closing the skill-writer ↔ skill-review tension. Small; deferred out of the approved edit scope (skill-review / loop-controller / orchestrator). Source: the `model-adaptation` skill + Anthropic's *Prompting Claude Fable 5* guide.

When the next batch of work arrives, add it below under a new dated section with fresh IDs (continuing the stable-prefix scheme). Completed rows move out to the archive via the completion sweep, so this section stays scoped to what's actually left to do.

---

## How work flows in

Reports don't rot here. A deep-dive, audit, or skill-review report becomes tracked work via the **report→ledger intake loop**: run the `plan-intake` skill on the report, approve the proposed entries, and they land here + in the [`PLAN.md`](../PLAN.md) closure log. That same skill runs the **completion sweep** as its final step — relocating any `done` rows to [`docs/COMPLETED-WORK.md`](COMPLETED-WORK.md) so this ledger never bloats. See the `living-plan` skill for the full convention.
