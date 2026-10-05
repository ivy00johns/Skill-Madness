# Sequential Execution

This document governs execution when multi-agent spawning (Agent Teams, Subagents via Task/Agent tool, Dynamic Workflows) is unavailable, or when single-agent sequential execution is requested.

## Principles

1. **One approval, then autonomous.** The owner approves the plan once, at `SCOPE_APPROVED`. That approval authorizes the whole `READY_QUEUE`: every contract, role slice, verify-and-fix retry and review in the approved plan. From there, run to the end without asking — no per-slice, per-role or per-file confirmations, and the owner stepping away is never a reason to stop. Make in-scope design decisions yourself and record them in `coordination/DECISIONS.md`.
   The run is bounded by structure, not by the owner watching: the approved slice list plus the 3-attempt circuit breaker per gate cap the total work. What it must **not** do is relaunch itself as a background or scheduled loop (cron, a shell `while` restarting the host CLI, an overnight headless run); that needs `loop-controller`'s `run_guarded.py` with hard call/cost/time limits.
2. **Same contracts, same file ownership, same gates.** The absence of parallel subagents changes the *scheduling*, not the engineering standards. File ownership boundaries, contract freezing, wave gates, and the mandatory QA gate apply unchanged.
3. **No self-certification.** The agent implementing a slice cannot independently certify that slice. Slices are checked with deterministic verifiers; final quality evaluation requires contract-auditor static pass and independent QE/reviewer verification. If no independent reviewer is available, state clearly: `UNVERIFIED — independent review required`.

## State Graph

Sequential execution follows a strict machine-checkable state transition graph:

```text
[DISCOVER]
    │
    ▼
[SCOPE_APPROVED]
    │
    ▼
[CONTRACTS_FROZEN]
    │
    ▼
[READY_QUEUE] ◄────────────────────────────────────────┐
    │                                                  │
    ▼                                                  │
[BUILD_SLICE]                                          │
    │                                                  │
    ▼                                                  │
[WAVE_VERIFY] ──fail (≤3 attempts)──► [BUILD_SLICE]    │
    │                                                  │
    ▼ pass                                             │
[REVIEW_PACKET]                                        │
    │                                                  │
    ▼                                                  │
[INDEPENDENT_QE] ──findings──► [READY_QUEUE] ─────────┘
    │
    ▼ pass
[ACCEPTED]

ANY STATE ──unhandled error / missing tool / crashed checker──► [BLOCKED]
ANY STATE ──circuit breaker (>3 failures) / budget ceiling──► [STOPPED]
ANY STATE ──human intervention requested / pause──► [PAUSED]
```

### State Definitions

- **`DISCOVER`**: Read project context, requirements, existing architecture, and capabilities. Formulate the execution plan.
- **`SCOPE_APPROVED`**: Present everything the owner needs to approve in **one** message: the plan, the roles, the ordered slices, the assumptions you are making about environment, data and constraints, and which actions would still need their go-ahead (see *When to stop and ask*). Proceed on one explicit approval. This is the only routine checkpoint.
- **`CONTRACTS_FROZEN`**: Author integration contracts (API, shared types, data contracts). Authoring must complete and contracts must be frozen before implementation begins.
- **`READY_QUEUE`**: An ordered list of bounded implementation slices, organized by dependency order.
- **`BUILD_SLICE`**: Execute one role packet for one bounded slice. Apply the matching role skill instructions. Strictly honor that role's file ownership.
- **`WAVE_VERIFY`**: Run deterministic checks (install, typecheck/lint, unit tests, source guards like `check_design_tokens.py` and `check_class_extraction.py`).
  - If checks fail: retry within circuit breaker limit (max 3 attempts).
  - If limit exceeded: transition to `STOPPED`.
- **`REVIEW_PACKET`**: Prepare a structured evidence packet (diff, test output, contract compliance summary, files touched).
- **`INDEPENDENT_QE`**: Static audit via `contract-auditor` followed by runtime verification via `qe-agent` (or independent human/external reviewer).
  - If self-evaluating in the same session: mark `UNVERIFIED — self-check only`.
  - If findings returned: append rework tasks to `READY_QUEUE`.
- **`ACCEPTED`**: All slices complete, all contracts fulfilled, full test suite and QA gate passing.
- **`BLOCKED`**: Missing prerequisite, broken verifier, syntax error in tooling, or absent authorization. Applies to the slice, not the build: park it and its dependents, record why, and keep draining every independent slice. Ask the owner about all blocked items together at the end.
- **`STOPPED`**: A slice hit the circuit breaker (3 consecutive failures on the same gate): park it and its dependents and continue with independent slices. The whole build stops only when nothing runnable remains or an external budget/iteration limit is hit.
- **`PAUSED`**: The owner asked to pause, or a decision falls outside the approved plan (see *When to stop and ask*). In-scope design choices are not a reason to pause.

## Role Packets

When acting as a specific role in sequential mode, work from a discrete **Role Packet**:

1. **Role identity & boundaries**: Explicitly adopt the role's instructions (e.g. `skills/roles/backend-agent/SKILL.md`). Touch ONLY files in that role's `owns` declaration. A packet from this orchestrator is the role's **dispatched** mode, not its solo mode: the approved plan already answers solo mode's scope, acceptance and path questions, and shared-file or cross-role needs are settled by the orchestrator's ownership map — not by asking the owner.
2. **Assigned slice**: Exactly what to build in this step, referencing the frozen contract.
3. **Checkpoints, not hand-offs to the owner**: Between roles, save state to disk (handoff packet, `READY_QUEUE` status, decisions log) and check git status, so a long run survives a context compaction or a host restart and can resume from the files. Do not ask the owner to reset context or relay between roles.
4. **Handoff evidence**: When finishing a role slice, produce the slice handoff packet (files modified, verifier commands executed, output logs) before transitioning to the next role or verifier.

## Finding role skills on this host

Load each role **by name** (`backend-agent`, `frontend-agent`, `qe-agent`,
`contract-author`, `contract-auditor`, …) the way this host loads skills: an
explicit skill activation, its installed rule/agent file, or the role's
`SKILL.md` read from the same installed skills location this orchestrator was
loaded from. Paths like `skills/roles/backend-agent/SKILL.md` are repo-checkout
paths; never assume them or `~/.claude`. Resolve each role's `references/` and
`scripts/` from that role's own installed root (exported roots carry an
`.ats-runtime.json` listing their bundled resources). If a role cannot be found, that slice is
`BLOCKED` — do not improvise the role from memory.

## Skills that are not installed on this host

Some skills the phases name are Claude-Code-only and are not exported to other
hosts. The step they serve still applies; perform it with what *is* available
and record the substitution in `coordination/MISSION_SKILLS.md` ("not installed
on this host — performed inline" or "BLOCKED: <missing tool>"). A substitute
never reports a PASS it could not observe.

| Named skill | Do this instead |
|---|---|
| `fix-until-green` | The `WAVE_VERIFY → BUILD_SLICE` retry edge: fix one real blocker per attempt, re-run the same checks, stop at 3 attempts. Never edit tests or checks to pass. |
| `render-sanity` | Its four checks by hand in a real browser (the `playwright` skill or the host's browser tool): smell scan for `undefined` / `?` / `—` / stuck `Loading…`, click through every list item, signed-out route matrix, signed-in route matrix. No browser available → DoD item 11 is `BLOCKED`, not PASS. |
| `contract-conformance-loop`, `coverage-loop`, `perf-loop`, `migration-loop` | In-session iterations inside this build: the same proof command and iteration cap, no extra approval (the approved plan covers it). |
| `orchestrator-task-loop`, Agent Teams, the Workflow tool | Not applicable — `READY_QUEUE` is the task list and you drain it one role packet at a time. |
| `project-profiler`, `dependency-coordinator`, `context-manager`, `deployment-checklist` | Do the step inline: a stack scan; one owner for each shared manifest; a written handoff file between roles; a pre-deploy checklist. The assumption audit in Phase 3 means: list the plan's unstated assumptions about environment, data and constraints and include them in the single `SCOPE_APPROVED` message — not a separate confirmation. |
| Any other named skill missing here | Note it in `MISSION_SKILLS.md` with the reason, tell the user once, and continue with the closest exported skill or inline step. |

## When to stop and ask

After `SCOPE_APPROVED`, stop for the owner only for:

- an irreversible or external action the approved plan did not name: a deploy, production data, a force-push, deleting work, spending money beyond the approved budget, or using new credentials;
- a contract change that alters the approved scope (internal contract fixes follow the contract protocol without asking);
- the end of the run, with one batched list of everything parked as `BLOCKED` or `STOPPED`.

Everything else — choosing libraries within the stack, splitting a slice, retrying a failed gate, rework from QE findings — proceeds without asking.

## Rules of Sequential Mode

- **Never implement code as the orchestrator**: Even in sequential mode, switch explicitly into the role persona (`backend-agent`, `frontend-agent`, etc.) with its specific ownership and constraints.
- **Run the approved queue to the end; never self-relaunch**: Keep working through the approved queue in the current session whether or not the owner is watching. Do not turn the build into a background, scheduled or self-restarting loop unless `run_guarded.py` (or an equivalent external wrapper) enforces max iterations, timeout, process locks and cancellation.
- **Independent verification is required, but never a reason to wait**: A single session cannot grant itself final QE certification. If the host can start a fresh non-interactive session of its own CLI from the shell, use that session as the independent `contract-auditor`/`qe-agent` reviewer within the approved budget. Otherwise finish the build, write `qa-report.json` with an explicit same-context caveat, and report `UNVERIFIED — independent review required` in the end-state report.
