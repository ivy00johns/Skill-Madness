# Split hygiene for skill scoring (SO-4)

Rules any future skill-scoring work in this library must follow — written now,
ahead of the `F5 skill-eval` / `skill-optimize` frontier (see
[`docs/FUTURE.md`](../FUTURE.md)), because scores collected without split
discipline can silently overfit or lie, and retrofitting hygiene after numbers
exist means throwing the numbers away. Ported from microsoft/SkillOpt's
measured practice (`[SO]`, intaken 2026-07-21).

## The four rules

1. **Stable per-item hashing.** A task's split assignment (train / validation /
   test) is a deterministic function of a stable per-item hash — never of
   insertion order, file order, or a re-rolled seed. The same task lands in the
   same split on every run, forever. Re-splitting on each run leaks eval items
   into training and inflates every score after the first.

2. **The held-out test set is touched exactly once.** Validation is for
   accept/reject decisions during optimization; **test** is read one time, at
   the end, to report the final number. A test set consulted during iteration
   is a validation set with a misleading name — report it as such or re-carve a
   fresh test set.

3. **Synthetic / generated tasks train only — never evaluate.** Model-generated
   tasks carry the generator's distribution and blind spots; scoring against
   them measures agreement with the generator, not capability. Generated items
   may augment *train*; validation and test are real tasks only.

4. **Multi-seed / multi-trial before trusting small deltas.** A single-run
   delta under ~1.5 points is noise until it survives repeated trials
   (different seeds / orderings). An optimizer that accepts edits on
   single-trial sub-noise improvements is doing a random walk with extra steps.

## Why this exists before the eval does

These rules only pay off once a skill eval exists (they gate `F5`'s efficacy
mode and its `evaluate_gate`-style accept/reject step) — but they must be *in
force from the first measurement*. SkillOpt's cautionary twin runs (`SO-5`,
recorded in `loop-controller`'s `references/safety.md`): the gated loop, which
followed this discipline, held its score; the ungated one collapsed −52.8
points on a plausible-but-wrong learned rule. The gate only works if the
numbers it reads obey these rules.

Source: `[SO]` — the 2026-07-20 SkillOpt deep dive
(`../DeepResearch/skillopt_deepdive/source-material/`, esp.
`06-validation-gate-and-scoring.md`, `08-benchmarks-and-environments.md`).
