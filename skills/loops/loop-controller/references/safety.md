# Loop safety — the guardrail stack, in full

A loop without enforcement is a way to spend money in your sleep. The dominant
non-convergence modes are **thrashing** (~36% of incomplete agent runs in one
benchmark) and **budget exhaustion** (~29%) — together the majority. The stack
below targets both. Alerting is not enough; every guard must *terminate*.

## Contents
- [Exit condition (default-FAIL)](#exit-condition)
- [Iteration cap / circuit breaker](#iteration-cap)
- [Token / cost budget — enforced](#budget)
- [No-progress and oscillation detection](#oscillation)
- [HITL checkpoints before irreversible actions](#hitl)
- [Checkpoints and rollback](#rollback)
- [Guardrails against making things worse](#dont-make-it-worse)
- [Staged adoption and rollback ladder](#staged-adoption)

---

## Exit condition

Phrase "done" as a **mechanical, observable proof**: a test exit code, a file
count, an empty queue, a coverage %, a fresh evaluator's verdict. Use a
**default-FAIL contract** — criteria start `false`, evidence flips them — so the
loop can't mark itself passing. Avoid subjective conditions ("looks good") on the
model-evaluator path; route those through a fresh-context evaluator instead (see
`authoring.md`).

## Iteration cap

Always set a hard cap. `--max-iterations` for hook/bash loops; "stop after N
turns" inside the `/goal` condition (it has no native cap). Reference defaults
from production loop engines (verify before hard-coding — these are
ralph-orchestrator's, partly from its legacy v1):

- `max_iterations: 100`
- `max_runtime_seconds: 14400` (4h)
- consecutive-failure limit: **5**

Stop-hook loops **must check `stop_hook_active`** in the hook payload before
blocking — an unconditional block is an infinite loop.

## Budget

A token/cost ceiling that **terminates** the loop. Per-loop, enforced:

- `/goal` has **no** native budget — embed a turn cap and watch `/cost`.
- Dynamic workflows take an explicit token budget — pass one.
- Bash loops need an external iteration + token counter that exits at the cap.

Sizing reality: "Autonomous loops consume significant tokens. A 50-iteration
cycle on large codebases can cost $50–100+ in API credits." Multi-agent loops
use 3–5×+ the tokens of a single session. The lesson from the documented **11-day
/ tens-of-thousands-of-dollars** runaway: it had observability but no
*enforcement*. Set per-agent budget caps with hard termination — non-negotiable
for anything unattended.

## Oscillation

Stop when the loop stops making progress:

- **Output repetition** — ≥~90% similarity to a recent iteration's output trips
  the breaker (one documented system repeated the same answer **58 times**
  without this guard).
- **No state change** — no files changed, no proof movement across an iteration.
- **Token growth** that is quadratic rather than linear across iterations — a
  sign of context bloat / re-reading without progress.

## HITL

Mandatory human review **before any irreversible action**: DB writes, deploys,
external API calls, force-push, anything that touches production. Implement as a
checkpoint that *pauses* the loop (ralph-orchestrator uses a `human.interact`
event with a default 300s timeout). Unattended loops run **only** what is
reversible and has a hard verifier — coverage, lint/type fixes, dependency-
update-then-test, docs. Never unattended: production data changes, deploys,
anything without a test gate.

## Rollback

- **Checkpoint commit every iteration** with a descriptive message (the
  coding-agent recipe). The git trail is your undo.
- On a wedged codebase, `git reset --hard` to the last green checkpoint and
  re-loop is usually cheaper than rescuing the mess.
- **Worktree isolation** lets parallel agents fail without contaminating each
  other — use it for any fan-out loop.

## Don't make it worse

- Validate **only the changed unit** each loop for *speed*, but re-run the
  **whole** proof before declaring done (catch fixes that broke something else).
- **Forbid editing or deleting tests to make them pass.** Anthropic's harness
  says, verbatim, *"It is unacceptable to remove or edit tests"* — and stores the
  feature list as JSON because the model is less likely to overwrite JSON than
  Markdown.
- Use a **fresh-context evaluator with no Write/Edit tools** so the grader
  cannot "fix" a failure by lowering the bar.
- **A suspiciously easy green is a finding.** When a gate flips red→green, read
  the diff that did it: did it *resolve* the finding or *relocate* it into the
  checker's blind spot (a banned `rounded-full` reborn as inline
  `borderRadius:"50%"`), silence it with an ignore directive, or delete the
  assertion? Adversarial verification checks the fix, not the count.
- **A self-improving loop must gate its own edits on measured, held-out
  results — and there is now hard evidence for why.** microsoft/SkillOpt's
  Sleep study ran twin overnight self-improvement loops on SearchQA, one with
  an accept/reject validation gate and one without. The ungated twin learned a
  plausible-but-wrong rule ("answer with the document-title string verbatim")
  and collapsed **−52.8 points** night over night; the gated twin rejected
  every one of those edits and lost nothing. For any loop that edits its own
  prompt, skill, or config, the gate is not polish — it is the difference
  between converging and self-lobotomizing.

## Staged adoption

Don't go from zero to overnight-unattended. Promote on evidence:

- **Stage 1 (attended, one repo):** run the loop with a human watching.
  **Promote when** it completes **5 consecutive runs** with no human intervention
  and no oscillation.
- **Stage 2 (fresh-context evaluator introduced):** add the separate grader.
  **Promote when** the evaluator's pass/fail agrees with your judgment **≥90%**
  of the time — tune its prompt against the divergences (Anthropic found Claude
  is "out of the box a poor QA agent" and needed several rounds of evaluator
  tuning; budget for it).
- **Stage 3 (unattended / overnight):** allow **only when** every loop has a
  hard external verifier, an *enforced* token budget, no-progress detection,
  checkpoint commits, and a sandbox.

**Roll a loop back to attended (or kill it) when** any of: token spend grows
non-linearly, output similarity >90% across iterations, the evaluator and you
disagree, or it touches an irreversible resource without a checkpoint.
