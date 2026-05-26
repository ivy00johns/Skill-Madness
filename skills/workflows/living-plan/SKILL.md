---
name: living-plan
version: 1.0.0
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

### 3. Tactical ledger — `docs/REMAINING-WORK.md`

Every open item, ID'd, prioritized, and sourced. Must document its own entry format and ID scheme at the top so new items are formatted consistently. The tactical ledger answers "what exactly needs to be done?"

Entry shape (adapt to project conventions):

| ID | Priority | Wave | Area | Source | Summary | Status | Owner |
|----|----------|------|------|--------|---------|--------|-------|

IDs are stable and never reused. Priority (P0–P3 or equivalent), Wave/Phase, and Source are the minimum useful columns.

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
| Strategic doc | `BUILD-PLAN.md` |
| Tactical ledger | `docs/REMAINING-WORK.md` |
| Frontier doc | `docs/FUTURE.md` |
| Intake skill | `plan-intake` (invoked after every deep dive or audit) |

The Hive's `docs/REMAINING-WORK.md` header documents its ID scheme (prefixed, stable, never reused), priority labels (P0–P3), wave labels (A/B/C/—), and area taxonomy — the exact information `plan-intake` needs to format new entries correctly.

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
