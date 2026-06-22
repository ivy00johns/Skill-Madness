---
name: codebase-exploration-loop
version: 1.0.0
description: >-
  Build a working mental model of an unfamiliar codebase by looping: fan out
  read-only subagents to map subsystems, synthesize, find the gaps in your
  understanding, and repeat until a written architecture summary answers every
  seed question — each answer citing where in the code it comes from. The
  deep-research fan-out shape applied to the LOCAL codebase (Read/Grep, no web),
  with a subagent-parallelism cap and a loop-until-dry stop on understanding
  gaps. Use when onboarding to a new repo,
  reverse-engineering someone else's code, or answering "I don't understand how X
  works here" before you touch it.
  Trigger on "help me understand this codebase", "onboard me to this repo", "how
  does X work in this code", "build a mental model of this project", "explore
  this codebase", "map this codebase", "I don't understand this code", "explore
  until I understand". A configuration of loop-controller.
requires_claude_code: true
min_plan: starter
disable-model-invocation: true
allowed-tools: ["Read", "Write", "Grep", "Glob", "Bash", "Agent", "Workflow"]
composes_with: ["loop-controller", "project-profiler", "repo-deep-dive", "orchestrator"]
spawned_by: []
---

# codebase-exploration-loop

> **A configuration of [`loop-controller`].** That skill supplies the loop
> machinery — primitive selection, the full guardrail stack, state
> externalization. This skill supplies the three things specific to "understand
> this codebase": the **seed-question proof** (a default-FAIL question list that
> only flips on a code citation), the **read-only fan-out** that maps subsystems
> in parallel, and the **loop-until-dry** stop on remaining understanding gaps.
> Read `loop-controller` for the guardrails; they're inherited, not repeated here.
>
> **Why `disable-model-invocation`:** this loop spends tokens fanning out a wave
> of subagents per iteration, repeatedly, until your questions are answered. It
> is user-driven — you want to *type* `/codebase-exploration-loop` with your
> questions, not have Claude silently launch an exploration swarm because you
> asked a passing question about a file.

## The 5-part contract

| Part | This loop |
|---|---|
| **trigger** | "I don't understand X" about an unfamiliar repo — onboarding, reverse-engineering, or an explicit `/codebase-exploration-loop` with a list of seed questions |
| **action** | ONE round: read the gap list → fan out read-only subagents (one per open subsystem/question, parallelism capped) → each returns findings + file:line citations → synthesize into the architecture summary → mark answered questions, surface newly-discovered gaps |
| **proof** | the architecture summary answers **every** seed question, each answer **citing a `path:line` (or symbol) in the code**, with zero open "I don't understand X" gaps — default-FAIL: every question starts `answered: false` and flips only on a citation |
| **memory** | `seed-questions.json` (the default-FAIL question list + the new gaps each round surfaces) and `ARCHITECTURE-SUMMARY.md` (the growing synthesis) — durable across rounds; no reliance on conversation memory |
| **stop** | every question `answered: true` with a citation **OR** loop-until-dry (a round surfaces no new gaps and answers nothing new) **OR** iteration/round cap **OR** no-progress for 2 rounds **OR** budget cap |

## The proof: seed questions answered with citations, default-FAIL

"Understood" is not "I read a lot of files and it feels familiar." It is **every
seed question on the list marked `answered: true`, and each answer points at the
`path:line` (or symbol) in the actual code that backs it**. Assume *not*
understood until that citation exists — that's the default-FAIL stance, and it's
what stops the loop from declaring victory on a vibe. An answer with no code
citation is an unanswered question.

Name the artifact: `seed-questions.json` (one entry per question, each defaulting
`answered: false`) plus `ARCHITECTURE-SUMMARY.md` (the prose synthesis that cites
the code per answer). Both must agree before the loop is done — a question can't
be `true` in the JSON without a citation in the summary.

## Step 1 — Capture the seed questions (default-FAIL)

Before any fan-out, write the seed questions to `seed-questions.json`, every one
`answered: false`. These are *your* questions — "where does a request enter?",
"how is auth enforced?", "what's the data model?", "where's the build
configured?" — not a generic checklist. If the user gave questions, use them
verbatim; otherwise propose a starter set and confirm. The list grows: when a
round reveals you didn't understand something you thought you did, add it as a
new default-FAIL entry. The loop is done only when the list is fully `true` *and*
stops growing. The JSON schema and the gap-discovery rule are in
`references/exploration.md`.

## Step 2 — Fan out read-only subagents (cap the parallelism)

This is the `deep-research` fan-out shape pointed at the **local codebase**:
one subagent per open subsystem or question, dispatched in parallel, each given
**Read/Grep/Glob/Bash-to-inspect only — no Write/Edit, no web**. A read-only
mapper cannot accidentally change the code it's studying, and (per
`loop-controller`'s evaluator pattern) a fresh subagent reports what's *there*
rather than what it hopes is there. Each returns a short findings memo with
`path:line` citations.

Cap the fan-out width per round (default ~4-6 concurrent) — per `loop-controller`
Step 5, more parallel readers do not equal faster understanding, they equal a
synthesis you can't reconcile and a budget you can't predict. The dispatch
recipe (and the `/deep-research`-vs-this distinction) is in
`references/exploration.md`.

## Step 3 — Synthesize, then find the next gaps

Merge the round's memos into `ARCHITECTURE-SUMMARY.md`: update the section per
subsystem, attach each citation to the question it answers, and flip those
questions to `answered: true`. Then do the load-bearing step — **read the
summary as a whole and ask what you still can't explain.** A subsystem memo that
answers "how does X work" usually exposes "...but what calls X, and where does
its data come from?" Those become new default-FAIL entries. This is the
loop-until-dry engine: the loop runs until a round both answers nothing new and
surfaces no new gaps.

## How this differs from its neighbors

This loop's whole reason to exist is the **convergence on YOUR questions** — it
is the lightweight, iterative member of a family of heavier one-shot tools, and
it *delegates* to them rather than re-implementing them.

- **vs [`repo-deep-dive`]** — that is a **one-shot, heavyweight deliverable**: a
  comprehensive 12-14 document reference series for a whole repo, grounded in a
  pre-run deep-research markdown. This loop is the **lighter, iterative,
  seed-question-driven** path that stops the moment *your* questions are answered
  — it may never document a subsystem you didn't ask about. When the user wants
  the full series, **hand off to `repo-deep-dive`** (the boundary and handoff
  trigger are in `references/exploration.md`); don't grow into it.
- **vs [`project-profiler`]** — that produces a fixed one-shot artifact
  (`CLAUDE.md` + `profile.yaml`) on a standard template. This loop's deliverable
  is the **question-answering summary plus the loop discipline**. It can *feed*
  project-profiler — invoke it to refresh `CLAUDE.md` from what the loop learned
  — but profiling is not its proof.
- **vs `deep-research`** — same fan-out → verify → synthesize *shape*, but
  deep-research goes to the **web with citations to sources**; this goes to the
  **local code with citations to `path:line`**, read-only, no network.

If after those boundaries this still reads like "deep-research on local code,"
that is exactly the point: the genuine contribution is the **loop-until-the-seed-
questions-are-answered convergence** and the **read-only fan-out discipline** —
not a new documentation format.

## Guardrails specific to this loop

Inherits the full stack from `loop-controller` → `references/safety.md`. The caps
this loop sets:

- **Round / iteration cap** — default ~6-8 rounds (read from
  `.claude/profile.yaml` if set). Hitting it is a *stop-and-report what's still
  unanswered*, not a license to mark questions `true` without a citation.
- **No-progress detection** — if a round answers no new question **and** surfaces
  no new gap, the loop is **dry** — stop. If the **same** gap survives **2
  consecutive rounds** with no new citation, surface it to the human; some
  questions need the code's author, not a third fan-out.
- **Budget cap** — a fan-out of subagents per round multiplies token spend; per
  `loop-controller` enforce a ceiling that *terminates* the loop, and keep the
  per-round width capped (Step 2).
- **Read-only is the boundary.** Mapper subagents get no Write/Edit and no web —
  full stop. This loop *studies* code; it does not modify it. Refreshing
  `CLAUDE.md` is a separate, explicit `project-profiler` invocation, not
  something a mapper does mid-round. There is no irreversible action inside the
  loop, so it is AFK-safe within that read-only boundary.
- **Never cheat the proof.** Don't flip a question to `answered: true` without a
  real code citation, and don't drop a hard question off the list to empty it. A
  summary that "answers" by hand-waving is a *finding*, not understanding.

## Choosing the driver primitive

Per `loop-controller` Step 1, this is a **dynamic-workflow / fan-out** loop, not
a `/goal` finish-line race — each round *is* a parallel dispatch:

- **Default — dynamic workflow / fan-out** (the `/deep-research` engine over
  local code): each round fans read-only mappers across subsystems, then
  synthesizes. Compose with the [`orchestrator`]'s Workflow mode when you want
  the fan-out managed as a workflow with an explicit token budget.
- **`/goal`** can drive the *outer* convergence — condition: "`seed-questions.json`
  has every entry `answered: true` with a citation, or stop after N rounds" — with
  each turn doing one fan-out-and-synthesize round. Remember `/goal` has no native
  budget; embed the round cap.

## Reference files

- `references/exploration.md` — the `seed-questions.json` schema and default-FAIL
  / gap-discovery rule, the read-only fan-out dispatch pattern (and how it differs
  from `/deep-research`), and the hand-off-to-`repo-deep-dive` boundary.

[`loop-controller`]: ../loop-controller/SKILL.md
[`repo-deep-dive`]: ../../workflows/repo-deep-dive/SKILL.md
[`project-profiler`]: ../../workflows/project-profiler/SKILL.md
[`orchestrator`]: ../../orchestrator/SKILL.md
