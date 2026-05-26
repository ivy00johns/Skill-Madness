---
name: plan-intake
version: 1.0.0
description: |
  Turn any report (repo-deep-dive output, audit, skill-review, QA findings, design audit) into approved entries in a project's living-plan ledger. Use when the user says "intake this report", "add findings to the plan", "turn this audit into work items", "update the ledger from this report", "feed the deep-dive into the plan", or has a finished report and wants it tracked instead of rotting. Format-agnostic: adopts the target project's existing entry format.
requires_agent_teams: false
requires_claude_code: true
min_plan: starter
owns:
  directories: []
  patterns: []
  shared_read: ["*"]
allowed-tools: ["Read", "Write", "Edit", "Glob", "Grep", "Bash"]
composes_with: ["plan-builder", "repo-deep-dive", "skill-review", "work-item-brief"]
spawned_by: []
---

# Plan Intake

> **Purpose:** Reports become tracked work instead of rotting. Plan-intake is the bridge between a finished report and a project's living tactical ledger.

## When this skill applies

Use this skill when:

- A `repo-deep-dive`, audit, `skill-review`, QA findings doc, or any other report exists and its findings are not yet reflected in the project's ledger.
- The user wants findings ingested as first-class tracked work items, not left as a one-off doc.
- The project already has a living ledger (e.g. `docs/REMAINING-WORK.md`) with its own entry format and ID scheme.

**This skill is not for creating a plan from scratch.** For that, use `plan-builder`. Plan-intake appends to an existing living plan — it never replaces or restructures the ledger's existing organization.

## What to do

Translate a finished report into approved, consistently-formatted entries in the target project's tactical ledger.

**Announce at start:** "Using plan-intake to turn the report into approved ledger entries."

## Inputs

1. **Report file** — a markdown document produced by `repo-deep-dive`, a design audit, `skill-review`, QA findings, or any other structured analysis. The user will @-mention or point to the file.
2. **Target ledger** — the project's living tactical ledger. Default: `docs/REMAINING-WORK.md`. The user may specify a different path.
3. **Strategic companion** — the project's high-level closure log or roadmap. Default: `BUILD-PLAN.md`. The user may specify a different file or indicate none exists.

## Workflow

### Step 1 — Read the ledger's own rules first

Before touching any content, open the target ledger and read its header section. Most well-maintained ledgers document:

- Entry format (fields, column order, required vs optional)
- ID scheme (prefix conventions, numeric ranges, or slug patterns; IDs that are stable and never reused)
- Status vocabulary (open, in-progress, done, deferred, etc.)
- Priority and wave/phase labels
- Area or category taxonomy

Adopt that project's format exactly. Never impose this skill's own format onto the ledger. If the ledger has no documented format, infer the format from the existing entries and note the inference in your proposal.

Example: The Hive's `REMAINING-WORK.md` "How this is organized" section defines Priority P0–P3, Wave A/B/C/— , Area, Source, Status, and Owner columns, plus a stable never-reused ID prefix scheme. A report from a Glass UI audit would get fresh IDs in the `G`-prefixed namespace (or whatever prefix the report source calls for), formatted to match every existing entry in that table.

### Step 2 — Extract findings from the report

Read the full report and identify every distinct actionable finding. Each finding that could stand alone as a work item becomes one candidate entry. Non-actionable observations (summaries, background, rationale) are context only — do not convert them into entries.

Criteria for a candidate entry:

- It describes something that could be done or fixed.
- It is scoped tightly enough to be assigned and tracked.
- It is not already implied by a broader entry already in the ledger.

### Step 3 — Deduplicate against the existing ledger

For each candidate entry, grep the ledger for existing entries covering the same subject, the same source link, or the same affected file or component. Flag likely duplicates — do not propose them as new entries. When in doubt, flag and let the human decide; do not silently drop candidates.

### Step 4 — Propose a review table

Present all non-duplicate candidates as a table for human review before writing anything. The table columns match the project's ledger format. At minimum show:

| Proposed ID | Priority | Wave/Phase | Area | Source | Entry summary (one line) |

- Assign proposed IDs using the project's ID scheme. For a new report source, use a fresh never-reused prefix bundle (check existing IDs to avoid collisions).
- Keep each entry summary to one line.
- If the ledger uses additional columns (Owner, Status, etc.), include them with appropriate defaults (e.g. Status: open, Owner: —).
- Annotate any entry flagged as a possible duplicate with a note pointing to the existing entry.

### Step 5 — Gate: get explicit human approval

Present the proposal table and **wait for explicit approval before writing anything.** This skill is fail-closed: no approval, no writes.

The human may:

- Approve the full table as-is.
- Approve a subset (strike individual rows).
- Edit priorities, waves, or IDs before approving.
- Reject and ask for a revised proposal.

Do not proceed until approval is unambiguous. If the response is ambiguous, ask once for clarification.

### Step 6 — Write approved entries into the ledger

On a feature branch (never directly on the default branch):

1. Insert each approved entry into the correct Area section of the ledger, maintaining the existing sort order within that section (typically by priority, then by ID).
2. If the project uses a strategic companion (e.g. `BUILD-PLAN.md`), and any approved entry is P0 or P1 priority (or the project's equivalent of high-urgency), add a brief note in the companion's open-items or closure-log section referencing the new IDs.
3. Never modify documents marked frozen, archived, or read-only (e.g. a spec doc with a "Status: Frozen" header). If the report source is one of those docs, read it for findings but do not edit it.

### Step 7 — Report what landed

After writing, report back:

- How many entries were proposed, how many approved, how many written.
- The IDs of every entry written (list them explicitly so the human can verify).
- The branch name and which files were modified.
- Any candidates that were dropped as duplicates, with pointers to the existing entries they matched.

## Behavior rules

- **Fail-closed.** No approval from the human, no writes to the ledger. This is non-negotiable.
- **Format-agnostic.** This skill has no opinion about what a ledger entry should look like. It adopts the project's existing format exactly. Two different projects may produce completely different entry shapes; that is correct.
- **Never touch frozen docs.** A report source marked frozen, archived, or read-only is read-only for findings extraction. Do not edit it.
- **Feature branch only.** All writes happen on a feature branch. Never write directly to the default branch (main/master).
- **Infer, don't invent.** If the ledger has no documented format, infer from existing entries and state the inference explicitly in the proposal table. Do not silently impose a format.
- **Conservative deduplication.** When unsure if a candidate duplicates an existing entry, flag it rather than silently dropping it. The human sees the flag and decides.
- **One skill, one ledger.** Process one target ledger per invocation. If the user wants findings distributed across multiple ledgers, run the skill once per ledger.

## Relation to other skills

```text
repo-deep-dive / skill-review / audit   →   plan-intake   →   ledger entries
                                                                      ↓
                                                              orchestrator consumes
```

- **`plan-builder`** creates a plan from scratch. `plan-intake` appends to an existing plan. Use plan-builder when there is no ledger yet; use plan-intake when the ledger already exists.
- **`repo-deep-dive`** produces the reports that plan-intake most commonly consumes.
- **`skill-review`** produces skill-quality findings that plan-intake can route into a skill-collection ledger.
- **`work-item-brief`** produces detailed briefs for individual items; plan-intake creates the items in the ledger that work-item-brief would then expand.
