# ADR 0001 — Keep `caveman` and `zoom-out` despite their upstream deletion

- **Date:** 2026-07-21
- **Status:** Accepted
- **Source:** 2026-07-08 maxed-out-window review (`MR-6`); decision originally recorded only in the DeepResearch vault's skills-comparative delta doc (`11-delta-2026-07.md`)

## Context

Skill-Madness adapted two skills from `mattpocock/skills` with attribution:

- `workflows/caveman` — from `productivity/caveman` (talk-discipline / output-trimming), then hardened: original examples, deliberately kept model-invocable.
- `workflows/zoom-out` — from `engineering/zoom-out` (the explicit-only reframing move).

Upstream subsequently **deleted both** (commits `7d3ada9`, `e112a6b`; confirmed absent at the v1.1.0 tag). Until this ADR, our keep decision existed only in the DeepResearch vault — outside this repo — and `ACKNOWLEDGMENTS.md` still cited both upstream paths as if live.

## Decision

**We keep both skills.** The upstream deletions reflect that library's anti-framework philosophy (a small promoted set, aggressively pruned), not a defect in the skills. In this library both fill assigned niches:

- `caveman` is the **talk-discipline** half of a deliberate pair — its build-discipline sibling (a ponytail-style YAGNI gate) is tracked as `CB-3`. It also feeds the model & effort tiering doctrine (output-trimming is one of the two dominant cost levers).
- `zoom-out` is the explicit-only reframing move and the origin of our `disable-model-invocation` convention notes.

This is a deliberate divergence from upstream, not drift.

## Consequences

- `ACKNOWLEDGMENTS.md` rows for both skills now note the upstream deletion and point here.
- Future comparative refreshes must not re-propose deleting either skill without new evidence — "upstream removed it" alone is not a reason.
- This is the first ADR: the `docs/adr/` convention (parked as `CB-5` in `docs/FUTURE.md`) starts here. Future *library-level* divergence or design decisions that are hard to reverse, surprising, and carry a real tradeoff get an ADR — not a vault-only note.
