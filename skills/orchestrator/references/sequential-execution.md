# Sequential Attended Execution

This document governs execution when multi-agent spawning (Agent Teams, Subagents via Task/Agent tool, Dynamic Workflows) is unavailable, or when single-agent attended execution is requested.

## Principles

1. **Attended, bounded, and staged.** Sequential execution progresses step-by-step with the user present. It does **not** fall back to an unbounded, unattended background loop.
2. **Same contracts, same file ownership, same gates.** The absence of parallel subagents changes the *scheduling*, not the engineering standards. File ownership boundaries, contract freezing, wave gates, and the mandatory QA gate apply unchanged.
3. **No self-certification.** The agent implementing a slice cannot independently certify that slice. Slices are checked with deterministic verifiers; final quality evaluation requires contract-auditor static pass and independent QE/reviewer verification. If no independent reviewer is available, state clearly: `UNVERIFIED — independent review required`.

## State Graph

Attended sequential execution follows a strict machine-checkable state transition graph:

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
- **`SCOPE_APPROVED`**: Present the plan, roles needed, and bounded slices to the user. Proceed only upon explicit approval.
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
- **`BLOCKED`**: Missing prerequisite, broken verifier, syntax error in tooling, or absent authorization. Requires human remedy.
- **`STOPPED`**: Reached circuit breaker (3 consecutive failures on the same gate) or hit external budget/iteration limit.
- **`PAUSED`**: User asked to pause, or human input needed on design decision.

## Role Packets

When acting as a specific role in sequential mode, work from a discrete **Role Packet**:

1. **Role identity & boundaries**: Explicitly adopt the role's instructions (e.g. `skills/roles/backend-agent/SKILL.md`). Touch ONLY files in that role's `owns` declaration.
2. **Assigned slice**: Exactly what to build in this step, referencing the frozen contract.
3. **Context resets & boundaries**: For long sessions, recommend a context reset or clean checkpoint between roles. Save modified state to disk and verify git status.
4. **Handoff evidence**: When finishing a role slice, produce the slice handoff packet (files modified, verifier commands executed, output logs) before transitioning to the next role or verifier.

## Rules of Attended Sequential Mode

- **Never implement code as the orchestrator**: Even in sequential mode, switch explicitly into the role persona (`backend-agent`, `frontend-agent`, etc.) with its specific ownership and constraints.
- **Refuse unbounded unattended fallback**: If the user is unavailable or requests "run unattended until done" in sequential mode, refuse unless an external process wrapper enforcing max iterations, timeout, process locks, and cancellation is active.
- **Independent verification is required**: A single session cannot grant itself final QE certification. When no external reviewer is present, generate `qa-report.json` with an explicit caveat noting same-context execution.
