# Scheduling and per-night mechanics

The body states the contract, the proof, and the boundaries. This reference is
the operational detail: the per-night algorithm, the last-run marker, the
changelog classification rubric, and the `/schedule` routine setup. The loop
*machinery* (guardrail stack, primitive mechanics, state-externalization
discipline) is not repeated here — it lives in `loop-controller`'s
`references/safety.md` and `references/primitives.md`.

## Contents
- [The per-night algorithm](#algorithm)
- [The last-run marker](#marker)
- [User-relevant vs internal — the changelog rubric](#rubric)
- [The no-change-night record](#no-change)
- [The /schedule routine setup](#schedule)
- [AFK-safe vs pause](#afk)

---

## Algorithm

One nightly fire = one sweep = (at most) one PR:

1. **Read the marker.** Resolve the last-run point (see below). No marker → first
   run; bootstrap from the latest release tag, or a recent baseline commit if
   there are no tags. Do not diff all of history.
2. **Diff the window.** `git diff <marker>..HEAD --stat` and the full patch. This
   diff is the *entire* work surface for the night — ignore anything outside it.
   Empty diff → jump to the no-change record (step 7), open no PR.
3. **Identify the changed doc surface.** Map changed code paths to the docs that
   describe them (README sections, `docs/`, API references, usage guides,
   inline-doc-derived pages). The mapping heuristics are the project's own; read
   `.claude/profile.yaml` for a declared docs root when present.
4. **Author the doc updates (in `docs-agent`'s house style).** For the changed
   surface, write the doc updates yourself — `docs-agent` is the orchestrator's
   build-phase doc role (`disable-model-invocation`, dispatched only inside a
   contract-first build), so this user-scheduled loop reuses its *documentation
   conventions*, not its dispatch. Scope the work to the diff, then re-read the
   updated docs and confirm they match the implementation in the diff (the
   default-FAIL check: assume stale until checked).
5. **Classify each change** user-relevant vs internal (rubric below).
6. **Append user-relevant entries to `CHANGELOG.md`.** Follow the project's
   existing changelog style (Keep a Changelog, or whatever the file already uses —
   match it, don't impose). One entry per user-relevant change, grouped under the
   right heading (Added / Changed / Fixed / Deprecated / Removed / Security).
   Never rewrite an already-published/released entry — only append to the
   unreleased section.
7. **No-change record** when the diff was empty or held only internal changes:
   write the explicit record (below) so a quiet night is distinguishable from a
   missed one. No PR is opened on a no-change night.
8. **Advance the marker** — but only *after* the PR is opened (step 9), atomically,
   so a crash mid-sweep doesn't silently swallow the window. On a no-change night,
   still advance the marker (the window was genuinely processed).
9. **Open ONE PR** via `git-pr` (title: `docs: nightly sweep <YYYY-MM-DD>`; body
   summarizes the doc surfaces touched + the changelog entries added). Then
   **stop** — HITL. Never merge.

## Marker

The marker defines the window; **the marker, not the wall clock, is the source of
truth**. A laptop-off gap just produces a wider diff on the next successful run —
no night is "missed" as long as the marker only advances on a completed sweep.

Two acceptable implementations (pick one per repo; record the choice in
`.claude/profile.yaml` if it has a slot):

- **Git tag** — e.g. a moving `docs-sweep-last` tag (or a dated tag
  `docs-sweep/2026-06-21`). Visible in `git log`, survives clone. Advance with
  `git tag -f docs-sweep-last HEAD` after the PR opens.
- **A `.claude/docs-sweep-last` file** holding the last-swept commit SHA. Simpler,
  but only as durable as the working tree; commit it (or keep it out of the PR and
  reset it deliberately) so it isn't lost.

Advancing atomically means: open the PR first, then move the marker, in that order
— if the PR step fails, the marker stays put and tomorrow re-tries the same
window. Never advance the marker without an opened PR or a recorded no-change
night.

## Rubric

A change earns a `CHANGELOG.md` entry **only if a user of the software would
notice or care.** "User" = whoever consumes this repo's output (end users, API
consumers, library importers, operators), not its maintainers.

**User-relevant (entry required):**

- New or removed user-facing feature, command, flag, endpoint, or config option
- A behavior change a user could observe (default changed, output format changed,
  error message changed in a way that matters)
- A user-facing bug fix
- A breaking change (always — and call it out as BREAKING)
- A security fix with user impact
- A deprecation users must act on
- A dependency bump that changes a runtime requirement (min Node/Python version,
  a new system dep)

**Internal (no entry — docs may still need updating):**

- Pure refactor with identical observable behavior
- Test-only changes, CI/workflow changes, lint/format-only diffs
- Internal dependency bumps with no user-visible effect
- Code comments, internal docstrings, dev tooling
- Performance work *unless* it crosses a documented SLO/limit a user relies on
  (then it's user-relevant — note the before/after)

When genuinely unsure, lean toward an entry but keep it terse; a spurious "Changed:
internal logging" is cheaper to delete in review than a missed breaking change is to
recover. Borderline calls are exactly what the morning PR review is for.

## No-change

A quiet night still leaves a trace, so a skipped night is never confused with a
missed one. Append (do not PR) a one-line record to a sweep log (e.g.
`.claude/docs-sweep-log` or a comment in the changelog's unreleased section,
matching the project's convention):

```
2026-06-21  no user-relevant changes since 2026-06-20 (marker a1b2c3d → e4f5g6h); docs verified current; no PR
```

Advance the marker, open no PR, end the sweep.

## Schedule

The primitive is a **scheduled cloud routine / Desktop scheduled task** via
`/schedule`, **not** `/loop` — `/loop` is session-scoped, expires after ~3 days,
and does not catch up on missed fires, so a laptop closed overnight kills exactly
the run this loop needs. The full reasoning is in `loop-controller`'s
`references/primitives.md`; this is just the setup.

Create the routine (one-time):

```
/schedule create
  name: nightly-docs-and-changelog
  cron: 0 2 * * *           # 02:00 daily; adjust to your timezone / quiet window
  prompt: /nightly-docs-and-changelog
```

What survives laptop-off: a **cloud routine** runs server-side independent of any
open session — the canonical choice when the machine may be off at fire time. A
**Desktop scheduled task** runs locally and only fires when the machine is awake;
acceptable if the machine is always on, but the marker-defined window (above) is
what makes a missed local fire harmless — the next successful run just sweeps a
wider diff.

To run a single sweep on demand without waiting for cron, invoke
`/nightly-docs-and-changelog` directly; it performs exactly one sweep against the
current marker and exits.

## AFK

Within the reversible boundary, the whole sweep is AFK-safe — that's the point of
running it overnight:

| Action | AFK-safe? |
|---|---|
| Diff since marker, read code + docs | yes |
| Edit the docs for the changed surface | yes (reversible, on a branch) |
| Append `CHANGELOG.md` entries (unreleased section) | yes |
| Commit + push the sweep branch | yes (own branch, fast-forward) |
| Open ONE PR | yes — this is the handoff point |
| Advance the marker (after PR opens) | yes |
| **Merge the PR** | **no — never, HITL** |
| **Rewrite a published/released changelog entry** | **no — append-only** |
| **Force-push a shared branch** | **no — HITL** |

The exit of every successful night is an opened PR awaiting human review. The loop
does not act past that line.
