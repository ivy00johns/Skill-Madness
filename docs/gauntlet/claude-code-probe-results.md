# Claude Code trigger probe results — 2026-10-07

The Claude Code cell the Oct 6 merge-readiness audit (A2) found missing:
does each skill still load unforced in Claude Code after the multi-host
description rewrites?

## Method

- **Host:** Claude Code 2.1.292–2.1.293, `claude -p` with stream-json output, real
  user config (plugins, hooks, and `~/.claude/skills` linked to this checkout
  at `review/universal-integration` = PR #82 + the three follow-up branches).
- **Model:** `claude-opus-5-5`.
- **Harness:** `scripts/gauntlet/claude-code-probe.py`. A load is a `Skill`
  tool call naming the row's skill (bare or plugin-prefixed), or a
  slash-command expansion of it. The run stops at the first skill decision.
  Skills that ship `disable-model-invocation: true` are skipped: Claude Code
  never offers them to the model, so they cannot be auto-selected by design.
- **Prompts:** the `coverage-matrix.md` positive trigger and near-miss control,
  one rep, run from an empty scratch repo.
- Raw records: `evidence/claude-code-probe/`.

## Roll-up

| | Result |
|---|---|
| Auto-selectable (`yes`) rows | 48 |
| Positive trigger loaded the skill | **39 / 48** |
| Near-miss controls that loaded the skill | **0 / 29** |
| Misses caused by this wave's description changes | **0** |

## Misses

Every miss ran `Bash` first to look for the project the prompt names
(Bazaar II, its ledger, its wiki) and ended without choosing a skill. The
matrix prompts assume that project exists; the probe's scratch repo is empty.

| Skill | Description changed vs `main`? | Note |
|---|---|---|
| orchestrator | yes | A/B, 3 reps each: head 0/3, main 0/3 — not a regression |
| skill-explorer | yes | A/B, 3 reps each: head 1/3, main 0/3 — no worse |
| madness | no | prompt starts with `/madness`; no slash expansion was observed in `-p` |
| architecture-rescue | no | |
| maintain-context | no | |
| repo-deep-dive | no | |
| wiki-research | no | |
| playwright | no | |
| caveman | no | |

## Caveats

- One rep per row, except the A/B. Selection is stochastic; treat a single
  miss as a lead, not a verdict.
- An empty working directory under-triggers project-shaped prompts. Re-running
  the misses inside a seeded project is the next useful check.
- Near-miss controls cover 29 rows only; the first batch was cut off by a plan
  usage limit before the rest ran.
