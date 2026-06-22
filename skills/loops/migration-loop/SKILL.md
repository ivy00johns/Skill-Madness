---
name: migration-loop
version: 1.0.0
description: >-
  Migrate a known, enumerated set of targets one at a time until EVERY one is
  done — one iteration picks the next un-migrated target from a checklist,
  transforms it, verifies behaviour-identical (the suite stays green), commits a
  checkpoint, and marks it migrated, with a hard exit that BOTH the suite is
  green AND a grep for the old pattern returns zero. The only loop over a fixed
  target set whose proof is "no legacy pattern remains," not just "tests pass."
  Use for a codemod across a repo, a Jest-to-Vitest swap, an API version bump, a
  framework migration, an import/dependency rename, or any mechanical transform
  applied to a finite list of files. Large sets may fan out via batch or a
  dynamic workflow with worktree isolation. Trigger on "migrate everything from
  X to Y", "run the codemod across the repo", "bump every call site", "swap the
  framework", "migrate all the tests", "finish the migration", "no old pattern
  left", "/migration-loop". A configuration of loop-controller.
requires_claude_code: true
min_plan: starter
disable-model-invocation: true
allowed-tools: ["Read", "Write", "Edit", "Bash", "Grep", "Glob", "Agent"]
composes_with: ["loop-controller", "orchestrator", "fix-until-green", "db-migration-agent"]
spawned_by: ["orchestrator"]
---

# migration-loop

> **A configuration of [`loop-controller`].** That skill supplies the loop
> machinery — primitive selection, the full guardrail stack, state
> externalization. This skill supplies the two things specific to "migrate a
> fixed set of targets to completion": a **default-FAIL target checklist** driven
> one entry per iteration, and a **proof that no legacy pattern remains** (a grep
> for the old pattern returning zero), not merely "tests pass." Read
> `loop-controller` for the guardrails; they're inherited, not repeated here.
>
> **Why `disable-model-invocation`:** this loop edits and commits code on its own
> — a checkpoint commit per migrated target — until the whole set is done. You
> want to *type* `/migration-loop` (or have the orchestrator dispatch it) — not
> have Claude silently start rewriting every file because it noticed an old API.

## The 5-part contract

| Part | This loop |
|---|---|
| **trigger** | a finite, enumerable set of targets needs the *same* transform (a codemod, a Jest-to-Vitest swap, an API version bump, a framework/import rename), plus a way to verify behaviour is preserved — or an explicit `/migration-loop` (optionally scoped to one path) |
| **action** | ONE iteration: pick the next `"migrated": false` target from the checklist → apply the transform to **just that target** → run the suite to confirm behaviour-identical → on green, **commit a checkpoint** naming the target → flip its checklist entry to `true` |
| **proof** | **EVERY** checklist entry `"migrated": true` **AND** the full suite exits 0 **AND** a grep for the legacy pattern returns **zero** matches — default-FAIL: assume incomplete until all three artifacts (the checklist, the suite exit code, the grep count) are observed together |
| **memory** | `migration-checklist.json` (one default-FAIL entry per target + the old→new mapping), `PROGRESS.md` (what's migrated / next), a git checkpoint commit per migrated target |
| **stop** | all three proof artifacts hold **OR** iteration cap **OR** no-progress for 3 rounds **OR** budget cap **OR** an HITL checkpoint for an irreversible target (see Guardrails) |

## The proof: checklist + grep-for-old-pattern, default-FAIL

"Done" is **not** "the suite is green." A green suite proves the targets you
*touched* still behave — it says nothing about the ones you *missed*. The thing
that distinguishes a real migration from a partial one is the third artifact: a
**grep for the legacy pattern returning zero**. Three signals, all required, all
default-FAIL (assume not-done until each is observed):

1. **The checklist is exhausted** — every entry in `migration-checklist.json` is
   `"migrated": true`. Each starts `false` and only flips when *that* target is
   transformed and its checkpoint commit lands.
2. **The full suite exits 0** — re-run the *whole* suite, not just the touched
   file's tests; the migration is behaviour-preserving only if nothing else
   regressed (`loop-controller` Step 5, "re-verify the whole").
3. **`grep -r '<legacy-pattern>'` returns zero** across the migrated scope —
   the mechanical proof that no call site, import, or usage was skipped. Pin the
   exact pattern(s) in the checklist so every iteration (and the final check)
   greps the *identical* string. A non-zero count is a *finding*: a missed
   target, not a passing migration.

Building the checklist/mapping, choosing the pattern(s), and the
"no legacy pattern remains" verification are detailed in
[`references/migration-checklist.md`](references/migration-checklist.md).

## Step 1 — Enumerate the targets and build the default-FAIL checklist

Discover the full target set *before* looping — a migration over a set you
haven't fully enumerated cannot prove completion. Use `Grep`/`Glob` to find every
occurrence of the legacy pattern, dedupe to a target list, and write each as a
JSON entry with `"migrated": false`, the old→new mapping, and the exact grep
pattern. Store it at the profile-defined path (default
`migration-checklist.json`). The checklist *is* the loop's scope: if a target
isn't on it, the loop won't migrate it, and the final grep will catch the gap.

## Step 2 — Decide sequential vs fan-out

- **Sequential (`/goal`, default)** — one target per iteration. Use when targets
  are interdependent, the transform is subtle, or the set is small enough that
  per-target review matters. The Haiku evaluator reads the suite output and the
  grep count you surface each turn.
- **Parallel (`/batch` / dynamic workflow)** — for large, *mechanically uniform*
  sets (hundreds of identical codemod sites). Fan out across **worktree-isolated**
  subagents (compose the [`orchestrator`]'s Workflow mode), each migrating a slice
  and committing in its own worktree. **Cap build/test parallelism at 1 per
  worktree** (`loop-controller` Step 5) — two builds at once destroy the
  backpressure signal. The whole-set grep + suite still run once after the merge
  as the single proof. The decision rule and the fan-out shape are in
  [`references/migration-checklist.md`](references/migration-checklist.md).

## Step 3 — Migrate one target, verify behaviour-identical, checkpoint

Apply the transform to **one** target (or one worktree slice). Then run the
**full** suite — a migration is only valid if behaviour is preserved, so the test
gate is the per-iteration verifier. If the suite goes red, the transform changed
behaviour: fix it (or **invoke [`fix-until-green`]** if it's a non-trivial gate
failure) before moving on — never advance the checklist over a red suite. On
green, **commit a checkpoint** naming the migrated target, then flip its entry to
`true`. The commit-per-target trail is the loop's undo: `git reset --hard` to the
last green target is cheaper than rescuing a wedged transform.

## Step 4 — Re-run the whole proof, repeat

After the last target, run all three proof artifacts together: the checklist must
be fully `true`, the full suite must exit 0, and the legacy-pattern grep must
return **zero**. A non-zero grep with a "fully migrated" checklist means a target
was missed during enumeration — add it and loop. When all three hold on one pass,
the loop is done; report the final checklist, the suite exit code, and the
`grep -c` output (zero) as evidence.

## Guardrails specific to this loop

Inherits the full stack from `loop-controller` → `references/safety.md`. The caps
this loop sets:

- **Iteration cap** — default ~1 per target plus slack (read from
  `.claude/profile.yaml` if set); for fan-out, a hard cap on concurrent worktrees.
  Hitting the cap is a *stop-and-escalate*, not a license to relax the grep or
  mark targets done without migrating them.
- **No-progress detection** — if the same target stays `"migrated": false` (or the
  legacy grep count stops dropping) for **3 consecutive rounds**, stop and
  escalate. The same target failing three times means the transform is wrong, not
  that it needs a fourth try.
- **Never fake completion.** Forbidden, each a *finding*: marking a target
  `"migrated": true` without transforming it, narrowing the grep pattern so it
  reports zero while usages remain, or deleting/skipping a test to keep the suite
  green over a behaviour change. A zero grep that came from a weakened pattern is
  not a migration.
- **Reversible code transforms are AFK-safe; irreversible resources are HITL.** A
  code/codemod migration behind a test gate with checkpoint commits per target is
  reversible — fine unattended. A migration that touches an **irreversible
  resource** — a real DB schema migration against live data, a destructive data
  backfill, an external system — is an **HITL checkpoint** (`loop-controller`
  guardrail 4): pause for the human, and route the schema-migration case to
  [`db-migration-agent`], which owns up/down migrations, dry-runs, and rollback.

## Choosing the driver primitive

Per `loop-controller` Step 1, by the target set:

- **Default — `/goal`** for sequential one-target-per-iteration: the proof is
  provable from the suite output + the grep count you surface, so
  `/goal "every entry in migration-checklist.json is migrated:true, the full
  suite exits 0, and a grep for the legacy pattern returns zero — or stop after N
  turns."` Remember the embedded turn cap — `/goal` has no native budget.
- **`/batch` / dynamic workflow** for large parallel sets with worktree isolation
  (hence `Agent` in `allowed-tools`), composing the [`orchestrator`]'s Workflow
  mode. The whole-set grep + suite run once after merge as the proof.

## Using it under the orchestrator

This is the **Migration inner loop** (archetype 6). The orchestrator dispatches
it for a planned migration, routing per-file failures back to the owning role
**by file** (a red suite in `src/api/` goes to the backend agent). The
orchestrator does **not** override a stuck loop — if migration-loop escalates
after no-progress, that's a real migration blocker, not a number to paper over. A
fully-migrated checklist informs the build; the `qe-agent`'s `qa-report.json`
still decides the gate (`loop-controller`'s rule: the loop informs, the gate
decides).

## How this differs from its neighbors

- **vs. [`fix-until-green`]** — that loop drives a *failing* suite to green; this
  loop drives a *fixed target set* to fully migrated. The suite green is only one
  of three proof artifacts here; the load-bearing one is the legacy-pattern grep.
  This loop *invokes* fix-until-green when a transform reds the gate.
- **vs. [`db-migration-agent`]** — that role owns a single irreversible schema
  migration (up/down, dry-run, rollback) as an HITL operation; this loop drives a
  *set* of reversible code transforms to completion and *delegates* the schema
  case to it at the HITL checkpoint.

## Reference files

- [`references/migration-checklist.md`](references/migration-checklist.md) —
  building the target checklist/mapping (the `migration-checklist.json`
  default-FAIL schema with a worked example), the sequential-vs-`/batch`-fan-out
  decision and the worktree-isolation shape, and the "no legacy pattern remains"
  verification (choosing the grep pattern, scoping it, and reading the count).

[`loop-controller`]: ../loop-controller/SKILL.md
[`fix-until-green`]: ../fix-until-green/SKILL.md
[`orchestrator`]: ../../orchestrator/SKILL.md
[`db-migration-agent`]: ../../roles/db-migration-agent/SKILL.md
