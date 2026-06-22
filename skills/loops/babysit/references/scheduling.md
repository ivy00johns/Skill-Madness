# babysit — the per-pass algorithm, scheduling recipe, and HITL boundary

babysit is the scheduled, guardrailed loop around [`git-pr-feedback`]. The
per-pass *work* is git-pr-feedback's; this reference covers only what babysit adds
on top: the loop handoff, the `/loop` scheduling recipe, the exact proof query,
and the AFK-safe-vs-pause boundary. Read [`loop-controller`] for the guardrail
stack and `primitives.md` for `/loop`'s mechanics — neither is repeated here.

## Contents
- [The per-pass algorithm](#per-pass)
- [The proof query](#proof)
- [Scheduling recipe (/loop + loop.md)](#scheduling)
- [The HITL boundary table](#hitl)
- [The per-PR fix log](#fix-log)

---

## Per-pass

One pass = one `git-pr-feedback` cycle, wrapped in loop discipline. Do **not**
re-implement the fetch/triage/reply mechanics — invoke `git-pr-feedback`; the
steps below are the loop's framing of its output.

1. **Identify the PR.** Default to the current branch's PR
   (`gh pr view --json number -q .number`). If the run is scoped to a PR number
   (see scheduling), use that one — babysit tends **one** PR per loop.
2. **Fetch state (default-FAIL starts here).** Run the proof query *first*
   (below). Treat the PR as unhealthy until it reads clean. Then have
   `git-pr-feedback` fetch inline + issue comments + review summaries
   (paginated), tagging each by author (`Copilot`/bot vs human) and category.
3. **Decide the single change for this pass:**
   - **Base moved, no other blocker** → a **routine fast-forward rebase** (within
     the boundary). If it can't fast-forward (needs a history rewrite / force-push
     of a shared branch) → **HITL pause**.
   - **One or more open findings** → pick **one root-cause** finding. A bot/nit is
     addressable unattended; a human reviewer's substantive thread is **HITL
     pause** (don't argue in a loop).
   - **Nothing open and mergeable** → the proof passes; stop.
4. **Address it.** Make the one change, run the **project gate** (the test/lint
   /typecheck the project uses — same detection as [`fix-until-green`]; if it
   exists and fails, fix or revert before pushing). Commit per [`git-commit`].
5. **Push (fast-forward only) and reconcile the thread.** Push your own commits;
   reply on GitHub to the finding(s) this pass addressed, via `git-pr-feedback`'s
   reply step. Resolve **bot** threads only.
6. **Re-check the whole PR**, not just the comment you touched — re-run the proof
   query. New comments or a new base push may have arrived; that's the next pass.
7. **Update the fix log** and let `/loop` fire the next pass on its interval.

**One change per pass** is the rule (loop-controller Step 5): it keeps the
re-fetch a clean binary-search signal about what actually moved the PR's health.

## Proof

The proof is two `gh` reads that must be clean **in the same pass**:

```bash
# mergeability + overall review decision
gh pr view <pr> --json mergeable,mergeStateStatus,reviewDecision
# → proof needs:  mergeable == "MERGEABLE"  AND  reviewDecision != "CHANGES_REQUESTED"

# open actionable comment count — via git-pr-feedback's paginated fetch,
# excluding threads already resolved or already replied-to by the PR author
gh api --paginate repos/{owner}/{repo}/pulls/{pr}/comments
gh api --paginate repos/{owner}/{repo}/issues/{pr}/comments
# → proof needs:  zero OPEN blocking/actionable comments
```

`mergeable == "MERGEABLE"` confirms rebased-onto-base + CI not failing;
`reviewDecision != "CHANGES_REQUESTED"` plus a zero open-blocking count confirms
no reviewer is still asking for changes. **Default-FAIL:** if any read is
ambiguous (e.g. `mergeable == "UNKNOWN"` while GitHub computes it), treat it as
not-yet-proven and re-check next pass — never assume healthy.

## Scheduling

The primitive is `/loop` (the watcher), per `loop-controller` Step 1. The
documented daily-driver recipe:

```
/loop 5m /babysit
```

This fires `/babysit` every ~5 minutes while the session is open. Remember (from
`loop-controller`'s `primitives.md`, not repeated): `/loop` is **session-scoped**,
**auto-expires after ~3 days**, and **does not catch up** missed intervals.

**Scoping to one PR.** `/babysit` defaults to the current branch's PR. To babysit
a specific PR regardless of the checked-out branch, pass the number
(`/babysit 1234`) or set it in `loop.md`.

**`loop.md` (the self-paced variant).** If you omit the interval (`/loop`),
Claude reads `loop.md` for what to do and picks a dynamic 1-min–1-hour delay. A
minimal `loop.md` for babysit:

```markdown
# loop.md — babysit PR #1234
Each pass: run /babysit scoped to PR 1234.
Stop when: zero open blocking findings AND the PR is mergeable,
or after 20 passes, or if the same finding survives 3 passes,
or if any HITL checkpoint is hit (force-push, human-reviewer thread, merge).
Never merge. Never force-push a shared branch.
```

Keep the stop conditions in `loop.md` so the self-paced run inherits the same
guardrails as the explicit-interval run.

## HITL

babysit runs **only inside the reversible boundary** unattended. Everything in
the right column is a checkpoint: stop, surface it, wait for the human.

| Situation | AFK-safe (do it) | HITL — pause |
|---|---|---|
| **Base moved** | fast-forward rebase that applies cleanly | rebase needing a **force-push** of a shared branch (history rewrite) |
| **Push** | fast-forward push of your own commits | any **non-fast-forward / force** push |
| **Bot / Copilot comment** | address the nit, reply, resolve the thread | — |
| **Human reviewer comment** | — | **reply to or resolve a human thread**; any substantive disagreement — don't argue in a loop |
| **Reviewer requested changes** | address clear, reversible bot-equivalent items | a human's `CHANGES_REQUESTED` that needs a design decision |
| **Gate** | run tests/lint/typecheck; fix or revert | a fix that touches something irreversible (migration on a real DB, external API) |
| **Merge** | — | **never auto-merge** — proof = *ready for the human to merge* |

The boundary rule is loop-controller's HITL guardrail specialized to PRs:
**reversible + bot-facing = unattended; irreversible or human-facing = pause.**

## Fix-log

The per-PR fix log is babysit's externalized memory (it survives across the
session-scoped `/loop` fires; loop-controller Step 4). One entry per pass:

```markdown
## PR #1234 — babysit log
- pass 3 (2026-06-21 14:05): addressed Copilot nit on api/routes.ts:88 → fixed in a1b2c3d, replied+resolved.
- pass 4 (14:10): base moved → fast-forward rebase, pushed. gate green.
- pass 5 (14:15): human reviewer asked to rename the public API → PAUSED (HITL: human design decision). Surfaced to user.
- DEFERRED: reviewer's rename request — needs human call, not loop-addressable.
```

Record both what was addressed and what was **deferred + why** — the deferred
list plus the no-progress counter (same finding 3×) is how a reviewer audits that
the loop stopped for the right reason rather than cheating the proof.

[`loop-controller`]: ../../loop-controller/SKILL.md
[`git-pr-feedback`]: ../../../git/git-pr-feedback/SKILL.md
[`git-commit`]: ../../../git/git-commit/SKILL.md
[`fix-until-green`]: ../../fix-until-green/SKILL.md
