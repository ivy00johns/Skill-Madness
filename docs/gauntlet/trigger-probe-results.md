# Trigger probe results — 2026-10-06

The first cross-model run of `scripts/gauntlet/trigger-probe.py`, after the
description fixes and the work-scoring change landed.

## Method

- **Host:** Hermes, in `isolated-home` mode. The probe installs all 78 on-disk
  skills into a scratch `HERMES_HOME`, so the injected skill index is the only
  catalog in play.
- **Models:** `deepseek-v4-flash` and `gemini-3-5-flash`.
- **Rows:** the sixteen skills that failed or wavered in the first probe pass —
  the five `explicit` rows (`code-review-agent`, `frontend-agent`,
  `loop-controller`, `perf-loop`, `zoom-out`) plus `context-manager`,
  `grill-me`, `living-plan`, `model-adaptation`, `orchestrator`, `render-sanity`,
  `skill-catalog`, `skill-explorer`, `skill-review`, `skill-update` and
  `skill-writer`.
- **Prompts:** the matrix positive trigger for each row, run once
  (`--repeat 1`). Selection is stochastic, so a single miss is a signal to
  investigate, not a verdict.
- **Verdicts:** `PASS` = the skill loaded; `WORKED` = it did not load but the
  host did the requested work; `MISS` = neither.

## Roll-up

| Model | PASS | WORKED | MISS | FALSE_POSITIVE | BLOCKED |
|---|---|---|---|---|---|
| deepseek-v4-flash | 11 | 1 | 4 | 0 | 0 |
| gemini-3-5-flash | 15 | 1 | 0 | 0 | 0 |

## Skills that fire for one model but not the other

Every difference runs in the same direction: Gemini selects these and DeepSeek
does not. No skill fired for DeepSeek but not Gemini.

| Skill | Mode | deepseek-v4-flash | gemini-3-5-flash | DeepSeek outcome |
|---|---|---|---|---|
| code-review-agent | explicit | MISS | PASS | asked for a diff instead of loading the skill |
| grill-me | must_fire | MISS | PASS | asked for the missing input instead of interviewing |
| model-adaptation | must_fire | MISS | PASS | refused; loaded sibling plan skills instead |
| render-sanity | must_fire | MISS | PASS | refused; loaded diagnose-loop and playwright instead |

This is worth a description pass: DeepSeek reads each of these prompts as a
request for an artifact it does not have, while Gemini loads the skill and
proceeds.

## Redundant on an index-injecting host

`skill-explorer` scored `WORKED` on both models: neither loaded it, and both
answered the routing prompt from the injected index. Under the old load-only
score that read as a failure; the work signal now reports it as served.

## Caveats

- One rep per prompt. A `MISS` here is a lead, not proof; rerun with
  `--repeat 3` before filing a description bug.
- The work signal is a heuristic over the host's tool activity and final text.
  It rejects refusals and input requests and accepts a short but substantive
  answer, so it can still be fooled in both directions. `--strict` disables it.
- The host returns a non-zero exit on many successful one-shot runs. The probe
  only scores `BLOCKED` when nothing loaded, so those rows are still graded.
- Raw JSONL and the per-model summaries stay in the gitignored
  `.workspaces/gauntlet-trigger-probe/`.

## Reproduce

```bash
python3 scripts/gauntlet/trigger-probe.py --model gemini-3-5-flash \
  --include-explicit --kind positive --repeat 1 \
  --only code-review-agent --only grill-me --only model-adaptation \
  --only render-sanity --only skill-explorer
```
