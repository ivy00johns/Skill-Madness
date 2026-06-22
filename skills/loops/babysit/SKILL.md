---
name: babysit
version: 1.0.0
description: >-
  Keep one of your open PRs healthy on a schedule: poll for new review activity,
  auto-address bot/Copilot nits and routine rebases, re-run the project gate, and
  reconcile the PR thread — looping until the PR has zero blocking findings and is
  mergeable, with HITL checkpoints on anything irreversible. This is the
  scheduled, guardrailed loop around git-pr-feedback (which does the per-pass
  fetch/triage/fix). Run it as Boris Cherny's daily-driver "/loop 5m /babysit",
  or invoke /babysit once. Use when you want a PR babysat while you work
  elsewhere, want review comments auto-handled on a cadence, or want a PR kept
  rebased and green. Trigger on "babysit my PR", "babysit prs", "watch this PR",
  "keep my PR green", "auto-address review comments on a schedule", "loop 5m
  babysit", "keep the PR rebased", "poll the PR for new feedback", "tend this
  pull request". Never auto-merges and never force-pushes a shared branch
  unattended. A configuration of loop-controller.
requires_claude_code: true
min_plan: starter
disable-model-invocation: true
allowed-tools: ["Read", "Edit", "Bash", "Grep", "Glob"]
composes_with: ["loop-controller", "git-pr-feedback", "git-pr", "git-commit", "loop"]
spawned_by: []
---

# babysit

> **A configuration of [`loop-controller`].** That skill supplies the loop
> machinery — primitive selection, the full guardrail stack, state
> externalization. This skill supplies the three things specific to "keep a PR
> healthy": the **per-pass recipe** (it schedules [`git-pr-feedback`], it does
> not re-implement it), the **mechanical proof** (zero open blocking findings +
> mergeable), and the **HITL boundary** that decides what's AFK-safe vs what
> pauses. Read `loop-controller` for the guardrails; they're inherited, not
> repeated here.
>
> **Why `disable-model-invocation`:** this loop commits, pushes, rebases, and
> touches a live PR thread on its own, on a clock. It is user-driven — you want
> to *type* `/loop 5m /babysit` (or `/babysit`), not have Claude silently start
> tending a PR because a reviewer happened to comment.

## The 5-part contract

| Part | This loop |
|---|---|
| **trigger** | an open PR of yours with potential review activity; scheduled via `/loop 5m /babysit`, or an explicit `/babysit` (optionally a PR number) |
| **action** | ONE pass: fetch new review findings (Copilot + human) via [`git-pr-feedback`] → triage → address **one root-cause finding** (or rebase if base moved) → re-run the project gate → push → reconcile the PR thread. One change per pass; re-check the whole PR state after |
| **proof** | the `gh` PR review/status query returns **zero OPEN actionable/blocking comments AND `mergeable == "MERGEABLE"`** (up to date with base, CI green) — default-FAIL: assume findings are unaddressed until the fetch proves otherwise (treat `mergeable == "UNKNOWN"` as not-yet-proven and re-check) |
| **memory** | a per-PR fix log (findings addressed, findings deferred + why), git history, and the PR thread itself — all durable across the session-scoped `/loop` fires |
| **stop** | zero blocking findings **AND** mergeable **OR** poll/iteration cap **OR** no-progress for 3 rounds (same finding unaddressed 3×) **OR** budget cap **OR** an HITL checkpoint is hit |

## The proof: zero blocking findings AND mergeable, default-FAIL

"Healthy" is not "I replied to the last comment." It is **two conditions
observed together from `gh`**: the PR has zero *open, actionable, blocking*
review comments, **and** GitHub reports it mergeable (rebased onto base, CI
green). Assume the PR is **not** healthy until a fresh fetch proves both — that's
the default-FAIL stance, and it's why every pass *re-fetches* rather than
trusting last pass's verdict. A loop that stops after answering one comment ships
a PR that picked up three new ones and went stale behind a base push.

Name the artifact explicitly: a `gh pr view --json mergeable,reviewDecision`
plus the open-comments count from `git-pr-feedback`'s fetch (see
`references/scheduling.md` for the exact query). Both must read clean *in the
same pass*.

## Step 1 — One pass = one git-pr-feedback cycle

The per-pass work **is** [`git-pr-feedback`]: identify the PR, fetch inline +
issue comments + review summaries (paginated), triage each by author and
category, address what's clear, reply on GitHub. **Do not re-document or
re-implement that** — invoke it. babysit adds only the loop discipline around it:
one root-cause change per pass, then re-check the *whole* PR state. If the base
branch moved and the only blocker is staleness, the pass is a routine rebase (not
a finding fix). The full per-pass algorithm and the handoff are in
`references/scheduling.md`.

## Step 2 — Schedule it with /loop (the watcher, not /goal)

Per `loop-controller` Step 1: this is a **watch/poll** job — you wait for review
activity to *change* on a cadence — so the primitive is **`/loop`**, the
scheduler, **not** `/goal` (which pushes to a finish line). The recipe is the
documented daily driver:

```
/loop 5m /babysit
```

`/loop` is **session-scoped, expires after ~3 days, and does not catch up** on
missed intervals — those mechanics (and the `loop.md` self-paced variant) live in
`loop-controller`'s `references/primitives.md`; don't re-document them. What goes
in `loop.md` and how to scope the run to one PR are in
`references/scheduling.md`.

## HITL is load-bearing for this loop

babysit runs **only inside the reversible boundary** unattended. The irreversible
or human-facing actions are **HITL checkpoints — never autonomous**:

- **Force-push / rebasing a shared branch** — pause. A fast-forward push of your
  own commits is fine; a history rewrite of a branch others may have pulled is
  not.
- **Resolving or replying to a *human* reviewer's conversation** — pause. A
  bot/Copilot nit can be answered and resolved unattended; a human's thread is a
  conversation, and **you do not argue with a reviewer inside a loop.** On any
  substantive disagreement with a human reviewer, stop and surface it.
- **Merging** — never. babysit does **not** auto-merge, full stop. Reaching the
  proof (zero blocking + mergeable) means *ready for the human to merge*, not
  "merge it."

Within the boundary — addressing Copilot/bot nits, routine fast-forward rebases,
re-running the gate, fast-forward pushes — it is AFK-safe. The full AFK-safe vs
pause table is in `references/scheduling.md`.

## Guardrails specific to this loop

Inherits the full stack from `loop-controller` → `references/safety.md`. The caps
this loop sets:

- **Poll / iteration cap** — `/loop`'s ~3-day session expiry is the outer bound;
  set an inner per-PR pass cap (default ~20) so a wedged PR doesn't burn the
  whole window. Hitting it is a *stop-and-escalate*, not a reason to loosen the
  proof.
- **No-progress detection** — if the **same blocking finding** survives **3
  consecutive passes** (addressed but the reviewer/check still flags it, or it
  can't be resolved within the reversible boundary), stop and surface it. Three
  passes on one finding means it needs a human, not a fourth attempt.
- **Budget cap** — a watch loop that fires every 5 minutes for days adds up;
  enforce a token/cost ceiling that *terminates* the loop (read it from
  `.claude/profile.yaml` when present), not just warns.
- **Never cheat the proof.** Don't mark a thread resolved without addressing it,
  don't dismiss a human reviewer's comment to clear the count, and don't merge to
  make "mergeable" moot. A green that came from silencing a reviewer is a
  *finding*, not a win.

## Choosing the driver primitive

`/loop 5m /babysit` is the scheduler. The *per-pass* exit (this pass made one
clean, reversible change and re-checked the PR) is provable from `gh` output, so a
pass can run under auto mode unattended within the HITL boundary above. The loop
as a whole has **no `/goal` finish line** — it watches until you stop it or a stop
condition fires.

## Reference files

- `references/scheduling.md` — the per-pass algorithm and the `git-pr-feedback`
  handoff, the scheduling recipe (`/loop 5m /babysit`, what to put in `loop.md`,
  scoping to one PR, the exact `gh` proof query), and the HITL boundary table
  (what's AFK-safe vs what pauses).

[`loop-controller`]: ../loop-controller/SKILL.md
[`git-pr-feedback`]: ../../git/git-pr-feedback/SKILL.md
[`git-pr`]: ../../git/git-pr/SKILL.md
[`git-commit`]: ../../git/git-commit/SKILL.md
