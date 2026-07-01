# Long-run hygiene for the Claude 5 family

The behavioral patterns a long-running or autonomous agent needs on the Claude 5 family
(Fable 5 + Mythos 5) that the shorter-turn era didn't. Each entry gives *what changed*, a
**drop-in instruction** (verbatim from Anthropic where they published one), and *where it
plugs into* `loop-controller`'s 5-part loop contract (trigger / action / proof / memory /
stop). Read when authoring or migrating any loop or autonomous harness.

Anthropic source: [Prompting Claude Fable 5](https://platform.claude.com/docs/en/build-with-claude/prompt-engineering/prompting-claude-fable-5).

## Contents

1. Longer turns by default (async harness)
2. Effort as the primary dial
3. Ground progress claims (anti-fabrication)
4. Don't end a turn on a promise (early-stopping guard)
5. Context-budget reassurance
6. Fresh-context verifier (already in `loop-controller`)
7. Send-to-user tool
8. Give the reason, not only the request
9. Readability when talking to the user
10. How this maps onto the 5-part loop contract

---

## 1. Longer turns by default (async harness)

**What changed.** A single request on a hard task can run for many minutes at higher
effort; autonomous runs can extend for hours. Blocking a client on that is the biggest
harness shift teams hit.

**The move.** Adjust client timeouts, streaming, and user-facing progress indicators
before migrating. Restructure harnesses to check runs **asynchronously** (scheduled jobs,
polls) rather than blocking until the run returns. In this toolkit that's already the
`/loop` (watch/poll) primitive and `/schedule` — prefer them over a blocking wait for any
run that can take minutes.

**To keep the model from overplanning an ambiguous task** (drop-in):

```text
When you have enough information to act, act. Do not re-derive facts already established
in the conversation, re-litigate a decision the user has already made, or narrate options
you will not pursue in user-facing messages. If you are weighing a choice, give a
recommendation, not an exhaustive survey. This does not apply to thinking blocks.
```

**Plugs into:** `trigger`/`stop` — poll-style triggers and async check-ins instead of one
blocking turn.

## 2. Effort as the primary dial

**What changed.** Effort is the primary control for the intelligence/latency/cost
trade-off. Lower effort on the Claude 5 family still performs well and often exceeds
`xhigh` on prior models.

**The move.** `high` is the default; `xhigh` for the most capability-sensitive work;
`medium`/`low` for routine. Reduce effort if a task completes but takes longer than
necessary, or when you want a quicker, more interactive style. In a multi-agent build, set
effort per role: `xhigh` for contracts and adversarial verification, `low`/`medium` for
docs and mechanical edits.

**To prevent unrequested tidying/refactoring at higher effort** (drop-in):

```text
Don't add features, refactor, or introduce abstractions beyond what the task requires. A
bug fix doesn't need surrounding cleanup and a one-shot operation usually doesn't need a
helper. Don't design for hypothetical future requirements: do the simplest thing that
works well. Don't add error handling, fallbacks, or validation for scenarios that cannot
happen. Only validate at system boundaries (user input, external APIs).
```

**Plugs into:** `action` — the per-iteration cost/quality knob; also a `stop`-budget lever
(lower effort = cheaper iterations).

## 3. Ground progress claims (anti-fabrication)

**What changed.** On long autonomous runs the model can emit *fabricated* status reports —
claiming work it didn't verify. This is distinct from the anti-*gamed-gate* discipline
loops already have (that guards the mechanical proof; this guards the model's narration).

**The move (drop-in):**

```text
Before reporting progress, audit each claim against a tool result from this session. Only
report work you can point to evidence for; if something is not yet verified, say so
explicitly. Report outcomes faithfully: if tests fail, say so with the output; if a step
was skipped, say that; when something is done and verified, state it plainly without hedging.
```

**Plugs into:** `proof`/`memory` — every progress line in `PROGRESS.md` must trace to a
tool result, not a hope. Complements Step 2's "measure the goal, not a stand-in".

## 4. Don't end a turn on a promise (early-stopping guard)

**What changed.** Deep into a session the model can end a turn with a text-only statement
of intent ("I'll now run X") *without* issuing the tool call, or pause to ask permission
when it already has enough to proceed.

**The move.** `loop-controller` handles this *mechanically* today (`/goal` re-prompts,
Stop-hooks block premature exit). Add the *prompt-level* self-check too, so the model
doesn't rely on the hook:

```text
Before ending your turn, check your last paragraph. If it is a plan, an analysis, a
question, a list of next steps, or a promise about work you have not done ("I'll…", "let
me know when…"), do that work now with tool calls. End your turn only when the task is
complete or you are blocked on input only the user can provide.
```

**For fully autonomous pipelines**, add the operating-context reminder (drop-in):

```text
You are operating autonomously. The user is not watching in real time and cannot answer
questions mid-task, so asking "Want me to…?" will block the work. For reversible actions
that follow from the original request, proceed without asking. Offering follow-ups after
the task is done is fine; asking permission before doing agreed work is not.
```

**Plugs into:** `stop` — pairs with the checkpoint rule so the loop stops *only* where a
human is genuinely required (see the HITL-before-irreversible guardrail), not on a
self-manufactured pause.

## 5. Context-budget reassurance

**What changed.** In very long sessions the model can suggest a new session, offer to
summarize and hand off, or trim its own work — most often when the harness shows it a
**remaining-token countdown**.

**The move.** Avoid surfacing explicit context-budget counts to the model where possible.
This is a real tension for loops: `loop-controller`'s budget guardrail watches `/cost` for
*enforcement*, but that number should drive the harness's stop decision, **not** be shown
to the model as a countdown. If the harness must show it, add reassurance (drop-in):

```text
You have ample context remaining. Do not stop, summarize, or suggest a new session on
account of context limits. Continue the work.
```

**Plugs into:** `stop`/`memory` — budget enforcement stays a *harness* decision reading
externalized state; the model keeps working. (Externalizing state to disk, which loops
already do, is what makes it safe to *not* show the model the countdown.)

## 6. Fresh-context verifier (already in `loop-controller`)

**What changed.** Separate, fresh-context verifier subagents outperform self-critique.

**The move.** This is already `loop-controller` Step 2's **fresh-context evaluator** — the
GAN / Plan-Generate-Evaluate pattern, spawned with no Write/Edit tools, blind to how the
work was built. Nothing to add; cite it. For long runs, make verification *periodic*:

```text
Establish a method for checking your own work at an interval as you build. Run this every
[interval], verifying your work with subagents against the specification.
```

**Plugs into:** `proof` — the subjective-bar grader, run at intervals, not just at the end.

## 7. Send-to-user tool

**What changed.** Long async agents need to surface a message the user must see *exactly as
written* — a deliverable, a numeric progress update, a direct answer — **without ending the
turn**. Tool inputs are never summarized, so content routed through a tool arrives intact.

**The move.** Give the agent a client-side tool; render its input directly in the UI and
return a simple ack:

```json
{
  "name": "send_to_user",
  "description": "Display a message directly to the user. Use for progress updates, partial results, or content the user must see exactly as written before the task finishes.",
  "input_schema": {
    "type": "object",
    "properties": {
      "message": { "type": "string", "description": "The content to display to the user." }
    },
    "required": ["message"]
  }
}
```

Defining the tool is not enough — without an instruction the model rarely calls it. Pair it
with elicitation language:

```text
Between tool calls, when you have content the user must read verbatim (a partial
deliverable, a direct answer to their question), call the send_to_user tool with that
content. Use send_to_user only for user-facing content, not for narration or reasoning.
```

**Note the interaction with refusals:** route *content* here, never a transcript of the
model's reasoning — that's the `reasoning_extraction` landmine (see `refusal-and-fallback.md`).

**Plugs into:** `action` — mid-turn user surfacing without breaking the loop; the async
complement to a loop that otherwise only speaks by ending its turn for HITL.

## 8. Give the reason, not only the request

**What changed.** The model performs better when it understands *intent* — context lets it
connect the task to relevant information instead of guessing.

**The move (drop-in framing):**

```text
I'm working on [the larger task] for [who it's for]. They need [what the output enables].
With that in mind: [request].
```

**Plugs into:** the loop's `trigger` framing and every subagent brief — state the *why*,
not just the *what*.

## 9. Readability when talking to the user

**What changed.** In extended agentic conversations the model can produce text that's hard
to follow: arrow-chain shorthand, deep implementation detail, references to thinking the
user never saw.

**The move (drop-in):**

```text
Terse shorthand is fine between tool calls (that's you thinking out loud). Your final
summary is different: it's for a reader who didn't see any of that. Open with the outcome —
one sentence on what happened or what you found — then the supporting detail. Drop the
working shorthand: complete sentences, no arrow chains or made-up labels, and give each
file/commit/flag its own plain-language clause. If you have to choose between short and
clear, choose clear.
```

**Plugs into:** `action` — the end-of-run summary a loop emits when it stops for HITL or
completes.

## 10. How this maps onto the 5-part loop contract

| Loop contract part | Long-run hygiene that lands here |
|---|---|
| **trigger** | Async/poll check-ins (1); give-the-reason framing (8) |
| **action** | Effort selection (2); send-to-user (7); readable summaries (9) |
| **proof** | Evidence-backed progress (3); periodic fresh-context verifier (6) |
| **memory** | Externalized state that makes budget reassurance safe (5); progress traced to tool results (3) |
| **stop** | Last-paragraph / autonomous-operation guard (4); budget as a harness decision, not a model-facing countdown (5) |

When you author a loop, walk this table: for each contract line, confirm the relevant
hygiene is wired. A loop that fills in the 5 parts but ignores this table will still
converge — it just fabricates status, stops on a promise, or quits early on a phantom
context worry on the way there.
