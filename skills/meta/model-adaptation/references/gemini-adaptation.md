# Gemini adaptation policy

## Why Gemini is in scope

The toolkit may execute on Google Gemini API or Gemini CLI runtimes. Preserve the distinction between Gemini API model features and Gemini CLI host features. Do not flatten Anthropic settings into Gemini or assume Claude profile defaults.

## Current landscape — facts and unknowns

The audit's 2026-10-02 source register ([Gemini thinking](https://ai.google.dev/gemini-api/docs/thinking), [function calling](https://ai.google.dev/gemini-api/docs/function-calling), [CLI hooks](https://geminicli.com/docs/hooks/)) reported internal thinking in Gemini 3 and 2.5 series (including `gemini-3.8-flash` examples). Flash/Pro labels seed candidate tiers, but exact eligible IDs, context limits, quota tiers, and prices must be checked on the active endpoint. Exact dollar prices, free quota amounts, and universal latency claims are **UNVERIFIED** until queried on the live service.

## Thinking and continuation — do not flatten APIs

- **Interactions API:** Dedicated chronological thought steps alongside other steps. Each thought step carries an encrypted `signature`; `summary` is optional and may be empty. Built-in tool steps can carry signatures; standard function calls, user inputs, and final model outputs do not.
- **generateContent API:** No dedicated thought blocks; signatures are metadata attached to parts (such as functionCall or final response parts).
- **Continuation:** Keep opaque continuation data in the exact representation returned by the API/SDK. Missing summary does not mean absence of reasoning, and a signature is not human-readable text. Do not invent pseudo-thinking blocks or strip required signature fields.
- **Thinking controls:** Use model-specific documented knobs (such as `thinking_level` where supported). Do not assume Anthropic `effort` or Codex `model_reasoning_effort` is universally accepted. Omit unsupported knobs.

## Function calling and host capability

Preserve call/response correlation and SDK continuation items. Allowlisted functions alone may execute. Under Gemini CLI, hook adapters require stdout to contain only valid JSON; logs and progress information must go to stderr to prevent execution bypasses.

## Prompt adaptation map

| Claude-tuned assumption | Gemini move |
|---|---|
| CLAUDE tool/session/profile names | CLI/API harness adapter plus shared AGENTS/task-state artifacts |
| `/goal` as finish wrapper | External verifier + bounded run controller, or tested AfterAgent adapter |
| `/loop` or ScheduleWakeup | External approved runner/CI unless host probe verifies native equivalent |
| Top-tier + `xhigh` | Model-specific documented thinking dial; cheap mechanical stage first |
| "1M means compaction no longer matters" | Scoped just-in-time source retrieval and revision-bound handoff |
| Anthropic refusal fallback | Safe same-provider permitted retry or explicit blocked state; do not bypass refusal policy |
| Self-evaluation in builder window | Independent subagent/session/human review with read-only artifacts |

## Image proxy status

Gemini models are **not allowlisted** by the repository's dense-glyph reading sweep. Default **not allowed** for pxpipe; preserve byte-exact values in text.
