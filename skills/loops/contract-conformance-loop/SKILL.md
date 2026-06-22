---
name: contract-conformance-loop
version: 1.0.0
description: >-
  Drive an implementation until EVERY criterion of an authored contract holds —
  a Plan-Generate-Evaluate (PGE / GAN-style) loop where the builder implements
  toward one not-yet-passing criterion and a FRESH-CONTEXT evaluator subagent
  (contract-auditor, spawned with no Write/Edit tools, default-FAIL) grades all
  criteria against evidence and never lets the builder self-grade. This is the
  loop form of the contract-author / contract-auditor pair. Use when a contract
  or acceptance-criteria spec exists and an implementation must be built or
  verified against it. Trigger on "build until the contract passes", "implement
  the spec until all criteria hold", "conform to the contract", "drive this to
  spec", "make the implementation match the contract", "loop until acceptance
  criteria pass", "build-until-spec", "PGE loop", "evaluate against the
  contract", "/contract-conformance-loop". A configuration of loop-controller.
requires_claude_code: true
min_plan: starter
disable-model-invocation: true
allowed-tools: ["Read", "Write", "Edit", "Bash", "Grep", "Glob", "Agent"]
composes_with: ["loop-controller", "contract-author", "contract-auditor", "orchestrator", "fix-until-green"]
spawned_by: ["orchestrator"]
---

# contract-conformance-loop

> **A configuration of [`loop-controller`].** That skill supplies the loop
> machinery — primitive selection, the full guardrail stack, state
> externalization. This skill supplies the two things specific to
> "build until the spec holds": a **fresh-context evaluator** as the proof
> (the [`contract-auditor`] graded against an authored contract, default-FAIL)
> and the **generator/evaluator split** that keeps the builder from grading its
> own work. Read `loop-controller` for the guardrails; they're inherited, not
> repeated here.
>
> **Why `disable-model-invocation`:** this loop edits and commits code on its
> own and spends tokens spawning an evaluator subagent each round, until every
> contract criterion passes. You want to *type* `/contract-conformance-loop` (or
> have the orchestrator dispatch it) — not have Claude silently start an
> autonomous build loop because a contract happened to exist.

## The 5-part contract

| Part | This loop |
|---|---|
| **trigger** | an authored contract exists ([`contract-author`] output in `contracts/`) plus an implementation to build or verify against it, or an explicit `/contract-conformance-loop` (optionally scoped to one contract) |
| **action** | ONE iteration: the **generator** (the builder / role agent) implements or fixes toward **one** not-yet-passing criterion → a **fresh-context evaluator subagent** ([`contract-auditor`], spawned with **no Write/Edit**) checks **ALL** criteria against evidence and returns a default-FAIL verdict with per-criterion pass/fail + feedback → failing criteria + feedback feed the next iteration |
| **proof** | every entry in the criteria JSON has passing **evidence confirmed by the fresh-context evaluator** (not the builder) — default-FAIL: each criterion starts `"passed": false` and only the evaluator's verdict, citing evidence, flips it |
| **memory** | `criteria.json` (the default-FAIL criteria, one entry per contract criterion), `PROGRESS.md` (what's done / next), a git checkpoint per criterion turned green |
| **stop** | the evaluator confirms **all** criteria pass **OR** iteration cap **OR** no-progress for 3 rounds **OR** budget cap |

## The proof: a fresh evaluator's verdict, default-FAIL

"Done" is **not** "the builder thinks the feature is built." It is **every
criterion in `criteria.json` flipped to `"passed": true` by the fresh-context
evaluator, each citing concrete evidence** — and re-confirmed against the *whole*
criteria set on the final round, not just the criterion last touched.

Two rules make this convergent rather than a rubber-stamp:

- **The grader is not the doer.** The builder is a pathological optimist about
  its own work; a same-context critic approves mediocre output. The evaluator is
  a *fresh* subagent that sees only the artifact + the contract, never the build
  reasoning. This is the PGE / GAN pattern from `loop-controller` Step 2.
- **The evaluator cannot edit.** It is spawned with **no Write/Edit tools** — so
  it can only *report* a failure, never "fix" one by quietly lowering the bar. It
  inspects (Read / Grep / Bash-to-run-tests) and returns a verdict.

This maps onto the existing pair: [`contract-author`] writes the spec the loop
builds against; [`contract-auditor`] **is** the evaluator. This loop does not
re-implement either — it sequences them in a bounded, default-FAIL loop. The full
generator/evaluator split, the `criteria.json` schema, and the evaluator dispatch
prompt are in [`references/pge-loop.md`](references/pge-loop.md).

## Step 1 — Build the default-FAIL criteria JSON

Read the authored contract from `contracts/` (the [`contract-author`] output:
`openapi.yaml`, `data-layer.yaml`, `types.<ext>`, and the Domain Rules in
`contracts/README.md`). Decompose it into **one testable criterion per checkable
fact** and write each as a JSON entry with `"passed": false`. Store it at the
profile-defined path (default `criteria.json`). A criterion the evaluator cannot
check against evidence is not a criterion — split it until it is. Schema and a
worked example: [`references/pge-loop.md`](references/pge-loop.md).

## Step 2 — Generator: implement toward ONE failing criterion

Pick the highest-leverage `"passed": false` criterion and have the builder
implement or fix **just that one**. One criterion per iteration — don't batch
features; batching destroys the signal about which change moved which criterion
(`loop-controller` Step 5). Update `PROGRESS.md` with what was attempted.

## Step 3 — Evaluator: grade ALL criteria from fresh context

Spawn the evaluator subagent ([`contract-auditor`]) **fresh, with no Write/Edit
tools**, blind to the builder's reasoning. Hand it only the contract + the
implementation + `criteria.json`. It re-checks **every** criterion against
evidence (re-verify the whole, not just the one touched — `loop-controller`
Step 5) and returns the criteria JSON with each entry either still `false` (plus
feedback) or flipped to `true` (plus the evidence that flipped it). The builder
never edits `criteria.json`; only the evaluator's verdict does.

## Step 4 — Feed failures back, checkpoint, repeat

Merge the evaluator's verdict into `criteria.json`. On a green-ward round (a
criterion newly `true`, nothing regressed), **commit a checkpoint** naming the
criterion satisfied — the git trail is the loop's undo and post-mortem. Feed the
still-failing criteria + their feedback into the next generator pass. When the
evaluator confirms **all** criteria pass on a single whole-set re-check, the loop
is done; report the final `criteria.json` as evidence.

## Guardrails specific to this loop

Inherits the full stack from `loop-controller` → `references/safety.md`. The
caps this loop sets:

- **Iteration cap** — default ~10–15 build/evaluate rounds (read from
  `.claude/profile.yaml` if set). Hitting the cap is a *stop-and-escalate*, not a
  license to weaken the contract or have the builder self-pass a criterion.
- **No-progress detection** — if **the same set of criteria stays `false`** for
  **3 consecutive rounds**, stop and escalate. Three rounds with the criterion
  count unchanged means the approach is wrong, or the criterion is ambiguous —
  surface it (it may be a contract gap, which [`contract-auditor`] flags rather
  than failing the implementation against).
- **Budget cap** — the evaluator subagent costs a full fresh context **per
  round**; a long run is materially more expensive than a self-graded loop.
  Watch `/cost`; terminate at the ceiling, don't just warn.
- **Never let the builder grade itself.** Forbidden, and each is a *finding*:
  the builder flipping a `criteria.json` entry to `true`, softening a criterion,
  or the evaluator being reused with the builder's context (it must be fresh and
  Write/Edit-free). A green that the builder wrote is not proof — only the
  evaluator's verdict is.
- **HITL before irreversible.** If satisfying a criterion would touch something
  irreversible (a migration against a real DB, an external API), that's an HITL
  checkpoint — pause for the human (`loop-controller` guardrail 4).

## Choosing the driver primitive

The canonical form is **a skill orchestrating a generator + an evaluator
subagent** — the evaluator subagent *is* the proof, so this loop always spawns it
(hence `Agent` in `allowed-tools`). Per `loop-controller` Step 1:

- **Canonical — generator + fresh-context evaluator subagent.** Use whenever any
  criterion is subjective or needs cross-file judgment (does the implementation
  *import* the shared types, do the domain rules actually hold). The evaluator's
  default-FAIL verdict is the stop signal.
- **`/goal` may substitute** *only* when **every** criterion is fully provable
  from command output (e.g. a contract reduced entirely to a test suite +
  schema-validation exit codes). Then `/goal "every criterion in criteria.json is
  passed:true, confirmed by the contract's own checks — or stop after N turns"`,
  and the loop degenerates toward [`fix-until-green`]. The moment a criterion
  needs judgment, fall back to the fresh evaluator.

## Using it under the orchestrator

This is the **build-until-spec inner loop** (archetype 2). The orchestrator
authors the contract via [`contract-author`] (its Phase 4), then dispatches this
loop with the builder role as generator and [`contract-auditor`] as the
evaluator. The orchestrator does **not** override a stuck loop — if the loop
escalates after no-progress, that's a real conformance blocker or a contract gap,
not a number to paper over. A satisfied `criteria.json` informs the build; the
`qe-agent`'s `qa-report.json` still decides the gate (`loop-controller`'s rule:
the loop informs, the gate decides).

## How this differs from its neighbors

- **vs. [`contract-auditor`]** — the auditor is a *one-shot* static audit that
  reports mismatches. This is the bounded *iterative* loop that drives them to
  zero, wrapping the auditor as its default-FAIL evaluator harness.
- **vs. [`fix-until-green`]** — that loop's proof is three exit codes; this
  loop's proof is per-criterion contract evidence graded by a *fresh evaluator*.
  Use fix-until-green when "done" is the test suite; use this when "done" is "the
  contract's criteria all hold," some of which no single exit code can prove.

## Reference files

- [`references/pge-loop.md`](references/pge-loop.md) — the generator/evaluator
  split in full, the `criteria.json` default-FAIL schema with a concrete JSON
  example, and the fresh-context evaluator dispatch (no Write/Edit, blind to the
  build reasoning, returns a per-criterion verdict).

[`loop-controller`]: ../loop-controller/SKILL.md
[`fix-until-green`]: ../fix-until-green/SKILL.md
[`contract-author`]: ../../contracts/contract-author/SKILL.md
[`contract-auditor`]: ../../contracts/contract-auditor/SKILL.md
