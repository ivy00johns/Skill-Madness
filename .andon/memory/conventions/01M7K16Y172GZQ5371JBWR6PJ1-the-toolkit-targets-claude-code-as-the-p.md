---
id: 01M7K16Y172GZQ5371JBWR6PJ1
kind: conventions
status: accepted
title: The toolkit targets Claude Code as the primary host but the SKILL.md format is platform-agnostic — Claude.ai,…
tags: [what-this-is]
paths: [SKILL.md]
source: import CLAUDE.md:12 ce81964226f32509
confidence: 0.7
supersedes: none
created: 2026-11-16
---

The toolkit targets Claude Code as the primary host but the SKILL.md format is platform-agnostic — Claude.ai, Copilot CLI, Codex, and Gemini CLI all consume it. Skills should describe work in terms of capabilities ("read the file", "run the command") rather than Claude-Code-specific tool names where reasonable, so the same skill body works across hosts.
