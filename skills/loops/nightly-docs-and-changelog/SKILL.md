---
name: nightly-docs-and-changelog
version: 1.0.1
description: >-
  Run a nightly sweep that keeps an existing repo's docs and changelog from
  rotting: diff the code since the last run, bring the docs for the changed
  surface back in line with the implementation, append every user-relevant
  change to CHANGELOG.md (or record a no-change night), and open ONE reviewable
  PR — never auto-merging. Scheduled to survive laptop-off via a cloud routine /
  Desktop scheduled task, NOT a session-scoped loop. Use when you want docs and
  the changelog kept current automatically while you sleep, when docs keep
  drifting behind code, when the changelog is always stale, or when you want a
  morning PR of doc+changelog updates to review. Trigger on: "keep the docs
  current", "nightly docs sweep", "update the changelog nightly", "docs keep
  drifting", "stale changelog", "overnight docs", "stop the docs rotting",
  "nightly doc PR". Drafts AFK; merges HITL. A configuration of
  loop-controller.
requires_claude_code: true
min_plan: starter
disable-model-invocation: true
allowed-tools: ["Read", "Write", "Edit", "Bash", "Grep", "Glob"]
composes_with: ["loop-controller", "docs-agent", "git-pr", "schedule"]
spawned_by: []
---

# nightly-docs-and-changelog

> **A configuration of [`loop-controller`].** That skill supplies the loop
> machinery — primitive selection, the full guardrail stack, state
> externalization. This skill supplies the three things specific to "keep an
> existing repo's docs+changelog from rotting on a nightly cadence": the
> **per-night recipe** (it diffs since the last run and authors the doc +
> changelog updates for that surface itself, following the documentation
> conventions [`docs-agent`] defines — docs-agent is the orchestrator's
> build-phase role and is not user-invocable on a schedule), the
> **mechanical proof** (docs match the changed surface AND every user-relevant
> change is recorded, ending in a reviewable PR), and the **HITL boundary** (it
> opens a PR and stops — it never merges docs). Read `loop-controller` for the
> guardrails; they're inherited, not repeated here.
>
> **Why `disable-model-invocation`:** this loop edits docs, writes the changelog,
> commits, and opens a PR on its own, on a schedule. It is user-scheduled — you
> *set it up* once (or type `/nightly-docs-and-changelog`), not have Claude
> silently start rewriting docs because some code changed during the day.

## The 5-part contract

| Part | This loop |
|---|---|
| **trigger** | a nightly cron fire from the scheduled routine (default ~02:00 local), or an explicit `/nightly-docs-and-changelog` to run one sweep now |
| **action** | ONE sweep: read the last-run marker → `git diff <marker>..HEAD` → for the changed surface, author the doc updates yourself (following [`docs-agent`]'s conventions) → classify each change user-relevant vs internal → append user-relevant ones to `CHANGELOG.md` (or write a no-change record) → advance the marker → open ONE PR via [`git-pr`] |
| **proof** | the docs for the changed surface match the current implementation **AND** every user-relevant change since the marker is recorded in `CHANGELOG.md` (or a no-change night is recorded), surfaced as a reviewable **docs/changelog diff + PR** — default-FAIL: assume docs are stale and the changelog incomplete until verified against the diff since the last run |
| **memory** | the **last-run marker** (a git tag/ref or `.claude/docs-sweep-last`), `CHANGELOG.md`, git history, and the open PR thread — all durable across nightly fires and laptop-off gaps |
| **stop** | proof met → PR opened (then **HITL** — stop, never merge) **OR** no diff since the marker (record a no-change night, no PR) **OR** iteration/pass cap **OR** no-progress for 3 nights (same surface still drifting) **OR** budget cap **OR** an HITL checkpoint is hit |

## The proof: docs current AND changelog complete, default-FAIL

"Current" is not "the docs looked fine last week." It is **two conditions
observed together against the diff since the last run**: the docs covering the
*changed surface* match the implementation, **and** every *user-relevant* change
since the marker has a `CHANGELOG.md` entry (a quiet night gets an explicit
no-change record so a skipped night is distinguishable from a missed one).
Assume **stale** until a fresh sweep proves both — that's the default-FAIL stance,
and it's why every night re-diffs from the marker rather than trusting yesterday.

Name the artifact explicitly: the **docs/changelog diff plus the PR** the sweep
opens. The PR *is* the proof a human reviews; an empty diff with a no-change
record is a valid (and common) outcome.

## Step 1 — Diff since the last run

The whole sweep is scoped by the last-run marker. Read it, diff `marker..HEAD`,
and that diff — nothing else — defines tonight's work surface. No marker yet
(first run) means bootstrap from the last release tag or a sensible recent
baseline, not the whole history. The marker mechanism (git tag vs `.claude/`
file), how to advance it atomically only after the PR opens, and how to recover a
missed night (the marker, not the clock, defines the window — a laptop-off gap is
just a wider diff next run) are in `references/scheduling.md`.

## Step 2 — Classify user-relevant vs internal, then write the updates

Two distinct outputs come off the same diff:

- **Docs that must track the code** — for the changed surface, author the doc
  updates yourself (you hold Write/Edit), following the documentation conventions
  [`docs-agent`] establishes for this repo. docs-agent is the orchestrator's
  build-phase doc role — `disable-model-invocation`, dispatched only inside a
  contract-first build with a lead, contracts, and an ownership map — so a
  user-scheduled nightly sweep on an already-shipped repo reuses its
  *conventions*, not its dispatch. This loop adds the *scheduling, diff-scoping,
  and proof*, and matches docs-agent's house style rather than inventing a second
  one.
- **The changelog** — only **user-relevant** changes get an entry. A new flag,
  a behavior change, a fixed user-facing bug, a breaking change: yes. An internal
  refactor, a test-only change, a lint fix, a dependency bump with no user-visible
  effect: no. The exact user-relevant-vs-internal rubric (with examples) is in
  `references/scheduling.md`.

## Step 3 — Open ONE PR, then stop (HITL)

Commit the docs+changelog changes and open **one** PR via [`git-pr`] titled for
the sweep date and summarizing what moved. Then **stop**. This loop **never
auto-merges** — docs and changelog wording is a human judgment call, and a PR
opened at 02:00 is meant to be reviewed at 09:00, not merged in the dark. One PR
per night keeps the review unit small; don't batch multiple nights into one PR.

## How this differs from its neighbors

- **vs [`docs-agent`]** — docs-agent is a **build-phase role**: it writes the docs
  *for a build in progress*, dispatched by the orchestrator alongside the other
  role agents. This skill is the **recurring nightly sweep** that keeps an
  *already-shipped* repo's docs and changelog from rotting over time. It owns the
  *cadence, the diff-since-last-run window, the changelog discipline, the
  default-FAIL proof, and the PR/HITL boundary* — and authors the doc updates
  itself in docs-agent's house style (docs-agent is orchestrator-only and not
  user-invocable, so this loop reuses its *conventions*, not its dispatch).
  Because the nightly sweep runs **outside** a parallel orchestrated build —
  there is never a concurrent docs-agent — editing the `docs/` + `CHANGELOG.md`
  that docs-agent owns *at build time* creates no live ownership conflict; the
  two never run at once, and this loop follows the same conventions. Remove this
  skill and docs-agent still can't keep your repo current on its own; nothing
  schedules it or scopes it to "what changed since last night."
- **vs [`git-pr`]** — git-pr is the PR mechanics; this loop calls it as its final
  step, it doesn't reinvent PR creation.
- **vs a bare `/loop`** — see Step 4: `/loop` is the wrong primitive for a nightly
  cadence, which is the whole reason this skill schedules differently.

## Step 4 — Schedule it to survive laptop-off (the routine, NOT /loop)

Per `loop-controller` Step 1, the primitive choice is load-bearing here and it is
**not `/loop`**. `/loop` is session-scoped, expires after ~3 days, and does not
catch up on missed fires — a laptop closed overnight kills it, which is exactly
the window this loop must run in. So the primitive is a **cloud routine /
Desktop scheduled task** (via `/schedule`) that fires on a real cron independent
of any open session and survives the machine being off. The full `/loop`-vs-
scheduled-routine reasoning lives in `loop-controller`'s
`references/primitives.md` — don't re-document it. The exact `/schedule` setup,
the cron line, and what the routine prompt invokes are in
`references/scheduling.md`.

## Guardrails specific to this loop

Inherits the full stack from `loop-controller` → `references/safety.md`. The caps
this loop sets:

- **Pass cap per night** — one sweep = one PR; cap the within-night iterations
  (default ~10) so a pathological diff can't burn the whole budget before
  morning. Hitting it is a *stop-and-open-a-partial-PR-and-flag*, not a license to
  hand-wave the docs.
- **No-progress detection** — if the **same changed surface** keeps drifting
  across **3 consecutive nights** (docs re-edited but never converge, or the same
  file shows up undocumented night after night), stop and surface it. Three nights
  on one surface means it needs a human, not a fourth automated pass.
- **Budget cap** — a nightly routine runs unattended for weeks; enforce a
  token/cost ceiling that *terminates* the sweep (read it from
  `.claude/profile.yaml` when present), not just warns.
- **HITL is the exit, not a checkpoint mid-loop.** Opening the PR is where this
  loop hands off to a human — it **never merges**, never force-pushes, and never
  rewrites a published CHANGELOG entry. Drafting docs + changelog and opening a PR
  is reversible and AFK-safe; merging is the human's call.
- **Never cheat the proof.** Don't advance the marker without opening a PR (that
  silently swallows a night's changes), don't drop a user-relevant change to keep
  the changelog short, and don't mark docs "current" without checking them against
  the diff. A clean night that came from skipping the diff is a *finding*, not a
  win.

## Choosing the driver primitive

The scheduled routine (`/schedule`) is the outer engine — it fires the sweep on
cron and survives laptop-off. Within a night, the sweep pushes to a finish line
(docs current + changelog complete + PR opened), provable from the diff and the
`gh` PR result, so the inner pass can run under auto mode unattended **inside the
reversible boundary** (draft + PR only). The loop as a whole has no `/goal`
finish line across nights — it watches the repo evolve and sweeps each night
until you unschedule it.

## Reference files

- `references/scheduling.md` — the per-night algorithm and the doc-writing
  conventions; the last-run marker mechanism (git tag vs `.claude/docs-sweep-last`,
  advancing it atomically, recovering a missed night); the user-relevant-vs-
  internal changelog rubric with examples; the no-change-night record format; and
  the `/schedule` routine setup (cron line, routine prompt, what survives
  laptop-off).

[`loop-controller`]: ../loop-controller/SKILL.md
[`docs-agent`]: ../../roles/docs-agent/SKILL.md
[`git-pr`]: ../../git/git-pr/SKILL.md
