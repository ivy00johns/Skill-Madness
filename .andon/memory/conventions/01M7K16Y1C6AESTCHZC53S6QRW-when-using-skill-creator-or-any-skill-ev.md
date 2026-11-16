---
id: 01M7K16Y1C6AESTCHZC53S6QRW
kind: conventions
status: accepted
title: When using /skill-creator (or any skill evaluation workflow) to audit, test, or iterate on skills, always place…
tags: [skill-creator-workspaces]
paths: []
source: import AGENTS.md:7 7554ac9cf129388f
confidence: 0.7
supersedes: none
created: 2026-11-16
---

When using `/skill-creator` (or any skill evaluation workflow) to audit, test, or iterate on skills, **always** place workspace directories in `.workspaces/` at the repo root — not as siblings to the skill directory. This overrides skill-creator's default behavior of creating `<skill-name>-workspace/` next to the skill.
