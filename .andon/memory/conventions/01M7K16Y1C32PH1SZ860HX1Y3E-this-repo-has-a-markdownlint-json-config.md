---
id: 01M7K16Y1C32PH1SZ860HX1Y3E
kind: conventions
status: accepted
title: This repo has a .markdownlint.json config at the root
tags: [markdownlint]
paths: [.markdownlint.json, SKILL.md]
source: import AGENTS.md:24 7fe08868d58e6993
confidence: 0.7
supersedes: none
created: 2026-11-16
---

This repo has a `.markdownlint.json` config at the root. When creating or editing any Markdown
file — especially SKILL.md files via skill-creator — **always fix markdownlint violations before
finishing**. Run a lint pass on every Markdown file you touch and resolve all warnings. The repo
disables MD013 (line length) and MD060 globally; all other rules are enforced.
