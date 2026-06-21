# The Agent Teams shared task list

This is the loop's **durable state** and its **proof artifact** — the analogue of
`fix-until-green`'s three exit codes, but a *whole-board predicate* instead of one
process's exit. Where `fix-until-green` reads `tests && lint && typecheck` into one
green/red, this loop reads N task verdicts into one **drained / undrained** signal.
Everything here is gated behind `CLAUDE_CODE_EXPERIMENTAL_AGENT_TEAMS=1`; without
it, none of this substrate exists and the loop degrades (see below).

## The experimental flag (precondition)

- Native Agent Teams is **disabled by default**. Set
  `CLAUDE_CODE_EXPERIMENTAL_AGENT_TEAMS=1` to enable the shared task list, the
  `TeammateTool`, the peer-message inbox, and the Teammate/Task lifecycle hooks.
- **Known limitations (prototype-behind-the-flag):**
  - **No session resumption** for in-process teammates — a killed teammate's
    context is gone; the *shared file* is what survives, not the teammate.
  - **Task-state propagation lags.** A transition you just triggered may not be
    visible on the next read. **Re-read before trusting a transition**, and treat a
    single read as a snapshot, never as ground truth across passes.
  - **Slow shutdown.** Tearing the team down is not instant; budget for it when
    you hit a cap or circuit breaker.
- **Fallback when unset:** the orchestrator's subagent path (Task/Agent fan-out)
  or sequential mode. Those runtimes have **no shared task list and no Teammate
  hooks** — the proof and the assignment discipline survive, but you drive them by
  hand / via the wave gate instead of via this substrate.

## Task states

```
pending ──claim──▶ in_progress ──mark done──▶ completed
   ▲                                              │
   └──────────── TaskCompleted gate FAIL ─────────┘  (rollback, failure as feedback)
```

- The three explicit states are `pending` → `in_progress` → `completed`, plus an
  **implicit gate verdict** attached when `TaskCompleted` fires: **PASS / FAIL /
  unrun**.
- A `completed` task whose gate is **unrun or FAIL does NOT count** toward the
  proof. `completed` is **necessary, not sufficient** — "completed" is the
  teammate's claim; the gate verdict is the proof.
- **Rollback edge:** a `TaskCompleted` FAIL re-opens `completed` → `pending` /
  `in_progress`, carrying the failure as feedback for the next attempt. This is the
  backpressure edge; it is what stops the board declaring victory on unverified
  work.

## blockedBy dependency edges

- Each task carries a **`blockedBy` set** (task ids). A task is **assignable only
  when every id in its `blockedBy` is `completed`-and-gate-passing** — a dependency
  that is merely `completed` (gate unrun/FAIL) does not unblock its dependents.
- **Seed edges from the orchestrator's dependency graph** — one task per
  contract-bounded unit of work. The edge set encodes the build order.
- **Cycle / dangling-edge checks belong to seeding, not the loop.** The loop trusts
  a well-formed graph; if seeding produced a cycle or an edge to a non-existent
  task, that's a seeding bug to surface, not something the loop should route around.

## Seeding the board

- **One task per contract-bounded unit:** a contract from `contracts/`, or an
  ownership-scoped slice of work. **Don't invent tasks the plan already defines** —
  read the orchestrator plan / `.claude/profile.yaml` first and seed from it.
- Set **`priority` and `blockedBy` at seed time** — the feeder (see `hooks.md`)
  sorts by priority within the assignable set, so priority is meaningless if it
  isn't seeded.
- Seeding is the orchestrator's job. If contracts exist but the board is empty,
  seed *then* loop — the loop does not author tasks mid-flight.

## How teammates work

- **Claim semantics:** a teammate moves a task `pending` → `in_progress`, works it
  **in its own context window**, and marks it `completed`. The lead never does the
  work — it routes and supervises.
- **TeammateTool + peer messaging:** coordination flows through the **shared file**
  and the **peer-message log / inbox**, not through the lead. The lead is **not a
  message relay** — it routes assignments and runs gates; teammates talk to each
  other directly. No central bottleneck.

## The drained-board predicate (the checkable routine)

This is the routine the loop runs **every pass** — the analogue of `gate-commands.md`
composing three exit codes into one pass/fail, here composing N task verdicts into
one board verdict. Read the task-list file and evaluate, **default-FAIL**:

```
DRAINED = true        # optimistic; any failing clause flips it false
for each task t on the board:
    if t.state != completed:                      DRAINED = false   # clause 1
    if gate_verdict(t) != PASS:                   DRAINED = false   # clause 2
    for b in t.blockedBy:
        if b.state != completed or gate_verdict(b) != PASS:
                                                  DRAINED = false   # clause 3
if any task is pending or in_progress:            DRAINED = false   # clause 4
if any idle teammate has an assignable task:      DRAINED = false   # clause 4
return DRAINED
```

- **Default-FAIL:** assume **undrained** until the **whole board** is observed
  satisfying all four clauses **in one read**. A partial read is not evidence.
- **"Restart the streak":** re-evaluate the **WHOLE board** after *any* task flips.
  A rollback on task M can **un-drain** a board that looked done because task N just
  passed — only a full re-read catches it. Never short-circuit on "the task I just
  touched is green."
- This predicate is clause-for-clause the §proof in `SKILL.md`; keep them in sync.

## Composing with the orchestrator's plan

- Read **caps** (`max_passes`, token/cost budget) and **state-file paths** from
  `.claude/profile.yaml` when present; the **seed source** is the orchestrator
  plan.
- Profile `minimal | standard | strict` governs advisory-vs-blocking handling of
  gate verdicts — strict treats a FAIL as a hard block; advisory surfaces it but
  lets the loop continue routing other tasks. The drained-board predicate is the
  same regardless; the profile only changes how aggressively a FAIL halts the pass.
