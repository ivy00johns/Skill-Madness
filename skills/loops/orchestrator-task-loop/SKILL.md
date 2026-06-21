---
name: orchestrator-task-loop
version: 1.0.0
description: >-
  The outer orchestration loop over the Agent Teams shared task list: the lead
  loops the board until EVERY task is completed AND each passes its TaskCompleted
  gate, feeding idle workers via the TeammateIdle hook so the team never stalls.
  One pass = read the board, assign the highest-priority unblocked task to each
  idle teammate, gate each completed task (pass counts it; fail rolls it back),
  re-verify the whole board. Generalizes ralph-orchestrator onto Agent
  Teams. Experimental — gated behind CLAUDE_CODE_EXPERIMENTAL_AGENT_TEAMS=1; falls
  back to the orchestrator's subagent/sequential path when off. Use to drain a
  task board or keep the team working until done under a build.
  Trigger on: "loop over the task list", "drain the task board", "keep the team
  working until done", "agent teams loop", "orchestrator task loop", "keep idle
  teammates fed". A configuration of loop-controller — it supplies the harness;
  this skill supplies the proof (the task list fully drained) and the
  assignment/supervision discipline.
requires_claude_code: true
requires_agent_teams: true
min_plan: starter
disable-model-invocation: true
allowed-tools: ["Read", "Write", "Edit", "Bash", "Glob", "Grep", "Agent", "Task", "Workflow"]
composes_with: ["loop-controller", "orchestrator", "fix-until-green", "qe-agent", "contract-auditor", "context-manager", "diagnose-loop", "git-commit", "loop", "schedule"]
spawned_by: ["orchestrator"]
---

# orchestrator-task-loop

> **A configuration of [`loop-controller`].** That skill supplies the loop
> machinery — primitive selection, the full guardrail stack, state
> externalization. This skill supplies the two things specific to draining the
> task list: a **mechanical proof** (every task `completed` **and** passing its
> `TaskCompleted` gate) and the **assignment/supervision discipline** that keeps
> the loop from declaring victory on a half-drained list. Read `loop-controller`
> for the guardrails; they're inherited, not repeated here.
>
> **Why `disable-model-invocation`:** this loop spawns teammates and drives an
> entire task list to completion on its own — assigning, supervising, gating, and
> re-triggering its own stop. You want to *type* `/orchestrator-task-loop` (or
> have the orchestrator dispatch it) — not have Claude silently start an unbounded
> team-supervision loop because a task board happened to exist.
>
> **Experimental.** Agent Teams is disabled by default and gated behind
> `CLAUDE_CODE_EXPERIMENTAL_AGENT_TEAMS=1`, with known limitations (no session
> resumption for in-process teammates, lagging task-state propagation, slow
> shutdown). This is a prototype-behind-the-flag skill. If the flag is unset, it
> refuses to start and points you at the orchestrator's subagent/sequential path
> (see Step 1 + the degradation note).

## The 5-part contract

| Part | This loop |
|---|---|
| **trigger** | A populated Agent Teams shared task list (tasks `pending`/`in_progress`, team spawned) **and** `CLAUDE_CODE_EXPERIMENTAL_AGENT_TEAMS=1` — or an explicit `/orchestrator-task-loop`. Dispatched by the orchestrator after contracts exist and the board is seeded (one task per contract-bounded unit, `blockedBy` edges from the dependency graph). |
| **action** | **One supervision pass:** read the board → for every `idle` teammate (surfaced by `TeammateIdle`), assign the highest-priority `pending` task whose `blockedBy` set is fully `completed` → let teammates work in their own context windows and claim tasks → on `completed`, run that task's `TaskCompleted` gate (**pass → done; fail → rolled back to `pending` with the failure as feedback**) → surface blocked/ambiguous tasks for HITL. **Assignment, not implementation** — the loop routes and supervises; teammates do the work. |
| **proof** | The board is **drained**: every task `completed` **AND** each passed its `TaskCompleted` gate **AND** no `blockedBy` edge points at a non-`completed` task — observed in one full read. Default-FAIL: assume undrained until that whole-board predicate holds. (See "The proof".) |
| **memory** | The **shared task list file** is the durable state (task states + `blockedBy` + gate verdicts survive across passes and fresh contexts) — this loop's "feature-list JSON," default-FAIL. Plus a **checkpoint commit per task**, the team's **peer-message log**, and an optional `PROGRESS.md` roll-up. No cross-iteration state lives in the lead's conversation. |
| **stop** | board drained (success) **OR** hard iteration (pass) cap **OR** the **3-failure circuit breaker** (board/task unchanged across 3 consecutive passes, or a task ping-pongs `completed`→gate-fail→`pending` ≥3×) **OR** enforced token/cost budget cap **OR** an HITL-blocked task with no unblocked work left. |

## The proof: a fully drained task list, default-FAIL

"Done" is **not** "every teammate said they finished." It is a mechanical,
default-FAIL predicate over the *whole* board, re-evaluated after every pass
("restart the streak"):

**`DONE` ⟺ for every task `t` on the board:**
1. `t.state == completed`, **and**
2. `t` passed its `TaskCompleted` gate (last verdict PASS — a `completed` task whose gate is unrun or failed does **not** count), **and**
3. every `b ∈ t.blockedBy` is itself `completed` and gate-passing (no dangling dependency), **and**
4. no `pending`/`in_progress` tasks remain, and no `idle` teammate has assignable work.

Each clause starts `false` and flips only on evidence read from the task-list
file. The proof is over the **board**, not the last task touched: completing task
N while a `TaskCompleted` rollback re-opened task M means the board is **not**
drained — only a full re-read catches it. This is exactly `loop-controller`'s
default-FAIL + re-verify-the-whole rule applied to a task board instead of one
exit code, and it is where this loop differs from a single-task loop: the verifier
is the *board predicate*, evaluated every pass.

## Step 1 — Detect the Agent Teams runtime, or degrade

Before assigning anything, confirm the substrate. Precedence:

1. **`CLAUDE_CODE_EXPERIMENTAL_AGENT_TEAMS=1`** must be set. If it is unset, this
   loop **refuses to start** — tell the user to set the flag, or hand back to the
   orchestrator's subagent/sequential path (the orchestrator's runtime tree:
   subagents via Task/Agent, else sequential). The shared task list + Teammate/Task
   hooks this loop relies on only exist under native Agent Teams.
2. **A spawned team + a populated shared task list.** If contracts exist but the
   board isn't seeded, that's the orchestrator's job, not this loop's — seed one
   task per contract-bounded unit of work, with `blockedBy` edges from the
   dependency graph, *then* loop.

Read caps (max passes, budget), state-file paths, and the seed source from
`.claude/profile.yaml` / the orchestrator's plan when present — don't invent tasks
the plan already defines. Substrate mechanics (states, `blockedBy`, TeammateTool,
peer messaging, the flag, known limitations) are in `references/agent-teams.md`.

## Step 2 — Assign ready work, keep idle workers fed

One pass routes work; it does not write code:

- **`TeammateIdle` = "assign new work."** When a teammate goes idle, pick the
  **highest-priority `pending` task whose `blockedBy` is fully `completed`** and
  assign it. This feeder is what keeps the loop converging instead of stalling
  with idle workers and undrained tasks.
- **Teammates work in their own context windows** and claim tasks
  (`pending`→`in_progress`). All coordination flows through the shared file +
  peer-message log — no central bottleneck.
- **Cap build/test parallelism per `loop-controller` Step 5.** Fan out search and
  read-only verification freely, but don't let two teammates run the integrated
  build at once — concurrent builds destroy the backpressure signal.

The assignment algorithm in full (priority + unblocked-set selection) is in
`references/hooks.md` under the `TeammateIdle` feeder.

## Step 3 — Gate each completed task (the inner loop hooks in here)

When a teammate marks a task `completed`, its **`TaskCompleted` gate** fires —
this is the proof's atom and the loop's backpressure edge:

- **Pass → the task counts toward the proof.**
- **Fail (exit 2) → the task is rolled back** to `pending`/`in_progress` with the
  failure surfaced as feedback. A task does **not** count until its gate is green.
- **Each task's gate can be driven by a [`fix-until-green`] inner loop.** The
  teammate working a code task runs `fix-until-green` to drive its
  tests+lint+typecheck red→green; only then does `TaskCompleted` pass and this
  outer loop counts it. The outer loop **never reaches into** a task's gate — it
  consumes the verdict. (This is the inner/outer composition; see "Under the
  orchestrator".)
- The gate may be a **deterministic script** (mechanical bars) or an
  **agent-type/prompt hook** — a fresh-context evaluator subagent with **no
  Write/Edit tools** (`loop-controller` Step 2) for subjective bars; for
  build-until-spec tasks, [`contract-auditor`] is the natural evaluator.
- **QA-gated tasks consult the qe-agent's `qa-report.json`** (`gate_decision.proceed`,
  CRITICAL blockers, contract_conformance/security ≥ 3) — the same gate the
  orchestrator already uses. The loop **informs, it does not decide**.

## Step 4 — Re-verify the whole board, checkpoint

After any task flips, re-scan the **entire** board against the §proof predicate —
not just the task that moved. "Restart the streak": a fix that completed task N
but a rollback that re-opened task M means the board is still undrained, and only a
full re-read catches it. On each task that passes its gate, **commit a checkpoint**
naming the task — the git trail is the loop's undo (`git reset --hard` to the last
green task + re-loop) and post-mortem. When the predicate holds for the whole
board, the loop is done; report the drained board as evidence.

## Guardrails specific to this loop

Inherits the full stack from `loop-controller` → `references/safety.md`. The caps
this loop sets, mapped onto the team substrate:

- **Hard iteration cap** — a max number of supervision passes (read from
  `.claude/profile.yaml` if set). Hitting it is **stop-and-escalate**, never
  "lower the gate."
- **Enforced token/cost budget** — a ceiling that **terminates**, not just warns.
  Agent Teams uses 3–5×+ a single session's tokens; the documented 11-day /
  tens-of-thousands-of-dollars runaway had observability but no enforcement. Set
  per-teammate budget caps **and** a board-level ceiling.
- **No-progress / oscillation = the orchestrator's 3-failure circuit breaker.** If
  board state (or a single task) is unchanged across **3 consecutive passes**, or a
  task ping-pongs `completed`→gate-fail→`pending` ≥3×, **stop and escalate**. This
  *is* `loop-controller`'s guardrail and the orchestrator's existing breaker — one
  vocabulary, not a new one. See `skills/orchestrator/references/circuit-breaker.md`.
- **Checkpoint commit per task** — commit working state each time a task passes its
  gate (Step 4).
- **HITL for ambiguous/blocked tasks** — pause and surface any task that's blocked
  with no path forward, ambiguous, or about to touch something irreversible
  (deploy, prod DB write, external API, force-push). Don't let the loop guess past a
  real block.
- **Sandbox** for any unattended run — workspace/worktree isolation so one
  teammate's failure can't contaminate the board or other teammates.
- **Never weaken the gate.** Forbidden, each a *finding*: editing the
  `TaskCompleted` gate, the task list, or `qa-report.json` to mark a task done. A
  task that went `completed` by relaxing its gate is not progress — read the diff
  that flipped it.

**Promote to unattended/overnight ONLY when every loop in the build has all five**
(`safety.md` Stage 3): a hard external verifier, an *enforced* token budget,
no-progress detection, checkpoint commits, and a sandbox. Until then, run
**attended** — and because Agent Teams is experimental, stay attended until the
loop completes consecutive clean runs (the staged-adoption ladder in
`loop-controller/references/safety.md`). **Roll back to attended / kill** when:
token spend grows non-linearly, board state is unchanged across passes, a
`TaskCompleted` gate and human judgment disagree, or a task is about to touch an
irreversible resource without a checkpoint.

**Degradation (required, `requires_agent_teams: true`).** When
`CLAUDE_CODE_EXPERIMENTAL_AGENT_TEAMS` is unset, this loop does not run — fall back
to the orchestrator's subagent path (Task/Agent fan-out with the wave gate driving
each wave red→green via `fix-until-green`) or sequential mode. The proof and the
discipline survive; only the shared-task-list substrate and the Teammate/Task hooks
are unavailable.

## Choosing the driver primitive

Per `loop-controller` Step 1, this loop's primitive is the **Stop/SubagentStop
hook + TeammateIdle hook combination**: the Stop hook blocks the lead's exit while
the board predicate (§proof) is not yet `DONE`; `TeammateIdle` keeps workers fed so
the board actually converges between blocks. Secondary, for interactive runs: a
`/goal`-style condition over the whole board ("every task `completed` and passing
its `TaskCompleted` gate, or stop after N passes"). The hook scripts, the
`stop_hook_active` guard, and the auto-conversion-to-SubagentStop note are in
`references/hooks.md`.

## Under the orchestrator (the wiring this unblocks)

`loop-controller` already notes the two-level structure — an inner loop per role,
an outer loop over the shared task list — and says "that orchestrator wiring is a
separate, later skill." **This is that skill.**

- **Outer = this skill.** Loops over the **whole board** (assignment + supervision):
  drain every task to `completed` + gate-passing.
- **Inner = [`fix-until-green`].** Drives **one task's** gate red→green (three exit
  codes, no cheating). They **compose**: a task's `TaskCompleted` gate is satisfied
  by dispatching `fix-until-green`; the outer loop consumes the verdict.
- **`qe-agent` still decides the build gate.** Echoing `fix-until-green`: the loop
  informs, the `qe-agent`'s `qa-report.json` / `gate_decision` decides — a rollback
  or a circuit-breaker escalation is a real blocker, not a number to paper over.
- **Generalizes ralph-orchestrator:** orchestrator decomposes → spawns workers →
  loops the board; `validation.failed` is a worker re-trigger. Here the orchestrator
  is the event router and `TaskCompleted` is the `validation.passed/failed` edge,
  onto Agent Teams' native shared task list.

## Reference files

- `references/agent-teams.md` — the shared-task-list substrate: states
  (`pending`→`in_progress`→`completed`), `blockedBy` edges, seeding one task per
  contract-bounded unit, teammates claiming/working in their own context windows,
  peer-message coordination, the drained-board predicate as a checkable routine, the
  `CLAUDE_CODE_EXPERIMENTAL_AGENT_TEAMS=1` flag, and the known-limitations caveats.
- `references/hooks.md` — the three hooks in full: the `TaskCompleted` gate (payload,
  exit-2 rollback, backing it with `fix-until-green` or `qa-report.json`), the
  `TeammateIdle` feeder (assignment algorithm), and the `Stop`/`SubagentStop`
  re-trigger (script + `stop_hook_active` guard + auto-conversion).

[`loop-controller`]: ../loop-controller/SKILL.md
[`fix-until-green`]: ../fix-until-green/SKILL.md
[`contract-auditor`]: ../../contracts/contract-auditor/SKILL.md
