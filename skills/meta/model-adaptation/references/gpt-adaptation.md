# OpenAI / GPT adaptation policy

## Why GPT is in scope

The toolkit may execute on OpenAI / GPT runtimes (such as OpenAI Codex, ChatGPT subagents, or OpenAI-compatible proxy endpoints). Do not attribute execution or frontend failures to model quality when the role was not delivered, or when nonexistent Anthropic settings were injected into the run.

## Current landscape — verified names, unknown entitlements/prices

The audit's 2026-10-02 source register ([Codex subagents](https://learn.chatgpt.com/docs/agent-configuration/subagents)) reported `gpt-6-luna` for faster/lower-cost lighter subagent work and `gpt-6.1-sol` for demanding work. Model availability depends on account/workspace, and agents may inherit model/effort. Those are documented statements, not an assumption of account entitlement or pricing. Exact prices, context length, output cap, accepted API effort values, latency, and benchmark scores are **UNVERIFIED** until queried on the live endpoint.

| Candidate tier | Selection rule | Known / unknown |
|---|---|---|
| Mechanical | Cheapest available model passing tool/format and held-out task checks | Luna named for lighter subagents in Codex docs; actual billing/effort UNVERIFIED |
| Implementation | Lowest-cost model passing task outcome/proof/architecture gates | No universal fixed GPT ID or effort default asserted |
| Independent review | Clean-context model with demonstrated reviewer quality | Sol named for demanding work; not compulsory for every review |

## Prompting and thinking adaptation

[OpenAI reasoning guidelines](https://developers.openai.com/api/docs/guides/reasoning-best-practices) recommend simple/direct instructions, specific successful outcomes, explicit constraints, zero-shot first then aligned examples when needed, and avoiding requests to "think step by step" or narrate chain of thought.

- **Markdown and XML:** Both Markdown and XML tags/section delimiters are explicitly permitted. XML delimiters in orchestrator or contracts are not Claude-only and do not require cosmetic mass rewrites.
- **Formatting workarounds:** Do not inject o1-era workarounds universally. Developer/system role choice is an endpoint/model adapter decision, not canonical skill-body prose.
- **Operational template:** Use short ordered sections: Goal/acceptance criteria, read-only context paths, allowed files/actions and explicit prohibited side effects, next small task + exact output shape + verifier command, fallback and stop conditions.
- **Concise evidence:** Preserve concise decision rationales and executed tool evidence; do not request chain-of-thought extraction.

## Wire and tool-call continuations

Preserve opaque reasoning/tool items according to the chosen endpoint/SDK rather than translating everything into plain text. Tool calls execute on the host: a model emitting pseudo-tool text does not execute actions. Validate tool calls against exposed JSON schemas. Reject unknown tool names cleanly and return supported schemas; do not invent success.

## Mapping from Anthropic-specific doctrine

| Existing doctrine | GPT move |
|---|---|
| `claude-*` IDs and universal `xhigh` | Resolve approved GPT ID and supported effort from catalog; omit unsupported knobs with explicit disclosure |
| Anthropic-specific refusal classifier / Opus reroute | Keep concise safe request and explicit blocked state; use only approved in-provider fallback, never policy circumvention |
| Top tier for every evaluator | Select independent grader by measured reliability and budget; deterministic checks first |
| `.claude/profile.yaml` default Anthropic | Observe endpoint/model/provider and explicit project policy; legacy default only in confirmed native Claude context |
| Claude tool spellings in allowed-tools | Host adapter maps semantic capability; model name alone grants none |
| Narrated reasoning discouraged | Preserve concise answer/evidence; no chain-of-thought extraction requested |
| 1M context reassurance | Scoped retrieval, checkpoint and fresh-context packet; do not assume infinite context |

## Image proxy status

No GPT model is currently allowlisted by the repository's dense-glyph reading sweep. Default **not allowed** for pxpipe; preserve byte-exact values in text.
