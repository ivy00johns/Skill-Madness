# Agent Spawning

The template, the permissions, and a worked example for spawning an implementation agent.

## Role label ≠ subagent type (read this first)

`backend-agent`, `frontend-agent`, `docs-agent`, `qe-agent`, etc. are **role labels** — they name a *kind* of work and a body of instructions (the matching skill under `skills/roles/`). They are **NOT** valid `subagent_type` values for the Agent/Task tool.

When you dispatch, the tool's `subagent_type` must be a type the host actually registers. Passing a role label like `docs-agent` fails with `Agent type 'docs-agent' not found`. So:

1. **Default to `general-purpose`.** It is always available and is the correct target for every role. The role is established by the *prompt*, not the type.
2. **Carry the role instructions in the prompt.** The subagent type does NOT auto-load the role skill. Invoke the role skill inside the agent (or paste its checklist) as part of the prompt body. "Be the docs agent" must mean "apply the docs-agent skill," delivered as text.
3. **Specialist types are optional and host-dependent.** If you've confirmed the host registers a closely-matching type, you MAY use it — but `general-purpose` + the role skill is always correct and never errors.

| Role label | Safe `subagent_type` (always works) | Specialist *if the host registers it* |
|---|---|---|
| backend-agent | `general-purpose` | `backend-architect`, `fullstack-developer` |
| frontend-agent | `general-purpose` | `frontend-developer` |
| infrastructure-agent | `general-purpose` | `deployment-engineer` |
| db-migration-agent | `general-purpose` | `backend-architect` |
| qe-agent | `general-purpose` | `test-engineer` |
| security-agent | `general-purpose` | `api-security-audit` |
| observability-agent | `general-purpose` | `error-detective` |
| performance-agent | `general-purpose` | `performance-profiler` |
| docs-agent | `general-purpose` | `api-documenter` |
| code-review-agent | `general-purpose` | `code-reviewer` |

When in doubt, use `general-purpose`. Never pass a `*-agent` label as `subagent_type`.

## Agent Prompt Template

Each agent receives ONLY what they need:

```text
You are the [ROLE] agent for this build.

## Your Ownership
- You own: [exact directories/files]
- Do NOT touch: [other agents' territories]
- Read-only: contracts/

## What You're Building
[Relevant plan excerpt — NOT the full plan]

## Contracts
### Shared Types (v1)
[Paste or reference]
### Contract You Produce (v1)
[The contract this agent implements]
### Contract You Consume (v1)
[The contract this agent depends on]

## Domain Rules
[Relevant business rules from contracts/README.md that this agent must enforce]

## Implementation Notes
[Per-agent guidance from contracts/README.md — libraries, patterns, framework specifics]

## Before Reporting Done
[Specific validation commands]
```

**Agent spawn permissions:** Spawn agents in a permission mode that allows file writes without per-tool prompts (in Claude Code, this is `mode: "auto"` on the Agent tool). Agents that cannot write files burn their entire context asking for permission instead of building.

## AFK / HITL Classification (required)

Every agent dispatch MUST declare whether it can finish unattended:

- **AFK (away-from-keyboard)** — the agent has everything it needs to complete its work without further input. No mid-flight clarifying questions, no permission stalls, no external secrets it can't read.
- **HITL (human-in-the-loop)** — the agent will pause at known checkpoints for a human. Document the checkpoints up front so the user knows when to expect a return.

Spawning without an explicit classification is forbidden (see Anti-Patterns in the main skill).

## Example: a filled-in backend-agent prompt

Here's what the template looks like in practice for a habit-tracker build. Notice how short the plan excerpt is — only the API/data sections, not the marketing copy or design system:

```text
You are the backend agent for the habit-tracker build.

## Your Ownership
- You own: src/api/, src/services/, src/models/, src/middleware/, .env.example
- Do NOT touch: src/components/, src/pages/, tests/ (qe agent owns)
- Read-only: contracts/

## What You're Building
Habit CRUD + JWT auth + streak calculation. Plan §3.2 (Habits API) and §3.4 (Auth).
Soft-delete only. Streaks reset at 04:00 in the user's timezone.

## Contracts
### Shared Types (v1)
See contracts/types.ts — Habit, User, AuthToken, ErrorEnvelope.
### Contract You Produce (v1)
contracts/api.openapi.yaml — implement exactly. URLs include trailing slashes.
### Contract You Consume (v1)
contracts/data-layer.yaml — Postgres via the Drizzle client in src/db/.

## Domain Rules
- Streak = consecutive days with ≥1 completion, computed in user TZ, reset at 04:00 local
- Soft-delete sets `deleted_at`; queries filter it out by default
- All timestamps stored UTC, returned ISO8601

## Implementation Notes
Express + Zod for validation. JWT in Authorization header. CORS origin from
ALLOWED_ORIGIN env var (verified against the Cloud Run config in Phase 0).

## Before Reporting Done
- `pnpm typecheck && pnpm test` clean
- `curl -i localhost:8000/api/habits/` returns 401 without auth, 200 with
- CORS preflight returns ALLOWED_ORIGIN, not `*`
```

The prompt is ~40 lines. The full plan was 12 pages. That ratio is the point — every line not relevant to the backend agent is noise that crowds out the work.

> **Ports come from the project's convention, never a hardcoded default.** This example uses `8000` (the house backend port; frontend `5173`, FreeLLMAPI proxy `3001`) — do **not** paste a literal `localhost:3000` into agent prompts. `3000` is a frontend framework default, and worked examples that carry it leak into project code as the API port. Read the project's `.env.example` / dev scripts / `profile.yaml` for the real ports and pass *those* to the agent — ideally the env-var form (`curl -i localhost:$API_PORT/...`) so a port that auto-stepped at startup still validates. See `references/port-conventions.md` for the full map, the per-service bands, and the preflight rule that lets two projects run at once without colliding.
