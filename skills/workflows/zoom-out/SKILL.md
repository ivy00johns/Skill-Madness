---
name: zoom-out
version: 1.1.3
description: >-
  Step back from the code to show which modules a change touches, how they
  connect, and what it affects that isn't obvious, using CONTEXT.md when
  present. Use before a structural decision or when a change feels bigger than
  expected. Trigger on "zoom out", "step back", "give me the big picture", "what
  else does this touch?".
disable-model-invocation: true
requires_agent_teams: false
requires_claude_code: false
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
