# Refusals & Fallback on the Claude 5 family

How the Claude 5 family (Fable 5 + Mythos 5) refuses, why a well-meaning skill can
provoke it, and how to configure the fallback so a refusal is a reroute rather than a
build failure. Read this when a skill/agent gets refused, when writing `security-agent`
prompts, or when auditing authored skills for the reasoning-extraction landmine.

Anthropic source: [Refusals and fallback](https://platform.claude.com/docs/en/build-with-claude/refusals-and-fallback)
and the [Fable 5 prompting guide](https://platform.claude.com/docs/en/build-with-claude/prompt-engineering/prompting-claude-fable-5).

## Contents

- The four classifier domains
- The `reasoning_extraction` landmine (the one that bites a skill toolkit)
- The `stop_reason: "refusal"` contract
- Configuring fallback to Opus 4.8
- Toolkit implications (security-agent, skill authoring)
- Audit recipe

## The four classifier domains

Fable 5 and Mythos 5 run safety classifiers that can decline a request and return
`stop_reason: "refusal"`. All four domains matter for this toolkit:

1. **Offensive cybersecurity** — building exploits, malware, or attack tooling. *Benign*
   security work (a `security-agent` doing defensive review, a pentest-flavored prompt in
   an authorized engagement) can also trip it. This is expected routing, not a bug.
2. **Biology & life sciences** — lab methods, molecular mechanisms. Beneficial
   life-sciences tasks may also trigger it. Rare in this toolkit, but real.
3. **Frontier-LLM development** (`frontier_llm`) — requests that could assist the
   development of competing AI models. Anthropic's docs note *benign machine-learning
   work can also trigger this category* — and this toolkit does exactly that kind of
   work (model layers like `use-freellmapi`, LLM-judge evals, multi-agent harnesses),
   so treat a refusal here as expected routing too.
4. **Reasoning extraction** — attempts to extract the model's *summarized thinking*. This
   is the one a skill-authoring toolkit provokes by accident (next section).

The first three are content-driven and mostly unavoidable for legitimate work in those
domains — the answer is fallback configuration, not prompt surgery. The fourth is
**self-inflicted** and fully in your control.

## The `reasoning_extraction` landmine

**The rule:** instructions that tell the model to **echo, transcribe, or explain its
internal reasoning as response text** can trigger the `reasoning_extraction` refusal
category on the Claude 5 family. The symptom is not a hard error the user sees — it's an
*elevated rate of silent fallbacks to Opus 4.8*, so you quietly lose the frontier model
on exactly the skills that carry this instruction.

Why a skill toolkit is uniquely exposed: authoring skills love phrases like these, and one
bad template propagates into every skill built from it.

**Phrasings that are refusal risks** (when they route to the *response*, not a thinking block):

- "Show your thinking / show your reasoning step by step in the output"
- "Narrate your reasoning as you go"
- "Reproduce / transcribe your chain of thought"
- "Explain your internal reasoning before answering"
- "Before the answer, write out every step of your thought process"

**Phrasings that are fine** (these are the opposite axis — the *skill doc* giving
rationale, or the model reasoning *internally*):

- "Explain **why** this instruction matters" (rationale in the SKILL.md — good practice,
  keep it)
- "Think carefully before answering" (invokes internal reasoning; doesn't ask to *emit* it)
- "Justify your recommendation with evidence" (asks for a supported conclusion, not a
  transcript of the reasoning process)

**The fix when you genuinely need reasoning visibility:**

- Read the structured `thinking` blocks from [adaptive thinking](https://platform.claude.com/docs/en/build-with-claude/adaptive-thinking)
  instead of asking the model to re-emit its reasoning as prose.
- For long async runs, surface progress with a **send-to-user tool** (see
  `long-run-hygiene.md`), not by narrating reasoning.

## The `stop_reason: "refusal"` contract

When a classifier declines, the API response carries `stop_reason: "refusal"` (rather than
`end_turn`, `max_tokens`, or `tool_use`). Your harness should branch on it explicitly:

- **Don't treat it as a crash or a build failure.** It's a routing signal.
- **Don't retry the identical request against the same model** — it will refuse again.
- **Do reroute** to a fallback model (Opus 4.8) or surface a clear message if no fallback
  is configured.

The word `refusal` appearing as a stop reason is a normal, handled branch — a harness that
only handles `end_turn`/`tool_use` will misread a refusal as a hang or an empty turn.

## Configuring fallback to Opus 4.8

A refusal should be a *reroute*, which means the fallback has to be configured — it is not
always automatic. Anthropic supports both:

- **Server-side fallback** — configure the request so a refused call is automatically
  retried against a fallback model (Opus 4.8) without a round-trip to your app.
- **Client-side fallback** — your harness catches `stop_reason: "refusal"` and re-issues
  the request against Opus 4.8 itself.

Either way, name **Opus 4.8** as the fallback target specifically (not a generic "Opus").
See Anthropic's [refusals-and-fallback](https://platform.claude.com/docs/en/build-with-claude/refusals-and-fallback)
for the exact configuration.

## Toolkit implications

- **`security-agent` / any pentest-flavored dispatch.** These prompts will sometimes trip
  the offensive-cyber classifier and reroute to Opus 4.8. That is expected — note it in the
  run log and carry on. Ensure the fallback is configured *before* a long unattended build
  so a mid-run refusal doesn't stall the wave. Don't rewrite legitimate defensive prompts to
  dodge the classifier; route around it with fallback instead.
- **Skill authoring.** Never ship a skill that instructs the model to reproduce its reasoning
  in the response. `skill-review` audits for this; `skill-writer` should not generate it.
- **Orchestrator.** The refusal-reroute note should state the `stop_reason: "refusal"`
  contract, name Opus 4.8 as the fallback, and say "configure the fallback", not "it reroutes
  automatically".

## Audit recipe

To sweep authored skills for the landmine:

```bash
grep -riE "show your (thinking|reasoning)|narrate.*(reasoning|thinking)|reproduce.*(reasoning|thought)|transcribe.*(reasoning|thought)|chain[ -]of[ -]thought" skills/
```

Triage each hit: does the instruction route the reasoning to the **response**? If yes, it's
a refusal risk — rewrite it (drop it, or switch to reading `thinking` blocks / send-to-user).
If it's the SKILL.md explaining *why* to the human, or asking for internal thinking without
emitting it, it's fine. Keep the whitelist of legitimate "explain why" rationale intact —
that's the pattern the toolkit *wants*.
