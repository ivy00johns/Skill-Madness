---
id: 01M7K16Y18J4MGAQJYG7GRMNNY
kind: decisions
status: accepted
title: File ownership is exclusive
tags: [key-design-decisions]
paths: []
source: import CLAUDE.md:50 81e4f3391d20c556
confidence: 0.7
supersedes: none
created: 2026-11-16
---

**File ownership is exclusive** — no two agent roles can own the same file. The orchestrator resolves conflicts before spawning. The canonical ownership map lives in the orchestrator skill.
