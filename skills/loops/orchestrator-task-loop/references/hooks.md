# The three hooks that drive orchestrator-task-loop

This loop is driven by **three native Agent Teams lifecycle hooks**:

- **`TaskCompleted`** — the per-task gate (the proof's atom).
- **`TeammateIdle`** — keeps the board fed so it converges.
- **`Stop` / `SubagentStop`** — blocks the lead's exit until the board drains.

All three are gated behind `CLAUDE_CODE_EXPERIMENTAL_AGENT_TEAMS=1`. When the flag
is unset every handler is **inert** — the loop refuses to start and degrades to the
orchestrator's subagent/sequential path (see the precondition check at the end).

## Hook 1 — TaskCompleted (the per-task gate)

Fires when a teammate marks a task `completed`. It runs **that task's gate** and is
the loop's **backpressure edge**.

**Exit-code contract:**

- **exit 0 → the task counts** toward the proof (gate verdict PASS).
- **exit 2 (or any non-zero) → roll the task back** to `pending` / `in_progress`
  and **surface the failure as feedback** for the next attempt. The task does
  **not** count until its gate is green.

The gate is **per-task**:

- a **deterministic script** for mechanical bars (tests/lint/typecheck/build), or
- an **agent-type / prompt hook** for subjective bars — a **fresh-context evaluator
  subagent with NO Write/Edit tools** (`loop-controller` Step 2), so the judge can't
  edit the thing it's grading.

**Backing it with `fix-until-green`.** For a code task, the teammate's gate **is** a
`fix-until-green` run: drive tests + lint + typecheck to exit 0, *then*
`TaskCompleted` passes. The **outer loop consumes the inner verdict** — it never
reaches into the inner loop. This is the inner/outer composition.

**Backing it with `qa-report.json`.** For a QA-gated task, consult the qe-agent's
report — `gate_decision.proceed`, CRITICAL blockers, and
`contract_conformance` / `security ≥ 3` — the **same gate the orchestrator uses**.
The loop **informs; the qa-report decides**.

**Sample payload sketch** (shape, not a literal schema):

```json
{ "hook": "TaskCompleted", "taskId": "be-auth-7", "teammate": "backend-1", "state": "completed" }
```

The handler reads `taskId`, runs that task's gate, and emits the exit code above.

## Hook 2 — TeammateIdle (the feeder)

Fires when a teammate goes idle. The handler = **"assign new work"** — this is what
keeps the outer loop **converging instead of stalling** with idle workers and
undrained tasks.

**Assignment algorithm in full:**

```
on TeammateIdle(teammate):
    assignable = [ t for t in board
                   if t.state == pending
                   and all(b is completed-and-gate-passing for b in t.blockedBy) ]
    if assignable is empty:
        if any task still pending/in_progress:
            # remaining work is blocked on an in_progress dependency, or genuinely stuck
            wait on the in_progress dependency, OR surface for HITL if nothing will unblock it
        else:
            # nothing left to assign — let the Stop hook evaluate the drained predicate
            return
    else:
        pick = max(assignable, key = priority)   # highest-priority unblocked pending task
        assign(pick, teammate)                    # pending -> in_progress (teammate claims)
```

Filter to the assignable set (`blockedBy` satisfied) → sort by priority → assign
one. If **none** are assignable but tasks remain, the remainder is **blocked** —
wait on an `in_progress` dependency, or escalate to HITL if nothing will unblock it.

## Hook 3 — Stop / SubagentStop (the re-trigger)

The lead's **`Stop` hook blocks exit while the board predicate is not `DONE`**, and
re-feeds "keep assigning and supervising." It carries over the **two invariants**
from `fix-until-green`'s stop-hook, in spirit:

1. **Guard `stop_hook_active`.** Block **iff** the board is undrained. When the flag
   is set **and** the board is drained, **let the stop through** — otherwise you get
   an infinite loop (the hook blocking its own re-entry forever).
2. **The drained-board check is the ONLY authority.** A **fully drained,
   all-gates-green** board must **always** allow the stop. Nothing else may veto a
   genuinely-done board.

**Repo Stop-hook contract:** signal a block by **printing
`{"decision":"block","reason":...}` to stdout and exiting 0** — *never* via a
non-zero exit. **Allowing** the stop prints **no decision** and exits 0.

**Reference gate script** (bash, mirrors `fix-until-green`'s `fix-until-green-gate.sh`):

```bash
#!/usr/bin/env bash
# orchestrator-task-loop Stop/SubagentStop gate
set -euo pipefail

# 0. Experimental-flag precondition — inert if teams are off.
[ "${CLAUDE_CODE_EXPERIMENTAL_AGENT_TEAMS:-}" = "1" ] || exit 0

payload="$(cat)"

# 1. Invariant 1: never re-block once already in a stop-hook re-entry.
if [ "$(jq -r '.stop_hook_active // false' <<<"$payload")" = "true" ]; then
  exit 0
fi

# 2. Let the loop's own guards decide escalation, not the hook:
#    a tripped cap / circuit breaker / budget / HITL block allows the stop.
if ./scripts/guardrail-tripped.sh; then
  exit 0
fi

# 3. The drained-board predicate (from agent-teams.md) is the ONLY authority.
if ./scripts/board-drained.sh; then
  exit 0                              # Invariant 2: drained board always allows stop.
fi

# 4. Undrained: block, naming the undrained tasks as the reason.
undrained="$(./scripts/board-undrained-tasks.sh)"
jq -cn --arg r "Board not drained; outstanding: $undrained. Keep assigning and gating." \
  '{decision:"block", reason:$r}'
exit 0
```

The script: read payload → check `stop_hook_active` → **allow if a guardrail
tripped** (so the loop's own caps/breaker/budget/HITL decide escalation, not the
hook) → run the drained-board predicate from `agent-teams.md` → **green board
allows**, **undrained board blocks** with the undrained tasks as the `reason`.

**Auto-conversion.** A `Stop` hook declared in the skill/agent **frontmatter is
auto-converted to `SubagentStop`** when the loop runs as a subagent — so the gate
**travels with the skill** and fires whether the loop is the top-level lead or a
spawned subagent. (Mirrors `fix-until-green`'s stop-hook auto-conversion note.)

## Wiring

- **Per-skill (inherited by subagents):** declare the hooks in frontmatter; the
  `Stop` → `SubagentStop` auto-conversion carries the gate to spawned teammates.
- **Orchestrated registration:** register alongside the existing **qa-gate hook** —
  the two coexist; `TaskCompleted` gates a single task, the qa-gate gates the build.
- **Profile `minimal | standard | strict`:** advisory-vs-blocking handling of a
  gate FAIL. `strict` blocks the stop on any FAIL; `minimal`/`standard` may surface
  a FAIL advisorily while continuing to route other tasks — but a **drained** board
  always allows the stop regardless of profile.

## The experimental-flag precondition check

A short guard at the top of **every** handler:

```bash
[ "${CLAUDE_CODE_EXPERIMENTAL_AGENT_TEAMS:-}" = "1" ] || exit 0
```

If `CLAUDE_CODE_EXPERIMENTAL_AGENT_TEAMS != 1`, the hooks are **inert** — the loop
**refuses to start** and **degrades** to the orchestrator's subagent / sequential
path (no shared task list, no Teammate hooks; the proof and discipline survive,
driven by hand / the wave gate instead).
