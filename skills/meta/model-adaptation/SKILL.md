---
name: model-adaptation
version: 1.1.0
description: |
  Adapt prompts, skills, and agent scaffolding when the underlying Claude model changes — currently the Claude 5 family (Fable 5 + Mythos 5) versus Opus 4.x. Stronger models need LESS scaffolding: this skill says what to PRUNE, what now backfires (narrating reasoning in the response trips a reasoning_extraction refusal), and what to add for long autonomous runs. Also the canonical home of the model & effort tiering policy: which model tier and effort level each task class gets (Anthropic ladder by default; never cross-vendor; FreeLLMAPI carve-out). Use when migrating a skill to a new model, when a skill "worked before and got worse", when agents get refused or fall back to Opus, or when picking model/effort per role, stage, or loop. Trigger on "migrate to Fable", "Fable 5", "Mythos 5", "model migration", "reasoning_extraction", "prune the prompt", "tune effort", "model tiering", "which model for which task", "tier down", "cut token costs", "cheaper model for bulk work", "long-running agent hygiene".
requires_claude_code: false
min_plan: starter
compatibility: "Claude Code or Claude.ai; reference/advisory skill. No special tools required — WebFetch is optional, only to re-pull the live Anthropic guide."
allowed-tools: ["Read", "Grep", "Glob", "Edit", "WebFetch"]
composes_with: ["skill-writer", "skill-review", "skill-update", "loop-controller", "orchestrator", "use-freellmapi", "claude-api"]
spawned_by: []
---

# model-adaptation

> The toolkit's home for **what changes about your prompts, skills, and scaffolding
> when the underlying Claude model changes** — currently the Claude 5 family
> (Fable 5 + Mythos 5) succeeding Opus 4.x. It advises and audits; it does not
> build. `skill-writer`/`skill-review` enforce the authoring half, `loop-controller`
> the long-run half, and `orchestrator` the multi-agent half — this skill is where
> the *why* and the migration checklist live so those enforcement points stay in sync.

## Why this skill exists

Model-adaptation guidance is the kind that rots. It's true only relative to a model
generation, it cuts across every skill, and it has no natural owner — so it survives
as scattered asides ("Fable 5 reroutes flagged agents", a stray `/effort` note) that
drift out of date the moment a new model ships and nobody remembers to reconcile them.
This skill is the single owner. When a new model lands, you update **one** landscape
table here and re-run the migration audit, instead of hunting the toolkit for stale
assumptions. Everything model-specific is quarantined in the *Current landscape*
section below; the patterns are written to outlive it.

Source of record: Anthropic's [Prompting Claude Fable 5](https://platform.claude.com/docs/en/build-with-claude/prompt-engineering/prompting-claude-fable-5)
and [Prompting best practices](https://platform.claude.com/docs/en/build-with-claude/prompt-engineering/claude-prompting-best-practices).
Re-fetch these when a new model generation ships — that's the trigger to update this skill.

## The core move: a capability jump means PRUNE, not ADD

The reflex when a stronger model arrives is to write *more* guidance to exploit it.
That reflex is usually wrong. A skill written for a weaker model is a cast made around
that model's failure modes — enumerated do's and don'ts, rigid templates, anti-laziness
nagging, "show your work" instructions. A stronger model has fewer of those failure
modes, so the cast now **constrains** rather than supports it, and Anthropic measures
this as a real *degradation* in output quality, not a wash.

So migration is mostly **subtraction**:

- **A brief instruction now beats an enumeration.** Where you once listed every bad
  behavior by name ("don't survey options, don't over-explain root causes, don't write
  narrating comments…"), one short instruction plus the *reason* now steers the whole
  cluster. Fewer words, better result. (This is why `skill-review`'s long-standing
  anti-pattern — *"Excessive MUST / NEVER / ALWAYS without explaining why"* in its
  audit checklist — was already the right instinct; the newer model rewards it more.)
- **Some old instructions now actively backfire.** The sharpest example: telling the
  model to reproduce, echo, or explain its internal reasoning *in the response* can trip
  a **`reasoning_extraction` refusal** on the Claude 5 family and silently elevate
  fallbacks to Opus. A tactic that helped a prior model now costs you the frontier model.
  See *The refusal landmine* below.
- **Trust defaults before adding a rule.** The migration question is "does the model
  already do this well without being told?" If yes, delete the instruction and let the
  default carry it. Add scaffolding back only where measured behavior needs it.

The opposite is also true in one direction: long *autonomous* runs need **new**
scaffolding the shorter-turn era didn't (async harness, evidence-backed progress, a
send-to-user channel). Subtract the prescription; add the long-run hygiene. See
`references/long-run-hygiene.md`.

## Current landscape (update this section when a new model ships)

This is the *only* part meant to age. The patterns below it are durable; these facts are not.

| Model | Role today | What to know for adaptation |
|---|---|---|
| **Fable 5** | Frontier (Claude 5 family) | Long-horizon autonomy (multi-day runs), strong first-shot correctness, dispatches parallel subagents readily, high bug-finding recall. Runs safety classifiers (offensive cyber, bio/life-sciences, frontier-LLM development, reasoning-extraction) → can return `stop_reason: "refusal"`. Adaptive thinking only; no extended-thinking budgets; summarized-only thinking output. |
| **Mythos 5** | Frontier sibling (Claude 5 family) | Same family, same prompting patterns and refusal behavior as Fable 5. Everything here that says "Fable 5" applies to Mythos 5 unless a future note says otherwise. |
| **Opus 4.8** | Prior baseline **and the fallback target** | The model a refused Claude 5 request should reroute to. Prompts/skills tuned for it are the ones this skill helps you prune. |

When "the next model" (a Mythos successor, an Opus 5) arrives: re-fetch the Anthropic
prompting guide, update this table, and run the *migration audit* at the bottom.

## The pattern catalog

Each pattern: what changed, the toolkit move, and where it's enforced so it can't drift.
Depth lives in the two reference files; this is the map.

### Bucket A — Authoring hygiene (enforced in `skill-writer` / `skill-review`)

| Pattern | What changed | The toolkit move | Enforced in |
|---|---|---|---|
| **Prune over-prescription** | Prior-model prescription degrades Claude 5 output | On migration, delete enumerations/rigid templates the model no longer needs; keep the *why*, drop the MUSTs | `skill-review` anti-pattern checklist (*"Excessive MUST/NEVER/ALWAYS"*, *"Overly rigid templates"*) — now flagged as a **model-driven** re-review trigger, not just static smell |
| **Reasoning-extraction refusal** | Telling the model to narrate/echo its reasoning as response text now trips a refusal | Never instruct "show your thinking / explain your reasoning in the output"; read structured `thinking` blocks or use a send-to-user tool instead | `skill-review` audit checklist (new anti-pattern) → detail in `references/refusal-and-fallback.md` |
| **Brief instruction > enumeration** | One instruction + the reason steers a whole behavior cluster | Prefer a short "why" over naming every behavior; don't carry the *description* field's "pushy / over-enumerate" style into *behavioral* instructions | `skill-review` audit checklist (*"Excessive MUST/NEVER/ALWAYS"* + the prior-model over-prescription trigger); `references/long-run-hygiene.md` has the drop-in brevity instruction |
| **Give the reason, not only the request** | The model connects the task to context better when it knows intent | Already a scored `skill-review` rubric dimension (*"explains WHY, not just WHAT"*) — the Claude 5 family rewards it more | `skill-review` deep-review rubric |

The one boundary to hold explicit: the **"pushy / over-enumerate"** philosophy is correct
for the frontmatter `description` (the trigger slot — you *want* to over-enumerate
contexts to combat under-triggering) and **wrong** for the skill body's behavioral
instructions (where over-enumeration is exactly the prescription that degrades the newer
model). Same word, opposite slots. `skill-writer` and `skill-review` keep these apart.

### Bucket B — Long-running agents (enforced in `loop-controller` / the loops)

Full drop-in instructions and where each plugs into the 5-part loop contract:
**`references/long-run-hygiene.md`**. Summary:

| Pattern | What changed | The toolkit move |
|---|---|---|
| **Longer turns by default** | A single request can run minutes; autonomous runs, hours | Structure harnesses to check **asynchronously** (scheduled/poll), not block; lengthen timeouts; add progress indicators |
| **Ground progress claims** | Long runs can emit *fabricated* status reports | Instruct: audit each progress claim against an actual tool result before reporting it (distinct from the anti-*gamed-gate* rule loops already have) |
| **Don't end a turn on a promise** | Deep in a run, the model can say "I'll now run X" with no tool call, or pause to ask when it has enough | Add a last-paragraph self-check + an autonomous-operation reminder to the loop prompt |
| **Context-budget reassurance** | Surfacing a token countdown makes the model prematurely summarize / suggest a new session | Don't show the model raw budget counts; if you must, add "you have ample context, don't stop" |
| **Fresh-context verifier** | Fresh verifiers beat self-critique | **Already covered** — `loop-controller`'s GAN / Plan-Generate-Evaluate evaluator is exactly this. Cite it; don't reinvent |
| **Send-to-user tool** | Long async agents need to surface verbatim content mid-turn | Give the agent a client-side `send_to_user` tool + elicitation language |
| **Effort as the primary dial** | Effort trades intelligence/latency/cost; low effort on Claude 5 can beat xhigh on prior models | Pick effort per task: `high` default, `xhigh` for the hardest, `medium`/`low` for routine |

### Bucket C — Multi-agent coordination (enforced in `orchestrator`)

| Pattern | What changed | The toolkit move | Enforced in |
|---|---|---|---|
| **Async, long-lived subagents** | Fable 5 dispatches subagents readily; blocking on the slowest one wastes its strength | Prefer async orchestrator↔subagent comms and long-lived subagents (cache reuse) over a strict block-on-every-reply relay, where the build allows | `orchestrator` coordination rules + its `references/workflow-orchestration.md` |
| **Effort per wave/role** | Effort is the main capability dial, not just the ultracode switch | Set `xhigh` for the hardest agent (contracts, adversarial verify), `low`/`medium` for routine (docs, mechanical edits) | `orchestrator` runtime section |
| **Refusal reroute contract** | A flagged agent returns `stop_reason: "refusal"` and reroutes to Opus 4.8 | Treat as expected routing; **configure** the server/client fallback rather than assuming it; note the security-agent implication | `orchestrator` + `references/refusal-and-fallback.md` |
| **State the boundaries / don't over-refactor at high effort** | At high effort the model may tidy/refactor beyond the ask, or act when only asked to assess | When the ask is a question or a "thinking out loud", the deliverable is the assessment — report and stop; scope refactors to the task | `orchestrator` coordination rules |

## Model & effort tiering (the cost doctrine)

Buckets B and C treat *effort* as the primary capability dial. This section is the
fuller doctrine — **model and effort chosen together, per task, not per project** —
and it is canonical here: `orchestrator` (per-role dispatch and Workflow-mode
stages), `loop-controller` (Step 6), and `use-freellmapi` point at this section
rather than restating it.

**The principle.** Cost leaks when a premium model does bulk work — fan-out
crawls, boilerplate, mechanical edits, first drafts — that a cheaper model in
the same family does just as well. Reserve the top tier for the load-bearing
reasoning: architecture/contract design, adversarial verification, final
synthesis, hard debugging. Two dials on the same call: `model` (the cheapest
tier that clears the task's quality bar) and `effort` (`low`→`max`; lower it for
routine passes, raise it only for the hardest reasoning). Output tokens cost
~5× input across the Anthropic family, so moving bulk work down a tier and
trimming output dominate every other cost lever.

**The provider-relativity rule (load-bearing).** Stay within one provider —
never reach cross-vendor to save tokens:

- **Default = Anthropic-native.** The ladder is Haiku → Sonnet → Opus → Fable,
  plus the effort dial. Read a project's declared provider from
  `.claude/profile.yaml`; absent that, assume Anthropic.
- **The doctrine is a shape** — cheapest-that-clears-the-bar for grunt work, top
  tier for the reasoning gate — instantiated with whatever single provider the
  project actually runs on, staying inside that provider's own ladder.
- **FreeLLMAPI is the only multi-provider carve-out** (see `use-freellmapi`): it
  deliberately aggregates free provider tiers behind one endpoint, the scarce
  resource is rate/quota rather than dollars, and the aggregation *is* the ladder.

**Task → tier map** (the durable part; the priced ladder lives in the reference):

| Task class | Examples | Model | Effort |
|---|---|---|---|
| **Mechanical / high-volume** | file transforms, migration edits, formatting, lint-fix application, boilerplate, broad research crawl, first drafts | Haiku, or Sonnet if it needs light reasoning | low/medium (none on Haiku) |
| **Standard implementation** | feature code, test authoring, straightforward role-agent build work | Sonnet | medium/high |
| **Load-bearing reasoning** | architecture & contract design, adversarial verification / fresh-context evaluator, final synthesis, hard debugging, ambiguity resolution | Opus or Fable | high/xhigh (max only when correctness ≫ cost) |

**Guardrails:**

- **No `effort` param on Haiku 4.5** — the API returns a 400. Tier down to
  Haiku *or* dial effort down, not both.
- **Don't reflexively `max`.** On the Claude 5 family `high`/`xhigh` is the
  sweet spot, and `low` effort often matches or beats prior-generation
  `xhigh`/`max` — so `low`/`medium` is the correct setting for routine work,
  not a compromise.
- **Pass `model` and `effort` explicitly on every Agent/Workflow spawn.**
  Per-agent defaults resolve to the *session-start* model, which goes stale the
  moment the user runs `/model` — the subagent-model footgun. This deliberately
  overrides the Workflow tool's generic "omit `opts.model` by default" guidance.
- **Conciseness ≠ reasoning suppression.** Output-trimming (`caveman`-style) is
  fine; instructing the model to expose its reasoning in the response trips the
  `reasoning_extraction` refusal (see the landmine below).

The priced Anthropic ladder (model IDs, $/1M, effort support), the
billing-surface table, provider-relative instantiation, and the per-consumer
wiring live in **`references/model-effort-tiering.md`** — like the *Current
landscape* table above, its model and pricing facts age; update both when a new
model ships.

## The refusal landmine (read this even if you read nothing else)

For a toolkit that **authors** prompts and skills, the highest-consequence change in the
Claude 5 family is a class of instruction that now causes a **refusal**:

> Instructions that tell the model to **echo, transcribe, or explain its internal
> reasoning as response text** can trigger the `reasoning_extraction` refusal category
> on the Claude 5 family, returning `stop_reason: "refusal"` and silently elevating
> fallbacks to Opus 4.8.

The danger is that a skill-authoring toolkit can bake this into *every* skill it produces
("narrate your reasoning", "show your thinking step by step in the output", "explain your
chain of thought"). If your app needs reasoning visibility, read the structured `thinking`
blocks from adaptive thinking, or surface progress with a send-to-user tool — never ask
the model to reproduce its reasoning in the response. `skill-review` now audits for this;
the full mechanics, the other classifier domains (offensive cyber, bio/life-sciences,
frontier-LLM development), and the fallback configuration are in
**`references/refusal-and-fallback.md`**.

## When a new model lands: the migration audit

Run this checklist against an existing skill/harness (or the whole toolkit) on a model change:

1. **Re-fetch the guide.** Pull Anthropic's current prompting guide for the new model and
   update the *Current landscape* table above **and the priced ladder in
   `references/model-effort-tiering.md`** (models, pricing, effort support all age).
   New behaviors = new audit items.
2. **Subtract first.** For each skill, ask per instruction: *does the new model already do
   this well without being told?* If yes, cut it. Rigid templates, anti-laziness nags, and
   long enumerations are the first candidates.
3. **Hunt the refusal landmine.** Run the **audit recipe** in
   `references/refusal-and-fallback.md` — that file owns the canonical grep (don't
   inline a variant here; divergent copies of the sweep are exactly the drift this
   skill exists to prevent). Every hit that routes reasoning to the *response* is a
   refusal risk — rewrite it.
4. **Check the long-run scaffolding.** For any loop/autonomous skill, confirm the
   `references/long-run-hygiene.md` patterns are wired: evidence-backed progress, the
   last-paragraph check, context-budget reassurance, effort selection, send-to-user.
5. **Check the coordination scaffolding.** For the orchestrator, confirm effort-per-wave,
   async/long-lived subagents, and the refusal→fallback contract.
6. **Re-benchmark, don't assume.** If the toolkit has evals (`skill-creator`), re-run them
   with and without the pruned instructions. Keep the cut only if quality holds or improves —
   the model updating its own approach on the fly is often better than the old rule.

## Reference files

- `references/refusal-and-fallback.md` — the four Claude 5 classifier domains, the
  `reasoning_extraction` landmine in depth (what trips it, the symptom, the fix, how to
  audit for it), the `stop_reason: "refusal"` contract, and server-side vs client-side
  fallback to Opus 4.8. Read when a skill gets refused, when writing security-agent
  prompts, or when auditing authored skills for the landmine.
- `references/long-run-hygiene.md` — the long-running-agent behavioral patterns with
  drop-in instruction text (verbatim from Anthropic where they published it) and where
  each plugs into `loop-controller`'s 5-part contract: async turns, evidence-backed
  progress, last-paragraph check, context-budget reassurance, the send-to-user tool,
  effort tiers, and user-facing readability. Read when authoring or migrating any loop.
- `references/model-effort-tiering.md` — the aging half of the tiering doctrine: the
  priced Anthropic ladder (model IDs, $/1M, effort support), the output-token asymmetry
  and billing-surface table, provider-relative instantiation, and how each consumer
  (orchestrator dispatch, Workflow-mode stages, loop-controller Step 6, use-freellmapi)
  wires the policy in. Read when assigning model+effort to roles/stages/loops, or when
  a new model ships and the ladder needs updating.
