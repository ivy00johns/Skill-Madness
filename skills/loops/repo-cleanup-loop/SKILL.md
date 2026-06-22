---
name: repo-cleanup-loop
version: 1.0.0
description: >-
  Keep a repo's git state intentional on a weekly cadence: scan every branch,
  PR, commit trail, and worktree, classify each as current / owned / safely
  removable-with-evidence, RECOVER any valuable work before deleting, then remove
  exactly one class of stale items with evidence — looping until every item is
  accounted for, with an HITL checkpoint on anything ambiguous and never a
  force-delete of unmerged work. The broad recurring evidence-gated loop that
  delegates the post-merge-branch case to git-post-merge-cleanup. Use when you
  want a repo kept tidy on a schedule, stale branches and worktrees pruned safely
  after sprints, or a weekly hygiene sweep that recovers before it deletes.
  Trigger on "clean up the repo weekly", "weekly repo hygiene", "prune stale
  branches and worktrees on a schedule", "tidy git state every week", "scheduled
  repo cleanup", "keep the repo state intentional", "sweep stale PRs and
  worktrees", "recover before deleting branches". A configuration of
  loop-controller.
requires_claude_code: true
min_plan: starter
disable-model-invocation: true
allowed-tools: ["Read", "Edit", "Bash", "Grep", "Glob"]
composes_with: ["loop-controller", "git-post-merge-cleanup", "loop"]
spawned_by: []
---

# repo-cleanup-loop

> **A configuration of [`loop-controller`].** That skill supplies the loop
> machinery — primitive selection, the full guardrail stack, state
> externalization. This skill supplies the three things specific to "keep the
> repo state intentional": the **per-class recipe** (it delegates the
> post-merge-branch case to [`git-post-merge-cleanup`], it does not re-implement
> it), the **mechanical proof** (a classified inventory where nothing is
> "safely removable" until evidence flips it), and the **recover-before-delete
> HITL boundary** that makes deletion safe. Read `loop-controller` for the
> guardrails; they're inherited, not repeated here.
>
> **Why `disable-model-invocation`:** this loop deletes branches, prunes refs,
> and removes worktrees on its own, on a clock — irreversible acts. It is
> user-driven: you want to *type* `/loop` it weekly (or run `/repo-cleanup-loop`
> once), not have Claude silently start pruning because it noticed debris.

## The 5-part contract

| Part | This loop |
|---|---|
| **trigger** | a weekly cadence (`/loop` or `/schedule`) over the whole repo, or an explicit `/repo-cleanup-loop` |
| **action** | ONE pass: scan repo state (branches + PRs + commits + worktrees) → classify each item → **recover** anything valuable → remove **one class** of safely-removable items **with evidence** → re-scan |
| **proof** | the repo state is intentional — **every** branch / PR / worktree is `current` OR `owned` OR `safely-removed-with-evidence` — default-FAIL: each inventory item starts `"reviewed": false` and only flips on classification + evidence |
| **memory** | the classified inventory JSON (per-item: kind, name, class, evidence, `"reviewed"`, `"recovered"`), a recovery log (what was salvaged + where), and git history / reflog as the durable undo trail |
| **stop** | every item `reviewed` and intentional (proof) **OR** iteration/pass cap **OR** no-progress for 3 passes (same item unresolved) **OR** budget cap **OR** an HITL checkpoint on an ambiguous item |

## The proof: a classified inventory, default-FAIL

"Tidy" is not "I deleted some merged branches." It is **every item in the repo's
git state accounted for**: each branch, open PR, dangling commit trail, and
worktree is classified `current` (active work), `owned` (someone's in-flight
work — leave it), or `safely-removable` **with recorded evidence** that it was
merged or its work recovered. Assume every item is **unreviewed** until the scan
classifies it — that's the default-FAIL stance, and it's why the inventory JSON
stores `"reviewed": false` per item rather than a prose summary. A model is far
less likely to quietly flip a JSON `false` than to soften a sentence.

Name the artifact explicitly: the inventory JSON written each pass (one record
per branch / PR / worktree). The pass is only done when no record reads
`"reviewed": false` and no record is `safely-removable` without an `evidence`
field. The classify / recover / remove algorithm and the exact evidence rules
are in `references/cleanup-algorithm.md`.

## Step 1 — One pass = scan → classify → recover → remove one class → re-scan

The per-pass work is a single sweep, not a free-for-all:

1. **Scan** the whole repo's git state — local + remote branches, open PRs (via
   `gh`), worktrees, and stale/dangling refs (`git worktree list`,
   `git branch -vv`, `git for-each-ref`, `gh pr list`).
2. **Classify** each item into the inventory (default-FAIL). Evidence rules and
   the bucket definitions live in `references/cleanup-algorithm.md`.
3. **Recover before you delete.** Any item that *looks* removable but holds work
   not on the default branch goes through the recovery step first — see the HITL
   section. This is the load-bearing safety act.
4. **Remove exactly one class** of safely-removable items with evidence (e.g.
   "fully-merged local branches" this pass, "gone remote-tracking refs" next).
   One class per pass keeps the signal about what each removal changed.
5. **Re-scan** and re-classify. The proof is about the *whole* state, re-checked
   — never trust last pass's inventory.

**Delegate the post-merge-branch case — do not re-implement it.** For the
fully-merged-local-branch, gone-remote-tracking-ref, and safe-worktree classes,
invoke [`git-post-merge-cleanup`] (its `--dry-run` for the scan, then its
confirmed execute). That skill already owns the branch/worktree classification
and the destructive-command ordering. This loop adds the *discipline around* it:
the default-FAIL whole-repo inventory, the recover-before-delete gate, the
one-class-per-pass cadence, and the weekly schedule. The exact delegation
boundary — what this loop hands off versus what it keeps — is in
`references/cleanup-algorithm.md`.

## Step 2 — Schedule it with /loop or /schedule (the watcher, not /goal)

Per `loop-controller` Step 1: this is a **watch/poll** job on a weekly cadence —
you keep the repo's state intentional as work accrues, you do not push it to a
single finish line — so the primitive is **`/loop`** (session-scoped) or
**`/schedule`** (a cloud cron that survives laptop-off — the better fit for a
*weekly* cadence), **not** `/goal`. `/loop`'s session-scope / ~3-day-expiry /
no-catch-up mechanics live in `loop-controller`'s `references/primitives.md`.

## How this differs from its neighbors

The one real overlap is **[`git-post-merge-cleanup`]**, and the boundary is
deliberate:

- **`git-post-merge-cleanup`** is a **focused one-shot tidy**: after a batch of
  PRs land, scan → classify → present a plan → act on confirmation, for three
  specific classes (merged local branches, gone remote-tracking refs, stale
  worktrees). It runs once, when you ask, and it is the *expert* on the branch
  and worktree classification.
- **`repo-cleanup-loop`** is the **broader, recurring, evidence-gated weekly
  loop over the whole repo** — branches *and* open PRs *and* commit trails *and*
  worktrees — that **recovers valuable work before deleting**, removes one class
  per pass, and re-scans until the whole inventory is intentional.

It is **not** a thin scheduled wrapper: the substance is the loop discipline, not
the branch logic it borrows — the default-FAIL whole-repo inventory, the
recover-before-delete step, one-class-per-pass, and the weekly schedule. When a
pass hits the merged-branch / gone-ref / safe-worktree classes it **delegates**
to `git-post-merge-cleanup` rather than re-implementing them. What it owns that
the one-shot does not: the recurring cadence, the PR + commit-trail scan, and the
recover-first gate.

## HITL is load-bearing for this loop

Deletion is the irreversible act, and **recovering valuable work before deleting
is the load-bearing safety step.** This loop runs only inside the reversible
boundary unattended; anything ambiguous is a **human checkpoint — never
autonomous**:

- **Never delete a branch / worktree / ref without evidence it is safely
  removable** — merged into the default branch, or its work demonstrably
  recovered. No evidence = not removable, full stop.
- **Recover before delete.** An item that holds commits not on the default
  branch is *valuable work*, not debris. Salvage it first (a `recovery/<name>`
  ref or tag, the commits cherry-picked or noted, the diff archived) and log
  where it went — *then* it is eligible for removal. Recovery happens before the
  delete, every time.
- **Never force-delete unmerged work.** Lowercase `git branch -d` (refuses
  unmerged) before uppercase `-D`; `-D` only after merge is confirmed or the
  human explicitly asks. No `git push --force`, no `--force` worktree removal of
  genuinely-unmerged work, unattended.
- **Ambiguous item = pause.** Squash-merged-but-shows-unmerged, a stale open PR
  with unpushed local work, a worktree with uncommitted diffs that don't match
  the default branch, a long-lived `develop`/`staging`/`production` branch —
  surface it, do not act. The "needs attention" bucket is the signal.

The full AFK-safe vs pause table and the recovery recipe are in
`references/cleanup-algorithm.md`.

## Guardrails specific to this loop

Inherits the full stack from `loop-controller` → `references/safety.md`. The caps
this loop sets:

- **Pass / iteration cap** — default ~10 passes per run (read from
  `.claude/profile.yaml` when present). One class removed per pass; hitting the
  cap is a *stop-and-report*, not a license to bulk-delete the rest.
- **No-progress detection** — if the **same item** stays `"reviewed": false`
  across **3 consecutive passes** (can't be classified, or can't be safely
  removed within the boundary), stop and surface it. Three passes on one item
  means it needs a human, not a fourth scan.
- **Budget cap** — a weekly scheduled sweep adds up over months; enforce a
  token/cost ceiling that *terminates* the run, not just warns.
- **Never cheat the proof.** Don't mark an item `safely-removable` without an
  `evidence` field, don't `git branch -D` to clear an unmerged item from the
  count, and don't skip the recovery step to "tidy faster." A clean inventory
  that came from force-deleting unrecovered work is a *finding*, not a win.

## Choosing the driver primitive

`/schedule` (preferred for weekly) or `/loop` is the scheduler. The *per-pass*
exit — this pass classified the inventory, recovered what was valuable, and
removed one class with evidence — is provable from `git`/`gh` output and the
inventory JSON, so a pass runs unattended **within the HITL boundary above**. The
loop as a whole has **no `/goal` finish line**; it watches and tidies on a
cadence until you stop it or a stop condition fires.

## Reference files

- `references/cleanup-algorithm.md` — the scan → classify → recover → remove
  algorithm, the per-class evidence rules and inventory-JSON shape, the
  recover-before-delete recipe, the AFK-safe vs pause table, and the exact
  delegation boundary to `git-post-merge-cleanup` (what to hand off, what to keep).

[`loop-controller`]: ../loop-controller/SKILL.md
[`git-post-merge-cleanup`]: ../../git/git-post-merge-cleanup/SKILL.md
