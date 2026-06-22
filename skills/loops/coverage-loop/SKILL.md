---
name: coverage-loop
version: 1.0.0
description: >-
  Grow a test suite until a coverage target is met: run coverage, find the
  lowest-covered meaningful unit, add REAL behavior-checking tests for it, then
  re-measure the whole report — looping until total (and per-target) coverage is
  at or above the configured target AND the full suite is green. Reads the target
  from .claude/profile.yaml (no hard-coded 80 or 100). Forbids gaming the number
  with assertion-free tests or excluding files from the coverage config — both are
  findings. Use when coverage is below target, when a build wave needs more tests,
  or as the QE coverage inner loop under an orchestrated build. Trigger on:
  "raise coverage", "hit the coverage target", "add tests until coverage", "get
  to N percent coverage", "coverage is too low", "loop until coverage passes",
  "grow the test suite", "cover the untested code", "/coverage-loop". A
  configuration of loop-controller.
requires_claude_code: true
min_plan: starter
disable-model-invocation: true
allowed-tools: ["Read", "Write", "Edit", "Bash", "Grep", "Glob"]
composes_with: ["loop-controller", "fix-until-green", "qe-agent", "orchestrator"]
spawned_by: ["orchestrator"]
---

# coverage-loop

> **A configuration of [`loop-controller`].** That skill supplies the loop
> machinery — primitive selection, the full guardrail stack, state
> externalization. This skill supplies the two things specific to "grow the suite
> to a coverage number": a **mechanical proof** (the coverage report meets the
> configured target with a green suite) and the **anti-gaming discipline** that
> keeps the number honest. Read `loop-controller` for the guardrails; they're
> inherited, not repeated here.
>
> **Why `disable-model-invocation`:** this loop writes test files and commits on
> its own and spends tokens re-running the full coverage suite each round, until
> the target is hit. You want to *type* `/coverage-loop` (or have the
> orchestrator dispatch it) — not have Claude start an autonomous test-writing
> loop because some file looked under-tested.

## The 5-part contract

| Part | This loop |
|---|---|
| **trigger** | coverage below the configured target, a build wave needing more tests, or an explicit `/coverage-loop` (optionally scoped to a path or per-target) |
| **action** | ONE iteration: run coverage → find the **lowest-covered meaningful unit** → add **real, behavior-checking** tests for it → re-run coverage over the **whole** report (and the full suite) |
| **proof** | the coverage report shows total **AND** every configured per-target threshold **>=** the target **AND** the full suite exits 0 — default-FAIL: assume **below target** until the freshly-generated report proves otherwise, read from the named artifact (`coverage.xml` / `lcov.info` / the `N% covered` summary line), not from memory of a prior run |
| **memory** | `coverage_plan.md` (the live TODO of under-covered units + a per-round `unit → tests added → new %` log), plus a git checkpoint per coverage-raising round |
| **stop** | report meets target **with the suite green** **OR** iteration cap **OR** no-progress for 3 rounds **OR** budget cap |

## The proof: a fresh coverage report at-or-above target, default-FAIL

"Done" is **not** "I added some tests" and **not** "the file I was looking at is
covered now." It is a **freshly-generated coverage report whose total (and every
configured per-target) percentage is at or above the target, with the full suite
green in the same run**. Assume **below target** until that report exists —
that's the default-FAIL stance. A loop that trusts a stale percentage, or that
raises one file while the global number slips, has not met the proof.

**Read the target from `.claude/profile.yaml`** (e.g. `coverage.target`,
`coverage.per_target`), falling back to the project's own coverage config
(`.coveragerc`, `jest.config` `coverageThreshold`, `pytest` `--cov-fail-under`,
`tarpaulin.toml`, …). **Never hard-code 80 or 100** — the target is the
project's, not this skill's. The per-stack coverage commands, how to read each
report format, and the anti-gaming rules are in
[`references/coverage.md`](references/coverage.md).

## Step 1 — Resolve the target, the command, and the report artifact

Before looping, pin three things for *this* project and record them in
`coverage_plan.md` so every iteration re-measures identically:

1. **The target** — from `.claude/profile.yaml`, else the project's coverage
   config. Capture both the total target and any per-target thresholds. **If
   neither declares a target, stop and ask** — a coverage loop with no target
   cannot converge; never invent one.
2. **The coverage command** — prefer the project's own named script (`npm run
   coverage`, `make coverage`, `pytest --cov`); stack defaults are in
   [`references/coverage.md`](references/coverage.md). Run what CI runs.
3. **The report artifact** — the file/summary the proof reads (`coverage.xml`,
   `lcov.info`, `coverage/coverage-summary.json`, the terminal `TOTAL … N%`
   line). The proof is read from this artifact, never asserted.

## Step 2 — Run coverage, find the lowest-covered meaningful unit

Generate a fresh report and parse it. Pick the **lowest-covered *meaningful*
unit** — a function, branch, or module that represents real untested behavior —
not whichever file is alphabetically first and not trivial generated/boilerplate
lines. One unit per iteration (`loop-controller` Step 5); chasing ten files at
once destroys the signal about which tests moved the number. Log the chosen unit
and its current % in `coverage_plan.md`.

## Step 3 — Add REAL tests for that unit

Write tests that **exercise the unit and assert on its observable behavior** —
inputs mapped to expected outputs, error paths, edge cases, branch conditions.
A test that calls a function purely to execute its lines without asserting on the
result is not a test; it is coverage theater (see the anti-cheat rules below).
Where the existing suite is itself red, **delegate to [`fix-until-green`]** to
restore green before adding more — coverage of a broken suite is meaningless, and
that loop owns the three-exit-code proof so this one doesn't re-implement it.

## Step 4 — Re-measure the WHOLE report, checkpoint

Re-run coverage over the **entire** report — not just the unit you touched — and
re-run the full suite. A round that raises one file but drops the global total,
or greens coverage while reding a test, has made things worse; only a whole-report
re-measure catches it (`loop-controller` Step 5, "restart the streak"). On a
coverage-raising round (total moved up, nothing regressed, suite green),
**commit a checkpoint** naming the unit covered — the git trail is the loop's undo
and post-mortem. When total and every per-target threshold are at or above target
with the suite green, the loop is done; report the final coverage report as
evidence.

## Guardrails specific to this loop

Inherits the full stack from `loop-controller` → `references/safety.md`. The caps
this loop sets:

- **Iteration cap** — default ~15–25 add-tests rounds (read from
  `.claude/profile.yaml` if set). Hitting the cap is a *stop-and-escalate*, not a
  license to game the number. The last percent toward a 100% target is often the
  cap-hitter — surface "stuck at X% on these units" rather than faking it.
- **No-progress detection** — if the coverage total **does not increase** for
  **3 consecutive rounds**, stop and escalate. Three rounds of flat coverage
  means the remaining gap is structurally hard (dead code, untestable glue,
  environment-bound paths) — a human call, surfaced with what was tried.
- **Budget cap** — re-running the full coverage suite **every round** is
  materially more expensive than a single test run; watch `/cost` and terminate
  at the ceiling, don't just warn.
- **Never game the coverage number.** Forbidden, and each is a *finding* if you
  catch it (mirrors [`fix-until-green`]'s never-cheat rule, points back to
  `loop-controller` guardrail 6): writing **assertion-free "tests"** that execute
  lines without checking behavior; **excluding files / adding ignore pragmas**
  (`.coveragerc` `omit`, `/* istanbul ignore */`, `# pragma: no cover`,
  `coveragePathIgnorePatterns`) to make the denominator shrink instead of covering
  the code; **lowering the configured threshold** to meet it; or deleting/skipping
  hard-to-cover tests. When the percentage jumps, read the diff that did it — a
  jump from new excludes, not new assertions, is the cheat.
- **AFK-safe within the reversible boundary.** Writing test files + running
  coverage is reversible and has a hard verifier — fine unattended. A test that
  would touch something irreversible (a real DB, an external API) is an HITL
  checkpoint — pause for the human (`loop-controller` guardrail 4).

## Choosing the driver primitive

Per `loop-controller` Step 1, the coverage % is provable from command output, so
the default is **`/goal`**:

- **Default — `/goal`:** `/goal "the coverage report shows total and every
  per-target threshold at or above the project's configured target, and the full
  suite exits 0, with no file excluded and no assertion-free test added — or stop
  after N rounds."` The Haiku evaluator reads the coverage summary you surface
  each turn; remember `/goal` has no native budget, so the turn cap and `/cost`
  are the backstops.
- **Stop-hook gate** when you want a coverage floor to ship *with* the build and
  block exit deterministically (an orchestrator wave gate that fails the wave if
  coverage regresses below target). The gate script runs the coverage command and
  parses the artifact; wire it per `loop-controller` → `references/safety.md`
  (`stop_hook_active` guard included).

## Using it under the orchestrator

This is the **QE coverage inner loop** and a natural **wave gate**. The
orchestrator dispatches it after a build wave to raise coverage on the wave's new
code, or wires the Stop-hook as a coverage floor. Under-covered code routes back
to the owning agent **by file** (`loop-controller`'s by-file routing): a thin
coverage report in `src/api/` is the backend agent's gap, not a generic "add
tests." The orchestrator does **not** override a stuck loop — if coverage-loop
escalates after flat coverage, that's a real testability blocker, not a number to
paper over. As always, the loop informs; the [`qe-agent`]'s `qa-report.json`
still decides the gate.

## How this differs from its neighbors

- **vs. [`fix-until-green`]** — that loop drives an **existing** suite to GREEN
  (three exit codes, a binary stop). This loop **grows** the suite to a coverage
  NUMBER. They compose: coverage-loop calls fix-until-green to keep the suite
  green while it adds tests, then measures the number fix-until-green can't see.
- **vs. the [`qe-agent`]** — the role agent owns the QA gate and `qa-report.json`
  one-shot. This is the bounded *iterative* loop that drives coverage up to the
  target before that gate is evaluated.

## Reference files

- [`references/coverage.md`](references/coverage.md) — per-stack coverage
  commands (node/jest+vitest+c8, python/coverage.py+pytest-cov, go, rust/tarpaulin,
  ruby/simplecov, java/jacoco, …), how to read each report format and per-target
  threshold, and the full anti-gaming rule set (assertion-free tests, exclude/omit
  config, threshold-lowering — and how to detect each from the diff).

[`loop-controller`]: ../loop-controller/SKILL.md
[`fix-until-green`]: ../fix-until-green/SKILL.md
[`qe-agent`]: ../../roles/qe-agent/SKILL.md
