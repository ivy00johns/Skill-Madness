---
name: perf-loop
version: 1.0.0
description: >-
  Drive a metric under its budget in a disciplined profile-optimize-reprofile
  loop run under REPEATABLE conditions: benchmark the whole measured set under a
  fixed environment, find the single highest-leverage hotspot or regression,
  optimize one thing, re-benchmark the WHOLE set, and repeat until the metric is
  under target on every measured path with no functional regression. The proof is
  a measured number from a named benchmark artifact, not a hunch. Use for latency,
  throughput, page-load, bundle-size, memory, or test-suite-speed targets, or as
  the performance-role inner loop under an orchestrated build. Trigger on:
  "optimize until under Nms", "get page load under budget", "profile and speed
  this up", "make it faster until target", "reduce latency loop", "performance
  budget", "shrink the bundle", "speed up the test suite", "benchmark until
  green", "perf loop", "/perf-loop". A configuration of loop-controller.
requires_claude_code: true
min_plan: starter
disable-model-invocation: true
allowed-tools: ["Read", "Write", "Edit", "Bash", "Grep", "Glob"]
composes_with: ["loop-controller", "fix-until-green", "performance-agent", "orchestrator"]
spawned_by: ["orchestrator"]
---

# perf-loop

> **A configuration of [`loop-controller`].** That skill supplies the loop
> machinery — primitive selection, the full guardrail stack, state
> externalization. This skill supplies the two things specific to "make it hit
> the budget": a **measured proof under repeatable conditions** (a named
> benchmark artifact, default-FAIL) and the **measurement discipline** that keeps
> a noisy benchmark from lying to the loop. Read `loop-controller` for the
> guardrails; they're inherited, not repeated here.
>
> **Why `disable-model-invocation`:** this loop edits and commits code on its own
> and spends real time re-running benchmarks until a metric is under target. You
> want to *type* `/perf-loop` (or have the orchestrator dispatch it) — not have
> Claude start an autonomous optimize loop because a number looked slow.

## The 5-part contract

| Part | This loop |
|---|---|
| **trigger** | a metric is over its budget (a slow path, a perf regression, a too-big bundle), or an explicit `/perf-loop` (optionally scoped to one path/benchmark) |
| **action** | ONE iteration: **benchmark the whole measured set under fixed conditions** → identify the **single highest-leverage** hotspot/regression → optimize **one thing** → **re-benchmark the WHOLE set** → re-run the functional suite |
| **proof** | the metric is **under target on EVERY measured path** in the benchmark output **AND** the functional suite still exits 0 — default-FAIL: assume over-budget until the benchmark, run under repeatable conditions, proves otherwise |
| **memory** | `perf_baseline.json` (the per-path measured numbers + variance, the durable baseline), `PROGRESS.md` (hotspot → change → delta log), a git checkpoint per measured improvement |
| **stop** | metric under target on every path AND suite green **OR** iteration cap **OR** no-progress for 3 rounds **OR** budget cap |

## The proof: a measured number under repeatable conditions, default-FAIL

"Fast enough" is **not** "the profiler looked better" or "the one path I touched
sped up." It is **every measured path under its target in the benchmark output,
re-measured across the whole set, with the functional suite still green** — and
the benchmark must be reproducible, or the number is noise, not proof. Assume
**over-budget** until you have that artifact. A loop that declares victory off a
single fast run on a warm cache ships a regression the next cold start exposes.

Two rules make the proof trustworthy:

- **A noisy benchmark is a broken proof.** Before any number counts, the
  measurement must be *repeatable*: warm-up runs discarded, a fixed environment
  (same machine/container, no competing load, pinned data set and inputs),
  multiple runs, and reported **variance**. If run-to-run spread is larger than
  the improvement you're claiming, you have measured nothing — tighten the
  harness before optimizing. The repeatable-benchmark checklist and per-stack
  profiling/benchmark tools are in [`references/benchmark-discipline.md`].
- **A speedup that breaks behavior is rejected.** Every optimization re-runs the
  functional suite — **delegate to [`fix-until-green`]**, don't re-implement the
  gate. A change that drops latency but reds a test is not an improvement; it's a
  regression that happens to be fast. The functional gate is part of the proof,
  not a separate concern.

## Step 1 — Read the budget and the benchmark command

Resolve, for *this* project, three things before looping — from
`.claude/profile.yaml` when present (so the same loop works across projects
without hard-coding):

1. **the metric** (p95 latency, page-load ms, bundle KB, peak RSS, suite wall-clock);
2. **the target** (the budget the metric must come in under, per measured path);
3. **the benchmark command** that produces the metric under repeatable conditions.

If the profile doesn't declare them, detect the stack's benchmark/profiling
tooling ([`references/benchmark-discipline.md`] has the per-stack table) and
**confirm the target with the human** — an unstated budget is not a proof. Record
all three in `perf_baseline.json` so every iteration measures the identical thing
the identical way.

## Step 2 — Benchmark the whole set, establish/refresh the baseline

Run the benchmark across **every** measured path under the fixed conditions from
Step 1 (warm-up discarded, multiple runs, variance recorded), and write the
per-path numbers to `perf_baseline.json`. This whole-set baseline is what "no
regression elsewhere" is checked against — a single-path benchmark cannot prove
the loop didn't slow down a neighbor.

## Step 3 — Identify the single highest-leverage hotspot

From the profile, pick the **one** change with the best expected delta-per-effort
— the dominant hotspot or worst regression against baseline, not the first slow
line you see. Optimize **one thing per iteration** (`loop-controller` Step 5):
batching destroys the signal about which change moved the number, and perf changes
routinely interact. Log the chosen hotspot + hypothesis in `PROGRESS.md`.

## Step 4 — Re-benchmark the WHOLE set, re-run the suite, checkpoint

Re-run the **entire** benchmark from scratch — not just the path you touched.
This is `loop-controller`'s "restart the streak": an optimization that speeds one
path while regressing another has made the set worse, and only a whole-set
re-measure catches it. Then re-run the functional suite via [`fix-until-green`]:
no green suite, no accepted improvement.

On a measured improvement (a path closer to budget, nothing regressed, suite
green), **commit a checkpoint** naming the hotspot fixed and the before/after
delta — the git trail is the loop's undo and its post-mortem. When every measured
path is under target and the suite is green, the loop is done; report the final
`perf_baseline.json` and benchmark output as evidence.

## Guardrails specific to this loop

Inherits the full stack from `loop-controller` → `references/safety.md`. The
caps this loop sets:

- **Iteration cap** — default ~10–20 optimize/re-benchmark rounds (read from
  `.claude/profile.yaml` if set). Hitting the cap is a *stop-and-escalate*: some
  budgets aren't reachable without an architectural change, which is a human
  decision, not a license to fake the number.
- **No-progress detection** — if the metric **doesn't improve** across **3
  consecutive iterations** (improvement smaller than the benchmark's own
  variance counts as no improvement), stop and escalate. Three rounds inside the
  noise floor means the approach is wrong or the budget needs revisiting.
- **Budget cap** — re-benchmarking the whole set every round is *slow* (wall-clock
  and, for cloud runners, money). A long perf loop is materially more expensive
  than a quick fix loop; terminate at the ceiling, don't just warn.
- **Never fake the metric.** Forbidden, and each is a *finding* if you catch it:
  weakening the benchmark (fewer iterations, a warmer cache, a smaller data set,
  dropping the slow path from the measured set), loosening the target without
  human sign-off, or reporting a single lucky run instead of the variance-aware
  number. Moving the measuring stick is not a speedup. (`loop-controller`
  guardrail 6, specialized to a measured proof.)
- **Never trade correctness for speed silently.** A faster path that reds a test
  is rejected by the [`fix-until-green`] re-run — that gate is non-negotiable.
- **HITL before irreversible.** Editing source + re-benchmarking is reversible with
  a hard verifier — fine unattended. A change touching an irreversible perf lever
  (a prod-affecting index migration, a cache-infra change) is an HITL checkpoint —
  pause for the human (`loop-controller` guardrail 4).

## Choosing the driver primitive

Per `loop-controller` Step 1, by how you're running it:

- **Default — `/goal`:** the proof is provable from the benchmark output you
  surface each turn, so `/goal "the benchmark reports every measured path under
  its target with run-to-run variance below the margin, and the functional suite
  exits 0 — or stop after N turns."` The evaluator reads the benchmark numbers you
  surface; remember `/goal` has no native budget, so embed the turn cap.
- **Stop-hook gate** when you want the budget check to ship *with* the build and
  block exit deterministically — a perf budget enforced as a wave gate (the
  benchmark script runs, exit non-zero if any path is over target). The
  `stop_hook_active` guard pattern is in `loop-controller`'s `references/safety.md`.

## Using it under the orchestrator

This is the **performance-role inner loop** (archetype 8). The orchestrator
dispatches it to drive a path under budget; it delegates the functional gate to
[`fix-until-green`] and the deep profiling judgment to [`performance-agent`]. The
orchestrator does **not** override a stuck loop — if perf-loop escalates after
no-progress or the cap, that's a real budget blocker (often an architectural one),
not a number to paper over. A satisfied `perf_baseline.json` informs the build;
the `qe-agent`'s `qa-report.json` still decides the gate (`loop-controller`'s
rule: the loop informs, the gate decides).

## How this differs from its neighbors

- **vs. [`fix-until-green`]** — its proof is exit codes (correctness); this loop's
  is a *measured number under repeatable conditions* (speed). perf-loop *composes*
  fix-until-green as its no-regression check — speed on top of, never instead of,
  green.
- **vs. a coverage loop** — both prove a measured artifact, but perf is the only
  loop whose proof is trustworthy *only when the measurement itself is repeatable*
  — variance is a first-class concern, not a footnote.

## Reference files

- [`references/benchmark-discipline.md`] — the repeatable-benchmark checklist
  (warm-up, fixed environment, multiple runs, variance, the noise floor), the
  per-stack profiling/benchmark tooling table (web/page-load, backend latency,
  bundle size, memory, test-suite speed), and the no-functional-regression rule
  (how perf-loop delegates to `fix-until-green`).

[`loop-controller`]: ../loop-controller/SKILL.md
[`fix-until-green`]: ../fix-until-green/SKILL.md
[`performance-agent`]: ../../roles/performance-agent/SKILL.md
[`references/benchmark-discipline.md`]: references/benchmark-discipline.md
