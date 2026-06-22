---
name: self-healing-loop
version: 1.0.0
description: >-
  Watch a production or CI error signal on a cadence and, when an ACTIONABLE
  error appears, trace its root cause, fix it in a branch, verify the failing
  signal now passes, and open a PR for a human to merge — never auto-deploy and
  never auto-merge a prod hotfix. One pass polls the error source: actionable
  error present means hand the hard diagnosis to diagnose-loop, fix the cause,
  verify, open or update a PR; no actionable error means record a clean-log
  confirmation. Use when you want an unattended watcher over CI status, error
  logs, alerts, or an observability feed that heals reversible failures and
  escalates the rest. Trigger on "watch the logs and fix errors", "self-heal CI",
  "production error sweep", "poll for failures and open a fix PR", "auto-fix the
  red build", "watch CI and heal it", "error sweep loop", "auto-heal production
  errors", "/self-healing-loop". A configuration of loop-controller.
requires_claude_code: true
min_plan: starter
disable-model-invocation: true
allowed-tools: ["Read", "Edit", "Bash", "Grep", "Glob"]
composes_with: ["loop-controller", "observability-agent", "diagnose-loop", "fix-until-green", "loop"]
spawned_by: []
---

# self-healing-loop

> **A configuration of [`loop-controller`].** That skill supplies the loop
> machinery — primitive selection, the full guardrail stack, state
> externalization. This skill supplies the three things specific to "watch and
> heal": a **poll cadence** over an external error signal, a **default-FAIL proof
> of the error gone** (a re-run, not a hope), and a **hard HITL boundary** at any
> prod-touching or irreversible fix. Read `loop-controller` for the guardrails;
> they're inherited, not repeated here.
>
> **Why `disable-model-invocation`:** this loop edits and commits code on its own
> and opens PRs on a schedule. You want to *type* `/self-healing-loop` (or wire
> it under `/loop`) — not have Claude silently start an autonomous heal loop
> because a log line looked alarming.

## The 5-part contract

| Part | This loop |
|---|---|
| **trigger** | a scheduled poll tick (via `/loop`) over an error source — red CI, an error-log query, an alert/Channel push — or an explicit `/self-healing-loop` |
| **action** | ONE pass: poll the source → triage actionable vs noise → if actionable, reproduce + root-cause (hand the hard diagnosis to [`diagnose-loop`]) → fix the cause in a branch → **verify** → open/update a PR; else record a clean-log confirmation |
| **proof** | the error is **resolved AND verified** — the re-run of the failing signal now passes / the log query is clean — default-FAIL: assume UNRESOLVED until the re-run proves it. Artifact = the green re-run output (or, on a quiet tick, a timestamped clean-log confirmation) |
| **memory** | `heal_log.md` (one entry per tick: signal seen, triage verdict, root cause, the PR opened, the verifying re-run) + the fix branch's git history; the last-seen error fingerprint so a known-open error isn't re-triaged each tick |
| **stop** | the verifying re-run passes and a PR is open (or the tick is clean) **OR** iteration cap **OR** no-progress for N ticks on the same error **OR** budget cap **OR** an HITL checkpoint is hit (a prod-touching / irreversible fix) — pause for the human, never proceed |

## The proof: the error is gone, and a re-run says so

"Healed" is **not** "I edited the file the stack trace pointed at." It is the
**failing signal re-run and observed passing** — the same test re-run green, the
same log query returning zero matches, the same endpoint returning 200. Assume
**unresolved** until that re-run exists; that is the default-FAIL stance. A fix
that is plausible but never re-verified is a guess, and a guess shipped to a PR
wastes the reviewer's time and your budget.

On a quiet tick (no actionable error), the proof is a **clean-log confirmation**:
a timestamped `heal_log.md` entry recording the source polled, the query run, and
the zero/green result. A watcher that records nothing on quiet ticks can't prove
it was actually watching.

## The HITL boundary is load-bearing

This loop runs unattended only inside the **reversible, hard-verifier-backed**
envelope: reproduce in a sandbox, fix on a branch, verify, open a PR. Everything
that touches live state is an **HITL checkpoint** — pause and surface, never act:

- **never auto-deploy** a hotfix (even a "one-line" one),
- **never auto-merge** a PR that fixes a prod error,
- **never** mutate production data, live infra, secrets, or external APIs to
  "heal" — those are human decisions.

The autonomous deliverable is *a PR a human merges*, not a healed production
system. When the only fix is irreversible (a data backfill, a rollback deploy),
the loop's job ends at: reproduced, diagnosed, fix proposed, **human paged**. The
full poll-source options, the actionable-vs-noise triage table, and the HITL
boundary table are in [`references/watch-and-heal.md`](references/watch-and-heal.md).

## Step 1 — Poll the error source, fingerprint what you see

Each tick, read the configured source (precedence: `.claude/profile.yaml` if it
declares one, else the project's CI/log tooling — the same feeds the
[`observability-agent`] instruments): CI status (`gh run list`), an error-log
query, or an alert/Channel push. Compute a stable **fingerprint** for
each error (normalized message + top frame) and compare against the last-seen set
in `heal_log.md` so a known-open error isn't re-diagnosed every tick. Source
options and example queries: [`references/watch-and-heal.md`](references/watch-and-heal.md).

## Step 2 — Triage: actionable vs noise

Not every red line earns a fix. **Actionable** = a reproducible defect in code
this repo owns, with a fix that fits the reversible envelope. **Noise** = a flaky
infra blip, a known-open error already in a PR, a third-party outage, or a signal
whose fix is inherently prod-touching (→ straight to HITL). Triage first; one
bad triage spends an entire diagnose cycle on a ghost. The triage table is in the
reference file. A noise tick still gets a `heal_log.md` entry.

## Step 3 — Reproduce and root-cause (delegate the hard part)

For an actionable error, **build a fast deterministic reproduction first**, then
trace the *cause*, not the first frame. This is exactly [`diagnose-loop`]'s
discipline — **invoke it**, don't re-implement it. Its Phase-1 binary-signal
reproduction is the thing that gets skipped under "just ship the fix" pressure
and the thing that makes the verify in Step 4 meaningful. Record the cause in
`heal_log.md`.

## Step 4 — Fix on a branch, verify, open the PR

Fix the root cause on a dedicated branch (never on the default branch). Then
**verify**: re-run the failing signal — for a red build, this is where you
delegate to [`fix-until-green`] to drive the whole gate (test + lint + typecheck)
clean, not just the one failing test. The verifying re-run output **is** the
proof. Commit a checkpoint, open or update a PR describing the cause, the fix,
and the green re-run, and **stop there** — the human merges. Append the tick's
outcome (PR link + verifying run) to `heal_log.md`.

## Guardrails specific to this loop

Inherits the full stack from `loop-controller` → `references/safety.md`. The caps
this loop sets:

- **Iteration cap** — bound the *ticks* (the `/loop` cadence is itself a cap:
  it's session-scoped and expires) and the heal attempts *within* a tick (read
  from `.claude/profile.yaml` if set). Hitting either is a *stop-and-escalate*.
- **No-progress detection** — if the **same error fingerprint** survives **N
  consecutive ticks** without the verifying re-run going green, stop and surface
  it. The same production error un-healed three ticks running means the fix is
  wrong or the cause is misdiagnosed — page the human, don't keep re-trying.
- **Budget cap** — a polling watcher can run for hours; each actionable tick
  spends a full diagnose + fix cycle. Watch `/cost`; terminate at the ceiling.
  Quiet ticks should be cheap — don't re-diagnose known-open errors.
- **HITL before anything irreversible** — the load-bearing boundary above. Any
  prod-touching / irreversible fix pauses for the human (`loop-controller`
  guardrail 4). Never auto-deploy, never auto-merge a prod hotfix.
- **Never weaken the signal to make the tick clean.** Forbidden, each a *finding*:
  muting an alert, deleting the failing test, narrowing a log query to hide the
  error, or marking healed without the verifying re-run. A clean log that came
  from silencing the check is not a heal.

## Choosing the driver primitive

Per `loop-controller` Step 1, this is a **watch / poll** loop, so the primitive is
**`/loop`**, not `/goal` — it watches an external signal change on a cadence
rather than pushing one task to a finish line:

- **Canonical — `/loop` poller.** `/loop 30m /self-healing-loop` (or the cadence
  the source warrants) runs one heal pass per tick. `/loop` is session-scoped,
  expires in ~3 days, and does no catch-up — re-arm it for a standing watcher
  (`references/primitives.md`). For a true always-on schedule across sessions,
  promote to a scheduled cloud routine.
- **Inside a tick**, the *heal* step degenerates to a finish-line loop — that's
  where [`fix-until-green`] (a `/goal` or Stop-hook loop) drives the red build to
  green as this loop's verifier.

## How this differs from its neighbors

- **vs. [`diagnose-loop`]** — diagnose-loop is the *inner* reproduce-and-root-cause
  discipline for one hard bug. This is the *outer* watch→heal→verify→PR cycle: it
  adds the polling cadence, the actionable-vs-noise triage, and the prod HITL
  boundary, and **invokes** diagnose-loop for the diagnosis it can't shortcut.
- **vs. babysit (review-and-revise)** — babysit polls a *PR's review comments* and
  revises the diff. This polls *production / CI error signals* and opens a *new*
  fix PR. Different source, different deliverable; both are `/loop` pollers.

## Reference files

- [`references/watch-and-heal.md`](references/watch-and-heal.md) — the poll-source
  options (CI status, error-log queries, an alert/Channel/webhook push) with
  example commands, the actionable-vs-noise triage table, and the HITL boundary
  table (what runs unattended vs what always pages a human).

[`loop-controller`]: ../loop-controller/SKILL.md
[`fix-until-green`]: ../fix-until-green/SKILL.md
[`diagnose-loop`]: ../../workflows/diagnose-loop/SKILL.md
[`observability-agent`]: ../../roles/observability-agent/SKILL.md
