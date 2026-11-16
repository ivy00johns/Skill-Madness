---
title: Install / Sync
tags: [install-sync]
paths: [skills/workflows/sync-skills/SKILL.md]
updated: 2026-11-16
---

Imported from `CLAUDE.md:14` by Andon (import CLAUDE.md:14 494188b9a2fb7a9a); the original stays there.

Use the `/sync-skills` command to create symlinks from `~/.claude/skills/` back to this repo. This keeps skills always in sync — edits in either location are reflected immediately.

```bash
# Via slash command (recommended)
/sync-skills

# Manual: create category symlinks + flattened discovery symlinks
# See skills/workflows/sync-skills/SKILL.md for details
```
