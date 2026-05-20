---
name: zoom-out
version: 1.1.0
description: "Step back from the current code and give a higher-level perspective: which modules are involved, how do they connect, what is this change touching that isn't obvious? Reads the project's CONTEXT.md / domain glossary when available. Explicit invocation only — does not auto-fire. Use when feeling stuck in detail, when a change feels bigger than expected, or before making a structural decision."
disable-model-invocation: true
requires_agent_teams: false
requires_claude_code: true
min_plan: starter
owns:
  directories: []
  patterns: []
  shared_read: ["*"]
allowed-tools: ["Read", "Grep", "Glob"]
composes_with: ["maintain-context"]
spawned_by: []
---

# zoom-out

Go up a layer. Map the modules involved in this change. Read the domain glossary (`CONTEXT.md`, configured via `setup-project-skills`) if one exists.

Output a numbered list of modules, one line per module describing its role, with arrows (`→`) showing connections between them. Example shape:

```text
1. AuthService — validates JWTs → 2. UserRepo
2. UserRepo — loads/persists users → 3. SessionStore
3. SessionStore — refresh-token cache → AuthService
```

Do not propose changes. The user asked for orientation, not a fix — if they wanted a fix they'd have invoked a different skill.
