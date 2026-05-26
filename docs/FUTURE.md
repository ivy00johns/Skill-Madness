# Future — Frontier (out of scope)

**Last updated:** 2026-05-26
**Companions:** [`PLAN.md`](../PLAN.md), [`docs/REMAINING-WORK.md`](REMAINING-WORK.md)

Items explicitly out of scope for the current plan. Kept here so they aren't lost; pulled into the ledger only if a future cycle prioritizes them.

## F1 — Multi-host installer reach ("convergence frontier")
The `agency-agents` comparison (184 agents, 11-tool install reach) sketches a ~10-day roadmap to broaden where skills can install (Copilot, Cursor-native, and other hosts) while preserving Skill-Madness's moats (contract layer, QA gate). Aspirational, not committed.
Source: `../DeepResearch/AllTheSkills/agency-agents_deepdive/source-material/11-convergence-frontier.md`.

## F2 — Skill marketplace / registry
A discoverable registry for publishing/pulling skills with remote version pinning (the `source` field reserved in `skills-lock.json` hints at this). No design committed.

## F3 — Per-host CI smoke tests
End-to-end verification that converted skills actually load and run on each non-Claude-Code host (not just that conversion produces a file). Today CI validates frontmatter, lint, catalog, hooks, and scan — but not live execution per host.

## F4 — README / docs image assets
Hero image, architecture diagram, and host-fidelity matrix graphic for the README. Cosmetic; deferred until the doc-polish backlog (M4) clears.
