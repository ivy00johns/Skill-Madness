# Skill-Madness — Start Here

> The one place to land. If you're lost, read this first.
> **Last updated:** 2026-07-01

## Status at a glance

A mature library of **71 skills** (contracts · git · loops · meta · orchestrator · roles · workflows), all PSFS-validated, full Ubuntu + macOS lint matrix on every push.

| Effort | State |
|--------|-------|
| **Skill curation** (8 new skills, 6 migrations, 3 merges, bulk edits — from the comparative deep dive) | ✅ Complete |
| **Ecosystem audit — surface pass** (style/compliance/cross-refs; 5 broken cross-refs, oversized descriptions, missing frontmatter) | ✅ Complete — all critical findings resolved |
| **Runtime + install layer** (hooks, catalog CI, plan/apply install, skill-health, skill-scan, PSFS standard) | ✅ Complete — shipped PR #8 |
| **Functional audit** (reports-v2: triggerability / completeness / real bugs) | ✅ Complete — P0 (#15) + P1 (#16) + P2 (#32) shipped; FA3 (#23) + FA6 closed; decisions FA7 (drop metadata, #34) + FA8 (advisory) resolved |
| **Doc-polish / process backlog** (reference files + thinking-move docs — IMPROVEMENT_PLAN Phases 2–4) | ✅ Complete — RF1–RF5 + TM1–TM3, PR1/PR2, CL1/CL2/CL3 all closed (#32, #34) |
| **Autonomous-loop library** (13 loops + `madness` router — DEEP-RESEARCH-LOOPS §10) | ✅ Complete — #24–#30, catalog 50 → 67, all CI green |
| **class-extraction-guard gate + backlog clear** (styling-organization gate + the final FA/PR/CL items) | ✅ Complete — #31–#34, catalog → 68, backlog cleared |
| **model-adaptation skill** (cross-model prompting/scaffolding owner — Fable 5 / Mythos 5 — + checks wired into skill-review / loop-controller / orchestrator) | ✅ Shipped 2026-07-01 — catalog → 69, meta 6 → 7; one small follow-up open (MA-1) |

The library, its tooling, the autonomous-loop library (13 loops + `madness`), and the **entire pre-loops backlog are all complete** (as of 2026-06-24: FA1–FA8 + RF/TM/PR/CL all closed across PRs #31–#34). On **2026-07-01** the `model-adaptation` skill shipped — the cross-model prompting/scaffolding owner (Fable 5 / Mythos 5), built from Anthropic's Fable 5 prompting guide, with its top checks wired into skill-review / loop-controller / orchestrator — taking the catalog to **69** (meta 6 → 7) and leaving **one small open follow-up (MA-1)**. Add the next batch via the `plan-intake` skill. Full narrative in [`PLAN.md`](PLAN.md) § "Where we are"; open + closed item detail in [`docs/REMAINING-WORK.md`](docs/REMAINING-WORK.md).

## Which doc is which (ownership map)

**Canonical — the living plan (edit these):**
- [`PLAN.md`](PLAN.md) — strategic roadmap: milestones + closure log
- [`docs/REMAINING-WORK.md`](docs/REMAINING-WORK.md) — tactical ledger: every **open** item, ID'd + prioritized (stays lean)
- [`docs/COMPLETED-WORK.md`](docs/COMPLETED-WORK.md) — tactical archive: every **closed** item, verbatim (append-only; fed by the completion sweep)
- [`docs/FUTURE.md`](docs/FUTURE.md) — frontier: explicitly out of scope

**Active reference (read, edit as the library evolves):**
- [`README.md`](README.md) — user-facing project overview + quick start
- [`CLAUDE.md`](CLAUDE.md) — agent primer (skill anatomy, categories, editing rules) · [`AGENTS.md`](AGENTS.md) — contributor workflow rules
- [`spec/PSFS.md`](spec/PSFS.md) + `spec/frontmatter.schema.json` — the Portable Skill Frontmatter Spec (canonical, v1.1.0)
- `contracts/installer/*` + `contracts/standards/*` — active installer + format specs
- `claude_docs/` per-skill docs · [`claude_docs/THE-GAUNTLET.md`](claude_docs/THE-GAUNTLET.md) — multi-skill stress-test brief
- `ACKNOWLEDGMENTS.md` (living attribution) · `claude_notes.txt` (pattern catalog, reference only)

**Frozen reference (read, don't edit — in the sibling DeepResearch repo):**
- `../DeepResearch/skills-comparative_deepdive/` — the 3-way comparison + `PLAN-skill-creator.md` queue that drove the curation pass (now executed)
- `../DeepResearch/AllTheSkills/alltheskills-design/` — original architectural blueprint
- `../DeepResearch/AllTheSkills/agency-agents_deepdive/` — 184-agent / 11-tool comparison (its "convergence frontier" lives in `docs/FUTURE.md`)

**Archived (history; superseded — do not treat as current):**
- [`docs/archive/superseded-plans/`](docs/archive/superseded-plans/) — the finished plan docs (BUILD_RESULTS, IMPROVEMENT_PLAN, the stale audit queue), each with a breadcrumb
- `audit/` *(gitignored — local working tree only)* — `reports-v1-sufrace/` is the completed surface/style audit campaign (MASTER_AUDIT_PLAN + per-skill reports, historical); `reports-v2/` is the newer **functional audit** (2026-05-28) whose findings were intaken to the ledger as `FA` items (see "How work flows in" below)
- `coordination/` — finished build manifest + QA gate reports from the runtime-layer build

## How work flows in

Reports don't rot here. A deep-dive, audit, or skill-review report becomes tracked work via the
**report→ledger intake loop**: run the `plan-intake` skill on the report, approve the proposed
entries, and they land in [`docs/REMAINING-WORK.md`](docs/REMAINING-WORK.md) + the [`PLAN.md`](PLAN.md) closure log.
See the `living-plan` skill for the full convention.

Most recent intake: the **reports-v2 functional audit** (2026-05-28) → ledger entries `FA1–FA8`, with its
P0/P1 remediation (PRs #15 / #16) recorded in the [`PLAN.md`](PLAN.md) closure log.
