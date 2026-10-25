---
name: skill-eval
version: 0.1.1
description: >-
  Measure whether a skill actually helps: build a `claude plugin eval` suite,
  run it with and without the skill under a required spend cap, and read the
  delta. Use when adding evals to a skill, converting evals.json, re-checking
  skills after a model upgrade, or deciding if a skill should be cut. Trigger
  on: "plugin eval", "eval this skill", "does this skill help", "skill delta".
requires_agent_teams: false
requires_claude_code: true
min_plan: starter
owns:
  directories: []
  patterns: []
  shared_read: ["skills/"]
allowed-tools: ["Read", "Write", "Bash", "Grep", "Glob"]
composes_with:
  [
    "skill-triage",
    "skill-review",
    "skill-update",
    "skill-writer",
    "model-adaptation",
  ]
spawned_by: []
---

# skill-eval

A skill can read well and still add nothing — the model would have done the
same work without it. `claude plugin eval` (Claude Code ≥ 2.1.269) measures
that directly: every case runs in an isolated session **with** the skill loaded
and again **without** it, and the report's **Δ (delta)** is the difference.
Δ > 0 is the skill's contribution. Δ ≈ 0 on a case the skill claims to own
means it isn't pulling its weight.

This skill wraps that runner for single skills in this repo. Its job is to
make suites correct and keep spend near zero: cheap checks are free, and the
only step that runs Claude sessions demands a cap you chose.

**What "cost" means here.** Every case run is a full Claude Code session on
whatever credential the CLI is logged in with. Logged in through claude.ai
(`claude auth status` shows `authMethod: claude.ai`), runs draw on the
subscription's usage allowance, not dollars. The runner's `costUsd` and
`--max-cost-usd` are estimated API-equivalent figures, which still work as a
size gauge and a cap. Real dollars are spent only with an API key, or with
paid extra usage past the plan limit. Check `claude auth status` before
telling the owner what a run will cost them.

## Where this fits

| Question                                                        | Skill                                     |
| --------------------------------------------------------------- | ----------------------------------------- |
| Which skill _fires_ for a request; who steals whose triggers    | `skill-triage` (Jev, fractions of a cent) |
| Does the skill _help_ once it fires — measured, with vs without | **skill-eval**                            |
| Is the SKILL.md well written, within budget, spec-conformant    | `skill-review`                            |
| Draft, iterate and hand-review outputs while authoring          | `skill-creator` (its `evals/evals.json`)  |

`evals/evals.json` (skill-creator's authoring format) and plugin-eval case
directories live side by side in the same `evals/` folder. `convert` turns the
first into the second; it never deletes or rewrites either.

## The script

`scripts/skill_eval.py` (Python stdlib). Run it from the repo root with a
skill directory as the target:

| Mode                               | Cost     | What it does                                                                                                                                                                                                     |
| ---------------------------------- | -------- | ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `convert <skill> [--negative "…"]` | free     | Each `evals.json` entry → a case dir with `prompt.md`, a display-only "skill fired" check and a judge rubric from its assertions. `--negative` adds a must-not-fire case. Existing case dirs are kept untouched. |
| `lint <skill>…`                    | free     | Enforces the runner's floor rules (below), flags sandbox-breaking paths, and prints the suite's session count and paid-grader count.                                                                             |
| `run <skill> --max-cost-usd N`     | **usage** | Lints, then runs `claude plugin eval` with/without ablation and a local-only report. The cap is required; there is no default.                                                                                   |
| `report <skill>`                   | free     | Δ, scores and the real `costUsd` from the latest `evals/results/*/aggregate-result.json`.                                                                                                                        |

Exit codes: 0 ok, 1 lint failure or a case below `--threshold`, 2 argument
error, 3 `claude` CLI missing or too old, 5 stopped at the cap (partial
results kept). Results land in `<skill>/evals/results/`, which is gitignored.

## The floor rules (why lint fails a suite)

These come from the runner's own authoring guide. Each one exists because
without it the number stops meaning anything:

- **At least one must-not-fire case.** A suite with only positive cases can't
  tell a skill that helps from one that fires on everything. The check is a
  `tool_used` grader with `tool: Skill`, `min: 0`, `max: 0`, **and**
  `arm: both` — leave out `arm` and it becomes display-only and never scores.
- **Every case has an outcome grader**, not just "the skill fired". A plain
  fired-check is excluded from the score under ablation; it can't move Δ.
  Grade what the user would notice: the answer, the file, the format.
- **`runs` ≥ 3** in the case file. Single runs are noise. For a pilot, pass
  `--runs 1` on the command line instead of lowering the floor in the file.
- **No absolute or `~/` paths** — cases run in a sandbox working directory.
- **Set `timeout_seconds` and `allowed_tools`** to fit the work. An
  under-set timeout scores 0, not "timed out", which reads as a broken skill.
  Tools beyond Read/Glob/Grep/Skill (Bash, Write, Edit, WebFetch, `mcp__*`)
  also need an operator grant at run time: `--allow-tools Write`.

## Cases that can actually measure something

A case can follow every floor rule and still be unable to show a difference.
The common ways that happens, all seen in real conversions:

- **The input isn't in the sandbox.** evals.json prompts often point at
  `~/repos/x` or an "attached" doc. In the sandbox both arms just report "not
  found", and Δ ≈ 0 says nothing about the skill. Build a small fixture repo
  and copy it in with a `case.yaml` `scaffold_script`, then run with
  `--scaffold`. Put contradictions in the fixture (a doc claim the code
  disproves) so a grader can tell careful work from a skim.
- **The skill pauses to ask.** Eval sessions can't answer a question. If the
  skill confirms before acting (an output folder, a destructive step), state
  the answer in the prompt ("write to `./out/` — confirmed"). Otherwise the
  with-arm scores worse _for following its own rule_.
- **Writing skills get read-only defaults.** `convert` gives every case
  Read/Glob/Grep/Skill, 20 turns and 600 s, and its notes flag cases that look
  like they write files. Those need Write in `allowed_tools`, a real budget
  (deep-dive-sized work can take 60 turns and 1500 s), `--allow-tools Write`
  at run time, and graders that read the file (`regex` with
  `target: {source: file, path}`, or `file_exists`). A judge on the last
  message can't see what the skill wrote.
- **`--ablation none` isn't a cheaper Δ.** It drops the without-arm, so there
  is no Δ at all. To save money, pilot one case with `--runs 1`.

## Grader choice is a cost choice

| Type                       | Cost       | Use for                                                                                                            |
| -------------------------- | ---------- | ------------------------------------------------------------------------------------------------------------------ |
| `regex`                    | free       | Mechanical claims: a ` ```mermaid ` block exists, a heading is present, a phrase is absent (`match: not_contains`) |
| `file_exists`              | free       | The skill must create a file (`path: <glob>`)                                                                      |
| `tool_used` / `tool_order` | free       | Fired / must-not-fire; tool sequencing                                                                             |
| `llm`                      | paid judge | Claims a pattern can't check. Write the rubric as concrete checkable claims                                        |
| `baseline`                 | paid judge | Preference between arms — rarely worth it                                                                          |

`convert` writes assertions into one `llm` rubric because evals.json
assertions are prose. After converting, rewrite any assertion that's really a
pattern as a free `regex` grader. The judge defaults to Haiku; the runner's
guide recommends `--judge-model sonnet` for nuanced rubrics, which costs more.
That trade is the owner's to make.

The judge is the small cost. **Sessions are the big one**: a full run is
(cases × runs × 2 arms) complete Claude sessions, each doing real work. `lint`
prints that count so the size is visible before anything is spent.

## The spend protocol

Session runs follow the same rule as every paid call in this repo: estimate,
run the smallest version, never raise a cap without asking.

1. `lint` — free. Read the session count.
2. **Pilot one case**: `run <skill> --case '<one>' --runs 1 --max-cost-usd 0.25`.
   Use the must-not-fire case first; it's the shortest.
3. `report` — real `costUsd` for those 2 sessions. Multiply by the session
   count from step 1 for the full suite, and tell the owner the figure
   (subscription usage, or dollars on an API key) before running it.
4. Full run only on the owner's yes, with a cap at that figure plus headroom.
   Exit 5 means the cap stopped it; report the partial result. Don't rerun
   with a higher cap on your own.

**Trust.** The first run in a folder asks whether you trust the plugin; a
non-interactive run can't answer. Ask the owner once, and pass `--trust` only
after a yes. It doesn't grant extra tools or scaffold scripts.

**Publishing.** `run` keeps the HTML report local (`--no-publish`). Pass
`--publish` only when the owner wants it on claude.ai.

## Reading a result

- **Δ > 0 on the skill's own cases** — it helps. Keep it.
- **Δ ≈ 0 where the skill claims value** — the model already does this
  unaided. That's a prune or rewrite candidate for `skill-update`, or a sign
  the cases are too easy (the model only reaches for skills on tasks it can't
  do trivially, so trivial prompts score the same with or without).
- **Must-not-fire case fails** — the description over-triggers. Take the
  prompt to `skill-triage collisions --skill <name>` to see who it's stealing
  from.
- **`report` warns a plugin `problem`** (`manifest_invalid`,
  `disabled_by_default`, `will_not_load`) — the with-arm ran without the skill.
  The scores are meaningless; fix loading first.
- **An implausible jump between runs** — suspect the judge being gamed;
  spot-check the transcripts before believing it.

Re-run a skill's suite after a model or Claude Code upgrade. Harness
behaviour shifts, and `model-adaptation` pruning should be backed by a Δ, not
a hunch.

## Anti-patterns

| Anti-pattern                                         | Why it fails                                                         |
| ---------------------------------------------------- | -------------------------------------------------------------------- |
| Running the full suite before a one-case pilot       | You learn the cost after paying it                                   |
| A suite with no must-not-fire case                   | Can't tell a useful skill from an over-eager one                     |
| `tool_used: Skill` as a case's only grader           | Excluded from the score; Δ is always 0                               |
| `llm` graders for mechanical checks                  | Paying a judge for what a regex does free                            |
| Lowering `runs` in the case file to save money       | Breaks the floor; use `--runs 1` for pilots only                     |
| Raising `--max-cost-usd` after exit 5 without asking | The cap is the owner's decision                                      |
| Absolute paths in prompts                            | The sandbox has a different cwd; the case fails for the wrong reason |
