# The Gauntlet II package

Authoring-time index for the Gauntlet II dogfood brief and its harness. Nothing here builds Bazaar II; the package is the written brief plus the tooling the run will use.

| File | Purpose |
|---|---|
| `GAUNTLET-II.md` | the single-prompt brief: rationale, pre-registration, Bazaar II spec, phases, guardrails |
| `coverage-matrix.md` | all 76 skills with phase, trigger, must-fire flag, and near-miss control |
| `trap-catalog.md` | the eleven seeded traps mapped to guards and UA rows |
| `scoring-rubric.md` | the four eval layers, four axes, and nine disqualifiers |
| `trace-schema.json` | JSON Schema for one trace record |
| `report-template.md` | the run report that feeds `plan-intake` as `[G2]` rows |

Harness tooling lives in `scripts/gauntlet/`: `trap-inject.sh`, `trap-verify.sh`, `trace-merge.py`, `score.py`.

## Deprecation

`GAUNTLET-II.md` supersedes the stale `claude_docs/THE-GAUNTLET.md` in the main checkout (that file is untracked and is not present in this worktree). When the main checkout is next touched, add this line under its title:

```text
> **Superseded:** this brief is replaced by `docs/gauntlet/GAUNTLET-II.md`.
```

The redirect is recorded here rather than as a new file so that merging this worktree never clobbers the untracked original.

## Status

Phase 1 (this package) is complete. Phase 2 — the run — starts only after the UA-01…UA-32 refactor lands and the owner chooses to run it. The harness scripts are authored but not executed.
