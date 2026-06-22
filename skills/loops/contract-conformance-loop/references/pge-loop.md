# The PGE loop: generator / evaluator split, criteria JSON, evaluator dispatch

This reference details the three mechanics specific to `contract-conformance-loop`:
the generator/evaluator separation, the default-FAIL `criteria.json` schema, and
how to dispatch the fresh-context evaluator. The loop machinery itself
(guardrails, primitive selection, state externalization) lives in
[`loop-controller`](../../loop-controller/SKILL.md); this file does not repeat it.

## Contents
- [Why the split exists](#why-the-split-exists)
- [The criteria.json schema (default-FAIL)](#the-criteriajson-schema-default-fail)
- [The generator pass](#the-generator-pass)
- [The evaluator dispatch (fresh context, no Write/Edit)](#the-evaluator-dispatch-fresh-context-no-writeedit)
- [Merging the verdict and looping](#merging-the-verdict-and-looping)

---

## Why the split exists

This is the Plan-Generate-Evaluate (PGE) harness, GAN-style. The contract is the
*plan* (authored once by [`contract-author`](../../contracts/contract-author/SKILL.md)).
Each round has two distinct actors with deliberately different powers:

| Actor | Who | Tools | Can it flip a criterion to `true`? |
|---|---|---|---|
| **Generator** | the builder / role agent | Read, Write, Edit, Bash | **No.** It only changes code. |
| **Evaluator** | [`contract-auditor`](../../contracts/contract-auditor/SKILL.md), spawned fresh | Read, Grep, Bash (run tests) — **no Write/Edit** | **Yes** — and it is the *only* actor that can. |

The separation is the whole point. A same-context critic that watched the build
rubber-stamps its own reasoning (measured self-bias). A doer that grades itself
is a pathological optimist. So:

1. **Fresh context.** Spawn a new evaluator each round; it sees only the artifact
   + the contract + `criteria.json`, never the generator's transcript.
2. **No edit tools.** With no Write/Edit, the evaluator *cannot* "fix" a failure
   by lowering the bar — it can only report. This is the structural guarantee
   that the proof is real.
3. **Default-FAIL.** Every criterion starts `false`; only the evaluator's
   evidence-citing verdict flips it. JSON, not prose — a model is far less likely
   to quietly rewrite `"passed": false` than to soften a sentence.

## The criteria.json schema (default-FAIL)

One entry per testable contract fact. Store at the profile-defined path (default
`criteria.json`). Every `passed` starts `false`; only the evaluator writes this
file.

```json
{
  "contract": "contracts/openapi.yaml + contracts/README.md",
  "generated_at": "2026-06-21T00:00:00Z",
  "criteria": [
    {
      "id": "C1",
      "source": "openapi.yaml#/paths/~1orders/post",
      "statement": "POST /orders/ returns 201 with the OrderResponse shape (id, status, items[], total) on a valid body",
      "how_to_verify": "run the API test for order creation; assert status 201 and response keys match contracts/types.ts OrderResponse",
      "passed": false,
      "evidence": null,
      "feedback": null
    },
    {
      "id": "C2",
      "source": "README.md#domain-rules",
      "statement": "Checkout atomically decrements stock and creates the order (no partial state on failure)",
      "how_to_verify": "grep the checkout handler for a transaction wrapper; run the concurrent-checkout test; confirm stock never goes negative",
      "passed": false,
      "evidence": null,
      "feedback": null
    },
    {
      "id": "C3",
      "source": "types.ts#OrderResponse",
      "statement": "Backend imports the shared OrderResponse type rather than hand-constructing the dict (no field-name drift)",
      "how_to_verify": "grep for an import of OrderResponse from contracts/types; confirm the handler uses it for serialization",
      "passed": false,
      "evidence": null,
      "feedback": null
    }
  ]
}
```

Field rules:

- **`statement`** is one observable fact. If it bundles two checks ("returns 201
  *and* sends the email"), split into two criteria — partial pass is invisible
  otherwise.
- **`how_to_verify`** names the *evidence* the evaluator must produce: a command
  to run, a file:line to confirm, a response to assert. "Looks correct" is not a
  verification.
- **`passed`** — written **only** by the evaluator. The generator touching this
  field is a finding (see SKILL.md guardrails).
- **`evidence`** — what the evaluator observed (command output snippet, file:line)
  when it flipped `passed` to `true`.
- **`feedback`** — the evaluator's reason a criterion is still `false`, fed into
  the next generator pass.

A criterion the evaluator cannot reduce to `how_to_verify` evidence is not ready
— split or sharpen it before the loop starts.

## The generator pass

Each round, the generator:

1. Reads `criteria.json` and picks the **single** highest-leverage `"passed":
   false` criterion (one whose `feedback` from last round is most actionable, or
   that unblocks others).
2. Implements or fixes **only** toward that criterion. One criterion per
   iteration — batching destroys the per-change signal
   ([`loop-controller`](../../loop-controller/SKILL.md) Step 5).
3. Records the attempt in `PROGRESS.md` (what it changed, which criterion id).
4. Does **not** edit `criteria.json` — grading is the evaluator's job alone.

If the criterion is a hard build/test failure (flaky, "passes locally fails in
CI"), the generator may invoke
[`fix-until-green`](../fix-until-green/SKILL.md) for that one criterion's gate
before handing back to the evaluator.

## The evaluator dispatch (fresh context, no Write/Edit)

Spawn [`contract-auditor`](../../contracts/contract-auditor/SKILL.md) as a fresh
subagent via the `Agent` tool, with **Read, Grep, Bash only — no Write/Edit**.
Hand it exactly three things and nothing about how the code was built:

- the authored contract (`contracts/`),
- the current implementation,
- `criteria.json`.

Dispatch prompt shape:

```
You are the contract conformance evaluator. You did NOT build this code and you
have no Write/Edit tools — you can only inspect and report.

For EVERY criterion in criteria.json, independently verify it against the
implementation using its `how_to_verify` (run the command, confirm the file:line,
assert the response). Do not trust any prior `passed` value — re-check the WHOLE
set from scratch (default-FAIL: assume false until you observe evidence).

Return criteria.json with, for each criterion:
  - passed: true ONLY if you observed concrete evidence; else false
  - evidence: the command output / file:line you observed (required when true)
  - feedback: the specific reason it is still false (required when false)

If a criterion is ambiguous or the contract contradicts itself, leave it false
and flag it as a CONTRACT GAP in feedback — do not fail the implementation
against an unclear contract.
```

Key constraints (all inherited from `loop-controller` Step 2 / `authoring.md`):

- **Re-check the whole set every round**, not just the criterion the generator
  touched — a fix for C1 can regress C3.
- **Fresh each round.** Do not reuse the evaluator subagent across rounds with
  accumulated context; that reintroduces self-bias.
- The evaluator returns a verdict; it never modifies code. If it finds the
  contract itself is wrong, it reports a gap (the auditor's existing
  "contract is truth, but flag contradictions" rule), which is an escalation, not
  a generator task.

## Merging the verdict and looping

1. Overwrite `criteria.json` with the evaluator's returned verdict (the evaluator
   is the only writer).
2. If **all** `passed: true` on this whole-set re-check → **done**; report the
   final `criteria.json` (with evidence) as proof.
3. Else: commit a checkpoint if any criterion went green this round (message
   names the criterion id), update `PROGRESS.md`, and feed the still-`false`
   criteria + their `feedback` into the next generator pass.
4. Apply the stop conditions from SKILL.md every round: iteration cap, no-progress
   for 3 rounds (the set of `false` criteria unchanged), or budget cap — each is
   a stop-and-escalate, never a license to self-pass a criterion.
