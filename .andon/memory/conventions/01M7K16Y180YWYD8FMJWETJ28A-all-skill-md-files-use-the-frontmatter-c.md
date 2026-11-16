---
id: 01M7K16Y180YWYD8FMJWETJ28A
kind: conventions
status: accepted
title: All SKILL.md files use the frontmatter convention defined in skills/meta/skill-writer/references/frontmatter-spec.md
tags: [skill-anatomy]
paths: [SKILL.md, skills/meta/skill-writer/references/frontmatter-spec.md]
source: import CLAUDE.md:36 f381cae2400a91fb
confidence: 0.7
supersedes: none
created: 2026-11-16
---

All SKILL.md files use the frontmatter convention defined in `skills/meta/skill-writer/references/frontmatter-spec.md`. This spec aligns with Anthropic's official Agent Skills standard. Required fields: `name` (kebab-case; `claude-*`/`anthropic-*` prefixes discouraged but allowed as documented exceptions), `version` (semver, top-level), `description` (trigger text, ≤1024 chars, no `<` or `>` in field values). Optional Anthropic fields: `compatibility`, `license`, `allowed-tools` (hyphen canonical; `allowed_tools` accepted as alias), `metadata`. Agent roles also declare `owns`, `composes_with`, `spawned_by`.
