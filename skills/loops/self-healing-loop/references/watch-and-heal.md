# Watch-and-heal: sources, triage, and the HITL boundary

Detail for `self-healing-loop`. The SKILL.md body holds the 5-part contract, the
proof, and the steps; this file holds the three things that need room: where to
poll, how to tell an actionable error from noise, and the exact line between what
runs unattended and what always pages a human.

This is the reference instance behind **Loop Library #004 — production error
sweep**: a `/loop` poller that drains actionable errors into fix PRs and leaves
everything irreversible to a human.

## Contents
- [Poll-source options](#poll-source-options)
- [Actionable-vs-noise triage](#actionable-vs-noise-triage)
- [The HITL boundary table](#the-hitl-boundary-table)
- [The heal_log.md entry shape](#the-heal_logmd-entry-shape)

---

## Poll-source options

Pick the source(s) the project actually emits. Precedence: a source declared in
`.claude/profile.yaml` wins; otherwise detect from the repo's tooling. Each tick
reads the source, then fingerprints what it sees (normalized message + top stack
frame) so a known-open error isn't re-diagnosed every tick.

| Source | How a tick reads it | Fingerprint on | Notes |
|---|---|---|---|
| **CI status (pull)** | `gh run list --branch <b> --status failure --limit N`, then `gh run view <id> --log-failed` | failing job + first failing assertion | The cheapest, most deterministic signal. Re-running the run is the verifier. |
| **Error-log query (pull)** | The project's log CLI / API filtered to `level>=error` since the last tick (e.g. a `logcli`/cloud-logging query, or grep over a captured log) | normalized message + top frame | Time-window the query to "since last tick" so volume stays bounded. |
| **APM / error tracker (pull)** | Query the tracker API for new/unresolved issues since last tick | the tracker's own group id | Prefer the tracker's grouping over your own fingerprint when it exists. |
| **Alert / Channel / webhook (push)** | Consume a queued alert payload the scheduler dropped for this tick | the alert's dedupe key | Push sources can arrive between ticks; drain the queue, don't just read the latest. |

A pull source pairs naturally with `/loop <cadence>`. A push source still rides a
`/loop` tick — the tick drains whatever the channel queued since the last one.
For a standing, cross-session watcher, promote the `/loop` poller to a scheduled
cloud routine (`/loop` is session-scoped, ~3-day expiry, no catch-up).

## Actionable-vs-noise triage

Triage **before** spending a diagnose cycle. One bad triage burns an entire
reproduce+root-cause pass on a ghost. A noise verdict still gets a `heal_log.md`
entry — recording *why* it was skipped is how you avoid re-triaging it next tick.

| Signal | Verdict | Why / what the tick does |
|---|---|---|
| Reproducible defect in code this repo owns, reversible fix | **Actionable** | Proceed: reproduce → root-cause → fix on a branch → verify → PR. |
| Same error fingerprint already has an open fix PR | **Noise (known-open)** | Skip; log "known-open, PR #N". Don't re-diagnose. |
| Flaky / intermittent infra blip (one-off timeout, transient 5xx that self-cleared) | **Noise (flake)** | Log it; if it recurs across ticks past the no-progress N, escalate as a flaky-test finding, don't keep healing. |
| Third-party / upstream outage (their API down, their cert expired) | **Noise (external)** | Not ours to fix in code; log + escalate if it blocks. |
| Real defect but the only fix is prod-touching / irreversible | **HITL** | Reproduce + diagnose + propose, then **page the human** — see the boundary table. |
| Error volume spiking / a possible incident | **HITL** | Don't autonomously "heal" an incident. Surface it; humans run incident response. |

The actionable path is the only one that ends in an autonomous PR. Everything
else either logs-and-skips or escalates.

## The HITL boundary table

The load-bearing rule: **run unattended only the reversible, hard-verifier-backed
part.** The autonomous deliverable is *a PR a human merges*, never a changed
production system.

| Action | Unattended? | Boundary |
|---|---|---|
| Reproduce the error in a sandbox | ✅ yes | reversible, no live state touched |
| Fix the root cause on a dedicated branch | ✅ yes | branch only, never the default branch |
| Re-run the failing signal to verify (the proof) | ✅ yes | read-only / sandboxed re-run |
| Open or update a PR with cause + fix + green re-run | ✅ yes | the deliverable; a human reviews and merges |
| **Merge** the fix PR | ❌ HITL | never auto-merge a prod hotfix |
| **Deploy** a hotfix (even one line) | ❌ HITL | never auto-deploy; humans own the deploy |
| Mutate **production data** (backfill, cleanup, migration vs a real DB) | ❌ HITL | irreversible; human decision |
| Change **live infra / secrets / external APIs** | ❌ HITL | irreversible; human decision |
| Mute an alert / silence a check to make the tick clean | 🚫 forbidden | a *finding*, not a heal — see SKILL.md guardrails |

When the only available fix falls in an ❌ row, the loop's job ends at
**reproduced → diagnosed → fix proposed → human paged**. It does not proceed and
does not pretend the tick is clean.

## The heal_log.md entry shape

One entry per tick, append-only, so the watcher's behavior is auditable and the
next tick can read the last-seen fingerprints.

```md
## 2026-06-21T14:30Z — tick
- source: CI (gh run list, branch main)
- seen: 1 failure — fingerprint `TypeError: cannot read 'id' of undefined @ src/api/users.ts:42`
- triage: ACTIONABLE (defect in owned code, reversible)
- root cause: user lookup returns null on soft-deleted rows; delegated to diagnose-loop
- fix: branch fix/users-null-guard — guard + regression test
- verify: `npm test` re-run exits 0 (full gate green via fix-until-green)  ← PROOF
- PR: #214 (open, awaiting human merge)

## 2026-06-21T15:00Z — tick
- source: CI (gh run list, branch main)
- seen: 0 failures
- clean-log confirmation ✅
```

A quiet tick still writes the clean-log confirmation — that is the proof the
watcher was actually watching.
