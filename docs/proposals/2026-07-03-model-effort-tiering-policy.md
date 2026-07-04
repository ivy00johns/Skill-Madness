# Proposal: Model & Effort Tiering Policy

**Status:** plan-only — write-up for hand-off to the implement stage. No skill edits made yet.
**Date:** 2026-07-03
**Owner skill (proposed):** `skills/meta/model-adaptation/` (it already owns cross-model decisions)
**Consumers:** `orchestrator`, `loop-controller`, Workflow-mode orchestration
**Origin:** review of the "5 tricks to cut Fable 5 tokens" thread — tricks #2 (right model per task) and #3 (conciseness) are the load-bearing ones; the toolkit already has the *mechanism* (per-agent `model` + `effort`) but no *doctrine* for which tier to use where.

---

## 1. The principle

**Use the right model *and* the right effort for each task — per task, not per project.** Cost leaks when a premium model does bulk work (fan-out crawls, boilerplate, mechanical edits, first drafts) that a cheaper model in the same family would do just as well. Reserve the top tier for the load-bearing reasoning: architecture/contract design, the adversarial verification gate, final synthesis, hard debugging.

This is two dials on the same call, applied together:

- **`model`** — pick the cheapest tier that clears the task's quality bar.
- **`effort`** — `output_config.effort` (`low`→`max`); lower it for routine passes, raise it only for the hardest reasoning.

Conciseness (the `caveman` skill) rides on top of both — it cuts output tokens regardless of tier.

## 2. Scope & the provider-relativity rule (load-bearing)

**Stay within one provider. Do not reach cross-vendor to save tokens.**

- **Default = Anthropic-native.** For every project that is not a FreeLLMAPI project, the ladder is the Anthropic family only: Haiku → Sonnet → Opus → Fable, plus the effort dial. Never substitute a non-Anthropic model (e.g. "use GPT for the bulk") — that was the one clearly-wrong move in the source thread.
- **Provider-relative template.** The doctrine is a *shape* — "cheapest-that-clears-the-bar for grunt work, top tier for the reasoning gate" — instantiated with **whatever provider the project actually runs on**. A project declares its provider (see §7); the tiering policy resolves the ladder for that provider and stays inside it.
- **FreeLLMAPI is the only multi-provider carve-out.** A FreeLLMAPI project *deliberately* aggregates many free provider tiers behind one endpoint (see `use-freellmapi`). There, the scarce resource is rate/quota, not dollars, and spanning providers is the whole point — so this policy's "one provider" rule does not apply; the FreeLLMAPI aggregation *is* the ladder.

## 3. Why it works — the output-token asymmetry

Across the whole Anthropic family, **output tokens cost 5× input**. That makes two levers dominate:

1. **Move bulk work down a tier** — a 2×–10× per-output-token cut with no quality loss on grunt tasks.
2. **Trim output** (`caveman`) — a flat cut on the dominant cost component.

The scarce resource depends on how the project bills, but the doctrine is identical for all three:

| Billing surface | What tiering saves |
|---|---|
| Metered API | Literal dollars (the price table in §4) |
| Subscription (Claude Code Max) | Usage-allowance burn — you stretch the allotment |
| FreeLLMAPI / free tiers | Rate-limit / quota headroom — you stay under provider caps |

## 4. The Anthropic default ladder

Per-1M-token pricing and effort support (source: `claude-api` reference, cached 2026-06-24). Note **Haiku 4.5 does not accept the `effort` parameter** (it 400s) — the effort dial applies to Sonnet-and-up.

| Tier | Model ID | $ in / out (1M) | Output vs Fable | Effort | Use for |
|---|---|---|---|---|---|
| **Cheapest** | `claude-haiku-4-5` | $1 / $5 | 0.1× | ❌ (no effort param) | High-volume mechanical passes, classification, simple extraction, cheap fan-out where reasoning is minimal |
| **Mid** | `claude-sonnet-5` | $3 / $15 ($2/$10 intro→2026-08-31) | 0.3× | low–max (+xhigh) | Standard implementation, test writing, most research crawl, routine role-agent build work |
| **High** | `claude-opus-4-8` | $5 / $25 | 0.5× | low–max (+xhigh) | Hard implementation, tricky debugging, the reasoning-heavy role work |
| **Top** | `claude-fable-5` | $10 / $50 | 1.0× | low–max (+xhigh) | Long-horizon autonomous builds, architecture/contract design, the adversarial verify gate, final synthesis |

Effort defaults: the API default is `high`; Claude Code defaults to `xhigh`. On the Claude 5 family, **`low` effort often matches or beats the `xhigh`/`max` output of prior-generation models** — so `low`/`medium` is the correct setting for routine work, not a compromise. Reserve `max` for correctness-critical, latency-insensitive steps.

## 5. Task → tier mapping (the doctrine)

| Task class | Examples | Model | Effort |
|---|---|---|---|
| **Mechanical / high-volume** | file transforms, migration edits, formatting, lint-fix application, boilerplate, broad research crawl, first drafts | Haiku, or Sonnet if it needs light reasoning | low/medium (none on Haiku) |
| **Standard implementation** | feature code, test authoring, straightforward role-agent build work | Sonnet | medium/high |
| **Load-bearing reasoning** | architecture & contract design, adversarial verification / fresh-context evaluator, final synthesis, hard debugging, ambiguity resolution | Opus or Fable | high/xhigh (max only when correctness ≫ cost) |

## 6. Application in the orchestrator / loops / Workflow

The knob already exists; this policy sets its defaults.

- **Workflow-mode fan-out** — the finders/mappers/transform stages take the mechanical tier (cheap + low effort); the verify/judge/synthesis stages take the top tier (premium + high). This matches the Workflow tool's own guidance ("`low` for cheap mechanical stages and higher tiers only for the hardest verify/judge stages"). Set `opts.model` **and** `opts.effort` per stage.
- **Orchestrator role dispatch** — assign model+effort per role from the task class in §5 (a QE mechanical sweep ≠ the architecture pass). The existing model-adaptation edit added an *effort*-per-role principle; extend it to *model*-per-role.
- **loop-controller** — Step 6 already carries "effort per iteration"; add a one-line pointer to this policy for the model choice, and keep the fresh-context evaluator on the top tier (it's the reasoning gate).

## 7. Provider-relative instantiation

A project's provider should be discoverable, not guessed:

- Read the project's declared provider from `.claude/profile.yaml` (the `project-profiler` / `setup-project-skills` convention). Absent that, **default to Anthropic**.
- **Anthropic** → the §4 ladder.
- **FreeLLMAPI** (project uses `use-freellmapi`) → the aggregated free tiers are the ladder; optimize for rate/quota and capability, not dollars; multi-provider spanning is expected.
- **Any other single provider** → that provider's own tier ladder; instantiate the same shape (cheap-for-grunt, top-for-reasoning) and **stay inside that provider**.

## 8. Guardrails / anti-patterns

- **No cross-vendor default.** Within a non-FreeLLMAPI project, never swap in a different vendor's model to save tokens. (The thread's "use GPT-5.5 for the bulk" is the anti-pattern; "GPT-5.5" is also an unverified model.)
- **Don't put `effort` on Haiku 4.5** — it returns a 400. Tier down to Haiku *or* dial effort, not both.
- **Don't reflexively `max`.** On the Claude 5 family, `high`/`xhigh` is usually the sweet spot; `low` clears routine work.
- **Read model from user choice, not the session-start default.** Per [[subagent-model-follows-user-choice]], per-agent `model`/`effort` defaults resolve to the *session-start* model — pass them explicitly on every Agent/Workflow call.
- **Conciseness ≠ reasoning suppression.** `caveman`-style output-trimming is fine; instructing the model to expose/echo its reasoning in the *response* trips Fable's `reasoning_extraction` refusal (see `model-adaptation`). Trim output, don't strip reasoning.

## 9. Integration plan (for the implement stage)

**Where it lands:**
1. `skills/meta/model-adaptation/` — add a "Model & effort tiering" section carrying §4 (ladder), §5 (task→tier map), and §7 (provider instantiation + the Anthropic default). This is the canonical home.
2. `skills/orchestrator/` — in Runtime Detection / dispatch, consult the tiering policy when assigning per-role `model`+`effort`; add the fan-out example from §6 to `references/workflow-orchestration.md`.
3. `skills/loops/loop-controller/` — one-line pointer from Step 6 to the tiering policy for model selection; keep the evaluator on the top tier.

**Definition of Done:**
- [ ] model-adaptation states the provider-relativity rule (Anthropic default; FreeLLMAPI carve-out; no cross-vendor) and carries the §4/§5 tables.
- [ ] The Haiku-has-no-effort caveat and the "don't reflexively max" note are present.
- [ ] Orchestrator dispatch + Workflow-orchestration doc show per-stage/per-role model **and** effort selection, keyed to the §5 task classes.
- [ ] Cross-links: model-adaptation ↔ orchestrator ↔ loop-controller ↔ use-freellmapi; `[[subagent-model-follows-user-choice]]` footgun referenced.
- [ ] Gates green: `catalog.sh --check`, `lint-skills.sh skills/`, markdownlint on touched files.

**Explicitly out of scope for this policy:** any runtime auto-switching of models (this is guidance the orchestrator/authors apply, not an automatic router); pricing that isn't in the `claude-api` reference (re-verify the table against it at implement time in case it has moved).
