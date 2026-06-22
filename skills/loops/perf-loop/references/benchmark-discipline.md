# Benchmark discipline for perf-loop

`perf-loop`'s proof is a *measured number under repeatable conditions*. That makes
the measurement harness part of the proof: a number from a noisy, unpinned
benchmark is not evidence, it's a coin flip. This reference has the
repeatable-benchmark checklist, the per-stack profiling/benchmark tooling, and the
no-functional-regression rule (how perf-loop delegates the correctness gate to
`fix-until-green`).

## Contents
- [Why a noisy benchmark is a broken proof](#noise)
- [The repeatable-benchmark checklist](#checklist)
- [Per-stack profiling and benchmark tools](#tools)
- [The no-functional-regression rule](#no-regression)
- [What goes in perf_baseline.json](#baseline)

---

## <a id="noise"></a>Why a noisy benchmark is a broken proof

The loop optimizes against deltas: "this change took p95 from 80ms to 60ms." If
run-to-run spread on the *same* code is ±25ms, that 20ms "win" is indistinguishable
from noise — you might have made it slower. Every non-convergence failure mode in
`loop-controller`'s safety stack has a perf-specific twin here:

- **False progress** — accepting a within-noise fluctuation as an improvement and
  checkpointing it. The loop "converges" on luck.
- **False no-progress** — a real improvement buried under variance, read as
  no-progress, triggering an early stop-and-escalate.
- **Cache/warm-up lies** — the second run is always faster because of JIT warm-up,
  filesystem cache, connection pools, or a CDN edge. Measuring the warm run as if
  it were representative ships a regression that only appears cold in production.

The rule: **the benchmark's own variance is the noise floor. An improvement
smaller than the noise floor counts as no improvement** (this is the no-progress
definition in the SKILL.md guardrails). Tighten the harness until the noise floor
is well below the budget margin *before* trusting any number.

## <a id="checklist"></a>The repeatable-benchmark checklist

Before any measured number counts as proof, the harness must satisfy all of:

1. **Warm-up runs discarded.** Run the path N times to warm caches/JIT, throw
   those away, then measure the steady state. State explicitly whether the budget
   is a warm or cold target — they are different proofs (a page-load budget is
   usually cold; a hot-path latency budget is usually warm).
2. **Fixed environment.** Same machine or container, same CPU governor / no
   throttling, no competing load (close the other heavy processes; on CI, a
   dedicated runner). A benchmark that shares a box with a build is not repeatable.
3. **Pinned inputs and data set.** Same request payloads, same seed data, same
   row counts, same feature flags. A "faster" query against a smaller table is not
   a speedup.
4. **Multiple runs + variance reported.** Never a single run. Report a stable
   statistic (median or p95, not mean — the mean hides tail behavior) **and** the
   spread (stddev, IQR, or min/max). The spread is the noise floor.
5. **Whole measured set, every round.** Re-benchmark *every* path, not just the
   one optimized — `loop-controller`'s "restart the streak." This is what proves
   an optimization didn't regress a neighbor.
6. **Isolate what you're measuring.** Separate cold vs warm, network vs compute,
   first-byte vs full-render where it matters, so the hotspot attribution is real
   and not an artifact of mixing phases.

If run-to-run spread exceeds the improvement you're claiming, **you have measured
nothing** — fix the harness (more warm-up, more runs, a quieter environment, a
larger sample) before continuing to optimize.

## <a id="tools"></a>Per-stack profiling and benchmark tools

Resolve the benchmark command from `.claude/profile.yaml` first; this table is the
fallback for detecting what to use. Profile to *find* the hotspot; benchmark to
*measure* whether the fix worked.

| Domain / metric | Profile (find the hotspot) | Benchmark (measure under repeatable conditions) |
|---|---|---|
| **Web page-load** (FCP/LCP/TTI, ms) | Chrome DevTools Performance, Lighthouse traces | Lighthouse CI (multiple runs, median), WebPageTest, Playwright + `performance.timing` over N runs |
| **Bundle size** (KB) | source-map-explorer, `webpack-bundle-analyzer`, `vite-bundle-visualizer` | `size-limit`, `bundlesize`, or a CI byte-count assertion against the budget |
| **Backend latency / throughput** (p95 ms, req/s) | flame graphs (`py-spy`, async-profiler, `pprof`), APM spans | `k6`, `wrk`, `oha`, `autocannon`, `vegeta` — fixed RPS, warm-up, percentile output |
| **Node.js CPU** | `--prof` + `--prof-process`, `clinic flame`, `0x` | `tinybench` / `benchmark.js`, `mitata` (reports variance) |
| **Python** | `cProfile` + `snakeviz`, `py-spy`, `scalene` (CPU+mem) | `pytest-benchmark` (statistical, rounds + warmup built in), `pyperf` |
| **Rust / Go** | `cargo flamegraph` / `perf`; `pprof`, `go tool trace` | `criterion` (statistical, outlier detection); `go test -bench` + `benchstat` for variance |
| **JVM** | async-profiler, JFR | JMH (forks, warm-up iterations, variance — the gold standard) |
| **Memory / RSS** | heap snapshots, `scalene`, `valgrind massif`, `pprof -inuse_space` | peak-RSS capture across N runs (`/usr/bin/time -v`, `psutil`), GC-pause stats |
| **Test-suite speed** (wall-clock) | per-test timing reports (`pytest --durations`, `jest --verbose`, `vitest --reporter`) | the suite runner's own total time across N runs; `benchstat` on repeated runs (Loop Library #011) |

Many runners (`criterion`, JMH, `pytest-benchmark`, `mitata`) implement the
checklist for you — warm-up, multiple rounds, and variance reporting are built in.
Prefer them over hand-rolled `time` wrappers, which usually skip warm-up and report
a single run.

## <a id="no-regression"></a>The no-functional-regression rule

A speedup that changes behavior is not a speedup — it's a regression that happens
to be fast. So **every accepted optimization re-runs the functional suite**, and
perf-loop **delegates that gate to [`fix-until-green`]** rather than re-implementing
it:

- After Step 4's whole-set re-benchmark, invoke `fix-until-green` (or, under the
  orchestrator, the QE inner loop) so test + lint + typecheck all exit 0.
- If the suite reds, the optimization is **rejected** regardless of the speed win.
  Either fix the correctness break (one root cause, per fix-until-green) or
  `git reset --hard` to the last green checkpoint and pick a different hotspot.
- An improvement is only checkpointed when **both** proofs hold in the same round:
  the path is closer to (or under) budget on the whole-set benchmark **and** the
  functional suite is green. Speed on top of green, never instead of it.

This is why `fix-until-green` and `performance-agent` are in `composes_with`:
perf-loop sequences them — the benchmark is its own contribution; correctness and
deep profiling judgment are delegated, not duplicated.

## <a id="baseline"></a>What goes in perf_baseline.json

The durable, path-addressable state the loop reads at the top of every iteration
(externalized per `loop-controller` Step 4). One entry per measured path:

```json
{
  "metric": "p95_latency_ms",
  "target": 50,
  "benchmark_cmd": "k6 run bench/api.js --summary-export=-",
  "conditions": {
    "warmup_runs": 3,
    "measured_runs": 10,
    "environment": "ci-perf-runner (dedicated)",
    "dataset": "seed/perf-fixtures.sql"
  },
  "paths": [
    { "name": "GET /feed",   "baseline": 82.4, "current": 48.1, "stddev": 2.3, "under_target": true },
    { "name": "GET /search", "baseline": 140.0, "current": 96.7, "stddev": 9.1, "under_target": false }
  ]
}
```

`under_target` is the per-path default-FAIL flag: it starts `false` and only flips
`true` when `current + stddev` is under `target` on a whole-set re-benchmark — a
within-noise pass doesn't count. The loop's proof is **every** entry `under_target:
true` with the functional suite green. `stddev` (or your chosen spread statistic)
is mandatory: it's the noise floor the no-progress check measures improvements
against.

[`fix-until-green`]: ../../fix-until-green/SKILL.md
