# repo-cleanup-loop — classify / recover / remove algorithm

The per-pass substance. `loop-controller` owns the loop machinery and the
guardrail stack; this file owns the three things specific to weekly repo hygiene:
the classification + evidence rules, the recover-before-delete recipe, and the
delegation boundary to `git-post-merge-cleanup`.

## Contents
- [The inventory (default-FAIL)](#inventory)
- [Scan](#scan)
- [Classify — buckets + evidence rules](#classify)
- [Recover before delete (load-bearing)](#recover)
- [Remove one class with evidence](#remove)
- [Delegation boundary to git-post-merge-cleanup](#delegation)
- [AFK-safe vs pause](#afk)

---

## Inventory

One pass writes/updates a single inventory JSON — the proof artifact. One record
per item (branch, open PR, worktree, dangling ref). Default-FAIL: every record
starts `"reviewed": false` and only flips on classification + evidence.

```json
{
  "generated": "2026-06-21T09:00:00Z",
  "default_branch": "main",
  "items": [
    {
      "kind": "branch",            // branch | pr | worktree | ref
      "name": "feat/add-retry",
      "class": "safely-removable", // current | owned | safely-removable | needs-attention
      "evidence": "merged into main (git branch --merged)",
      "recovered": null,           // null, or where the work was salvaged to
      "reviewed": true
    }
  ]
}
```

Rules a reviewer checks: no record stays `"reviewed": false` at pass end; no
record is `"safely-removable"` without a non-empty `"evidence"`; any record whose
work was salvaged has a `"recovered"` pointer. Store it at a profile-defined path
(default `.claude/repo-cleanup-inventory.json`).

## Scan

Whole-repo state, read-only:

```bash
git fetch origin --prune                       # refresh remote-tracking refs
git branch -vv                                 # local branches + tracking status (gone?)
git branch --merged origin/$DEFAULT            # merged-into-default (local)
git branch -r --merged origin/$DEFAULT         # merged-into-default (remote)
git branch -r --no-merged origin/$DEFAULT      # context: still in flight
git worktree list                              # worktrees (first entry = main, never a candidate)
git for-each-ref --format='%(refname) %(committerdate:relative)' refs/heads
gh pr list --state open --json number,headRefName,isDraft,updatedAt,mergeable  # open PRs
```

`$DEFAULT` is resolved, never assumed `main`:
`git symbolic-ref -q --short refs/remotes/origin/HEAD | sed 's@^origin/@@'`.

## Classify

Bucket every scanned item. Evidence is mandatory to reach `safely-removable`.

| Bucket | Means | Evidence required | Action |
|---|---|---|---|
| **current** | active work (default branch, the checked-out branch, an open non-stale PR) | n/a | keep, mark reviewed |
| **owned** | someone's in-flight work — unmerged but live (recent commits, an open PR with activity) | n/a | leave, mark reviewed |
| **safely-removable** | merged into `$DEFAULT`, OR squash-merged with empty diff vs `$DEFAULT`, OR its work already recovered | the merge proof or the `recovered` pointer | eligible for removal this/next pass |
| **needs-attention** | ambiguous: gone-remote + unmerged, stale PR with unpushed work, worktree diff that doesn't match `$DEFAULT`, protected long-lived branch | n/a | HITL — surface, do not act |

Evidence rules, concretely:

- **Merged-local branch** — present in `git branch --merged origin/$DEFAULT` and
  not `$DEFAULT`. Evidence = that membership.
- **Squash-merged** — absent from `--merged` but `git diff $DEFAULT...<branch>`
  is empty. Evidence = the empty diff. This is the one case where `-D` is later
  justified.
- **Gone remote-tracking ref** — `git branch -vv` marks it `[gone]`. Removable
  **only if also merged**; `[gone]` + unmerged is `needs-attention`, never an
  autonomous delete.
- **Safe worktree** — branch merged into `$DEFAULT`, or uncommitted changes all
  already on `$DEFAULT`. Evidence = the merge/empty-diff check, not eyeballing.
- **Stale open PR** — open with no activity past a threshold. Closing a PR is a
  human/communication act → `needs-attention`, never autonomous.
- **Protected branches** (`$DEFAULT`, `develop`, `staging`, `production`) — never
  removable, regardless of merge status.

## Recover

**The load-bearing safety step. Recovery happens before any delete, every time.**

An item that *looks* removable but holds commits not on `$DEFAULT` is valuable
work, not debris. Before it can become `safely-removable`, salvage the work and
record where it went:

1. Detect unmerged commits: `git log --oneline origin/$DEFAULT..<branch>` — any
   output means there is work not on the default branch.
2. If there is unmerged work, it is **not** safely removable yet. Either:
   - it is genuinely live → reclassify `owned` (leave it), or
   - the human confirms it should be retired → **recover first**: tag or branch
     it as a recovery ref so the commits are reachable without the original
     branch —
     ```bash
     git tag recovery/<name> <branch>          # or: git branch recovery/<name> <branch>
     git log --oneline origin/$DEFAULT..<branch> > .claude/recovery/<name>.log
     ```
     set `"recovered": "recovery/<name>"` on the record, *then* it is eligible.
3. `git reflog` is the durable backstop — but a deliberate recovery ref + log is
   the contract, not an accident of reflog retention.

Never skip recovery to "tidy faster." A clean inventory bought by deleting
unrecovered work is a finding, not a win.

## Remove

Remove **exactly one class** of `safely-removable` items per pass, with evidence,
then re-scan. Order matters — worktrees before their branches (else
`git branch -d` refuses a branch checked out elsewhere). Safety floor:

- Lowercase `git branch -d` (refuses unmerged) **before** `-D`. `-D` only on a
  confirmed empty-diff squash-merge or explicit human request.
- Never `git push --force`; never `--force`-remove a worktree with genuinely
  unmerged work, unattended.
- For the branch/worktree/ref classes, the destructive commands and their
  ordering are `git-post-merge-cleanup`'s job — delegate (below) rather than
  re-typing them here.

## Delegation

The post-merge classes overlap exactly with `git-post-merge-cleanup`. **Delegate
them; do not re-implement.**

| Hand off to `git-post-merge-cleanup` | Keep in this loop |
|---|---|
| fully-merged local branch deletion | the default-FAIL whole-repo inventory |
| gone remote-tracking ref pruning | open-PR + commit-trail scan |
| safe-worktree removal + ordering | recover-before-delete gate |
| the `-d`-before-`-D` / `--force` floor | one-class-per-pass cadence |
| its plan/confirm presentation | the weekly schedule (`/loop` / `/schedule`) |

Recipe: run `git-post-merge-cleanup --dry-run` to get its classified plan for the
branch/ref/worktree classes, fold that into this loop's inventory (recording its
evidence), run the recover step on anything it flags `needs attention`, then have
it execute the confirmed class. This loop never re-derives branch-merge logic —
it consumes `git-post-merge-cleanup`'s and wraps it in the recurring,
evidence-gated, recover-first discipline that the one-shot does not provide.

## AFK

| AFK-safe unattended (within the boundary) | HITL — pause for a human |
|---|---|
| classify the inventory (read-only scan) | delete/remove **anything** with unmerged work |
| delete a branch proven merged into `$DEFAULT` | force-delete (`-D`) without confirmed empty-diff |
| prune a gone remote-tracking ref that is **also** merged | close/comment on an open PR |
| remove a worktree proven safe (merged / empty-diff) | act on a `needs-attention` item |
| create a `recovery/<name>` ref + log | `git push --force` / rewrite shared history |
| re-scan + update the inventory JSON | touch a protected branch (`develop`/`staging`/`production`) |

Within the safe column the loop runs on its weekly cadence unattended. The moment
an item lands in `needs-attention` — or removal would touch unrecovered work —
stop the pass and surface it. The full guardrail stack (caps, no-progress,
budget enforcement, checkpoint commits) is inherited from `loop-controller` →
`references/safety.md`; this file only adds the cleanup-specific evidence and
recovery rules.
