---
name: fix-until-green
version: 1.0.0
description: >-
  Drive a failing build to passing in a disciplined loop: run the project's full
  gate (tests + lint + typecheck), fix one root cause, re-run the whole gate, and
  repeat until all three exit clean — with a hard iteration cap, no-progress
  detection, and a rule against cheating the gate green. Use when tests/CI are
  red and you want them green, when a build wave fails its checks, or as the QE
  inner loop under an orchestrated build. Trigger on: "fix until green", "make
  the tests pass", "get CI green", "fix the failing tests", "make it green",
  "drive the build to passing", "red to green", "loop until tests pass", "fix
  lint and type errors", "keep fixing until the suite is clean", "make the wave
  gate pass". A configuration of loop-controller — it supplies the harness; this
  skill supplies the proof (three exit codes) and the fix discipline.
requires_claude_code: true
min_plan: starter
disable-model-invocation: true
allowed-tools: ["Read", "Write", "Edit", "Bash", "Grep", "Glob"]
composes_with: ["loop-controller", "orchestrator-task-loop", "qe-agent", "diagnose-loop", "git-commit", "orchestrator"]
spawned_by: ["orchestrator"]
---

# fix-until-green

> **A configuration of [`loop-controller`].** That skill supplies the loop
> machinery — primitive selection, the full guardrail stack, state
> externalization. This skill supplies the two things specific to "get the build
> green": a **mechanical proof** (three exit codes) and the **fix discipline**
> that keeps the loop from cheating its way there. Read `loop-controller` for the
> guardrails; they're inherited, not repeated here.
>
> **Why `disable-model-invocation`:** this loop edits and commits code on its own
> until a gate passes. You want to *type* `/fix-until-green` (or have the
> orchestrator dispatch it) — not have Claude start an autonomous edit loop
> because a test happened to fail.

## The 5-part contract

| Part | This loop |
|---|---|
| **trigger** | red suite / CI, a failed build wave, or an explicit `/fix-until-green` (optionally scoped to a path) |
| **action** | run the whole gate → read the highest-signal failure → fix **one root cause** → re-run the **whole** gate |
| **proof** | `test` exits 0 **AND** `lint` exits 0 **AND** `typecheck` exits 0 — default-FAIL (assume red until all three are observed clean **in the same run**) |
| **memory** | `fix_plan.md` (live TODO of remaining failures + the failure→fix log) once the loop runs past one iteration or has to escalate — a single trivial mechanical fix doesn't need the ceremony; plus a git checkpoint per green-ward step |
| **stop** | all three clean **OR** iteration cap **OR** no-progress for 3 rounds **OR** budget cap |

## The proof: three exit codes, default-FAIL

"Green" is not "the test I was looking at passes." It is **all three of test,
lint, and typecheck exiting 0 in the same run**, with no test removed or weakened
to get there. Assume **red** until you have observed all three clean together —
that's the default-FAIL stance. A loop that calls it done after fixing the one
visible failure ships the other two broken.

Some stacks fold lint/typecheck into the test command or omit one (a dynamically
typed project may have no typecheck step). Detect what actually exists (Step 1);
a step that genuinely doesn't exist passes vacuously, but **don't assume** —
absence must be confirmed, not guessed.

## Step 1 — Detect the gate commands

Find the three commands for *this* project before looping. Precedence:

1. **`.claude/profile.yaml`** if present — it may declare `test` / `lint` /
   `typecheck` explicitly. Use those verbatim.
2. **Declared scripts** — `package.json` `scripts`, `Makefile` targets,
   `pyproject.toml` / `tox.ini`, `Cargo.toml`, `go.mod`, `composer.json`. Prefer
   the project's own named script (`npm run test`, `make check`) over a raw tool
   invocation, so you run what CI runs.
3. **Stack default** — only if nothing is declared. The per-stack table (node,
   python, rust, go, ruby, java, …) is in `references/gate-commands.md`.

Record the three resolved commands in `fix_plan.md` so every iteration runs the
identical gate. Running a *different* command than CI is the most common way a
"green" loop produces a still-red PR.

## Step 2 — Run the whole gate, read the real failure

Run all three commands, capture exit codes and output. Then **pick one
root-cause failure to fix** — not the first line of the stack trace, the *cause*.
Twenty failures with one shared cause is one fix, not twenty. Don't shotgun
edits across many failures in a single iteration; that destroys the signal about
what actually moved the gate.

## Step 3 — Fix one root cause

- **Mechanical failures** (a clear type error, a missing import, an off-by-one
  the assertion points straight at) — fix directly.
- **Hard failures** (flaky tests, "passes locally fails in CI," a performance
  regression, intermittent races, "I can't reproduce it") — **invoke
  [`diagnose-loop`]** rather than guessing. Its Phase-1 discipline (build a fast,
  deterministic, binary-signal reproduction first) is exactly what a fix loop
  needs and exactly what gets skipped under pressure to go green.
- **Change one variable per iteration** so the re-run tells you whether *that*
  fix worked. This is what makes the loop a binary search instead of guessing.

## Step 4 — Re-verify the whole gate, checkpoint

Re-run **all three** commands from scratch — not just the one you touched. A fix
that greens the failing test but reds typecheck has made the gate worse, and only
a full re-run catches it. This is the "restart the streak" rule: the proof is
about the *whole*, re-checked after every change.

On a green-ward step (strictly fewer failures, nothing new broken), **commit a
checkpoint** with a message naming the root cause fixed — the git trail is the
loop's undo and its post-mortem. When all three exit 0 together, the loop is
done; report the final gate output as evidence.

## Guardrails specific to this loop

Inherits the full stack from `loop-controller` → `references/safety.md`. The
caps this loop sets:

- **Iteration cap** — default ~15–25 (read from `.claude/profile.yaml` if set).
  Hitting the cap is a *stop-and-escalate*, not a license to weaken the gate.
- **No-progress detection** — if the **same set of failures** survives **3
  consecutive iterations**, stop and escalate. The same failure three times means
  the approach is wrong, not that it needs a fourth try. Surface the stuck
  failure to the human with what was tried.
- **Never cheat the gate green.** Forbidden, and each is a *finding* if you catch
  it: deleting or `skip`-ping a failing test, weakening an assertion, adding an
  ignore directive (`// eslint-disable`, `# type: ignore`, `@ts-expect-error`) to
  silence rather than fix, or relocating a violation into the checker's blind
  spot. If a test is genuinely wrong, that's a human decision — surface it, don't
  unilaterally delete it. (Anthropic's harness, verbatim: *"It is unacceptable to
  remove or edit tests."*)
- **AFK-safe only within the reversible boundary.** Editing source + running the
  gate is reversible and has a hard verifier — fine unattended. If a fix would
  touch something irreversible (a migration against a real DB, an external API,
  anything destructive), that's an HITL checkpoint — pause for the human.

## Choosing the driver primitive

Per `loop-controller` Step 1, by how you're running it:

- **Default — `/goal`:** the proof is provable from command output, so
  `/goal "the test, lint, and typecheck commands for this project all exit 0 in
  the same run, with no test removed or weakened — or stop after N turns."` The
  Haiku evaluator reads the gate output you surface each turn. Remember the
  embedded turn cap — `/goal` has no native budget.
- **Stop-hook gate** when you want the check to ship *with* the build and block
  exit deterministically (the orchestrator wave gate, a per-skill gate other role
  skills inherit). The gate script + `stop_hook_active` guard are in
  `references/stop-hook.md`.
- **`claude -p` (Ralph)** for a long, greenfield, fresh-context-per-iteration run
  — sandboxed, with an external iteration/token counter.

## Using it under the orchestrator

This is the **QE inner loop** and a natural **wave gate**. When the orchestrator
dispatches it (or wires the Stop-hook into a wave), failures route back to the
owning agent **by file**: a red typecheck in `src/api/` goes to the backend
agent, not a generic "fix it." The orchestrator does **not** override a stuck
loop — if fix-until-green escalates after no-progress, that's a real blocker for
the QA gate, not a number to paper over. The relationship to the QA gate is
exactly `loop-controller`'s rule: the loop informs, the `qe-agent`'s
`qa-report.json` still decides.

## Reference files

- `references/gate-commands.md` — per-stack detection of the test / lint /
  typecheck commands (node, python, rust, go, ruby, java, php, …) and how to
  compose three exit codes into one pass/fail.
- `references/stop-hook.md` — the Stop-hook gate that ships with this skill: the
  script, the `stop_hook_active` guard, and how to wire it into a build or have a
  role skill inherit it.

[`loop-controller`]: ../loop-controller/SKILL.md
[`diagnose-loop`]: ../../workflows/diagnose-loop/SKILL.md
