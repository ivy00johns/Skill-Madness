# File Ownership Map

This table is the **canonical** ownership map for the whole Skill-Madness toolkit — it enumerates **every** skill that declares exclusive ownership of a directory or pattern, not just the build-time role agents. When in doubt, this overrides any individual skill's frontmatter.

**Precedence rules:**

1. **Directory ownership takes precedence over pattern ownership.** If a pattern (e.g. `docs/adr/**`) would land inside a directory owned by another skill, the more specific directory owner wins.
2. **Subdirectory carve-outs are explicit.** A deeper-nested directory can be carved out of a broader owner (e.g. `performance-agent` owns `tests/performance/` carved out of qe-agent's `tests/`; `setup-project-skills` owns `docs/agents/` and `maintain-context` owns `docs/adr/`, both carved out of docs-agent's `docs/`).
3. **No path has two owners.** Every owned directory/pattern below resolves to exactly one skill. Skills not listed here own nothing — their write capability (if any) comes from `allowed-tools`, not ownership.

## Build-time role agents

These are spawned by the orchestrator during a multi-agent build. File ownership between them is exclusive and resolved before any agent is spawned.

| Agent Role | Owns (Exclusive) | Shared Read | Never Touches |
|------------|-----------------|-------------|---------------|
| orchestrator | `.gitignore` | `contracts/`, `.claude/handoffs/`, `*` | `src/` |
| backend-agent | `src/api/`, `src/services/`, `src/models/`, `src/middleware/`, `src/utils/` | `contracts/`, `shared/`, `src/types/` | `src/components/`, `src/pages/`, `.env.example` |
| frontend-agent | `src/components/`, `src/pages/`, `src/hooks/`, `src/styles/`, `public/`, `*.tsx`, `*.jsx`, `*.vue`, `*.svelte`, `*.css` | `contracts/`, `shared/`, `src/types/`, `assets/` | `src/api/`, `src/services/` |
| infrastructure-agent | `.github/workflows/`, `nginx/`, `k8s/`, `terraform/`, `scripts/deploy/`, `Dockerfile*`, `docker-compose*`, `Makefile`, `justfile`, **`.env.example`** | All (read-only) | `src/` |
| qe-agent | `tests/` *(excl. `tests/performance/`)*, `e2e/`, `__tests__/`, `*.test.*`, `*.spec.*`, `qa-report.md`, `qa-report.json` | All (read-only) | `src/` (test files in `src/` owned by the directory's agent) |
| performance-agent | `tests/performance/`, `load-tests/` | All (read-only) | `src/` |
| security-agent | `.github/security/`, `SECURITY.md` | All (read-only) | `src/` |
| db-migration-agent | `migrations/`, `seeds/`, `prisma/`, `alembic/`, `knex/migrations/` | `src/models/` | `src/` (non-migration) |
| observability-agent | `src/telemetry/`, `src/logging/`, `monitoring/`, `alerts/` | `src/` | other agents' `src/` |
| docs-agent | `docs/` *(excl. `docs/agents/` and `docs/adr/`)*, `README.md`, `CHANGELOG.md`, `CONTRIBUTING.md` | All (read-only) | `src/`, config files, test files, `docs/agents/`, `docs/adr/` |
| code-review-agent | *(nothing — review only)* | All (read-only) | everything (read-only role) |
| contract-author | `contracts/`, `schemas/`, `openapi.yaml`, `asyncapi.yaml` | `*` | `src/` |
| contract-auditor | *(nothing — audit only)* | `contracts/`, `src/`, `backend/`, `frontend/`, `docs/` | everything (read-only role) |

## Workflow & meta skills that own paths

These skills run outside (or alongside) a build but still claim exclusive ownership of specific paths. They are part of the canonical map so their paths never collide with a role agent's.

| Skill | Owns (Exclusive) | Notes |
|-------|-----------------|-------|
| setup-project-skills | `docs/agents/` | **Carve-out** from docs-agent's `docs/`. Writes the per-repo config (`domain-docs.md`, `contract-format.md`, `work-item-tracker.md`). |
| maintain-context | `docs/adr/`, `CONTEXT.md` | **Carve-out** from docs-agent's `docs/`. `docs/adr/` is a directory (precedence over patterns); `CONTEXT.md` is the domain glossary. |
| context-manager | `.claude/handoffs/` | Session-handoff files. Orchestrator shares-read this directory. |
| project-profiler | `CLAUDE.md`, `.claude/profile.yaml` | Generated project profile + machine-readable profile. |
| llm-wiki | `index.md`, `wiki/log.md`, `wiki/overview.md` | Root knowledge-base index + `wiki/` log/overview pages (canonical layout: root `index.md` entry, `wiki/` articles). |
| settings-consolidator | `settings.local.json` | Claude Code permission files (merged into the global one). |
| work-item-brief | `briefs/**/*.md` | Generated work-item brief documents. |
| railway-deploy | `railway.toml` | Railway deployment config. (No directory ownership; pattern-only.) |
| sync-skills | `skills/workflows/sync-skills/` | Owns only its own subtree — the toolkit's `skills/` tree is otherwise un-owned. |

**Skills that own nothing:** `skill-update`, `skill-writer`, `skill-review`, `skill-explorer`, `deployment-checklist`, `claude-design-brief`, `architecture-rescue`, `ui-brief`, `diagnose-loop`, `wiki-research`, `plan-builder`, `playwright`, `render-sanity`, `living-plan`, `zoom-out`, `repo-deep-dive`, `dependency-coordinator`, `mermaid-charts`, `plan-intake`, `caveman`, `grill-me`, `nano-banana`, and the git skills (`git-commit`, `git-pr`, `git-pr-feedback`, `git-post-merge-cleanup`). Their `owns` blocks are empty by design; any write capability comes from `allowed-tools`. In particular `skill-update` owns nothing — it edits skills via `allowed-tools`, exactly like its sibling meta skills, so it does not swallow the `skills/` tree (which would otherwise collide with `sync-skills`).

## The three explicit carve-outs under `docs/`

`docs-agent` owns `docs/` broadly, but two subtrees are owned by other skills and **must not** be written by docs-agent:

| Path | Exclusive owner | Carved out of |
|------|-----------------|---------------|
| `docs/agents/` | `setup-project-skills` | `docs/` (docs-agent) |
| `docs/adr/` | `maintain-context` | `docs/` (docs-agent) |
| `docs/` (everything else) | `docs-agent` | — |

Without these carve-outs, docs-agent's `docs/` directory ownership would silently swallow both subtrees (directory ownership beats pattern ownership), so each carve-out is declared as a directory in the owning skill's frontmatter and called out here.

## The `.env.example` resolution

`.env.example` is owned by **infrastructure-agent only**. backend-agent does **not** own or create it: backend defines the variable names and safe local-dev defaults its services need and hands them to infrastructure-agent (via the lead), who writes the committed `.env.example`. The gitignored `.env` (real local values) remains backend-agent's concern. See `team-sizing.md` for the shared-infrastructure file assignment table.

## Conflict resolution

**Rule**: If two roles would touch the same file, resolve the conflict by assigning that file to exactly one role before spawning. Unresolvable conflicts → human decision.

## Contract-First Architecture

Contracts prevent the ~42% of multi-agent failures caused by specification problems. Before any agent is spawned:

1. **Shared types first** — single source of truth for all entities
2. **API contract** — exact URLs, methods, request/response JSON shapes, status codes
3. **Data layer contract** — function signatures, storage semantics, cascade behavior
4. **Cross-cutting concerns** — each assigned to exactly one agent

Use the `contract-author` skill and templates in `contracts/contract-author/references/`.
