# Workflow-driven orchestration (ultracode)

How to run the contract-first madness build on the **Workflow tool** — deterministic JS
that fans out subagents — instead of hand-spawning agents one message at a time. Read this
when ultracode is on (`/effort ultracode` or the `ultracode` prompt keyword), when the user
asked for a workflow in their own words, or when a build is large enough that
message-by-message dispatch would lose the thread.

## Table of contents
- [The model](#the-model)
- [When NOT to use a workflow](#when-not-to-use-a-workflow)
- [Phase → workflow mapping](#phase--workflow-mapping)
- [Role-agents as workflow agents](#role-agents-as-workflow-agents)
- [Skeleton: the implement workflow](#skeleton-the-implement-workflow)
- [Skeleton: the verify workflow](#skeleton-the-verify-workflow)
- [Caveats that bite](#caveats-that-bite)

## The model

Nothing about the philosophy changes. Design and contracts are still 50% of the effort and
still happen **inline, in the main loop** — that's the human-in-the-loop architecture work.
What changes is the *execution substrate* for the parallel-implement and verify phases:
instead of you spawning agents and shepherding replies by hand, you author a Workflow script
that spawns them deterministically with real control flow (fan-out, barriers, loop-until-green,
adversarial verification).

The Workflow tool runs the script in the background and hands you back structured results.
The contracts in `contracts/` remain the integration layer — workflow agents share the same
working tree, so they read the same contracts and write to their owned directories exactly as
a hand-spawned agent would. File ownership (`references/file-ownership.md`), the QA gate rules,
and the wave gate all still apply; the workflow is just how the agents get launched.

**One workflow per phase, run in sequence.** Ultracode's guidance is to author a workflow per
phase (implement → verify → ...) and read each result before launching the next. That keeps you
in the loop at every gate — you inspect the implement workflow's summaries, run/confirm the wave
gate, then launch verify. Don't try to cram the whole build into one mega-script; you lose the
gates that make multi-agent builds safe.

## When NOT to use a workflow

- **The design/contract phase.** It's interactive architecture work with you and (often) the
  user. Keep it inline. Putting contract authoring inside a workflow buries the most important
  decisions in a subagent.
- **HITL phases.** A workflow agent runs to completion and returns once — there's no pausing
  mid-agent for a human. Any phase classified HITL (see `references/agent-spawning.md`) stays
  inline. Workflow agents are inherently AFK; only dispatch AFK work into them.
- **Trivial builds.** One or two agents with no verification loop is faster dispatched directly.

## Phase → workflow mapping

| Build phase | Substrate | Why |
|---|---|---|
| 0–4: external audit, plan read, skills manifest, **contracts** | Inline (main loop) | Architecture + HITL; the 50% that can't be delegated |
| Pre-build creative (`nano-banana`, design briefs, `repo-deep-dive`) | Inline or its own workflow | These produce artifacts agents consume; run before implement |
| **Implement** (role-agents, by wave) | **Workflow** | Deterministic fan-out is exactly what `parallel`/`pipeline` are for |
| Wave gate (install + typecheck + test) | Inline barrier between implement waves | You must see failures and route them; see `references/wave-gate.md` |
| **Verify** (qe-agent, render-sanity, ux-review, code/security review) | **Workflow** | Find → adversarially verify is the canonical review pattern |
| Mission completion check, end-state report | Inline | Audit + human handoff |

## Role-agents as workflow agents

This is the "WITH our madness" part. A workflow `agent()` becomes one of your role-agents by
**invoking the role skill from inside the agent's prompt** — the portable path, since every
role skill is built to "work standalone regardless of runtime":

```js
agent(
  `You are the backend agent for this build. Begin by invoking the \`backend-agent\` skill
   (Skill tool) to load your role instructions, then execute the brief below against the
   contracts in contracts/.

   ${distilledBrief}`,                       // the agent-spawning.md template, filled in
  { label: 'backend', phase: 'Implement', schema: AGENT_REPORT }
)
```

The brief is the **same distilled template** from `references/agent-spawning.md` (ownership,
plan excerpt, contracts produced/consumed, domain rules, before-reporting-done). Don't paste the
whole plan — distillation matters more here, not less, because you're spawning many at once.

If a role happens to be registered as a custom subagent type, `agent(prompt, {agentType:
'backend-agent'})` is a shortcut — but the skill-invocation-in-prompt approach above always works
and is the default. Either way, return a structured report via `schema` so the gate logic is data,
not prose:

```js
const AGENT_REPORT = {
  type: 'object',
  required: ['role', 'status', 'filesTouched', 'validation'],
  properties: {
    role: { type: 'string' },
    status: { enum: ['done', 'blocked', 'partial'] },
    filesTouched: { type: 'array', items: { type: 'string' } },
    validation: { type: 'string', description: 'commands run + results' },
    blockers: { type: 'array', items: { type: 'string' } },
  },
};
```

## Skeleton: the implement workflow

One wave of role-agents in parallel (they own disjoint directories, so no write conflicts), each
loading its role skill and building against the contracts. `parallel` is the right call here
because the wave gate downstream needs *all* agents done before it runs.

```js
export const meta = {
  name: 'madness-implement',
  description: 'Fan out role-agents for one implementation wave against the contracts',
  phases: [{ title: 'Implement' }],
};

const AGENT_REPORT = { /* as above */ };

// `args` carries the per-role briefs you distilled inline (pass them in the Workflow call).
const briefs = args.briefs;   // [{ role: 'backend', prompt: '...' }, ...]

const reports = await parallel(
  briefs.map((b) => () =>
    agent(b.prompt, { label: b.role, phase: 'Implement', schema: AGENT_REPORT })
  )
);

return reports.filter(Boolean);
```

You then read `reports` inline, run the wave gate (`references/wave-gate.md`), and route any
`status: 'blocked'` back to that role in the next wave. For a dependency-ordered build (backend
before frontend-that-calls-it), use `pipeline` so each item flows through stages without a global
barrier — but most waves are a flat `parallel`.

When agents would touch overlapping paths and ownership can't fully partition them, add
`isolation: 'worktree'` to those `agent()` calls so they build on isolated copies — but it's
expensive (per-agent worktree setup), so reserve it for genuine conflicts; clean directory
ownership avoids needing it.

## Skeleton: the verify workflow

Find → adversarially verify. The qe-agent produces the real `qa-report.json` (gate it per the
main skill's QA Gate Rules); the review/sanity agents surface findings, and each finding is
checked by an independent skeptic so plausible-but-wrong issues don't stall the build.

```js
export const meta = {
  name: 'madness-verify',
  description: 'QE gate + render-sanity + reviews, with adversarial verification of findings',
  phases: [{ title: 'QA' }, { title: 'Review' }, { title: 'Verify' }],
};

const QA_REPORT = { /* mirror skills/roles/qe-agent/references/qa-report-schema.json */ };
const FINDINGS = { type: 'object', required: ['findings'],
  properties: { findings: { type: 'array', items: {
    type: 'object', required: ['title', 'severity', 'file'],
    properties: { title: {type:'string'}, severity: {type:'string'}, file: {type:'string'} } } } } };
const VERDICT = { type: 'object', required: ['real'],
  properties: { real: {type:'boolean'}, reason: {type:'string'} } };

// QE gate first — its report is authoritative and you do NOT override it.
const qa = await agent(
  `Invoke the \`qe-agent\` skill, write + run tests against the contracts, and emit qa-report.json.`,
  { label: 'qe', phase: 'QA', schema: QA_REPORT }
);

// Review dimensions in parallel; each finding gets independently verified as it lands.
const LENSES = [
  { key: 'render-sanity', prompt: 'Invoke `render-sanity`; run all four checks on the live app.' },
  { key: 'ux',            prompt: 'Invoke `ux-review`; walk the routes at desktop + mobile.' },
  { key: 'code',          prompt: 'Run `code-review` on the diff.' },
  { key: 'security',      prompt: 'Run `security-review` on the diff.' },
];

const verified = await pipeline(
  LENSES,
  (l) => agent(l.prompt, { label: l.key, phase: 'Review', schema: FINDINGS }),
  (review, l) => parallel((review?.findings ?? []).map((f) => () =>
    agent(`Adversarially verify this ${l.key} finding — try to REFUTE it. Default real=false if unsure: ${f.title} (${f.file})`,
          { label: `verify:${f.file}`, phase: 'Verify', schema: VERDICT })
      .then((v) => ({ ...f, real: v?.real }))))
);

const confirmed = verified.flat().filter(Boolean).filter((f) => f.real);
return { qa, confirmed };
```

Read `qa` against the QA Gate Rules and act on `confirmed`. If the gate fails or criticals
remain, fix and re-run verify — a **loop-until-green** with a hard cap (e.g. 3 rounds, matching the
circuit breaker) so a stubborn failure surfaces to the human instead of spinning.

## Caveats that bite

- **`meta` is a pure literal** — no variables, function calls, or template strings in it. Use the
  same phase titles in `meta.phases` as in your `phase()`/`{phase: ...}` calls.
- **Nesting is one level.** The orchestrator (main loop) launches the workflow; a role-agent
  *inside* a workflow cannot call the Workflow tool again. Don't write briefs that tell an agent
  to "run a workflow."
- **Permissions.** Workflow subagents always run in `acceptEdits` and inherit your tool
  allowlist regardless of the session's permission mode — file edits are auto-approved, but
  shell commands, web fetches, and MCP tools outside the allowlist still prompt mid-run.
  Pre-add the commands the agents will need (the wave-gate install/typecheck/test commands at
  minimum) to the allowlist before launching a long run; the `settings-consolidator` skill can
  bootstrap this. The launch prompt itself depends on session mode: default/acceptEdits prompts
  per run (unless "don't ask again" was chosen), auto prompts on first launch only and skips
  entirely under ultracode, bypass/`claude -p`/SDK never prompt.
- **Ultracode is session-only.** It resets on every new session, so re-check the opt-in signals
  each session — yesterday's ultracode doesn't carry over. Resume is same-session only too: if
  Claude Code exits mid-run, the next session starts the workflow fresh. Don't park a wave gate
  across a session boundary.
- **Flagged agents reroute via a refusal (Claude 5 family).** Fable 5 / Mythos 5 run safety
  classifiers for offensive-cybersecurity and biology/life-sciences content; a security-review
  or pentest-flavored agent prompt can trip them. The API returns `stop_reason: "refusal"`, and
  the request should reroute to **Opus 4.8** — but that fallback is *configured*, not automatic.
  Set up server-side or client-side fallback to Opus 4.8 **before** a long unattended run, or a
  mid-wave refusal stalls the workflow (a harness that only handles `end_turn`/`tool_use` misreads
  the refusal as a hang). Treat a handled refusal as expected routing, not a build failure — note
  it in the run log and carry on; don't rewrite a legitimate defensive prompt to dodge the
  classifier, route around it with the fallback. Full contract + config:
  `model-adaptation/references/refusal-and-fallback.md`.
- **Set model AND effort per agent, not one global level.** A workflow `agent()` takes `model`
  and `effort` options; set both per stage from the model & effort tiering policy in
  `model-adaptation` (task→tier map in its SKILL.md; priced ladder in its
  `references/model-effort-tiering.md`). Mechanical fan-out stages — finders, mappers,
  transforms, first drafts — take the cheap tier (Haiku, which takes no `effort` param, or
  Sonnet at `effort: 'low'`); verify/judge/synthesis stages take the top tier at
  `high`/`xhigh` (e.g. the adversarial-verify agents above). On the Claude 5 family a
  lower-effort agent often matches `xhigh` on prior models, so spending `xhigh` only where the
  work is hardest keeps a large fan-out affordable without dropping quality where it counts.
  This deliberately overrides the Workflow tool's generic "omit `opts.model` by default"
  guidance: an omitted model resolves to the session-start model (stale after `/model`), so
  this toolkit passes both explicitly on every `agent()` call. Stay inside one provider's
  ladder — never mix vendors within a build (`use-freellmapi` projects are the sole carve-out).
- **Save the run.** Once an implement or verify workflow does what you want, save it from
  `/workflows` (`s`) into `.claude/workflows/` — the next build of the same shape reruns the
  identical orchestration as a `/command` instead of re-authoring the script.
- **Pipeline by default; barrier only when a stage needs all prior results.** Implement waves and
  QA-finding dedup are genuine barriers (`parallel`); most else pipelines.
- **No silent caps.** If you bound coverage (top-N findings, sampled routes, no retry), `log()`
  what you dropped. Silent truncation reads as "covered everything" — the same audit ethos as the
  mission-skills manifest.
- **Scale to budget under ultracode.** If a token target is set, size the fleet and the
  verify-round count to `budget` rather than a fixed number; with no target, use sensible defaults
  (one agent per owned domain, 1 verifier per finding).
- **The QA gate is still law.** The verify workflow informs you; it doesn't get to override
  `gate_decision`. Fix and re-run.
