# Wave Gate

Between every wave of parallel agents, the orchestrator runs the project's install + typecheck + test loop from a clean state. This is non-negotiable.

## Why

Parallel agents writing independent files — different package manifests, different test setups, different framework conventions — produce latent integration bugs that grep-based per-agent validation cannot catch. Examples seen in the wild: missing workspace dep declarations (the import resolves locally but breaks the moment a clean install runs), framework decorators that don't escape encapsulation (every test 500s), deprecated runtime invocations that pass linting but error at execution, host-side port collisions in compose files, omitted compile config files (the typechecker prints help instead of typechecking).

## The gate

After every wave of parallel agents reports done, BEFORE declaring the wave complete or dispatching the next wave, run the project's three integrated checks. Use whatever the project's stack provides — the gate is **install + typecheck + test from a clean state**, not a specific tool:

| Stack signal | Install | Typecheck/lint | Test |
|---|---|---|---|
| `pnpm-workspace.yaml` | `pnpm install` | `pnpm -r run typecheck` | `pnpm -r run test` |
| `package.json` (npm/yarn) | `npm ci` / `yarn install` | `npm run typecheck` (per package) | `npm test` |
| `pyproject.toml` + Poetry | `poetry install` | `poetry run mypy .` or `poetry run ruff check .` | `poetry run pytest` |
| `pyproject.toml` + uv | `uv sync` | `uv run mypy .` | `uv run pytest` |
| `Cargo.toml` workspace | `cargo fetch` | `cargo check --workspace` | `cargo test --workspace` |
| `go.mod` | `go mod download` | `go vet ./...` | `go test ./...` |
| `Gemfile` | `bundle install` | `bundle exec rubocop` | `bundle exec rspec` |
| `pom.xml` / `build.gradle` | `mvn -B verify` (covers all three) | — | — |

For polyglot monorepos, run the gate for every language present (Node + Python both, etc.).

## On failure

If any step fails, the wave is **not complete**. Route each specific failure back to the responsible agent (via SendMessage if the runtime supports it, otherwise spawn a fix subagent with the agent role) with the exact error output. Repeat until all three steps pass.

Agent self-validation can be bypassed by grep tricks, missing files, or unran tests. The integrated gate cannot — if install fails, the workspace is broken, full stop. Catching it here is 30 minutes of fix work; catching it when the human runs the project is a credibility hit and a damaged handoff.

**The orchestrator does not declare "build complete" without a clean integrated gate.** This applies whether or not a QE agent is in the loop — the wave gate is the orchestrator's own check, not delegated.

## Clean state means clean (avoiding false greens)

The gate is only as honest as the state it runs in. A "green" that came from a dirty environment or a misread exit code is worse than a red — it ships a broken build with a passing label. Four traps that have produced false greens in real builds:

- **Kill watch/dev servers and clear the build cache before the production build + e2e steps.** A `next dev` (or any watcher) writing the build directory while `next build` reads it yields phantom errors that have nothing to do with the code — e.g. `Cannot find module for page: /api/...` from a half-written `.next`. The build "fails" on a ghost, or worse, a stale cache lets a broken build "pass." Stop the dev server, `rm -rf` the cache, then build.
- **Don't trust a wrapped exit code.** `cmd; echo done` reports the echo's status (0), not `cmd`'s — a failed build reads as green. Use `cmd && echo OK || echo "FAIL=$?"`, or read the tail for the framework's own success line (`✓ Compiled successfully`). Never infer pass from "the command returned."
- **"test" means the full suite — unit + integration + e2e — not the files you think the wave touched.** Cross-file breakage (a drifted contract, a stale snapshot, a fixture that no longer matches) is the entire reason the gate exists; a scoped subset is blind to exactly the integration bugs the wave introduced. Gating typecheck + build but skipping the full test run is how a stale test slips to the human.
- **Run e2e against the production build, not a live dev/watch server.** A loaded `dev --turbo`/watch server compiles per-route on first hit, so an e2e suite pointed at it spends its wall-clock waiting on compiles and times out (minutes→hours); the same suite against a fresh `next start` / built artifact finishes in seconds. It's also correctness — dev and prod can render and route differently.

## Wire source-convention gates at bootstrap, not at the end

`design-token-guard` and any lint / strict-type / convention gate is cheapest when it exists **before the first line of UI is written**. Scaffold its config + pre-commit hook + CI step in the bootstrap wave. Then the first frontend-agent commit is already checked and the gate can hard-fail from day one — instead of being retrofitted onto a fleet of finished files, where it inherits a backlog, can only run report-only ("ratchet") to avoid blocking the whole build, and leaves a manual multi-file burndown for later. Retrofitting works, but the burndown it creates is pure avoidable cost.
