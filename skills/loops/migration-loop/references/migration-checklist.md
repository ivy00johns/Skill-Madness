# Migration checklist, fan-out, and the "no legacy pattern remains" proof

Everything `migration-loop` needs beyond the SKILL.md body: how to build the
default-FAIL target checklist, when to go sequential vs fan out with `/batch`,
and how to make the legacy-pattern grep an honest proof. The loop machinery
(guardrails, primitives, state externalization) lives in `loop-controller` —
this is only what is specific to migrating a fixed set.

## Contents
- [Building the target checklist / mapping](#checklist)
- [Sequential vs `/batch` fan-out](#fanout)
- [The "no legacy pattern remains" verification](#grep)

---

## Building the target checklist / mapping {#checklist}

A migration can only prove completion if its scope is fully enumerated *before*
the loop runs. The checklist *is* the scope.

1. **Define the old→new mapping first.** What is the transform, exactly? E.g.
   `jest.fn()` → `vi.fn()`, `import ... from 'jest'` → `'vitest'`, `/v1/` →
   `/v2/`, `componentWillMount` → `componentDidMount`. Mappings that aren't a
   pure rename (signature changes, semantic differences) need a per-case note so
   each iteration knows *how* to transform, not just *what* to find.
2. **Enumerate every target.** Grep the legacy pattern across the migration
   scope, then dedupe to a list of files (or call sites). This is the same grep
   that becomes the final proof — pin its exact string now.
3. **Write the default-FAIL checklist.** One entry per target, each
   `"migrated": false`. A model is far less likely to quietly rewrite a JSON
   `false` than to soften a sentence (`loop-controller` Step 2). Store at the
   profile-defined path (default `migration-checklist.json`).

Schema:

```json
{
  "migration": "jest-to-vitest",
  "legacy_patterns": ["from 'jest'", "jest\\.fn\\(", "jest\\.mock\\("],
  "verify": { "suite": "npm test", "grep_scope": "src/ test/" },
  "mapping": [
    { "from": "from 'jest'",  "to": "from 'vitest'" },
    { "from": "jest.fn(",     "to": "vi.fn(" },
    { "from": "jest.mock(",   "to": "vi.mock(" }
  ],
  "targets": [
    { "id": "src/auth/login.test.ts",  "migrated": false, "commit": null },
    { "id": "src/auth/logout.test.ts", "migrated": false, "commit": null },
    { "id": "src/api/users.test.ts",   "migrated": false, "commit": null }
  ]
}
```

Each iteration: read the checklist → pick the next `"migrated": false` target →
apply every relevant `mapping` entry to it → run `verify.suite` → on green,
commit and set that target's `"migrated": true` and `"commit": "<sha>"`. Read the
caps and the state-file path from `.claude/profile.yaml` when present so the same
skill works across projects (`loop-controller` Step 4).

## Sequential vs `/batch` fan-out {#fanout}

**Decision rule:** *Is the transform mechanically uniform across a large set, or
does each target need judgment?*

| Use | When | Shape |
|---|---|---|
| **Sequential `/goal`** | small set, interdependent targets, subtle/non-pure transform, per-target review matters | one target per iteration, one checkpoint commit each; the suite + grep count surfaced to the `/goal` evaluator |
| **`/batch` / dynamic workflow** | large set (dozens–hundreds), the transform is a pure mechanical codemod, targets are independent | fan out worktree-isolated subagents, each migrating a slice and committing in its own worktree; merge; run the proof once |

Fan-out rules (inherited from `loop-controller` Step 5 and the orchestrator's
Workflow mode):

- **Worktree isolation per subagent.** Each parallel agent works in its own git
  worktree so commits don't collide. Compose the `orchestrator`'s Workflow mode
  to fan out (`agent({agentType})`) rather than hand-spawning.
- **Cap build/test parallelism at 1 per worktree.** Two builds running at once
  destroy the backpressure signal that tells you a transform broke something. The
  *number of worktrees* can be many; the *builds inside each* run one at a time.
- **The proof is whole-set, post-merge.** Per-slice green is not the proof — after
  merging all worktrees, run the full suite and the whole-scope grep **once**.
  Partial greens across slices can still hide a target that no slice owned.
- **Budget.** A fan-out spawns N fresh contexts; it is materially more expensive
  than a sequential loop. Take an explicit token budget (dynamic workflows accept
  one) and terminate at the ceiling, don't just warn.

## The "no legacy pattern remains" verification {#grep}

This is what makes `migration-loop` a *migration* and not "tests happen to pass."
A green suite proves the targets you touched still behave; the grep proves you
didn't *miss* any.

- **Grep the exact pinned pattern(s).** Use the `legacy_patterns` from the
  checklist verbatim — the same strings you enumerated with. A passing migration
  is `grep -rE -c '<pattern>' <grep_scope>` returning **zero** for every pattern.
- **Scope it honestly.** Restrict to the migration scope (`verify.grep_scope`),
  but do not narrow it to dodge known stragglers. **Narrowing the pattern or the
  scope so the count reads zero while real usages remain is a *finding*, not a
  pass** (`loop-controller` guardrail 6 — don't move the number instead of fixing
  the cause).
- **Exclude only true non-targets, explicitly.** Comments referencing the old
  name, a CHANGELOG entry, a compat shim you deliberately kept — exclude these by
  path with a documented reason in the checklist, never by quietly weakening the
  regex. If you're unsure whether a hit is a real usage, it's a target: add it.
- **A non-zero count after a "complete" checklist = a missed target.** The
  enumeration in Step 1 was incomplete. Add the newly-found target(s) to the
  checklist as `"migrated": false` and loop again. This self-correcting check is
  exactly why the grep, not the checklist alone, is the load-bearing proof.
- **Report the raw count as evidence.** The loop's done-proof is the trio: the
  fully-`true` checklist, the suite exit code (0), and `grep -c` output (0).
  Surface all three; "looks migrated" is not evidence.
