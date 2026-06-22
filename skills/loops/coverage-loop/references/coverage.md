# coverage-loop reference: commands, reports, and anti-gaming

The body has the contract, the proof, and the caps. This file has the mechanical
detail: how to run coverage per stack, how to read the report (and per-target
thresholds), and the full set of anti-gaming rules with how to detect each.

## Contents
- [Resolving the target](#resolving-the-target)
- [Per-stack coverage commands](#per-stack-coverage-commands)
- [Reading the report](#reading-the-report)
- [Picking the lowest-covered meaningful unit](#picking-the-unit)
- [Anti-gaming rules (each is a finding)](#anti-gaming-rules)

---

## Resolving the target

Precedence, highest first. **Never hard-code 80 or 100** — read the project's.

1. **`.claude/profile.yaml`** — preferred. Look for a coverage block, e.g.:
   ```yaml
   coverage:
     target: 85          # total %, the global floor
     per_target:         # optional per-path / per-package floors
       src/api: 90
       src/payments: 100
     command: "npm run coverage"   # optional explicit command override
     report: "coverage/coverage-summary.json"  # optional artifact override
   ```
2. **The project's own coverage config** — when the profile is silent:
   - Python: `.coveragerc` / `pyproject.toml [tool.coverage]`, or
     `--cov-fail-under=N` in `pytest`/`tox`/CI.
   - Node: `jest.config` `coverageThreshold.global`, `vitest` `coverage.thresholds`,
     `.nycrc` / `c8` `--check-coverage --lines N`.
   - Rust: `tarpaulin.toml` `fail-under`.
   - Go: a CI `go tool cover` gate (often a script asserting a floor).
   - Ruby: `SimpleCov.minimum_coverage N` in `spec_helper`/`test_helper`.
   - Java: JaCoCo `<limit>` rules in the maven/gradle plugin config.
3. If neither declares a target, **stop and ask** — a coverage loop with no
   target has no proof and cannot converge. Do not invent one.

Capture **both** the total target and every per-target floor: the proof requires
*all* of them at-or-above, not just the global number.

## Per-stack coverage commands

Prefer the project's own named script (`npm run coverage`, `make coverage`) so you
run what CI runs; these are the stack defaults only when nothing is declared. Each
must emit a machine-readable report artifact, not just a TTY summary.

| Stack | Command (default) | Report artifact |
|---|---|---|
| Node (Jest) | `npx jest --coverage --coverageReporters=json-summary text` | `coverage/coverage-summary.json` |
| Node (Vitest) | `npx vitest run --coverage` | `coverage/coverage-summary.json` / `lcov.info` |
| Node (c8/nyc) | `npx c8 --reporter=json-summary --reporter=text <test cmd>` | `coverage/coverage-summary.json` |
| Python (coverage.py) | `coverage run -m pytest && coverage xml && coverage report` | `coverage.xml` + report stdout |
| Python (pytest-cov) | `pytest --cov --cov-report=xml --cov-report=term-missing` | `coverage.xml` |
| Go | `go test ./... -coverprofile=coverage.out && go tool cover -func=coverage.out` | `coverage.out` + `-func` total line |
| Rust | `cargo tarpaulin --out Xml` | `cobertura.xml` |
| Ruby | `COVERAGE=1 bundle exec rspec` (SimpleCov) | `coverage/.last_run.json` / `coverage/.resultset.json` |
| Java (JaCoCo) | `mvn test jacoco:report` / `gradle test jacocoTestReport` | `target/site/jacoco/jacoco.xml` |
| PHP (PHPUnit) | `phpunit --coverage-clover=coverage.xml` | `coverage.xml` (Clover) |

Always request a **structured** reporter (json-summary, xml, clover, the `-func`
total) — the proof parses the artifact, and a human-only text table is fragile to
read mechanically.

## Reading the report

Parse the artifact for the **total** and (when per-target floors exist) the
per-path numbers:

- **coverage-summary.json** (Node) — `.total.lines.pct` / `.total.statements.pct`
  / `.total.branches.pct`; per-file under each path key. Use the metric the
  project's threshold targets (lines vs statements vs branches).
- **coverage.xml / cobertura** (Python/Rust/PHP) — the root `<coverage>`
  `line-rate` / `branch-rate` (a 0–1 fraction → ×100); `<package>` / `<class>`
  for per-target.
- **JaCoCo `jacoco.xml`** — `<counter type="LINE" missed="" covered="">`; total
  pct = `covered / (covered + missed)`; per-`<package>` for per-target.
- **Go `-func` output** — the final `total:` line's percentage; per-function rows
  above it for the lowest-covered unit.
- **SimpleCov `.last_run.json`** — `.result.line` (and `.result.branch`).

Decide pass per metric the threshold names: if the project gates **branch**
coverage, line coverage at-or-above target is *not* the proof. Match the metric.

## Picking the unit

The lowest-covered **meaningful** unit, in rough priority:

1. A per-target path below its floor (these block the proof directly).
2. A function/module with real untested behavior and many uncovered branches —
   high leverage, real bugs hide here.
3. Uncovered error/edge paths in otherwise-covered units.

Skip and do **not** count as "covered": generated code, vendored files, trivial
getters/`__repr__`/boilerplate, and anything the project legitimately excludes in
committed config (don't add new excludes — see below). One unit per iteration;
log `unit → tests added → before% → after%` in `coverage_plan.md`.

## Anti-gaming rules

Each of these moves the *number* without covering *behavior*. Each is a
**finding**, not a shortcut — this mirrors [`fix-until-green`]'s never-cheat rule
and `loop-controller` guardrail 6 ("never let the loop weaken its own gate").
When the percentage jumps, **read the diff that produced it**: a jump from new
assertions is real; a jump from new excludes or a lowered threshold is the cheat.

- **Assertion-free "tests."** Calling a function purely to execute its lines with
  no `assert` / `expect` / verification of the result. It raises coverage and
  proves nothing. Every added test must assert on observable behavior (return
  value, raised error, emitted side effect, branch outcome). Detect: an added
  test body with no assertion API call, or a test that can't fail.
- **Excluding files / ignore pragmas to shrink the denominator.** Adding to
  `.coveragerc`/`pyproject` `omit`, `# pragma: no cover`, `/* istanbul ignore
  next */`, `c8 ignore`, `jest` `coveragePathIgnorePatterns`, JaCoCo `<excludes>`,
  or `nocov` blocks so uncovered code stops counting. Covering code means *testing*
  it, not hiding it. Detect: a coverage jump whose diff is changes to coverage
  config or new ignore comments, not new tests. (Pre-existing, legitimately-
  committed excludes are fine — do not *add* new ones to hit the number.)
- **Lowering the configured threshold.** Editing `coverageThreshold`,
  `--cov-fail-under`, `fail-under`, `minimum_coverage`, or the profile's
  `coverage.target` downward so the existing number "passes." The target is the
  proof; moving it is moving the goalpost. Detect: a diff to the threshold config.
- **Deleting or skipping hard-to-cover tests** (or the units themselves) to drop
  them from the report. Same prohibition as fix-until-green: a genuinely-wrong or
  genuinely-dead unit is a *human* decision — surface it, don't unilaterally
  delete it to make coverage look complete.
- **Testing against mocks that bypass the real code path.** A test that mocks the
  unit under test (rather than its dependencies) executes the mock, not the code —
  coverage of the real path is illusory. Assert against the real unit; mock only
  its boundaries.

When the remaining gap is genuinely untestable (environment-bound glue, dead code
that should be deleted by a human, a path requiring an irreversible resource),
that is a **no-progress / HITL escalation** per the body — report it with what was
tried; do not paper over it with any of the above.

[`fix-until-green`]: ../../fix-until-green/SKILL.md
