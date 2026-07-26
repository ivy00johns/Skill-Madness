# BUILD_RESULTS — ledger drain (build/ledger-drain, 2026-07-24)

**Status: COMPLETE on branch `build/ledger-drain` — 9 of 10 open ledger rows closed, both gates green, board reduced to CB-10.** This is a docs/skills/tooling build; its real value path (lint + catalog + full bats suite exercising the shipped scripts and skills) was run end-to-end and observed green — no mocked scaffolding anywhere. Not merged, not pushed: the branch awaits your review per git policy.

## What shipped (15 commits, da0711c..HEAD)

| Ledger row | Deliverable | Commit |
|---|---|---|
| RV2 (user decision) | Root MIT LICENSE (ivy00johns 2026) — README badge/links now truthful | 81532d2 |
| HE-1 | `docs/audit-evidence/` sanitized projection (typed headers, verbatim [FAUDIT] target + qe-agent exemplar), plan-intake 1.3.0 in-repo citation rule, ledger short-link repointed | dc6b718 |
| HE-2 | 14-row unresolved-decision routing index ("review"→5 decisions, "deploy"→3); madness load budget — one skill, or none | dc6b718 |
| WC-2 | agent-spawning: ~60-line split gate + 10-box pre-dispatch checklist; skill-writer: cost-tagged anti-patterns (pattern #6) | 7f621dc |
| PX-3 | Image-proxy model allowlist in model-adaptation — fail-closed, glyph-sweep re-verification per model release | d7424c5 |
| WC-1 | lint-skills.sh ERROR on literal `$ARGUMENTS` in skill bodies + 2 bats cases + lint-rules.md v1.4.0 | 83b68b2 |
| PX-1 | New skill `use-pxpipe` — opt-in harness token-saver proxy wiring (compression AND cache-warmth verification; loopback-only; gist-only caveat; never vendored) | 8172614 |
| CB-3 | New skill `yagni-gate` — persistent 7-rung YAGNI build gate with when-NOT-to-be-lazy guardrails (adapted from DietrichGebert/ponytail, MIT; renamed to avoid taking the upstream identity) | 8e73164 |
| PX-2 | madness asks the token-saver question once, riding the existing expensive-route confirm; 4 don't-ask conditions | 9f37d00 |
| — | Catalog ripple 71→**73** (README/CLAUDE/PLAN/START-HERE/plugin.json/marketplace.json, mermaid box, table rows 59–60 + loop renumber) | 06ae2f7 |
| — | Adversarial findings fixed (2 MEDIUM + 4 LOW — stale model ID, missing version bump, description near ceiling, budget/side-launch reconciliation, env-relative note, allowlist-conditional hatch) | 11e9d19 |

Support commits: intake docs (98117ec, on `docs/harness-engineering-intake`), scaffold+LICENSE (81532d2), QA report (847a601), ledger sweep + this report (final commit). Unrelated `capture.mjs` settle fix parked on `fix/walkthrough-capture-settle` (a12b5da).

## Verification (all observed this session)

- **QE gate:** `proceed=true` — full suite **346/346** (~5 min), lint **0 errors**, catalog `--check` clean at 73, frontmatter conformance for both new skills, LICENSE/link/heading integration checks, every commit mapped to a ledger item. Schema-valid report: `coordination/ledger-drain-qa-report.json`. Scores 5/5/5/5/5, zero blockers.
- **Adversarial review (default-refute, fresh context):** 7 checks, **0 refuted claims** — WC-1's lint verified with a hostile fixture (ERROR + exit 1), HE-1's projections byte-diffed against sources, decision-index names resolved on disk, refusal-landmine sweep clean, trigger tests re-run against current sibling descriptions. Findings (2 MEDIUM + 4 LOW) all fixed in 11e9d19 and re-linted.

## Deferred / not done, with reasons

- **CB-10** — stays open-speculative per its own row (earns weight the first time a loop self-answers a gate).
- **`code-review` third pass** — deferred: adversarial skill-review + independent QE already reviewed the diff at outcome level; run `/code-review` (or `/code-review ultra`) on the PR if you want the third opinion.
- **WC-1 per-host `$ARGUMENTS` translation** — deliberately not built (no rewrite mechanism exists in convert.sh; the loud lint forces the design conversation when a real use case appears).
- **LOW-3 second half** — teach lint/catalog to resolve the decision index's skill names (filed below as a follow-up).

## Handoff — needs YOU before a PR

1. **Review the published audit fragments** (HE-1): `docs/audit-evidence/2026-05-28-functional-audit/master-audit.md` republishes the full May master audit verbatim — including its now-largely-stale §2 scorecard and §10 roadmap (staleness notes are attached, but you're publishing a mostly-remediated snapshot as evidence; confirm you're comfortable).
2. **PR strategy** — one branch, 15 commits; squash-merge is the repo default. `fix/walkthrough-capture-settle` and `docs/harness-engineering-intake` (now fully contained in the build branch) need their own disposition.
3. **Local-only oddity, untouched:** the v1 audit dir is misspelled on disk (`reports-v1-sufrace`); renaming is a local-fs action outside the build's ownership.

## Recommend intake (F-class follow-ups discovered while building)

- **Hand-maintained name lists bit again** (4th recurrence): the CLAUDE.md workflows enumeration missed both new skills until a manual grep caught it. Root fix: extend `catalog.sh --check` to parse and verify the CLAUDE.md category name-lists against disk.
- **Decision-index linting** (adversarial LOW-3): the routing table's new index is hand-maintained and un-linted; a rename breaks it silently. Fold its backticked names into `lint-skills.sh`'s known-name resolution.
- **Environment-relative refs in routing docs**: `ux-review` / plugin-namespaced refs resolve only in this environment; the index now carries a note, but a portable-refs convention for routing docs would close it properly.
