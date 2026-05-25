# Mission skill manifest — AllTheSkills runtime layer (ECC deep-dive build list)

Source: `DeepResearch/The-Hive/ecc_deepdive/source-material/14-alltheskills-frontier.md` · Scanned: 2026-05-24

This is a CLI / docs / tooling build (bash + python3 + JSON Schema + Markdown). It has
**no UI surface**, so the creative and render-validation skills (`nano-banana`,
`ui-ux-pro-max`, `frontend-design`, `ux-review`, `render-sanity`) do not apply and are
recorded N/A below rather than left as empty boxes.

## Phase P0 — Hooks layer (shipped PR #8)
- [x] `orchestrator` — ✅ coordinated; contracts under `contracts/hooks/`.
- [x] `qe-agent` — ✅ `coordination/hooks-p0-qa-report.json`.

## Phase P1 — Plan/apply install + catalog invariant (shipped PR #8)
- [x] `orchestrator` — ✅ coordinated; `contracts/installer/{catalog-invariant,plan-apply}.md`.
- [x] `qe-agent` — ✅ `coordination/p1-qa-report.json`.

## Phase P2 — Skill-health telemetry + supply-chain scanner (shipped PR #8)
- [x] `orchestrator` — ✅ coordinated; `contracts/installer/{skill-health,skill-scan}.md`.
- [x] `qe-agent` — ✅ `coordination/p2-qa-report.json`.

## Phase P3 — Publish the frontmatter standard (this build)
- [x] `orchestrator` — ✅ coordinated; contract `contracts/standards/psfs.md`.
- [x] `contract-author` — ✅ folded into the lead (contract authored directly by orchestrator).
- [x] `qe-agent` — ✅ `coordination/p3-qa-report.json` (PASS, 5/5 across the board).
- [x] `repo-deep-dive` — ✅ invoked in the prior session; it produced the source material
  (`ecc_deepdive/source-material/`) this entire build list derives from.
- [x] `llm-wiki` / `wiki-research` — ✅ the deep-dive's findings were filed into the
  DeepResearch Obsidian wiki (`wiki/comparisons/ecc-vs-alltheskills.md`) in the prior session.

## N/A for this build (no UI surface)
- `nano-banana`, `ui-ux-pro-max`, `frontend-design`, `ux-review`, `render-sanity` — N/A:
  this build ships scripts, a JSON Schema, a Markdown standard, and bats tests; there is
  nothing to render in a browser.
- `code-review` / `security-review` — folded into the QE pass (the PSFS security surface —
  the `^[^<>]*$` angle-bracket prohibition on frontmatter strings — was verified there and
  scored security 5/5).
