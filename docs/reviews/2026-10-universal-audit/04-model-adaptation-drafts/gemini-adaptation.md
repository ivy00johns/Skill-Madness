# Gemini adaptation — draft, not installed

Depth proposed for model-adaptation. Verified **2026-10-02** against [Gemini thinking](https://ai.google.dev/gemini-api/docs/thinking), [function calling](https://ai.google.dev/gemini-api/docs/function-calling), [Gemini CLI subagents](https://geminicli.com/docs/core/subagents/) and [CLI hooks](https://geminicli.com/docs/hooks/). Preserve the distinction between Gemini API model features and Gemini CLI host features.

## Why Gemini is in scope

Current model doctrine has Anthropic and DeepSeek references but no Gemini adaptation. [Provider-relative ladder](../../../../skills/meta/model-adaptation/references/model-effort-tiering.md#L83) says other providers should instantiate their ladder without supplying wire guidance. Meanwhile [converter:711](../../../../scripts/convert.sh#L711) excludes roles/loops from Gemini, although current official CLI docs describe independent-context subagents and lifecycle hooks. Installation limitation is not a model limitation.

## Current landscape — facts and unknowns

The live thinking guide says Gemini **3 and 2.5 series** use internal thinking; it includes `gemini-3.8-flash` examples. This verifies what the guide documents, not account availability, pricing, context limits, or relative quality in this library. Flash/Pro labels can seed candidate tiers but exact eligible IDs and endpoint controls must come from the user's approved catalog. Dollar prices, free quota amounts, universal latency claims and exhaustive model support are **UNVERIFIED** in this audit.

## Thinking and continuation — do not flatten APIs

The live guide distinguishes:

- **Interactions API:** dedicated chronological thought steps alongside other steps. Each thought step has required encrypted `signature`; `summary` is optional and may be empty. Standard function calls, user inputs and final model outputs do not carry signatures in this representation; built-in tool steps can.
- **generateContent API:** no dedicated thought blocks; signatures are metadata attached to parts, including functionCall or final response parts.

Keep opaque continuation data in the exact representation returned by the API/SDK. Missing summary does not mean no reasoning, and a signature is not human-readable reasoning. Do not copy `reasoning_content` rules from DeepSeek or Anthropic content-block assumptions into this adapter. Endpoint-specific errors should be surfaced and tested, not “fixed” by deleting required fields.

Thinking controls vary by model and API. The guide contains `thinking_level` examples for Interactions. Do not assume Anthropic `effort`, Codex `model_reasoning_effort`, or an arbitrary numeric token budget is accepted everywhere. Exact settings for the selected model are **UNVERIFIED** until its docs and request validation are checked. Use the smallest supported setting that passes a task eval, not a blanket `max`.

## Function calling and host capability

The function-calling documentation describes function name/arguments/schema and the external application executing calls. It does not turn a bare API response into a filesystem or scheduler. Preserve call/response correlation and SDK/model continuation items; allowlisted functions alone may execute. Read current endpoint docs for streaming and multiple-call behavior rather than guessing from a partial example.

Gemini CLI's documented host supports specialist subagents with separate context/toolsets and hook events including BeforeTool/AfterTool, BeforeAgent/AfterAgent, SessionStart/End and PreCompress. Browser agent is disabled by default and requires first-run consent; documented headless default is false. Exact installed CLI/version/flags here are **UNVERIFIED** because no billed session was launched.

Hook adapters require special care: official docs say stdout must be only JSON, and polluted stdout can fall back to allowing execution. Existing Claude [QA success/warn logs](../../../../hooks/scripts/qa-gate.sh#L85) must go to stderr under Gemini. Map semantic `completion_gate` to tested AfterAgent retry/halt semantics; do not reuse Claude Stop JSON without validation.

## Prompt adaptation map

| Claude-tuned assumption | Gemini move |
|---|---|
| CLAUDE tool/session/profile names | CLI/API harness adapter plus shared AGENTS/task-state artifacts |
| `/goal` as finish wrapper | External verifier + bounded run controller, or tested AfterAgent adapter |
| /loop or ScheduleWakeup | External approved cron/CI unless installed host probe verifies native equivalent |
| Top-tier + `xhigh` | Model-specific documented thinking dial; cheap mechanical stage first |
| “1M means compaction no longer matters” | Scoped just-in-time source retrieval and revision-bound handoff |
| Anthropic refusal fallback | Safe same-provider permitted retry or explicit blocked state; do not bypass refusal policy |
| Self-evaluation in builder window | Independent subagent/session/human review with read-only artifacts |

No verified Gemini-specific rule forbids XML or Markdown here; formatting superiority is **UNVERIFIED**. Use concise sections and concrete acceptance criteria, then measure behavior. Distinguish rationale (“why shared chrome matters”) from asking the model to reveal its internal thought process.

## Tiering and budget

Within an approved Gemini provider policy: cheap catalog candidate for extraction/classification/test log summarization; mid candidate for standard scoped code; high candidate for consequential contracts/security/adversarial review. Flash or Pro name alone is not acceptance evidence. Quota failures are operational blocked results, not successful negative trigger cases. Allow approved free tiers via FreeLLMAPI after real catalog capability checks and privacy consent; record routed model, not only requested `auto`.

## Audit checklist for Gemini runs

1. Confirm API vs CLI, installed skills, resource paths and hooks enabled.
2. Test continuation handling with function calls; never expose signatures as proof text.
3. Check actual thinking/output schema controls and context budget.
4. Prove configured hook blocks on failed verifier and validator crash; ensure stderr logs and bounded cancellation.
5. Use visible browser observations where the UI doctrine demands them; unavailable browser means blocked verification, not source-inferred PASS.
6. Record actual routed provider/model/effort, billing/quotas, skill and adapter hashes.

## Image proxy and consumers

Gemini is **not allowlisted** in the repo's dense-glyph measurements. Keep image-proxy default denied until calibrated fidelity eval and economics justify it; no “multimodal implies OCR-safe” shortcut.

Orchestrator, loop-controller, frontend/render skills and model-adaptation should consume this adapter through capabilities and catalog tiers. Preserve native Claude branches unchanged. This report proposes the reference only; no skill or settings file was edited.
