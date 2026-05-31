---
name: context-manager
version: 1.2.0
description: |
  Manage context window usage, compaction strategy, and session handoffs for long-running multi-agent builds. Writes and validates structured handoff files so continuation agents can pick up cleanly. Trigger on: "compact this", "handoff this conversation", "we're running out of context", "save state", "transfer to a new session", "context is too full", "summarize this session for the next one", "continue in a fresh session".
requires_agent_teams: false
requires_claude_code: true
min_plan: starter
owns:
  directories: [".claude/handoffs/"]
  patterns: []
  shared_read: ["*"]
allowed-tools: ["Read", "Write", "Edit", "Bash", "Glob"]
composes_with: ["orchestrator"]
spawned_by: []
---

# Context Manager

Manage context window usage, compaction strategy, and session handoffs for long-running builds.

This is a **user-invocable** helper. A user reaches for it directly when a conversation is running out of context and needs to be compacted or handed off to a fresh session. It is **not** spawned by the orchestrator during a build.

> **During an orchestrated build, handoff validation is governed by `orchestrator/references/handoff-protocol.md`** (the protocol the orchestrator actually runs). This skill is for user-driven compaction/handoff outside that loop.

## Role

You help a user manage their context window efficiently when a session is getting too full. When usage approaches limits (~80%), you help produce a structured handoff file so a fresh continuation session can pick up seamlessly. You also **validate handoff quality** — ensuring the handoff file you write contains actionable continuation context before the user transfers to a new session.

## Your Ownership

- **You own (exclusive):** `.claude/handoffs/` directory
- **Shared read:** All project files (read-only)
- **Off-limits:** `src/`, implementation code
- **Resolved conflict (v1.1):** `.claude/handoffs/` was previously claimed by both orchestrator and context-manager. Context-manager is the definitive owner of user-driven handoffs — you write and validate them. (Build-loop handoffs during an orchestrated build are governed separately by `orchestrator/references/handoff-protocol.md`.)

## Inputs

- **Context signal** — the current session is approaching ~80% context usage
- **Handoff draft (optional)** — the user may provide a draft handoff file for you to validate and improve
- **Compaction request (optional)** — the user asks for help compacting the session before resorting to a full handoff

## When to Act

- Session context usage approaches 80%
- A long-running task needs to continue across multiple sessions
- The user wants to transfer the conversation to a fresh session

## Handoff Protocol

When the session needs to hand off, write a structured YAML file to `.claude/handoffs/`. See `references/compaction-guide.md` for the full specification.

### Handoff File Structure

```yaml
handoff_version: "1.0.0"
agent_role: [role name]
timestamp: [ISO 8601]
session_id: [string]
context_usage_pct: [number]

task_state:
  assigned_task: [what was assigned]
  completion_pct: [honest estimate]
  completed_subtasks: [list]
  remaining_subtasks: [list]
  blockers: [list]

decisions_made:
  - decision: [what was decided]
    rationale: [why]
    affects_files: [which files]

files_modified: [list of relative paths]
files_created: [list of relative paths]
contracts_consumed: [which contract files were read]

continuation_context: |
  [Free-text: what the continuation agent needs to know.
   Key variable names, error states, partial work, next action.
   ≤500 words.]

suggested_first_action: [exact next step]
```

### Continuation in a Fresh Session

After the handoff file is written, the user starts a fresh session and points it at the latest file in `.claude/handoffs/`. The continuation session reads `files_modified` and `files_created` to understand current state, then begins with `suggested_first_action`.

> **Inside an orchestrated build, the read/validate/spawn behavior on a handoff is governed by `orchestrator/references/handoff-protocol.md` — not this skill.** This skill covers writing and quality-checking the user-driven handoff file; it does not duplicate the orchestrator's build-loop validation.

## Context Efficiency Tips

For a session approaching its context limit:

- Avoid re-reading files already in context
- Summarize long outputs before storing in context
- Focus on the current task, not previously completed work
- Use `references/compaction-guide.md` for compaction strategies

## Coordination

- Handoff files are append-only — never modify a previous handoff
- Each handoff gets a unique filename: `{role-or-session}-{timestamp}.yaml`
- **Quality gate (your job):** Before declaring a handoff ready, validate that `continuation_context` is specific and actionable (not vague), `suggested_first_action` is an exact next step, and `completion_pct` is an honest estimate. Reject and rewrite vague handoffs.
