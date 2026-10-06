---
name: zoom-out
version: 1.1.1
description: |
  Guide a decision from a higher level: step back from the code to show which modules a change touches, how they connect, and what it affects that is not obvious. Reads the project's CONTEXT.md or domain glossary when available. Use when asked to "step back", "zoom out", "give me the big picture", "which modules does this change touch?", "what does this change affect?", "what am I missing here", before a structural decision when you want a map first, or when a change feels bigger than expected.
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
