# Authoring a new loop skill

Every concrete loop is a *configuration* of `loop-controller`: fill in the 5-part
contract, name a mechanical proof, pick a primitive, inherit the guardrails. This
reference has the loop taxonomy (pick your archetype), the fresh-context
evaluator pattern (for subjective proofs), and a step-by-step authoring template.

## Contents
- [The loop taxonomy — 10 archetypes](#taxonomy)
- [The fresh-context evaluator (PGE / GAN) pattern](#evaluator)
- [Authoring template](#template)

---

## Taxonomy

Pick the archetype your loop matches; it tells you the structure, the natural
entry/exit, and which role owns it. Most real loops are one of these or a
composition of two.

| # | Archetype | One iteration does | Exit (proof) | Owner |
|---|---|---|---|---|
| 1 | **Fix-until-green** | run tests → fix one failure → re-run | test exit 0 AND lint AND typecheck clean | QE |
| 2 | **Build-until-spec** | generator builds one feature; evaluator checks it vs the contract | every contract criterion has passing evidence (default-FAIL) | role agent + contract-auditor |
| 3 | **Refine-until-quality** | generate → fresh-context judge scores vs rubric → regenerate | all rubric dimensions ≥ threshold, or max rounds (5–15) | any role + evaluator subagent |
| 4 | **Research-until-answered** | fan-out searches → verify each claim vs sources → synthesize | loop-until-dry (K rounds find nothing new) or all sub-questions answered | docs/research |
| 5 | **Review-and-revise** | reviewer (fresh context) finds issues → author fixes → re-review | reviewer returns zero blocking findings | security/QE + author role |
| 6 | **Migration** | one file per iteration (or worktree fan-out) → verify behaviour-identical → commit | every target migrated, full suite green, no legacy pattern remains | orchestrator + roles |
| 7 | **Coverage** | run coverage → find lowest-covered unit → add tests → re-measure | coverage report ≥ target, suite green | QE |
| 8 | **Performance** | benchmark under repeatable conditions → optimize highest-leverage → re-benchmark | metric under target on every measured path, no regression | performance |
| 9 | **Self-healing** | watch logs/CI → on actionable error, trace root cause → fix → verify → PR | error resolved and verified, or clean-log confirmation | observability + role |
| 10 | **Exploration** | fan-out read-only subagents map subsystems → synthesize → find gaps | a written architecture summary answers the seed questions | project-profiler |
| 11 | **Orchestrate-until-drained** | assign the next unblocked task to an idle teammate; gate each completed task | every task `completed` AND passing its `TaskCompleted` gate, no dangling `blockedBy` (default-FAIL, whole-board) | orchestrator |

Row 11 is the **meta-archetype**: an outer loop over a *list* of any-archetype
inner loops (each task's gate may itself be a Fix-until-green, Build-until-spec,
or Review-and-revise loop). It doesn't slot cleanly into a single row because its
proof is a *whole-board predicate*, not one process's exit — it's
`orchestrator-task-loop`, the Agent Teams configuration of this harness.

Two structural rules every archetype shares: **name the proof artifact**
(coverage report, benchmark, PR, audit, evaluator verdict), and **re-verify the
whole after each fix** (re-run the full suite / re-score the whole rubric), not
just the changed unit.

## Evaluator

When the proof can't be reduced to an exit code — UI quality, doc clarity, API
ergonomics, "does this design doc's acceptance criteria actually hold" — the
proof is a **fresh-context evaluator subagent**, built GAN-style so it can't
rubber-stamp the work:

1. **Separate model context from the doer.** The evaluator must not have built
   the thing. A same-context critic approves its own mediocre work (measured:
   self-bias is real). Spawn a *fresh* agent that sees only the artifact + the
   rubric, not the build reasoning.
2. **No Write/Edit tools.** Give the evaluator read/inspect tools only (for a UI,
   Playwright MCP to click through the live app; for code, Read/Grep/Bash-to-run-
   tests). With no edit tools it *cannot* "fix" a failure by lowering the bar —
   it can only report.
3. **Default-FAIL rubric with hard thresholds.** Each criterion starts `false`;
   any dimension below threshold **fails the iteration and returns detailed
   feedback** for the next pass. Store the rubric as JSON.
4. **Negotiate a sprint contract first.** Before each build sprint, the doer and
   evaluator agree on a shared, testable definition of "done" for that sprint.

This is Anthropic's Plan-Generate-Evaluate harness: a Planner expands a brief
into a spec (deliberately under-specifying *how*), a Generator builds in sprints,
and a fresh-context Evaluator grades each sprint against the rubric. In their
test, a solo agent produced a barely-functional prototype in ~20 min for ~$9;
the full harness ran ~6 h, cost ~$200, and delivered a polished, working app. The
evaluator is what closes the gap — and it needs prompt-tuning against human
judgment before it grades reasonably (Claude is "out of the box a poor QA agent";
budget for the tuning, per `safety.md` Stage 2).

This maps directly onto this repo's existing pair: **contract-auditor** is the
evaluator, **contract-author** writes the spec the loop builds against.

## Template

To add `skills/loops/<name>/`:

1. **Write the 5-part contract** (trigger, action, proof, memory, stop) at the
   top of the body. If you can't fill all five, the loop isn't ready.
2. **Name the proof artifact and make it default-FAIL.** Exit code, coverage
   file, benchmark, or an evaluator verdict — never "looks done."
3. **Pick the primitive** via SKILL.md Step 1 / `primitives.md`. State it
   explicitly: "`/goal` with condition X" or "Stop-hook gate running script Y."
4. **Inherit the guardrails** — don't re-document them; point at
   `loop-controller`'s `references/safety.md` and state only this loop's specific
   caps (its N, its budget, its no-progress signal).
5. **Externalize state** to profile-defined paths (`PROGRESS.md`, task JSON,
   `fix_plan.md`); never rely on conversation memory across iterations.
6. **Frontmatter:** `disable-model-invocation: true` for any loop that edits /
   commits / spends autonomously (you want to invoke it deliberately);
   `composes_with: ["loop-controller", …]`; `spawned_by: ["orchestrator"]` if the
   orchestrator dispatches it; declare `allowed-tools`.
7. **Ship the gate** if the proof is a script — a Stop-hook that travels with the
   skill (see `primitives.md` → Stop hooks), guarding `stop_hook_active`.

Suggested frontmatter skeleton:

```yaml
---
name: <loop-name>
version: 1.0.0
description: >-
  <what it loops to> — keeps working until <mechanical proof>. Use when <triggers>.
  A configuration of loop-controller. Trigger on: "...", "...".
requires_claude_code: true
disable-model-invocation: true
allowed-tools: ["Read", "Edit", "Bash", "Grep", "Glob"]
composes_with: ["loop-controller", "<role/skill>"]
spawned_by: ["orchestrator"]
---
```

Keep the body lean — the contract, the proof, the primitive, this-loop's caps,
and pointers back here. The machinery lives in `loop-controller`; your skill is
the *configuration*.
