# Gate-command detection by stack

The gate is **three exit codes** — `test`, `lint`, `typecheck` — composed into
one pass/fail. This reference resolves those three commands for a project and
composes them. Always prefer what the project *declares* (and what CI runs) over
a raw tool default; the table is the fallback when nothing is declared.

## Resolution order (per command)

1. `.claude/profile.yaml` keys `test` / `lint` / `typecheck`, if present — verbatim.
2. The project's own named script (so you run exactly what CI runs):
   `package.json` `scripts`, `Makefile` targets, `pyproject.toml`/`tox.ini`,
   `Cargo.toml` aliases, `composer.json` scripts, `Taskfile.yml`, `Justfile`.
3. The stack default below — only if nothing is declared.

Record the three resolved commands in `fix_plan.md` and run the **identical**
trio every iteration.

## Per-stack defaults

| Stack | test | lint | typecheck |
|---|---|---|---|
| **Node / TS** | `npm test` (or `pnpm test` / `yarn test`) | `npm run lint` → else `npx eslint .` | `npx tsc --noEmit` (TS only) |
| **Node / JS** | `npm test` | `npx eslint .` | — (none; passes vacuously) |
| **Python** | `pytest` (or `python -m pytest`) | `ruff check .` → else `flake8` | `mypy .` → else `pyright` (if configured) |
| **Rust** | `cargo test` | `cargo clippy -- -D warnings` | `cargo check` |
| **Go** | `go test ./...` | `golangci-lint run` → else `go vet ./...` | `go build ./...` |
| **Ruby** | `bundle exec rspec` → else `rake test` | `bundle exec rubocop` | `srb tc` (Sorbet, if present) |
| **Java / Kotlin** | `./gradlew test` → else `mvn test` | `./gradlew check` / `mvn checkstyle:check` | compile step (`./gradlew compileJava` / `mvn -q compile`) |
| **PHP** | `composer test` → else `vendor/bin/phpunit` | `vendor/bin/php-cs-fixer fix --dry-run` | `vendor/bin/phpstan analyse` (if present) |
| **.NET** | `dotnet test` | `dotnet format --verify-no-changes` | `dotnet build` |

Notes:
- A step that genuinely doesn't exist for the stack (no typecheck in plain JS)
  **passes vacuously** — but confirm absence, don't assume it. A missing `tsc`
  in a TS project is a red gate, not a vacuous pass.
- Monorepos: detect per-package or use the workspace runner the repo already
  uses (`turbo run test lint typecheck`, `nx run-many`, `pnpm -r`). Prefer the
  one command CI invokes.
- If lint/typecheck are already folded into the test script (common in CI-tuned
  `make check` / `npm run ci`), that single command *is* the gate — don't
  double-run.

## Composing three exit codes

Run all three, capture each exit code, and report a single pass/fail plus which
leg failed (so failures route by concern). The loop is **green only when all
three are 0 in the same run**.

```bash
# Resolve TEST_CMD / LINT_CMD / TYPECHECK_CMD per the order above first.
gate() {
  local rc=0
  for leg in "TEST:$TEST_CMD" "LINT:$LINT_CMD" "TYPECHECK:$TYPECHECK_CMD"; do
    local name="${leg%%:*}" cmd="${leg#*:}"
    [[ -z "$cmd" ]] && { echo "[$name] (none — vacuous pass)"; continue; }
    echo "[$name] $cmd"
    if ! eval "$cmd"; then
      echo "[$name] FAILED"
      rc=1
    fi
  done
  return $rc
}
gate   # exit 0 == green; non-zero == still red
```

Keep the per-leg output — Step 2 of the skill reads it to pick the single
root-cause failure to fix next, and Step 4 re-runs the whole `gate` from scratch.
