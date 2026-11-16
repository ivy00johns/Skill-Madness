---
id: 01M7K16Y19BXSC7V84EECJ6SMQ
kind: decisions
status: accepted
title: Descriptions are short and specific
tags: [key-design-decisions]
paths: []
source: import CLAUDE.md:54 aefbebb4f96ae99d
confidence: 0.7
supersedes: none
created: 2026-11-16
---

**Descriptions are short and specific** — what the skill does, "Use when…", and a few phrases users really say; target ≤400 chars. Claude Code's skill listing has a shared character budget (1% of the context window: about 8,000 chars on 200k), and over it descriptions are cut to the bare skill name, so the longest-winded catalog loses its long tail. Under-triggering is fixed with precise trigger phrases and routing (`madness`, `skill-explorer`), checked with `skill-triage`, not with length (DR-1, 2026-10-25; replaced "pushy").
