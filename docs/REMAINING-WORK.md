# Remaining Work — Tactical Ledger

**Last updated:** 2026-08-03 (deep-dive intake — DV-1–DV-5 implemented and closed same-session)
**Companions:** [`PLAN.md`](../PLAN.md) (strategic roadmap + closure log), [`docs/COMPLETED-WORK.md`](COMPLETED-WORK.md) (completed archive — every closed item, verbatim), [`docs/FUTURE.md`](FUTURE.md) (frontier overflow)

> ## Open: CB-10 only (as of 2026-08-03)
>
> On 2026-07-24 the **orchestrated ledger drain** (branch `build/ledger-drain`) closed **9 of the 10 open rows** in one session: **RV2** (user chose the MIT LICENSE), **HE-1–HE-2** first (the harness: audit-evidence projection + decision-keyed routing/load budget), then **WC-1–WC-2 + PX-3** (converter `$ARGUMENTS` guard · split gate/checklist/cost-tagged patterns · image-proxy allowlist), then the two new skills **PX-1 (`use-pxpipe`) + CB-3 (`yagni-gate`)** and **PX-2** (madness token-saver question), catalog 71→**73**. Gated by QE `proceed=true` (346/346 bats, lint 0 errors, schema-valid report) and a default-refute adversarial review (0 refuted; its 2 MEDIUM + 4 LOW fixed same-session). All rows swept verbatim to [`docs/COMPLETED-WORK.md`](COMPLETED-WORK.md); dive framings live in that section's narrative. Still open: **CB-10** (speculative by design — earns weight the first time a loop self-answers a gate). Prior sweeps' history lives in the archive's section headers.
>
> Add new items by running the `plan-intake` skill on a report (audit, deep-dive, skill-review) — don't hand-add. See the `living-plan` skill for the convention.
>
> On 2026-08-03 the **deep-dive intake** (a Freebuff/deepseek vendor review of this repo — the first full cross-vendor pass since the `model-adaptation` "never cross-vendor" doctrine landed) proposed 5 rows (`DV-1`–`DV-5`) via the `plan-intake` skill, got explicit approval ("let's implement"), and was **implemented + closed same-session** on the Freebuff worktree branch: the hooks-suite TTY hang (DV-1), the unwired `--changed` CI gate (DV-2), the README macOS gating overstatement (DV-3), the scaffold 0.1.0 plugin manifests (DV-4), and the 7 re-populated >950 descriptions (DV-5). Verified live: lint 0 errors (116 warnings, unchanged), catalog clean (73), hooks suite 45/45 in 21s bare (was: hang forever), all fast + installer suites green (~346 tests), `--changed origin/main` 0 drifts. Rows swept verbatim to [`docs/COMPLETED-WORK.md`](COMPLETED-WORK.md); the board is **CB-10 only** again.

> **Editing this doc?**
> 1. If you closed an item, run the **completion sweep**: move its row to [`docs/COMPLETED-WORK.md`](COMPLETED-WORK.md) (verbatim) and confirm the closure log in `PLAN.md`. Keep this file to open / in-progress items only.
> 2. If a finding comes from a report (audit, deep-dive, skill-review), intake it via the `plan-intake` skill — don't hand-add.

## ID convention

ID prefixes are stable and never reused: `RF` (reference-file gaps), `TM` (thinking-move additions), `PR` (process additions), `CL` (cleanup), `FA` (functional-audit findings), `MA` (model-adaptation follow-ups), `RV` (offline-window review findings), `SR` (2026-07-03 full-library review findings), `MT` (model & effort tiering), `PF` (portability / convert-pipeline follow-ups discovered during the SR/MT sweep, PR #45), `UF` (direct user-feedback findings, hand-added), `CB` (comparative-borrow findings from the 2026-07-06 skills-comparative refresh), `MR` (2026-07-08 maxed-out-window review findings), `SO` (2026-07-21 SkillOpt deep-dive borrows), `WC` (2026-07-21 ai-website-cloner-template deep-dive borrows), `PX` (2026-07-21 pxpipe deep-dive adoption), `HE` (2026-07-22 harness-engineering deep-dive borrows), `DV` (2026-08-03 deep-dive vendor review findings). Source short-links: `[IP]` → `docs/archive/superseded-plans/IMPROVEMENT_PLAN.md`; `[SCR]` → the 2026-07-06 skills-comparative deep-dive refresh (`../DeepResearch/skills-comparative_deepdive/source-material/11-delta-2026-07.md` — mattpocock/skills v1.0.1, refreshed 2026-07-08 to **v1.1.0** ↔ Skill-Madness, plus the `ponytail` YAGNI borrow); `[MWR]` → [`docs/reviews/2026-07-08-maxed-window-review.md`](reviews/2026-07-08-maxed-window-review.md); `[FAUDIT]` → [`docs/audit-evidence/2026-05-28-functional-audit/master-audit.md`](audit-evidence/2026-05-28-functional-audit/master-audit.md) (in-repo projection per HE-1; the working `audit/` tree stays gitignored); `[REV]` → the 2026-07-01 offline-window review; `[SRR]` → [`skill-review-report.md`](../skill-review-report.md) (repo root); `[METP]` → [`docs/proposals/2026-07-03-model-effort-tiering-policy.md`](proposals/2026-07-03-model-effort-tiering-policy.md); `[SO]` → the 2026-07-20 SkillOpt deep dive (`../DeepResearch/skillopt_deepdive/source-material/`, esp. `14-frontier-assessment.md`) + wiki comparison `../DeepResearch/wiki/comparisons/skillopt-vs-alltheskills.md`; `[WCT]` → the 2026-07-21 ai-website-cloner-template deep dive (`../DeepResearch/ai-website-cloner-template_deepdive/source-material/`); `[PX]` → the 2026-07-21 pxpipe deep dive (`../DeepResearch/pxpipe_deepdive/source-material/` — teamchong/pxpipe, MIT, v0.8.0); `[HE]` → the 2026-07-22 harness-engineering deep dive (`../DeepResearch/harness-engineering_deepdive/source-material/`, esp. `09-frontier-assessment.md`) + wiki comparison `../DeepResearch/wiki/comparisons/harness-engineering-vs-skill-madness.md`; `[DV]` → the 2026-08-03 deep-dive vendor review (Freebuff/deepseek session; findings verified against the in-repo evidence cited per row).

---

## Open / in-progress

### 2026-07-06 — skills-comparative borrows (`CB`)

- **CB-10** `[open · P3 · speculative]` — **HITL/AFK ticket classification as a named cross-loop contract.** Upstream types every unit of work human-in-the-loop or agent-alone, with the binding rule that an agent answering a HITL step *itself* has broken the contract by definition (their fix for `/wayfinder` grilling itself). Our loops already carry HITL gates and `agent-spawning.md` already classifies AFK/HITL — this would generalize the *self-answering-is-breach* rule as a named contract across loop gates + `grill-me`/`find-unknowns`. Filed speculative: overlaps existing coverage; earns full weight the first time a loop is caught self-answering a gate. Source: `[SCR]`.

---

## How work flows in

Reports don't rot here. A deep-dive, audit, or skill-review report becomes tracked work via the **report→ledger intake loop**: run the `plan-intake` skill on the report, approve the proposed entries, and they land here + in the [`PLAN.md`](../PLAN.md) closure log. That same skill runs the **completion sweep** as its final step — relocating any `done` rows to [`docs/COMPLETED-WORK.md`](COMPLETED-WORK.md) so this ledger never bloats. See the `living-plan` skill for the full convention.
