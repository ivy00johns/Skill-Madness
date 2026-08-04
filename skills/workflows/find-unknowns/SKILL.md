---
name: find-unknowns
version: 1.0.1
description: >-
  Convert your unknown-unknowns to known — cheaply, before they get expensive to
  fix. Owns two moves: a blindspot pass (research an unfamiliar domain and learn
  the questions you don't yet know to ask) and a comprehension quiz (after a big
  change, explain the diff and verify you understand it before merging). Routes
  the rest of the unknowns lifecycle to the owning skills. Use when you're in
  unfamiliar territory, can't articulate what "good" looks like, feel like you're
  missing something, or want to be sure you understand what got built. Trigger on
  "find my unknown unknowns", "blindspot pass", "what am I missing", "I don't know
  this domain/codebase", "teach me my blind spots", "map my unknowns", "quiz me on
  this change", "do I actually understand this diff", "only merge if I understand
  it", "comprehension check". Sibling to grill-me — that interviews you on
  decisions you already hold opinions about; this surfaces the ones you don't.
requires_agent_teams: false
requires_claude_code: false
min_plan: starter
owns:
  directories: []
  patterns: []
  shared_read: ["*"]
allowed-tools: ["Read", "Grep", "Glob", "Bash", "WebSearch", "WebFetch"]
composes_with: ["grill-me", "plan-builder", "maintain-context", "repo-deep-dive", "interactive-doc", "artifact-publish", "superpowers:brainstorming"]
spawned_by: []
---

# find-unknowns

The map is not the territory. Your prompt, your plan, your mental model — that's
the map. The codebase, the domain, the real constraints — that's the territory.
The gap between them is your **unknowns**, and on a capable model the work is
bottlenecked less by the model's ability and more by *your* ability to surface
those unknowns before they get expensive. Every explainer, brainstorm, interview,
and quiz is a cheap way to find out what you didn't know — before it costs you a
bad implementation to find out the hard way.

## Name the four unknowns

When you bring a problem, it breaks down four ways. Naming which kind you're
short on tells you which move to reach for:

| Quadrant | What it is | Cheapest way to surface it |
|---|---|---|
| **Known knowns** | What you put in the prompt | Already written down |
| **Known unknowns** | What you know you haven't figured out | An **interview** → `grill-me` |
| **Unknown knowns** | So obvious you'd never write it, but you'd know it on sight | A **brainstorm / prototype** to react to |
| **Unknown unknowns** | What you haven't considered at all — you don't even know the question | A **blindspot pass** (this skill) |

The dangerous quadrant is the last one: you can't ask about what you don't know
exists, and it's the one that surfaces late, deep in implementation, when
reverting is expensive. That's the gap this skill is built to close.

## What this skill owns vs. routes

This skill owns the two ends of the "do I actually understand this?" question —
the **before** (blindspot pass) and the **after** (comprehension quiz). The
middle of the lifecycle is already well-covered; route to the owner rather than
re-doing it here:

| You want to… | Go to |
|---|---|
| Be interviewed on decisions you already have opinions about | `grill-me` |
| Generate directions / a throwaway prototype to react to | `superpowers:brainstorming`, `ui-brief`, `claude-design-brief` |
| Turn resolved decisions into a plan (leading with what's most likely to change) | `plan-builder` |
| Log deviations you hit mid-build so the next attempt learns | `maintain-context` |
| Deeply map an unfamiliar codebase | `repo-deep-dive`, `zoom-out` |
| Package the result into a pitch/explainer for buy-in | `interactive-doc`, `artifact-publish` |

Reach for the owner, hand back here for the two moves below.

## Move 1 — Blindspot pass (before you build)

Use when you're in territory you don't know well: a new module, an unfamiliar
domain, a design you can't yet articulate. The problem isn't that you have the
wrong answers — it's that you don't know the *questions*. You can't see what good
looks like, what's already been tried, or which potholes are waiting.

The move is the inverse of an interview. Instead of asking you what you think,
Claude researches the terrain and teaches you your unknown unknowns, then hands
you back the questions you're now equipped to answer (or to hand off as
requirements).

1. **Get the starting point — context is load-bearing.** Tell it who you are,
   what you already know, and what you're trying to do. "I know nothing about the
   auth modules here" produces a very different pass than "I've written auth
   before but not in this stack." Say so.
2. **Research the terrain.** Grep/read the relevant code paths; `WebSearch` /
   `WebFetch` the domain when the unknowns are conceptual rather than local. The
   best reference of all is *source code* — if a library or a sibling module
   already does the thing well, point at it and have Claude read how it's built,
   not just what it looks like.
3. **Return a map, not a verdict.** Structure the output as: the terrain (the
   pieces and how they connect), your grouped unknown unknowns, what "good" looks
   like here, the historical context / prior attempts, and the potholes to avoid —
   ending with the handful of questions you should now be able to answer or route
   to `grill-me`. An HTML artifact is often the clearest form (→ `interactive-doc`
   / `artifact-publish`).

This is *not* `grill-me`: grill-me interrogates opinions you already hold and
resolves your **known** unknowns; the blindspot pass surfaces the **unknown**
ones you didn't know to have opinions about. Run this first, then grill-me.

**Example prompts**

- "I'm adding a new auth provider but I know nothing about the auth modules in
  this codebase. Do a blindspot pass — find my unknown unknowns and teach me
  enough to prompt you well."
- "I need to color-grade this video and don't know what color grading even is.
  Teach me my unknown unknowns about it so I can react."
- "Before I scope this, search the codebase and tell me what I'm not seeing about
  how sessions are currently persisted."

## Move 2 — Comprehension quiz (after it's built)

Use after a large change, especially an agent-driven one. Reading the diff gives
you only a light understanding, because most of the behavior lives in how the new
code interacts with existing paths — which the diff doesn't show. Merge on that
light understanding repeatedly and you accrue **comprehension debt**: the code
outruns your mental model, the system works but nobody knows *why* it's shaped
the way it is, and the bill comes due at the next bug. (`loop-controller` names
this as the human-side failure mode of autonomous loops; this is its antidote.)

The move: before you merge, have Claude bring you up to the level of the change,
then test that it stuck.

1. **Read the change and what it touches.** The diff *plus* the existing code
   paths it now runs through — that interaction is where understanding actually
   lives. In Claude Code, `git diff` / `git log`; elsewhere, paste the diff.
2. **Explain it back.** A short report: what changed, why, the intuition behind
   the approach, and how it interacts with what was already there.
3. **Quiz on the non-obvious.** Questions aimed at the behavior a reader would
   *miss* — edge cases, interactions, the "why this and not the obvious
   alternative." Not trivia the diff makes obvious.
4. **Grade honestly and close the gaps.** You merge only when you can pass it. A
   miss isn't a failure — it's the exact spot your understanding was thin, so fill
   it and re-check.

**Example prompts**

- "Give me an HTML report on this change — what was done, the intuition, how it
  hits existing code paths — with a quiz at the bottom I have to pass before I
  merge."
- "I let an agent refactor the payment flow and the tests are green. Quiz me on
  the diff — I only want to merge if I actually understand what it did."

## Why this is worth the minutes

None of this produces shippable output — it produces *understanding*, and that's
the point. A blindspot pass costs a few minutes; discovering the same unknown
three days into an implementation costs the implementation. A comprehension quiz
costs one round of Q&A; comprehension debt costs a future debugging session on
code no one understands. Spend the cheap discovery now so you don't pay the
expensive kind later.
