# Mission skill manifest — SR/MT backlog sweep (full-library review + tiering)

Source: `docs/REMAINING-WORK.md` § "2026-07-03 — full-library review (`SR`) + model & effort tiering (`MT`)" · Scanned: 2026-07-03
Branch: `fix/sr-mt-backlog-sweep` · Runtime: Agent Teams (parallel subagents + shared task board)

Scope: **SR1–SR24 + MT-1** (the intaken ledger). `docs/FUTURE.md` F5–F18 are explicitly
out of scope per FUTURE.md's own rule (frontier items enter only via a future intake).
This is a CLI/docs/tooling build with **no UI surface** — the creative and render-validation
skills (`nano-banana`, `ui-ux-pro-max`, `frontend-design`, `ux-review`, `render-sanity`,
`design-token-guard`, `class-extraction-guard`) are N/A, recorded here rather than left empty.

`docs/agents/` is absent — proceeding with defaults (single-context, format-by-detection,
local briefs); flagged to the user to run `/setup-project-skills` for durability.

Every box must end the build either ✅ (invoked, with the artifact path)
or annotated with a one-line reason for deferral. Empty boxes are bugs.

## Wave 1 — parallel file-disjoint fixes (A1–A5, B1–B4)
- [ ] `orchestrator` — this build's coordinator; contracts = the ledger rows themselves.
- [ ] `fix-until-green` — explicitly dispatched as the wave-gate driver (catalog --check + lint + bats red→green without cheating).

## Wave 2 — SR1 portability audit (`requires_claude_code` × 71 skills + README claims)
- [ ] `skill-review` conventions — the audit consumes the review's H1 finding; no re-review needed.

## Wave 3 — QE + adversarial verification
- [ ] `qe-agent` — mandatory; produces `coordination/sr-mt-qa-report.json` per qa-report-schema.
- [ ] `code-review` — adversarial diff pass on the script-heavy changes (B1/B2/B3, SR1).

## Pre-build (already done, prior sessions)
- [x] `skill-review` — ✅ produced `skill-review-report.{md,json}` (the SR source).
- [x] `plan-intake` — ✅ PR #44 (the ledger entries this build implements).

## Edited-not-invoked (MT-1 targets)
- `model-adaptation`, `orchestrator`, `loop-controller`, `use-freellmapi` — these skills
  are MT-1's edit targets (the tiering policy lands in their bodies), not invocations.

## N/A for this build (no UI surface)
- `nano-banana`, `ui-ux-pro-max`, `frontend-design`, `ux-review`, `render-sanity`,
  `design-token-guard`, `class-extraction-guard` — nothing renders in a browser.
- `contract-author` — the ledger rows are the contracts; no API surface to author.
