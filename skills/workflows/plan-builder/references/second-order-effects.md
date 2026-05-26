# Second-order effects

A thinking move for tracing the downstream and ripple consequences of a plan decision.

First-order thinking asks "what does this decision do?" Second-order thinking asks "what does *that* do?" Plans that stop at first-order consequences routinely produce correct implementations with wrong outcomes — the thing built is exactly what was asked for, but the effects it creates create other effects that nobody wanted.

## The move

For any significant decision in the plan, work through three levels:

1. **First-order effect.** What is the immediate, intended result of this decision? (Usually the reason the decision was made in the first place.)
2. **Second-order effects.** What does that result cause? Who or what else is affected by the change this decision produces? Look for effects on: users, adjacent systems, team workflow, data, cost, and time. Aim for at least two second-order effects per significant decision.
3. **Third-order effects.** For the most significant second-order effect, ask: what does *that* cause? This is often where the unintended consequence lives.
4. **Name the unintended consequence.** Write down the most likely bad outcome that the decision produces via its second or third-order chain — the thing nobody would list as a goal but that follows from the causal logic.
5. **Identify the feedback loop.** Does any effect loop back to influence the original decision or the system that makes decisions? Feedback loops (positive and negative) are often the difference between a plan that stays stable over time and one that degrades.

## When to use it

- Decisions that affect systems or people beyond the immediate scope of the build
- Plans with a time horizon longer than 30 days
- Any change to a shared resource (a schema, a shared API, a platform feature)
- When a plan feels obviously correct — that feeling is often a sign that second-order effects haven't been examined

## What it prevents

- Correct implementation, wrong outcome
- Optimizing one metric while degrading another
- Fixing a problem in a way that causes the same problem to recur faster
- Surprises that "nobody could have predicted" (but were predictable)

## Worked example

Decision: switch the pagination model from offset-based to cursor-based.

**First-order effect:** Queries that would time out under heavy load now run in bounded time.

**Second-order effects:**
- Frontend must be rewritten to pass cursors instead of page numbers — touches every list view.
- The "jump to page N" feature in the UI becomes impossible to implement cheaply — that feature will need to be cut or re-thought.
- API consumers outside the team will need to migrate — creates a deprecation/versioning obligation.

**Third-order effect (from "API consumers must migrate"):** Consumers who don't migrate will start failing silently when the offset API is removed. If removal is on a timeline that isn't communicated, this surfaces as an incident, not a planned deprecation.

**Unintended consequence:** The performance fix triggers a breaking API change that causes a partner integration outage six months later.

**Feedback loop:** Partner outages create pressure to restore the offset API, which undoes the performance fix. The loop: good decision → unmanaged migration → incident → pressure to revert.

**Revised plan:** Include an explicit deprecation window and migration guide in the plan. The technical decision is still the right one; the second-order chain just revealed that the implementation plan needs a non-technical component.
