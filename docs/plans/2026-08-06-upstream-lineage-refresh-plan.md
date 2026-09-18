# Upstream Lineage Refresh — Architecture Reasoning

> **SUPERSEDED (same day) by [`2026-08-06-full-upgrade-plan.md`](2026-08-06-full-upgrade-plan.md).**
> This plan scoped 5 upstreams; the real corpus is 27. Kept for its Phase-1 sweep record only.
> Two of its claims were **disproved** by the wider sweep: `davidondrej/skills` is `NO_LINEAGE`
> (SM owes it nothing — the only mentions are in this file), and its "18 skills" count for
> `anthropics/skills` is wrong (17 + a template). Read the full plan instead.

**Date:** 2026-08-06 · **Invoking repo:** Skill-Madness (`main` @ `4b6c84e`, catalog 73)

## What This Is

Skill-Madness derives ~8 skills and a dozen structural patterns from four credited upstream
projects, plus an uncredited fifth. Those upstreams have drifted — `mattpocock/skills` alone is
**133 commits and two minor versions** ahead of what `ACKNOWLEDGMENTS.md` describes. This effort
brings every lineage repo current, reviews what actually changed, refreshes the comparative deep
research, lands the resulting work in the ledger, and ships a new skill so the whole loop becomes a
command instead of a memory.

The deliverable is **not** "adopt everything new upstream." It is an evidence-backed delta, a
corrected attribution record, a prioritized borrow list, and a repeatable process.

## Source Material Analysis

Phase 1 (upstream sweep) is **complete** — executed during planning, because a plan built on
assumed deltas would be fiction. All five upstreams are now local and current at
`~/Repos/ai-tools-and-frameworks/`:

| Upstream | Status before | Action taken | Delta |
|---|---|---|---|
| `mattpocock/skills` | HEAD 2026-07-08, ~v1.1.0 | pulled → **v1.2.2** (`8b36d4f`, 2026-08-05) | **133 commits**; 51 A / 10 D / 53 M / 2 R |
| `davidondrej/skills` | HEAD 2026-07-05 | pulled → `04bd15a` | **64 commits, 78 files** |
| `multica-ai/andrej-karpathy-skills` | HEAD 2026-04-20 | fetched | **0 commits — unchanged** |
| `anthropics/skills` | *not cloned* | **cloned** → `anthropics-skills/` | 18 skills + `spec/` + `template/` |
| `msitarzewski/agency-agents` | *not cloned* | **cloned** → `agency-agents/` | division-based agent library |

### Verified headline findings

These are diffed in-session, not inferred:

1. **`grill-me` reversed its core constraint.** Upstream `productivity/grill-me` is now a
   3-line stub (`disable-model-invocation: true`) that delegates to `productivity/grilling`.
   The real skill, `grilling`, replaced *"one question at a time"* with a **round-based frontier
   model** — ask every question whose prerequisites are settled in one numbered round, each with a
   recommended answer. `ACKNOWLEDGMENTS.md` records "one question at a time" as one of the three
   constraints SM's `grill-me` took from upstream. **That premise is now contradicted upstream.**
   This is the single highest-value decision in the review.

2. **The 100-line rule lost its source.** `productivity/writing-great-skills` (which
   `ACKNOWLEDGMENTS.md` cites as `productivity/write-a-skill`, "since removed upstream") is now
   **fully deleted**. Its successor is `productivity/writing-for-agents` + a `SKILL-MECHANICS.md`
   reference, built around a new central concept — the **context pointer** ("the pointer's *wording*,
   not its target, decides when the agent reaches the material... a must-have target behind a weakly
   worded pointer is a variance bug"). That is a direct, sharper reframing of SM's own "pushy
   descriptions" doctrine and its biggest single borrow candidate.

3. **Nine upstream skills now have no SM counterpart:** `wizard` (promoted in-progress →
   engineering), `wait-what`, `to-questionnaire`, `codebase-design`, `implement`, `research`,
   `resolving-merge-conflicts`, `domain-modeling`, `setup-ts-deep-modules`.

4. **`davidondrej/skills` is entirely uncredited** despite being cloned locally, and its update is
   substantial: a large `agent-orchestration/` expansion (`corral-launch-agents`, `launch-subagent`,
   `codex-subagent`, `herdr`, `git-worktree`, `goal-loop`, `fable-review`, `gpt-review`) plus a
   repo-wide `agents/openai.yaml` per-skill export pattern. That export pattern is directly relevant
   to SM's own 11-tool `convert.sh` installer.

5. **`caveman` and `zoom-out` remain absent upstream** — consistent with
   `docs/adr/0001-keep-caveman-zoom-out.md`. Not re-litigated.

6. **`anthropics/skills` ships a `spec/` and `template/`** never compared against SM's `spec/PSFS.md`,
   because the repo was never cloned locally.

## Key Decisions

1. **Phase 1 executed during planning, not deferred.** Verify-before-claiming makes an unfetched
   delta unplannable. Cost was low and read-mostly; the payoff is that every finding above is
   evidence-backed.

2. **Delta review fans out per-repo, one agent each.** The four changed upstreams are fully
   independent — no shared state, no ordering constraint. Karpathy is skipped entirely (0 commits);
   spending a review agent on an unchanged repo is waste.

3. **Review output is a report, not direct edits.** This repo's established convention is
   report → `plan-intake` → ledger (`docs/REMAINING-WORK.md` + `PLAN.md` closure log). Writing
   skill edits straight from a review bypasses the gate that keeps work tracked.

4. **The comparative deep dive goes 2-way → 4-way.** It currently compares SM against mattpocock
   only. With anthropics and davidondrej now on disk and agency-agents credited for the installer,
   a 2-way comparison under-describes the actual lineage.

5. **DeepResearch writes are gated on explicit confirmation.** It is a separate repo from the
   invoking one. The report lands in Skill-Madness first; the deep-research refresh is proposed and
   confirmed before anything is written to `../DeepResearch/`.

6. **Adoption is opt-in per borrow, never bulk.** Upstream reversed a rule SM deliberately took
   (finding 1) and deleted skills SM deliberately kept (finding 5). Upstream change is evidence, not
   instruction. Every borrow gets a ledger row and a decision, and divergences get an ADR like
   `0001` rather than a silent drift.

7. **The new skill is a workflow, not a loop.** This is an on-demand refresh triggered when an
   upstream moves — not a condition-driven "work until X is true" job. `skills/workflows/` is the
   right home; `loops/` would be a category error.

## Assumptions and Risks

| # | Assumption / Risk | Mitigation |
|---|---|---|
| A1 | The `~/Repos/ai-tools-and-frameworks/skills/` clone (stale duplicate of mattpocock, HEAD 2026-05-13) is dead weight | **Not touched.** Surfaced for the user's decision — see Open Question Q1. No deletion without an explicit ask naming it. |
| A2 | `davidondrej/skills` is genuine SM lineage, not just a repo you happened to clone | Confirmed in scope by the user this session. If the review finds no actual derivation, the outcome is "no attribution needed" — a legal result, not a failure. |
| A3 | Upstream's round-based `grilling` is better than SM's one-question-at-a-time | **Explicitly not assumed.** Finding 1 is written up as a decision with both sides, resolved by the user, and recorded as an ADR either way. |
| R1 | 133 commits of mattpocock churn is mostly docs-restructuring noise, burying the few real skill changes | Review is scoped to `skills/**/SKILL.md` + reference files first; repo-level docs churn is summarized, not enumerated. |
| R2 | Scope creep into "adopt all 9 missing skills" | The plan produces a *prioritized borrow list*; authoring any adopted skill is separate ledger work, gated by `yagni-gate`. |
| R3 | `catalog.sh --check` cannot guard the `CLAUDE.md`/`README.md` prose name lists (4th recorded bite) | Phase 5 adds the new skill to those lists by hand **and** the new skill's own checklist carries the step. |

**Note on counts:** 77 `SKILL.md` files exist under `skills/` (71 non-archive + 6 archive);
`plugin.json` publishes **73**. `catalog.sh --check` reports clean. This is the
bucket-as-publication-gate pattern working as designed — not a defect.

---

# Upstream Lineage Refresh — Build Plan

> Sequential-with-one-fan-out. Phase 2 is the only parallel stage; everything else is ordered.
> This is a research + authoring job, not a multi-component software build — the orchestrator's
> contract/QA-gate machinery does not apply.

## Goal

Bring Skill-Madness's understanding of its upstream lineage current as of 2026-08-06, correct the
attribution record, refresh the comparative deep research from 2-way to 4-way, land every resulting
action as a tracked ledger row, and ship a `workflows/` skill that makes the whole loop re-runnable
on demand. Done when: every upstream is current (✅), a delta report exists with per-finding
evidence, `ACKNOWLEDGMENTS.md` matches upstream reality, the ledger holds the borrow decisions, and
catalog is clean at 74.

## Inputs and Tooling

- **Upstream clones:** `~/Repos/ai-tools-and-frameworks/{mattpocock-skills, davidondrej-skills, andrej-karpathy-skills, anthropics-skills, agency-agents}` — all current as of 2026-08-06
- **Lineage record:** `ACKNOWLEDGMENTS.md` (the 8-skill derivation table + pattern list)
- **Existing research:** `../DeepResearch/skills-comparative_deepdive/` (2-way, refreshed 2026-07-06/08; borrows B1–B7 open)
- **Ledger:** `docs/REMAINING-WORK.md` (open board: CB-10 only), `PLAN.md` closure log
- **Specs the new skill must satisfy:** `spec/PSFS.md`, `skills/meta/skill-writer/references/frontmatter-spec.md`
- **Gates:** `scripts/catalog.sh --check`, `scripts/lint-skills.sh`
- **Skills consumed:** `plan-intake` (Phase 4), `skill-writer` (Phase 5), `yagni-gate` (borrow triage)

## Work Streams

### Stream 1 — Upstream Sweep ✅ COMPLETE

- **Responsibility:** every lineage repo local and current; missing clones filled
- **Owns:** `~/Repos/ai-tools-and-frameworks/` (clones only — no SM files)
- **Depends on:** none
- **Outcome:** 3 pulled, 2 cloned, 1 unchanged. Duplicate clone surfaced, untouched (Q1).

### Stream 2 — Delta Review

- **Responsibility:** produce the evidence-backed change report per upstream
- **Owns:** `docs/reviews/2026-08-06-upstream-delta.md`
- **Depends on:** Stream 1
- **Key features:**
  - Per-repo: new / deleted / renamed / materially-modified skills, `SKILL.md` scope first
  - Re-verify all 8 lineage anchors in the `ACKNOWLEDGMENTS.md` derivation table
  - Flag every case where upstream **reversed** a pattern SM adopted (finding 1 is the known one)
  - Score each new upstream skill: *borrow / already-have / deliberately-decline*
  - **Every claim cites a diff produced in-session** — no asserted change without evidence

### Stream 3 — Deep-Research Refresh

- **Responsibility:** take `skills-comparative_deepdive` from 2-way to 4-way; re-test borrows B1–B7
- **Owns:** `../DeepResearch/skills-comparative_deepdive/` — **separate repo, gated on Q2**
- **Depends on:** Stream 2

### Stream 4 — Ledger Intake

- **Responsibility:** convert the report into approved, ID'd ledger rows via `plan-intake`
- **Owns:** `docs/REMAINING-WORK.md`, `PLAN.md`, `ACKNOWLEDGMENTS.md`
- **Depends on:** Stream 2
- **Key features:** attribution back-fill (davidondrej + corrected mattpocock pointers + version bump to v1.2.2); one row per borrow decision; ADR for each deliberate divergence

### Stream 5 — The New Skill

- **Responsibility:** make Streams 1–4 a repeatable command
- **Owns:** `skills/workflows/upstream-sync/` (name pending Q3)
- **Depends on:** Streams 1–4 (the process must be *run* before it is *written* — otherwise the skill encodes a guess)

## Shared Data Model — the lineage manifest

Both Stream 2 and Stream 5 need one machine-readable record of what SM derives from where. Today
that lives only as prose in `ACKNOWLEDGMENTS.md`, which is why it silently went stale. Define once:

```yaml
# skills/workflows/upstream-sync/references/lineage.yml
upstreams:
  - id: mattpocock
    remote: https://github.com/mattpocock/skills.git
    clone: ~/Repos/ai-tools-and-frameworks/mattpocock-skills
    last_reviewed: { date: 2026-08-06, ref: 8b36d4f, version: v1.2.2 }
    derives:
      - sm: workflows/grill-me
        upstream: productivity/grilling   # was productivity/grill-me — now a stub
        took: [recommend-then-ask, ask-code-not-user]
        diverged: [one-question-at-a-time]  # upstream moved to round-based frontier
```

`last_reviewed.ref` is what makes the next run a `git log <ref>..HEAD` instead of a re-read of
everything. This file is the durable fix for the staleness that caused this whole effort.

## Dependency Graph

```
Stream 1 (done) → Stream 2 (fan-out ×4) → ┬→ Stream 3 (gated on Q2)
                                          └→ Stream 4 → Stream 5
```

Stream 3 and Stream 4 are independent of each other and can run concurrently after Stream 2.

## Key Features (ordered, each individually assignable)

1. **Sweep all five upstreams** — Stream 1 — ✅ complete
2. **Delta review: mattpocock** (133 commits, v1.1.0→v1.2.2) — Stream 2 — *largest single unit*
3. **Delta review: davidondrej** (64 commits, 78 files; squashed snapshots ⇒ file-diff only) — Stream 2
4. **Delta review: anthropics/skills** (first-ever; compare `spec/` + `template/` against `spec/PSFS.md`) — Stream 2
5. **Delta review: agency-agents** (first-ever; verify the 5 credited installer adaptations still hold) — Stream 2
6. **Resolve finding 1** — one-question-at-a-time vs round-based frontier → decision + ADR — Stream 4
7. **Resolve finding 2** — adopt the `context pointer` model into `skill-writer` / `skill-review`? — Stream 4
8. **Attribution back-fill** — davidondrej section, corrected mattpocock pointers, v1.2.2 stamp — Stream 4
9. **Borrow triage** — the 9 uncovered upstream skills through `yagni-gate` — Stream 4
10. **Deep-research refresh** — 2-way → 4-way, B1–B7 re-tested — Stream 3
11. **Author `upstream-sync`** + `lineage.yml` — Stream 5
12. **Catalog + name lists** — `plugin.json` 73→74, `CLAUDE.md` + `README.md` prose lists (R3) — Stream 5

## Validation Criteria

- [ ] All five upstreams local, current, and recorded with a `last_reviewed` ref
- [ ] `docs/reviews/2026-08-06-upstream-delta.md` exists; **every** change claim cites an in-session diff
- [ ] All 8 `ACKNOWLEDGMENTS.md` lineage anchors re-verified against current upstream paths
- [ ] `ACKNOWLEDGMENTS.md` credits davidondrej and names the correct upstream skill for each SM skill
- [ ] Findings 1 and 2 each have an explicit user decision recorded (adopt / decline / ADR)
- [ ] Every borrow is a ledger row in `docs/REMAINING-WORK.md` — none left only in the report
- [ ] Deep dive is 4-way with B1–B7 re-tested *(only if Q2 = yes)*
- [ ] `skills/workflows/<new-skill>/SKILL.md` passes `lint-skills.sh` and PSFS frontmatter validation
- [ ] `scripts/catalog.sh --check` clean at **74**; `CLAUDE.md` + `README.md` prose lists updated
- [ ] The duplicate clone (Q1) is resolved by explicit user instruction, or left untouched
- [ ] No upstream clone, SM file, or DeepResearch file deleted or overwritten without an explicit ask

## Agent Hints

- **Suggested team size: 4**, and only for Stream 2. One agent per changed upstream. Everything
  else is sequential and cheap — spawning agents for it would add coordination cost for no speedup.
- **Natural split:** the four repos share nothing. Zero coordination risk within Stream 2.
- **Load imbalance:** mattpocock (133 commits) is several times the size of the others. Give it the
  most capable agent and expect it to finish last; don't barrier the cheap reviews behind it.
- **Coordination risk:** Streams 4 and 5 both touch `CLAUDE.md`. Sequence them — Stream 5 last —
  or the name-list edit collides with the ledger edit.
- **Special handling:** davidondrej's history is 64 identical "Publish sanitized skills snapshot"
  commits. Commit messages carry **zero** signal there; that agent must work from
  `git diff --name-status` + content diffs only.
- **Read-only discipline:** Stream 2 agents read upstream clones and write only their report
  section. No agent edits an upstream clone or an SM skill.

## Open Questions

- **Q1 — the duplicate clone.** `~/Repos/ai-tools-and-frameworks/skills/` is a second, stale
  (2026-05-13) clone of `mattpocock/skills`, alongside the current `mattpocock-skills/`. Delete,
  rename to something explicit, or leave? *Left untouched pending your word.*
- **Q2 — DeepResearch writes.** Stream 3 writes to `../DeepResearch/`, a different repo. Confirm
  before it runs, or keep the refresh inside Skill-Madness and port it manually later?
- **Q3 — skill name.** `upstream-sync` (what it does) vs `lineage-refresh` (matches the
  `ACKNOWLEDGMENTS.md` vocabulary). Affects the directory, `plugin.json`, and both prose name lists.
