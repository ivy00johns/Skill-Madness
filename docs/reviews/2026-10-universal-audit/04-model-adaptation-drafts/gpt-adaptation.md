# OpenAI / GPT adaptation — draft, not installed

Depth proposed for model-adaptation, matching the existing [DeepSeek reference](../../../../skills/meta/model-adaptation/references/deepseek-adaptation.md#L1). Facts checked against live official docs in this audit on **2026-10-02**; dated legacy examples are not current universal guarantees. Host capability detection remains separate.

## Why GPT is in scope

The owner reported a GPT Luna frontend refusal followed by inline CSS, hash classes and repeated chrome. The particular transcript, actual model identity, effort, host exposure, and generated site are **UNVERIFIED**. The repository host/dispatch filter and guard escapes were verified in [core case study](../03-multi-agent-core.md). Do not attribute those failures to model quality when the role was not delivered or declared itself inapplicable.

## Current landscape — verified names, unknown entitlements/prices

[Official Codex subagent documentation](https://learn.chatgpt.com/docs/agent-configuration/subagents), fetched this session, names `gpt-6-luna` for faster/lower-cost lighter work and `gpt-6.1-sol` for demanding work. It says model availability depends on account/workspace and agents may inherit model/effort. Those are verified **documentation statements**, not availability of either model in this session or proof that the owner's “Luna” was that exact identifier. Exact prices, context length, output cap, accepted API effort values, latency and superiority on Skill Madness are **UNVERIFIED**. Query the approved endpoint/catalog before selecting them.

| Candidate tier | Selection rule | Known / unknown |
|---|---|---|
| Mechanical | Cheapest available model that passes tool/format and held-out task checks | Luna named for lighter subagents in Codex docs; actual billing/effort UNVERIFIED |
| Implementation | Lowest-cost model passing task outcome/proof/architecture gates | No universal fixed GPT ID or effort default asserted |
| Independent review | Clean-context model with demonstrated reviewer quality | Sol named for demanding work; not compulsory for every review |

## Prompting and thinking adaptation

[OpenAI reasoning best practices](https://developers.openai.com/api/docs/guides/reasoning-best-practices), retrieved in full this session, recommends simple/direct instructions, specific successful outcomes, explicit constraints, zero-shot first then aligned examples when needed, and avoiding requests to “think step by step” or narrate chain of thought. It explicitly permits **Markdown, XML tags and section delimiters**. Therefore XML in [orchestrator](../../../../skills/orchestrator/SKILL.md#L57) is not inherently Claude-only and needs no cosmetic mass rewrite.

The same page contains o1/o3/o4-era family descriptions. Treat those as scoped examples, not a claim about every new GPT. Its `Formatting re-enabled` workaround is explicitly o1-era API behavior; **do not inject it universally**. Likewise developer/system role choice is an endpoint/model adapter decision, not canonical skill-body prose.

Operational template:

```text
Task: implement the approved frontend scope using the standalone role doctrine.
Constraints: shared header/footer source; stylesheet layout classes; no inline layout.
Allowed work: scoped source edits and local tests only; no deploy or global installs.
Proof: current test/typecheck results; source guards; visible mobile/desktop checks.
Missing tool: choose the declared safe adapter or report BLOCKED; do not abandon doctrine.
Return: changed artifacts, evidence, unresolved decisions, and remaining budget.
```

This is a portable contract, not an asserted GPT-specific magic prompt. All-caps warnings may mark invariants, but repeat them only when measured failure warrants it. Cheap models benefit from concrete examples/short ordered stages; that hypothesis requires eval, not vendor folklore.

## Wire and tool-call continuations

The reasoning guide states that Responses API reasoning items associated with tool calls can improve continuity and reduce repeated reasoning; it recommends passing relevant prior output items or using continuation IDs. Chat Completions has different stateless semantics. Preserve opaque reasoning/tool items according to the chosen endpoint/SDK rather than translating everything into text. Whether current Luna/Sol accept a particular continuation mode is **UNVERIFIED** until endpoint validation.

The application executes tools. A model emitting `TeamCreate` text does not create a team. Exposed tool JSON schemas, actual tool results, scope and deadlines are the harness's authority. Reject unknown tool names cleanly and return a supported-tool listing; do not invent success.

## Mapping from Anthropic-specific doctrine

| Existing doctrine | GPT move |
|---|---|
| `claude-*` IDs and universal `xhigh` | Resolve approved GPT ID and supported effort from catalog; unsupported setting is error/omitted with explicit disclosure |
| Anthropic-specific refusal classifier / Opus reroute | Keep concise safe request and explicit blocked state; use only approved in-provider fallback, never policy circumvention |
| Top tier for every evaluator | Select independent grader by measured reliability and budget; deterministic checks first |
| `.claude/profile.yaml` default Anthropic | Observe endpoint/model/provider and explicit project policy; legacy default only in confirmed native Claude context |
| Claude tool spellings in allowed-tools | Host adapter maps semantic capability; GPT name alone grants none |
| Narrated reasoning discouraged | Preserve concise answer/evidence; no chain-of-thought extraction requested |
| 1M context reassurance | Actual model/harness limit unknown: scoped retrieval, checkpoint and fresh-context packet |

## Cost ladder instantiation

Keep single-provider default, cheap mechanical work, strongest affordable reasoning where it pays, and one-time strong skill author/optimizer as in existing MT1/MA2 doctrine. Add explicit approved cross-provider review only under [cross-vendor policy](cross-vendor-tiering.md). No hardcoded GPT prices are verified here. Record reserved maximum and observed usage, not estimated savings from a model label.

## Audit additions for GPT runs

1. Confirm whether host is Codex, Freebuff, or bare API; test skill/resource presence before blaming model.
2. Ensure portable role/plan route does not reject solo execution.
3. Verify one file/tool/exit-code/structured-output round trip; paid probe requires approval.
4. Keep builder and evaluator context separate. Codex subagents are documented, but this Freebuff session exposes no agent spawning.
5. Protect CSS/layout/test/config criteria from rename-only or metric-only fixes.
6. Record exact model ID, endpoint, effort, skill hash, adapter and outcome; missing identity = UNVERIFIED.

## Image proxy status and consumer wiring

No GPT model is measured/allowlisted by the repo's glyph sweep. Default **not allowed** for pxpipe; preserve byte-exact values in text. Do not extrapolate vision support into dense glyph fidelity.

Orchestrator role dispatch and loop-controller select capabilities before model tier; solo frontend doctrine runs whether or not a child agent exists. Model-adaptation owns this reference; converter should export it progressively rather than inline all vendor documentation into every rule file.
