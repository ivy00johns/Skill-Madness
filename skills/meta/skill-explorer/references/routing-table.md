# Routing Table

Common user requests → recommended skill. Use this as a fallback when SKILL.md's "rules of thumb" section doesn't cover the case. Two indexes: the phrase tables below key on what the user *says*; the decision index ("By unresolved decision") keys on which decision is actually *open* — use it when a shared term matches several plausible skills.

## By task type

### Building things

| User says... | Use | Notes |
|---|---|---|
| "build X with an agent team" / "swarm build" | `orchestrator` | Multi-agent build is its actual job |
| "build a feature in this codebase" | `feature-dev:feature-dev` | Single-developer feature flow |
| "build a [website/app/page] from this research/PRD" | `plan-builder` then `orchestrator` | Plan first, build second |
| "build the API / backend" (within an orchestrated build) | `backend-agent` | Spawned by orchestrator |
| "build the UI / frontend" (within an orchestrated build) | `frontend-agent` | Spawned by orchestrator |
| "build the deployment / Docker / CI" | `infrastructure-agent` | |
| "set up the database / migrations" | `db-migration-agent` | |

### Designing / writing UIs

| User says... | Use | Notes |
|---|---|---|
| "the UI sucks, redesign it" / "write me a design brief" | `ui-brief` | Produces the brief; hand off to a builder after |
| "build a polished frontend page/component" | `frontend-design:frontend-design` | High-design-quality output |
| "design / plan a UI but make it look like [reference]" | `ui-brief` | Captures the reference and constraints |
| "comprehensive UI/UX review of the running app" | `ux-review` | Opens browser, takes screenshots, fixes |
| "general UI/UX guidance, palettes, fonts, layout" | `ui-ux-pro-max` | Library of styles + component examples |

### Planning / spec work

| User says... | Use | Notes |
|---|---|---|
| "make a plan for this build" | `plan-builder` | Especially with research / PRD inputs |
| "make a plan for this feature task" | `claude-mem:make-plan` | Phased implementation plan |
| "write the API/data contract" | `contract-author` | Before agents implement |
| "audit implementations against the contract" | `contract-auditor` | After agents implement |
| "set up dependency pinning before parallel agents run" | `dependency-coordinator` | Monorepo cross-package locks |

### Reviewing / auditing

| User says... | Use | Notes |
|---|---|---|
| "review this PR / code" | `code-review-agent` or `code-review:code-review` | |
| "security review / audit auth" | `security-agent` or `security-review` | |
| "address PR feedback / copilot comments" | `git-pr-feedback` | |
| "audit all my skills" / "skill ecosystem health" | `skill-review --scope=all` | Broad scan |
| "deep review one skill" | `skill-review --scope=<skill-name>` | Single skill |
| "apply the recommendations from a skill review" | `skill-update` | Plan + apply in one workflow |

### Skill ecosystem itself

| User says... | Use |
|---|---|
| "what skills do I have" / "I forgot the name" / "which skill for X" | `skill-explorer` (this skill) |
| "create a new skill" | `skill-writer` |
| "audit / scan all skills" | `skill-review --scope=all` |
| "deep review one skill" | `skill-review --scope=<skill-name>` |
| "sync skills to global / link them" | `sync-skills` |
| "consolidate Claude Code permissions / settings" | `settings-consolidator` |

### Git / GitHub

| User says... | Use |
|---|---|
| "commit these changes" | `git-commit` or `commit-commands:commit` |
| "open a PR" | `git-pr` or `commit-commands:commit-push-pr` |
| "address PR comments" | `git-pr-feedback` |
| "clean up branches" / "clean up worktrees" / "post-merge cleanup" | `git-post-merge-cleanup` |
| "use a worktree for isolated work" | `superpowers:using-git-worktrees` |
| "delete merged [gone] branches" | `commit-commands:clean_gone` |

### Quality / testing / performance

| User says... | Use |
|---|---|
| "verify the build / qa gate" | `qe-agent` |
| "run E2E tests / browser tests / screenshots" | `playwright` |
| "load test / performance benchmark" | `performance-agent` |
| "set up logging / metrics / tracing" | `observability-agent` |
| "TDD / test-first development" | `superpowers:test-driven-development` |
| "debug a bug systematically" | `superpowers:systematic-debugging` |

### Documentation / knowledge

| User says... | Use |
|---|---|
| "write API docs / README / changelog" | `docs-agent` |
| "set up an LLM wiki / knowledge base" | `llm-wiki` |
| "deep dive on this open-source repo" | `repo-deep-dive` |
| "research a topic and file findings" | `claude-obsidian:autoresearch` |
| "save this to my Obsidian wiki" | `claude-obsidian:save` |
| "ingest this source into the wiki" | `claude-obsidian:wiki-ingest` |
| "lint / health check the wiki" | `claude-obsidian:wiki-lint` |
| "query my wiki for X" | `claude-obsidian:wiki-query` |

### Infra / deployment

| User says... | Use |
|---|---|
| "deploy to Railway / put this online" | `railway-deploy` |
| "pre-deploy checklist / staging readiness" | `deployment-checklist` |
| "set up Docker / docker-compose / CI" | `infrastructure-agent` |

### Visuals / content

| User says... | Use |
|---|---|
| "diagram this / mermaid chart" | `mermaid-charts` |
| "generate an image / product photo / hero banner" | `nano-banana` |
| "open a canvas / add to canvas" | `claude-obsidian:canvas` |

### Memory / search

| User says... | Use |
|---|---|
| "did we already solve this / how did we do X last time" | `claude-mem:mem-search` |
| "explore this codebase structurally" | `claude-mem:smart-explore` |
| "build a knowledge brain from past observations" | `claude-mem:knowledge-agent` |
| "timeline report of this project's history" | `claude-mem:timeline-report` |

### Autonomous loops

All loop skills are `disable-model-invocation: true` — name them, then the user dispatches by slash command (or the orchestrator dispatches the build loops). `loop-controller` is the front door when no concrete loop fits.

| User says... | Use |
|---|---|
| "make the tests/lint/typecheck pass", "run until green", red CI | `fix-until-green` |
| "keep my PR green / rebased / address review comments while I'm away" | `babysit` |
| "build until the contract/spec criteria hold" | `contract-conformance-loop` |
| "raise coverage to N%" | `coverage-loop` |
| "get this benchmark under budget / keep optimizing until X" | `perf-loop` |
| "watch the logs/CI and fix what breaks" | `self-healing-loop` |
| "migrate/transform every file matching X" | `migration-loop` |
| "keep the docs and changelog fresh overnight" | `nightly-docs-and-changelog` |
| "keep dependencies current / audited" | `dependency-health-loop` |
| "explore/map this codebase until my questions are answered" | `codebase-exploration-loop` |
| "clean up stale branches/PRs/worktrees weekly" | `repo-cleanup-loop` |
| "drain the Agent-Teams task board until every task passes" | `orchestrator-task-loop` |
| "loop until…" (nothing above fits), "author a new loop", "loop safely" | `loop-controller` |

### Settings / harness

| User says... | Use |
|---|---|
| "stop prompting me for permissions / set up overnight mode" | `settings-consolidator` |
| "configure hooks / settings.json" | `update-config` |
| "fewer permission prompts from common tools" | `fewer-permission-prompts` |
| "rebind a keyboard shortcut" | `keybindings-help` |
| "schedule a recurring task" | `loop` (interval) or `schedule` (cron) |

## By unresolved decision

Descriptions are deliberately pushy, so collision-prone terms ("deploy", "review") match several skills on topic. Topic overlap is not the test — each skill resolves a *different decision*, and usually only one of those decisions is open in the request. Route to the skill that resolves the open decision; if no decision is open, no skill is warranted — say so instead of force-fitting the closest miss.

Note: plugin-namespaced and globally-installed refs in this index (`code-review:code-review`, `ux-review`, `security-review`) are environment-relative — they resolve in this toolkit author's setup, not necessarily in yours. Treat them as placeholders for your host's equivalent.

| Unresolved decision | Resolved by |
|---|---|
| Which skill should even fire for this request? | `madness` (routes and launches) / `skill-explorer` (names and stops) |
| How should this build be split across parallel agents? | `orchestrator` |
| What is the plan, before anything gets built? | `plan-builder` |
| What condition must provably hold before iteration stops? | `loop-controller` (picks the concrete loop) |
| Is this diff correct and safe to merge? | `code-review-agent` / `code-review:code-review` |
| Can this code be exploited? | `security-agent` / `security-review` |
| Does the running app look and behave right to a user? | `ux-review` |
| Are the skills themselves healthy? | `skill-review` |
| Which reviewer comments still need addressing? | `git-pr-feedback` |
| Is this build safe to ship right now? | `deployment-checklist` |
| How does this project get onto its hosting platform? | `railway-deploy` |
| How should the deploy machinery itself (Docker, CI) be built? | `infrastructure-agent` |
| Who may perform a consequential mutation (push, deploy, delete), and does it need a human first? | the confirm gate in `madness` / the HITL guardrails in `loop-controller` |
| Is the needed skill missing, or present but failing to trigger? | `references/troubleshooting.md` (symptom taxonomy) → `sync-skills` if missing, `skill-update` if mis-triggering |

## Disambiguation: when two skills look similar

- **`orchestrator` vs `feature-dev:feature-dev`**: orchestrator coordinates *multiple* parallel agents on a multi-component build. feature-dev is for a single developer working through one feature. If the user is building one thing, use feature-dev.
- **`ui-brief` vs `frontend-design:frontend-design`**: ui-brief writes the *brief* (positioning, design language, page treatment). frontend-design *executes* the build. Brief comes first if the design isn't decided.
- **`plan-builder` vs `claude-mem:make-plan`**: plan-builder consumes research docs / PRDs / Compass artifacts to produce a build plan for orchestrator. make-plan is a lighter phased plan for direct execution by `claude-mem:do`.
- **`skill-review` modes**: `--scope=all` is the bulk ecosystem audit; `--scope=<skill-name>` is the deep dive on a single skill. One skill, two modes — pick by argument.
- **`code-review-agent` (repo skill) vs `code-review:code-review` (plugin)**: repo's code-review-agent is the role-agent version used in orchestrated builds. The plugin code-review is for reviewing a PR end-to-end.
- **`git-commit` vs `commit-commands:commit`**: git-commit is the repo's documented convention guide. commit-commands:commit is a plugin slash-command. Either works; prefer the convention guide when it matters that the message follows repo style.

## When no skill fits

If a request genuinely doesn't match any skill:

1. Say so explicitly — "no skill covers this directly".
2. Name the closest miss and explain the gap.
3. Suggest `skill-writer` if the user might want to author a new skill for the pattern.

Don't force a bad recommendation just to give an answer.
