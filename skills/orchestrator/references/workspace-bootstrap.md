# Workspace Bootstrap Deliverables

When the plan establishes any project with more than a single source file — a multi-package workspace, a service plus a frontend, a single-app repo with build/test machinery — the orchestrator's bootstrap step MUST produce a **root README.md** as part of the skeleton. The README is the single artifact a human reaches for when they sit down to set up the project — every other doc (CLAUDE.md, plan documents, ADRs) is for downstream agents or operations, not the human running `git clone && setup`.

## Required README sections

Omit only if genuinely irrelevant to this project:

1. **What the project is** — one paragraph, no marketing
2. **Stack** — bullet list of language, framework, database, queue, deploy target
3. **Prerequisites** — the things the human needs installed BEFORE the first build command (language runtime version, package manager, Docker, OS-specific deps, etc.)
4. **Setup** — exact commands in order: install dependencies, bring up infrastructure dependencies if any (docker compose, dev DB), copy env template, run migrations, run seed, run tests
5. **Start** — the dev commands the human runs to launch each service
6. **Tests** — how to run unit, integration, e2e
7. **Deploy** — the actual deploy command for the target deployment platform
8. **Project structure** — short tree showing top-level layout with one-line descriptions
9. **Known issues** — any latent bugs, unresolved type errors, deferred work the human will hit when running the project (be honest — shipping with hidden setup pain damages trust)
10. **Documentation map** — table linking to the deeper docs (CLAUDE.md, plans, ADRs, qa reports)

Use the project's actual commands — `pnpm install`, `cargo build`, `poetry install`, `bundle install`, `make setup` — never placeholders. The README is dead if its commands don't run.

A project ships without a root README → the human's first impression is "where do I even start?" That is a build failure, regardless of how clean the contracts are.

## One-command dev (mandatory for multi-service projects)

If the project has more than one long-running dev process — typically an API plus a web frontend, possibly plus a worker, gateway, or background job — the workspace root MUST expose a single `dev` script that launches all of them in one terminal with prefixed/colored output. The human should never need to open four terminals to run a dev stack.

| Stack | Aggregator |
|---|---|
| Node monorepo (pnpm/npm/yarn) | root devDep `concurrently` or `npm-run-all`; `"dev": "concurrently --names api,web --prefix-colors cyan,magenta 'pnpm dev:api' 'pnpm dev:web'"` |
| Node + Turborepo | `turbo dev` — runs the `dev` task across packages |
| Python (multiple services) | `honcho` / `foreman` against a `Procfile`; or a `make dev` target |
| Go | `make dev` invoking each service via `&` plus a `wait` trap; or `air` per service under `tmuxinator` |
| Polyglot | `mprocs`, `overmind`, or a `Procfile`-based supervisor |

Also: do not include scripts that point at services that don't exist yet. `dev:worker` referencing an `apps/worker/` that ships as a placeholder Dockerfile is dead-on-arrival — strip it from the root or leave a clear `# TODO` comment so the human doesn't try to run it and get confused.

## Collision-free ports (mandatory for any project that binds a port)

The single most common reason a freshly-generated project fails its *first* `dev`
run is a port collision — the project hardcodes a framework default (classically
`3000`), and a leftover process or a second project already holds it, so the
service dies with `EADDRINUSE` instead of stepping aside. A build that crashes on
first run is not done, however clean the contracts are.

Two non-negotiables, both specified in `references/port-conventions.md` (the house
port map, per-service bands, and a copy-paste `free_port` helper):

1. **Preflight, then bind.** The root `dev` script resolves every port *before*
   launching — prefers the canonical port (API `8000`, web `5173`; **never**
   `3000`), and if it's busy takes the next free port in that service's band,
   exports it, and prints the resolved URL. Services read the port from env
   (`API_PORT`, `WEB_PORT`), never a literal.
2. **No hardcoded ports in source.** A literal `localhost:3000` / `localhost:8000`
   in app or test code is a finding — the frontend must point at the *resolved*
   API port, or the auto-step breaks the cross-service link the moment a port
   shifts.

This is what lets two projects (or a project plus a stale process) be up at once
without manual coordination: project A binds 8000, project B's preflight sees it
busy and takes 8001. See `references/port-conventions.md` for the bands and the
`scripts/dev-ports.sh` snippet to drop into the workspace.
