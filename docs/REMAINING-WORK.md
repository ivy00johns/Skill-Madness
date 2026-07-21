# Remaining Work — Tactical Ledger

**Last updated:** 2026-07-21 (overnight-drain sweep)
**Companions:** [`PLAN.md`](../PLAN.md) (strategic roadmap + closure log), [`docs/COMPLETED-WORK.md`](COMPLETED-WORK.md) (completed archive — every closed item, verbatim), [`docs/FUTURE.md`](FUTURE.md) (frontier overflow)

> ## Open: RV2 + CB-3 + CB-10 (as of 2026-07-21)
>
> On 2026-07-21 the **user-authorized overnight drain** closed **31 of the 34 open rows** across six PRs (**#55–#60**: doc polish + MR-8 fable-handoff integration + CB-2 craft doctrine · RV16 orchestrator dedupe · PF1/PF4 converter scripts-shipping · MR-5/CB-9 loop hygiene + expand–contract · MR-6/MR-7/SO-4 ADR + drift + split-hygiene standard · CB-1 two-axis code review), swept to [`docs/COMPLETED-WORK.md`](COMPLETED-WORK.md) with the full history of prior sweeps. What's left below: **RV2** (human-gated license decision — deliberately excluded from the drain), **CB-3** (the ponytail YAGNI build-gate skill — deferred with a written reason: a new-skill build ripples the catalog count through README/plugin.json and deserves a focused session, not the tail of an overnight run), and **CB-10** (filed speculative). The un-intaken pxpipe + ai-website-cloner dive findings await approval in the root `INTAKE-DRAFT-2026-07-21-pxpipe-cloner.md` (fail-closed — nothing filed until approved). Fuller narrative of everything before tonight lives in the archive's section headers.
>
> Add new items by running the `plan-intake` skill on a report (audit, deep-dive, skill-review) — don't hand-add. See the `living-plan` skill for the convention.

> **Editing this doc?**
> 1. If you closed an item, run the **completion sweep**: move its row to [`docs/COMPLETED-WORK.md`](COMPLETED-WORK.md) (verbatim) and confirm the closure log in `PLAN.md`. Keep this file to open / in-progress items only.
> 2. If a finding comes from a report (audit, deep-dive, skill-review), intake it via the `plan-intake` skill — don't hand-add.

## ID convention

ID prefixes are stable and never reused: `RF` (reference-file gaps), `TM` (thinking-move additions), `PR` (process additions), `CL` (cleanup), `FA` (functional-audit findings), `MA` (model-adaptation follow-ups), `RV` (offline-window review findings), `SR` (2026-07-03 full-library review findings), `MT` (model & effort tiering), `PF` (portability / convert-pipeline follow-ups discovered during the SR/MT sweep, PR #45), `UF` (direct user-feedback findings, hand-added), `CB` (comparative-borrow findings from the 2026-07-06 skills-comparative refresh), `MR` (2026-07-08 maxed-out-window review findings), `SO` (2026-07-21 SkillOpt deep-dive borrows). Source short-links: `[IP]` → `docs/archive/superseded-plans/IMPROVEMENT_PLAN.md`; `[SCR]` → the 2026-07-06 skills-comparative deep-dive refresh (`../DeepResearch/skills-comparative_deepdive/source-material/11-delta-2026-07.md` — mattpocock/skills v1.0.1, refreshed 2026-07-08 to **v1.1.0** ↔ Skill-Madness, plus the `ponytail` YAGNI borrow); `[MWR]` → [`docs/reviews/2026-07-08-maxed-window-review.md`](reviews/2026-07-08-maxed-window-review.md); `[FAUDIT]` → `audit/reports-v2/00-MASTER-AUDIT.md` (gitignored — local working tree only); `[REV]` → the 2026-07-01 offline-window review; `[SRR]` → [`skill-review-report.md`](../skill-review-report.md) (repo root); `[METP]` → [`docs/proposals/2026-07-03-model-effort-tiering-policy.md`](proposals/2026-07-03-model-effort-tiering-policy.md); `[SO]` → the 2026-07-20 SkillOpt deep dive (`../DeepResearch/skillopt_deepdive/source-material/`, esp. `14-frontier-assessment.md`) + wiki comparison `../DeepResearch/wiki/comparisons/skillopt-vs-alltheskills.md`.

---

## Open / in-progress

### 2026-07-02 — offline-window review residuals (`RV`)

- **RV2** `[open · P2 · human decision]` — **LICENSE file missing while MIT is claimed everywhere.** README badge (:13) and `[MIT](LICENSE)` (:~724) link a file that has never existed in any branch; plugin.json + marketplace.json declare `"license": "MIT"`; the "keep the notice" clause has no notice to keep. Human decision: add an MIT LICENSE at the root (copyright line) or repoint/remove the claims. (Excluded from the 2026-07-21 overnight drain as human-gated; the confirm question went unanswered.) Source: `[REV]`.

### 2026-07-06 — skills-comparative borrows (`CB`)

- **CB-3** `[open · P2]` — **Add a `ponytail`-style YAGNI build-gate skill — the build-discipline sibling to `caveman`'s talk-discipline.** A persistent, user-invocable mode that runs a pre-build "ladder" (does this need to exist at all → reuse what already lives in the codebase → stdlib → native platform feature → already-installed dep → one line → only then minimum code) with hard **"when NOT to be lazy"** guardrails (trust-boundary validation, error handling that prevents data loss, security, accessibility, *understanding the problem first*, and one runnable check per non-trivial change). Adapt from `DietrichGebert/ponytail` (MIT, 75.8K★; benchmarked ~54% less code / ~20% cheaper while keeping every safety guard). Fills the gap `architecture-rescue` (post-hoc deletion test) and `find-unknowns` don't cover: an *up-front* over-build reflex. Overlaps **UF-1** (shipped 2026-07-07, which added the YAGNI over-build check *inside* `plan-intake`); CB-3 is the general reusable skill that would generalize it. Observable change: agents stop over-building (a date-picker lib becomes `<input type="date">`). (Deferred from the 2026-07-21 overnight drain: a new skill changes the catalog count and README table/diagram, which conflicted with the run's open PRs; schedule as a focused build.) Source: `[SCR]`.
- **CB-10** `[open · P3 · speculative]` — **HITL/AFK ticket classification as a named cross-loop contract.** Upstream types every unit of work human-in-the-loop or agent-alone, with the binding rule that an agent answering a HITL step *itself* has broken the contract by definition (their fix for `/wayfinder` grilling itself). Our loops already carry HITL gates and `agent-spawning.md` already classifies AFK/HITL — this would generalize the *self-answering-is-breach* rule as a named contract across loop gates + `grill-me`/`find-unknowns`. Filed speculative: overlaps existing coverage; earns full weight the first time a loop is caught self-answering a gate. Source: `[SCR]`.

---

## How work flows in

Reports don't rot here. A deep-dive, audit, or skill-review report becomes tracked work via the **report→ledger intake loop**: run the `plan-intake` skill on the report, approve the proposed entries, and they land here + in the [`PLAN.md`](../PLAN.md) closure log. That same skill runs the **completion sweep** as its final step — relocating any `done` rows to [`docs/COMPLETED-WORK.md`](COMPLETED-WORK.md) so this ledger never bloats. See the `living-plan` skill for the full convention.
