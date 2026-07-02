# CLAUDE.md

> **Lost? Start at [`START-HERE.md`](START-HERE.md)** — status at a glance + which doc is canonical vs frozen vs archived.
> **Also read `AGENTS.md`** — it contains shared instructions for all AI agents working in this repo.

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What This Is

A multi-agent orchestration toolkit for Claude Code — 69 OSS-publishable skills in `skills/`. Skills are symlinked to `~/.claude/skills/` for global availability.

The toolkit targets Claude Code as the primary host but the SKILL.md format is platform-agnostic — Claude.ai, Copilot CLI, Codex, and Gemini CLI all consume it. Skills should describe work in terms of capabilities ("read the file", "run the command") rather than Claude-Code-specific tool names where reasonable, so the same skill body works across hosts.

## Install / Sync

Use the `/sync-skills` command to create symlinks from `~/.claude/skills/` back to this repo. This keeps skills always in sync — edits in either location are reflected immediately.

```bash
# Via slash command (recommended)
/sync-skills

# Manual: create category symlinks + flattened discovery symlinks
# See skills/workflows/sync-skills/SKILL.md for details
```

## Skill Anatomy

Every skill follows this structure:

```text
skill-name/
├── SKILL.md              # YAML frontmatter + markdown instructions (≤5,000 words; warn at 500 lines)
└── references/           # On-demand reference files (unlimited size)
```

All SKILL.md files use the frontmatter convention defined in `skills/meta/skill-writer/references/frontmatter-spec.md`. This spec aligns with Anthropic's official Agent Skills standard. Required fields: `name` (kebab-case; `claude-*`/`anthropic-*` prefixes discouraged but allowed as documented exceptions), `version` (semver, top-level), `description` (trigger text, ≤1024 chars, no `<` or `>` in field values). Optional Anthropic fields: `compatibility`, `license`, `allowed-tools` (hyphen canonical; `allowed_tools` accepted as alias), `metadata`. Agent roles also declare `owns`, `composes_with`, `spawned_by`.

## Skill Categories

- **`skills/orchestrator/`** (1) — Entry point. 14-phase build playbook, runtime detection, contract-first coordination. References: phase-guide, team-sizing, circuit-breaker, handoff-protocol.
- **`skills/roles/`** (10) — Implementation agents (backend, frontend, infrastructure, qe, security, performance, observability, docs, db-migration, code-review). Each has a SKILL.md + reference files with validation checklists.
- **`skills/contracts/`** (2) — contract-author (generates contracts from templates) and contract-auditor (verifies implementations match). Templates: OpenAPI, AsyncAPI, Pydantic, TypeScript, JSON Schema.
- **`skills/meta/`** (7) — skill-writer, skill-review, skill-update, skill-explorer, skill-catalog, madness (the front-door router: reads intent, picks the right starting skill — orchestrator / plan-builder / a loop / a role or workflow / skill-explorer — and launches it, confirming before anything expensive; the active counterpart to skill-explorer), model-adaptation (the model-migration reference: what to prune, what now triggers a `reasoning_extraction` refusal, and the long-run/effort scaffolding to add when the underlying Claude model changes — Fable 5 / Mythos 5 today; enforced via skill-review, loop-controller, and orchestrator).
- **`skills/git/`** (4) — Git workflow conventions: git-commit, git-pr, git-pr-feedback, git-post-merge-cleanup.
- **`skills/workflows/`** (32) — plan-builder, plan-intake, living-plan, context-manager, deployment-checklist, dependency-coordinator, project-profiler, wiki-research, interactive-doc, settings-consolidator, sync-skills, ui-brief, claude-design-brief, mermaid-charts, nano-banana, playwright, render-sanity, repo-deep-dive, llm-wiki, railway-deploy, architecture-rescue, caveman, diagnose-loop, grill-me, maintain-context, zoom-out, setup-project-skills, work-item-brief, website-walkthrough-video, design-token-guard, use-freellmapi, class-extraction-guard.
- **`skills/loops/`** (13) — Autonomous-loop skills. loop-controller (the foundation harness: the 5-part loop contract, primitive selection — `/goal` vs `/loop` vs Stop-hook vs bash Ralph vs dynamic workflows, the mandatory guardrail stack, and the fresh-context evaluator), fix-until-green (drive tests+lint+typecheck to passing without cheating the gate), orchestrator-task-loop (the outer loop over the Agent Teams shared task list — drain the board until every task is completed + passing its TaskCompleted gate, feeding idle workers via TeammateIdle; experimental, behind CLAUDE_CODE_EXPERIMENTAL_AGENT_TEAMS=1), contract-conformance-loop (build-until-spec: implement until every authored-contract criterion holds, graded by a fresh-context evaluator subagent the builder can't self-grade — the loop form of the contract-author/contract-auditor pair), babysit (scheduled review-and-revise: keep a PR rebased and green by auto-addressing review comments via `/loop 5m /babysit`, with HITL on anything irreversible — the scheduled loop around git-pr-feedback), coverage-loop (grow the test suite to a coverage target without gaming the metric), perf-loop (profile → optimize → re-benchmark until a metric is under its budget under repeatable conditions, with no functional regression), self-healing-loop (watch logs/CI → root-cause → fix → verify → PR on a poll cadence, with HITL before any prod-touching fix), migration-loop (transform an enumerated target set one file per iteration until all are migrated, the suite is green, and no legacy pattern remains), nightly-docs-and-changelog (a `/schedule` routine that keeps an already-shipped repo's docs + changelog from rotting, surviving laptop-off), dependency-health-loop (scheduled audit + one-gated-bump-per-pass + green gate, HITL on major bumps), codebase-exploration-loop (fan-out read-only mappers until a written architecture summary answers every seed question — the loop form of repo onboarding), and repo-cleanup-loop (weekly evidence-gated branch/PR/worktree hygiene that recovers valuable work before deleting). Every concrete loop is a configuration of loop-controller.

## Key Design Decisions

- **File ownership is exclusive** — no two agent roles can own the same file. The orchestrator resolves conflicts before spawning. The canonical ownership map lives in the orchestrator skill.
- **QE gates the build** — the qe-agent outputs `qa-report.json` per `skills/roles/qe-agent/references/qa-report-schema.json`. Build blocks on CRITICAL blockers or contract_conformance/security scores < 3.
- **Two-runtime degradation** — Agent Teams → subagents → sequential. Only the orchestrator needs this logic; role skills work standalone.
- **Progressive disclosure** — frontmatter (~100 tokens) always loaded, SKILL.md body loaded on trigger, references loaded on demand.
- **Descriptions are "pushy"** — skill descriptions intentionally over-enumerate trigger contexts to combat under-triggering.

## Editing Skills

When modifying a skill:

- Keep SKILL.md body ≤5,000 words (Anthropic guideline); soft warning past 500 lines. Move detail to `references/`. Heavy skills may exceed when the length is load-bearing.
- Description field is the primary trigger mechanism — include action verbs, specific contexts, and keyword variations
- `owns.directories` must not overlap with other agent roles
- Maintain the frontmatter convention (see `skills/meta/skill-writer/references/frontmatter-spec.md`)
- If using symlinks (default), edits are automatically reflected in both locations
