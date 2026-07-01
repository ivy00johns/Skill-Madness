---
name: living-plan
version: 1.1.0
description: |
  Document and set up the living-plan convention: a front door (START-HERE.md), a
  strategic doc, a tactical ledger, and a frontier doc, wired to an intake loop so
  reports become tracked entries rather than rotting. Use when the user says "set up
  a living plan", "make this plan a living doc", "organize project plans", "give this
  project a planning front door", "stop my docs from rotting", or wants to establish
  a report-to-ledger intake loop on a project.
requires_agent_teams: false
requires_claude_code: true
min_plan: starter
owns:
  directories: []
  patterns: []
  shared_read: ["*"]
allowed-tools: ["Read", "Write", "Edit", "Glob", "Grep", "Bash"]
composes_with: ["plan-intake", "plan-builder", "repo-deep-dive", "work-item-brief"]
spawned_by: []
---

# Living Plan

> **Purpose:** Make plans that stay alive. A living plan has a single front door, three
> canonical documents, and one intake loop. Reports become tracked work — they never just rot.

## The Convention

A living plan has **three layers + one front door + one intake loop**.

### 1. Front door — `START-HERE.md` (one screen)

The single place to land. Contains:

- **Status at a glance** — current milestones or waves and their state. A few lines, updated regularly.
- **Ownership map** — which docs are canonical (edit these), which are frozen reference (read, don't edit), and which are archived (history, superseded). One-line description per doc.
- **How work flows in** — one sentence pointing to the intake loop.

Keep it to one screen. If it grows longer, something belongs in one of the canonical docs instead.

### 2. Strategic doc — `BUILD-PLAN.md` or `PLAN.md`

The roadmap: waves or milestones with their scope and exit criteria, plus a **closure log** that records what shipped and when. The strategic doc answers "where are we going and what have we finished?"

### 3. Tactical ledger — `docs/REMAINING-WORK.md` (+ `docs/COMPLETED-WORK.md`)

Every **open / in-progress** item, ID'd, prioritized, and sourced. Must document its own entry format and ID scheme at the top so new items are formatted consistently. The tactical ledger answers "what exactly needs to be done **next**?"

Entry shape (adapt to project conventions):

| ID | Priority | Wave | Area | Source | Summary | Status | Owner |
|----|----------|------|------|--------|---------|--------|-------|

IDs are stable and never reused. Priority (P0–P3 or equivalent), Wave/Phase, and Source are the minimum useful columns.

**Keep the open ledger lean.** Completed rows are the single biggest source of bloat — a mature project accumulates hundreds of `done` rows, and every session that reads the ledger pays for all of them in tokens for zero planning value. So the tactical layer is **two files**:

- `docs/REMAINING-WORK.md` — open + in-progress only (the to-do list, stays short and cheap to load).
- `docs/COMPLETED-WORK.md` — the **completed archive**: every `done` row, verbatim, append-only. History is preserved in full; it just lives where it doesn't tax the working doc.

The archive is the *tactical* record (every EM-### row). It complements — does not duplicate — the strategic **closure log** in the build plan (one line per wave/milestone close). Both exist: the closure log is the digest, the archive is the detail. The open ledger's header points to both so nothing feels lost. See **The Completion Sweep** below for how rows move.

### 4. Frontier doc — `docs/FUTURE.md`

Items explicitly out of scope for the current roadmap. Keeps them from cluttering the tactical ledger while ensuring they aren't lost. Short, updated as scope decisions are made.

### Small-project collapse

Small projects may collapse layers 2–4 into a single file (e.g. one `PLAN.md` with sections for roadmap, open items, and out-of-scope ideas). Always keep the front door and the intake loop — those are non-negotiable.

## The Intake Loop (the load-bearing rule)

Reports don't rot here. Any finished report — deep dive, audit, skill-review, QA findings — enters the living plan via this loop:

```
report  →  plan-intake skill  →  proposed entries  →  human approval  →  ledger + closure log
```

The rule: **every report-producing workflow ends by proposing entries.** `repo-deep-dive` invokes `plan-intake` on its gap/integration findings. Audit and skill-review outputs go through `plan-intake` before they're filed. Nothing is "done" until it has either landed in the ledger or been explicitly dismissed.

`plan-intake` is fail-closed: nothing writes to the ledger without explicit human approval.

## The Completion Sweep (the other load-bearing rule)

Intake is one half of keeping the ledger honest; the **completion sweep** is the other. Intake brings open work *in*; the sweep moves finished work *out*. Without it, the open ledger grows without bound and every future read gets more expensive for less signal — the exact failure the two-file split exists to prevent.

The rule: **when an item reaches `done`, it does not stay in the open ledger.** It moves to the completed archive in the same motion that marks it done.

```
item ships  →  flip status to done  →  move the row to docs/COMPLETED-WORK.md
            →  add/confirm a one-line entry in the closure log (BUILD-PLAN.md)
```

Three places update, each with a distinct job:

1. **`docs/REMAINING-WORK.md`** — the row is *removed* (it's no longer "remaining").
2. **`docs/COMPLETED-WORK.md`** — the row is *appended*, verbatim, in ID order. The full detail (what shipped, commit, caveats) is preserved here, not deleted.
3. **`BUILD-PLAN.md` closure log** — gets the strategic one-liner (date · wave/item · result) if this completion closes a wave or is otherwise worth the digest. Per-item rows don't each need a closure-log line; wave closes do.

**When to run the sweep:** batch it, don't thrash. Sweep at a natural close — when a wave/PR lands, when `plan-intake` runs (it sweeps as a final step — see that skill), or whenever the open ledger has accumulated a handful of `done` rows. A row may sit `done` in the open ledger briefly between ship and sweep; that's fine. What's not fine is `done` rows accumulating there permanently.

**Preserve, don't summarize.** The archive keeps each row *as written* — the same fail-closed honesty as intake. Don't compress a completed item's detail on the way out; that detail is exactly why the archive exists. Trimming happens by *relocation*, never by deletion.

If a project is small enough that one ledger never gets long, the sweep can be deferred — but document that choice, because "the ledger is short" is a property that quietly stops being true.

## Setting It Up on a New Project

### Step 1 — Copy the front-door template

```bash
cp template/START-HERE.template.md START-HERE.md
```

Open `START-HERE.md` and fill every `{{PLACEHOLDER}}`. The ownership map is the most important part: list every planning doc and classify it as canonical, frozen reference, or archived. This is the map new contributors (and future Claude sessions) use to navigate.

### Step 2 — Ensure the three canonical docs exist

Check whether `BUILD-PLAN.md` (or `PLAN.md`), `docs/REMAINING-WORK.md`, and `docs/FUTURE.md` exist. If any are missing:

- Use `plan-builder` to create a strategic doc + tactical ledger from scratch when none exist.
- Create `docs/FUTURE.md` as a simple markdown list — it doesn't need a formal structure.
- If the project already has equivalent docs under different names, use those; update `START-HERE.md` to name them correctly.

### Step 3 — Point CLAUDE.md and README at START-HERE.md

Add a line near the top of `CLAUDE.md` (and optionally `README.md`) directing new sessions to `START-HERE.md`. Example:

```markdown
> Start here: see `START-HERE.md` for the current status and ownership map.
```

### Step 4 — Adopt the intake loop

Install or sync the `plan-intake` skill so it's available in the project's skill set. Announce to the team (or to your future self in `START-HERE.md`) that reports go through `plan-intake` before being filed.

## Reference Implementation

**The Hive** (`/Users/johns/Repos/the-hive-ecosystem/The-Hive`) is the canonical example:

| Role | File |
|------|------|
| Front door | `START-HERE.md` |
| Strategic doc | `BUILD-PLAN.md` (with the closure log) |
| Tactical ledger (open) | `docs/REMAINING-WORK.md` |
| Tactical archive (done) | `docs/COMPLETED-WORK.md` |
| Frontier doc | `docs/FUTURE.md` |
| Intake skill | `plan-intake` (invoked after every deep dive or audit; sweeps done → archive) |

The reference ledger's header documents its ID scheme (prefixed, stable, never reused), priority labels (P0–P3), wave labels, and area taxonomy — the exact information `plan-intake` needs to format new entries correctly — and points at the completed archive + closure log so a reader who lands on the open ledger can find finished work without it bloating the to-do list.

**Worked example (PetriDishOfMadness, 2026-06-27):** the open ledger had grown to 502 lines / 226 rows, **185 of them `done`** — every session re-read the whole wall of shipped work. The completion sweep relocated those 185 rows (plus the historical status narrative and stale intake notes) to `docs/COMPLETED-WORK.md`, leaving a **89-line** open ledger of just the 41 open/in-progress items. Nothing was lost; the working doc got ~80% cheaper to load.

## Relation to Other Skills

```text
repo-deep-dive / skill-review / audit
              |
              v
          plan-intake  ←──  living-plan convention
              |
              v
      ledger entries  →  orchestrator / work-item-brief
```

- **`plan-intake`** is the intake loop made executable. `living-plan` documents the convention; `plan-intake` runs it.
- **`plan-builder`** creates a strategic doc + ledger from scratch. Use it in Step 2 when neither exists.
- **`repo-deep-dive`** ends by calling `plan-intake` on its findings whenever the target project has a ledger.
- **`work-item-brief`** expands individual ledger entries into full implementation briefs.
