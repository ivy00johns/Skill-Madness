# Skill-Madness — Start Here

> The one place to land. If you're lost, read this first.
> **Last updated:** 2026-05-26

## Status at a glance

A mature library of **47 skills** (contracts · git · meta · orchestrator · roles · workflows), all PSFS-validated, full Ubuntu + macOS lint matrix on every push.

| Effort | State |
|--------|-------|
| **Skill curation** (8 new skills, 6 migrations, 3 merges, bulk edits — from the comparative deep dive) | ✅ Complete |
| **Ecosystem audit** (47-skill review; 5 broken cross-refs, oversized descriptions, missing frontmatter) | ✅ Complete — all critical findings resolved |
| **Runtime + install layer** (hooks, catalog CI, plan/apply install, skill-health, skill-scan, PSFS standard) | ✅ Complete — shipped PR #8 |
| **Doc-polish backlog** (reference files + thinking-move docs — IMPROVEMENT_PLAN Phases 2–4) | 🟡 ~11 items open — see ledger |

The library and its tooling are done. The only open work is documentation polish. Full narrative in [`PLAN.md`](PLAN.md) § "Where we are".

## Which doc is which (ownership map)

**Canonical — the living plan (edit these):**
- [`PLAN.md`](PLAN.md) — strategic roadmap: milestones + closure log
- [`docs/REMAINING-WORK.md`](docs/REMAINING-WORK.md) — tactical ledger: every open item, ID'd + prioritized
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
- `audit/` — the completed 47-skill audit campaign (MASTER_AUDIT_PLAN + 48 per-skill reports), historical
- `coordination/` — finished build manifest + QA gate reports from the runtime-layer build

## How work flows in

Reports don't rot here. A deep-dive, audit, or skill-review report becomes tracked work via the
**report→ledger intake loop**: run the `plan-intake` skill on the report, approve the proposed
entries, and they land in [`docs/REMAINING-WORK.md`](docs/REMAINING-WORK.md) + the [`PLAN.md`](PLAN.md) closure log.
See the `living-plan` skill for the full convention.
