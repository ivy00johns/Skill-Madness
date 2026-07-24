# Model & effort tiering — the priced ladder and consumer wiring

Depth for the **Model & effort tiering** section of the model-adaptation
SKILL.md. Everything in this file is model- and pricing-specific and therefore
**ages** — like the SKILL.md *Current landscape* table, update it when a new
model ships or pricing moves. Facts verified against the `claude-api` reference
on 2026-07-03.

## Why tiering works — the output-token asymmetry

Across the Anthropic family, **output tokens cost 5× input**. That makes two
levers dominate:

1. **Move bulk work down a tier** — a 2×–10× per-output-token cut with no
   quality loss on grunt tasks.
2. **Trim output** (the `caveman` skill) — a flat cut on the dominant cost
   component, on top of whichever tier is chosen.

The scarce resource depends on how the project bills, but the doctrine is
identical for all three:

| Billing surface | What tiering saves |
|---|---|
| Metered API | Literal dollars (the price table below) |
| Subscription (Claude Code Max) | Usage-allowance burn — you stretch the allotment |
| FreeLLMAPI / free tiers | Rate-limit / quota headroom — you stay under provider caps |

## The Anthropic default ladder

Per-1M-token pricing and effort support. Note **Haiku 4.5 does not accept the
`effort` parameter** (it returns a 400) — the effort dial applies to
Sonnet-and-up.

| Tier | Model ID | $ in / out (1M) | Output vs Fable | Effort | Use for |
|---|---|---|---|---|---|
| **Cheapest** | `claude-haiku-4-5` | $1 / $5 | 0.1× | none (400s) | High-volume mechanical passes, classification, simple extraction, cheap fan-out where reasoning is minimal |
| **Mid** | `claude-sonnet-5` | $3 / $15 ($2/$10 intro through 2026-08-31) | 0.3× | low–max (+xhigh) | Standard implementation, test writing, most research crawl, routine role-agent build work |
| **High** | `claude-opus-4-8` | $5 / $25 | 0.5× | low–max (+xhigh) | Hard implementation, tricky debugging, the reasoning-heavy role work |
| **Top** | `claude-fable-5` | $10 / $50 | 1.0× | low–max (+xhigh) | Long-horizon autonomous builds, architecture/contract design, the adversarial verify gate, final synthesis |

Effort defaults: the API default is `high`; Claude Code defaults to `xhigh`. On
the Claude 5 family, `low` effort often matches or beats the `xhigh`/`max`
output of prior-generation models — so `low`/`medium` is the correct setting
for routine work, not a compromise. Reserve `max` for correctness-critical,
latency-insensitive steps.

## The optimizer/target split (role-based tiering)

The ladder above tiers by *task difficulty*. There is a second, role-based rule
for any setup where one model **authors or optimizes** an artifact (a skill, a
prompt, a config) that another model then **executes under**: put the strong
tier on the author/optimizer side and the cheap tier on the execution side.

The evidence is microsoft/SkillOpt's cross-model study: the same optimized
skill produced roughly **2× the score gain** on a weaker execution model than
on a strong one — the weaker model has more headroom, so the optimization
dollars land where they buy the most. The economical pattern is therefore
"cheap deployed target + one strong optimizer," not "strong everywhere":

- **Author / optimize / review** a skill or prompt on the top tier (it runs
  once per revision).
- **Execute and validate under** it on the cheap tier (it runs on every task,
  and benefits most from the optimization).

This composes with, and does not replace, the task-difficulty ladder — the
fresh-context evaluator in a loop is still top-tier (it is a reasoning gate,
not an execution pass).

## Provider-relative instantiation

A project's provider should be discoverable, not guessed:

- Read the declared provider from `.claude/profile.yaml` (the
  `project-profiler` / `setup-project-skills` convention). Absent that,
  **default to Anthropic**.
- **Anthropic** → the ladder above.
- **FreeLLMAPI** (the project uses `use-freellmapi`) → the aggregated free
  tiers are the ladder; optimize for rate/quota and capability, not dollars;
  multi-provider spanning is expected — and this is the *only* setup where it
  is.
- **Any other single provider** → that provider's own tier ladder; instantiate
  the same shape (cheap-for-grunt, top-for-reasoning) and stay inside it. Never
  substitute a different vendor's model to save tokens.

## Wiring into the consumers

The knob already exists everywhere; this policy sets its defaults. Consumers
point here — they don't duplicate the tables.

- **Orchestrator role dispatch** — assign `model` + `effort` per role from the
  SKILL.md task→tier map (a QE mechanical sweep is not the architecture pass).
  See the *"Model and effort are per-role dials"* paragraph in the
  orchestrator's Runtime Detection section.
- **Workflow-mode fan-out** — finder/mapper/transform stages take the
  mechanical tier (cheap model, low effort); verify/judge/synthesis stages take
  the top tier at high effort. Set `opts.model` **and** `opts.effort` per
  stage. This deliberately overrides the Workflow tool's generic "omit
  `opts.model` by default" guidance: an omitted model resolves to the
  session-start model, which goes stale after `/model`. See the orchestrator's
  `references/workflow-orchestration.md`.
- **loop-controller (Step 6)** — workers and routine iteration passes tier
  down; the fresh-context evaluator stays on the top tier — it is the
  reasoning gate.
- **use-freellmapi** — the carve-out described above. Within any build that is
  not a FreeLLMAPI project, never mix vendors to save tokens.
- **use-pxpipe** — checks the image-proxy allowlist below before enabling the
  proxy; it wires the proxy, the SKILL.md's *Image-proxy model allowlist*
  section owns the policy.

## Image-proxy allowlist — current state

The aging half of the SKILL.md's *Image-proxy model allowlist* section: which
models may sit behind a pxpipe-style image proxy today. Numbers are the
2026-07-21 pxpipe deep dive's measurements (its ~20-call glyph sweep over dense
rendered text — `teamchong/pxpipe`, v0.8.0). Re-run the sweep and update this
table on every model release, the same cadence as the ladder above.

| Model | Behind the image proxy? | Measured (pxpipe dive, 2026-07-21) |
|---|---|---|
| **Fable 5** | Allowed | 13–15/15 on the dense-hex glyph sweep |
| **Mythos 5** | Allowed | Same family and read behavior as Fable 5 (dive groups them in the 13–15/15 band) |
| **Opus 4.8** | **Not allowed** | 6/15 on dense hex — misreads surface as confident wrong answers, not errors |
| **Any unlisted / new model** | **Not allowed** (default) | Earns a slot only by passing the glyph sweep |

One interaction to keep in view: a refused Claude 5 request falls back to
Opus 4.8 (`references/refusal-and-fallback.md`) — so a session on an allowed
model can land on a disallowed one mid-run. The `use-pxpipe` wiring is where
that wrinkle gets handled; this table only records who passes.
