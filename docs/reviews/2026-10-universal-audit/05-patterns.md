# Engineering patterns — W5

## Decision rule

Use the simplest mechanism that preserves the owning invariant. A universal skill is not one that silently substitutes a weaker check; it declares supported mode, proof and limitations. Sources below were checked against live official pages during this audit (2026-10-02); recommendations are proposals, not installed behavior.

## Workflow primitives: good doctrine, excessive coupling

Source: Anthropic [Building effective agents](https://www.anthropic.com/engineering/building-effective-agents) (December 2024): distinguish predictable workflows from agent-directed tool use; use chaining, routing, parallelization, orchestrator-workers and evaluator-optimizer where they pay; prefer simple composable patterns. This is not proof of any current model's benchmark performance.

| Primitive | Existing good application / evidence | Shortfall | Concrete change / why it pays |
|---|---|---|---|
| Prompt chaining | Contracts precede role dispatch in [orchestrator:103](../../../skills/orchestrator/SKILL.md#L103); source boundary authoring distinct from static auditor and runtime QE | Single-agent path does not specify proof/checkpoint transitions and can contradict no-implement rule | Preserve phase contracts; explicit attended role-pass packets and block on failed input proof, UA-03. Prevents “all phases completed” narrative without artifacts |
| Routing | [madness:66](../../../skills/meta/madness/SKILL.md#L66) chooses by unresolved decision and asks cost consent; [yagni-gate](../../../skills/workflows/yagni-gate/SKILL.md#L20) supports no-build option | Router can choose role/loop unavailable after conversion; broad overlap skill-writer/creator and wiki/interactive-doc needs output-based routing | Resolve capability/installation availability before launch; route simple authoring to writer, empirical optimization to creator, source mapping to deep-dive, persistent knowledge to wiki; do not add router skill, UA-02/17 |
| Parallelization | [team-sizing:18](../../../skills/orchestrator/references/team-sizing.md#L18) counts actual concurrent work; [file-ownership:16](../../../skills/orchestrator/references/file-ownership.md#L16) prevents conflicting edits | More workers cost tokens and do not help dependency chains; no subagent here | Parallel only independent ownership/dependency slices; sequential independent sessions equivalent for isolation but slower; never tool-call parallelism as substitute for agents |
| Orchestrator-workers | [agent-spawning:9](../../../skills/orchestrator/references/agent-spawning.md#L9) avoids nonexistent subagent types; role doctrine remains separate | Host-name gates suppress useful workers even where Codex/Gemini/Cursor/Hermes document isolation | Shared doctrine plus native/generated adapter; preserve CC opt-ins and contracts, UA-01/02 |
| Evaluator-optimizer | [loop-controller:81](../../../skills/loops/loop-controller/SKILL.md#L81) requires measurable proof; [circuit-breaker](../../../skills/orchestrator/references/circuit-breaker.md#L1) escalates repeated failure | Builder selfgrade or mutable criteria can certify itself; strict checker can fail open; creator optimization evaluates wrong candidate | Independent evaluator with frozen inputs/rubric, deterministic checks first; fail-closed errors and split hygiene, UA-12/14/17/18 |

Small read-only interviews (`grill-me`, `zoom-out`, `architecture-rescue`) do not need state-machine engines or multi-agent wrappers. Scheduled operations and dependency DAGs do need explicit controller state because they must survive timeouts, retries and partial completion.

## Explicit state and resumability: adopt the contract, not a framework

Source: [LangGraph persistence](https://docs.langchain.com/oss/python/langgraph/persistence): checkpointer state is associated with a thread, checkpoints enable recovery/human intervention; durable stores differ from in-memory persistence. SQLite/Postgres are examples, not dependencies already adopted here.

The repo already has substantial state concepts: [task-loop dependencies and rollback:54](../../../skills/loops/orchestrator-task-loop/SKILL.md#L54), [circuit breaker](../../../skills/orchestrator/references/circuit-breaker.md#L1), [handoff protocol:12](../../../skills/orchestrator/references/handoff-protocol.md#L12). What is missing is a portable machine-checkable transition contract between those artifacts, particularly for the sequential branch. No evidence justifies replacing native Workflow with LangGraph.

Proposed minimal graph:

```text
DISCOVER -> APPROVED_PLAN -> CONTRACTS_VALID -> READY_QUEUE
READY_QUEUE -> BUILD_SLICE -> OBJECTIVE_VERIFY
OBJECTIVE_VERIFY --fail within limit--> BUILD_SLICE
OBJECTIVE_VERIFY --pass--> INDEPENDENT_REVIEW
INDEPENDENT_REVIEW --findings--> READY_QUEUE
INDEPENDENT_REVIEW --pass, exact revision--> ACCEPTED
ANY --checker error / missing authority--> BLOCKED
ANY --budget/circuit/cancel--> STOPPED
ANY --human decision--> PAUSED
```

Each transition requires `{run_id, source_revision, contract_digest, task_id, owner, prior_state, next_state, proof_paths, verifier_digest, usage_reservation, timestamp}`. This is a design example, not a current schema. Checkpoint after a completed transition; resumed job rereads code/revision/authority and invalidates obsolete proof. Writes/commands use idempotency keys where applicable; a resumed deploy must not automatically repeat an external mutation. A human approval cannot be reconstructed from model text.

Start with a versioned JSON/file-backed controller and an attended checklist reader. If concurrent workers are approved, add locked state/claim and cancellation. Native Claude Workflow/teams remain preferred on their existing opt-in path. This pays here by making “sequential fallback,” rollback and restart precise, rather than creating an ecosystem framework for small skills. F15/F16 already park runner/scheduler substrates; [FUTURE:63](../../../docs/FUTURE.md#L63) must be reconciled rather than shadowed.

## Loop engineering and adversarial termination

Sources: [Ralph operator pattern](https://ghuntley.com/ralph/) describes the shell loop; it does **not** establish safe termination, approvals or spend control. [Reflexion paper](https://arxiv.org/abs/2303.11366) studies verbal feedback/episodic memory; feedback can aid iteration but is not a correctness or security proof for current coding models.

Strong existing work:

- Five-part action/proof/stop/guardrail/artifact contract and default-FAIL completion in [loop-controller](../../../skills/loops/loop-controller/SKILL.md#L81).
- No-progress/oscillation, retry and stop-hook recursion doctrine in [safety:40](../../../skills/loops/loop-controller/references/safety.md#L40); quantitative-metric anti-cheat [97](../../../skills/loops/loop-controller/references/safety.md#L97).
- Full integrated install/typecheck/test gate rather than agent claims in [wave-gate:28](../../../skills/orchestrator/references/wave-gate.md#L28).

Shortfalls and fixes:

1. **Bound iterations outside the model.** `/cost` observation and `/goal` prompt budget are not guaranteed hard cancellation. Ralph templates need wrapper max runtime/calls/token/cost and lock/kill handling on every path, UA-13. Attended one-pass mode can be useful without pretending to be an overnight loop.
2. **Verifier errors are a separate terminal state.** Strict QA missing/crashed validator allows today; migration grep must distinguish match/no-match/error, UA-12/14/31. “No findings because no file could be read” is BLOCKED, not PASS.
3. **Freeze the measure.** Coverage denominator/exclusions/assertions, perf workload/dataset/hardware/config, tests and acceptance contracts cannot be weakened by workers. Existing prose is strong; external read-only verifier snapshot plus reviewer approval closes cheap metric escapes.
4. **Reflection is bounded memory, not self-certification.** Save root cause, attempted action, observed result and next falsifiable hypothesis; don't keep every chain of thought or trust a narrative as proof. Expire contradictory/stale hypotheses when revision changes.
5. **Independent acceptance.** A deterministic verifier can restore independence for objective tests. Subjective architecture/UI acceptance needs fresh reviewer context or human; different provider alone does not make a reviewer independent if fed builder reasoning.

Per-loop plans and the full gate-gaming register appear in [core report](03-multi-agent-core.md). TaskCompleted/TeammateIdle reference templates are not automatically shipped installed hooks: [manifest](../../../hooks/hooks.manifest.json#L1) has six different existing events.

## Context engineering and model-portable prose

Sources: Anthropic [Effective context engineering](https://www.anthropic.com/engineering/effective-context-engineering-for-ai-agents) treats context as finite attention, emphasizing scoped tools, retrieval, compaction and isolated subagents. [OpenAI reasoning best practices](https://developers.openai.com/api/docs/guides/reasoning-best-practices) favors direct goals/simple instructions and does not require prompting chain of thought. Both discuss clear delimiters; XML is not inherently Claude-only. [Agent Skills specification](https://agentskills.io/specification) formalizes progressive disclosure and self-contained relative resources, recommending fewer than 5,000 tokens / 500 lines in the body.

Already good:

- [context-manager](../../../skills/workflows/context-manager/SKILL.md#L20) and [handoff startup:71](../../../skills/orchestrator/references/handoff-protocol.md#L71) preserve task state on disk and reread boundaries.
- [skill-writer:64](../../../skills/meta/skill-writer/SKILL.md#L64) uses progressive disclosure; large reference trees in Payload, model-adaptation and orchestrator defer detail.
- [long-run hygiene](../../../skills/meta/model-adaptation/references/long-run-hygiene.md#L1) already scopes/reset contexts. No need to invent session-handoff as a competing memory system.

Gaps:

- Orchestrator's **5,463 body words** are not 5,463 tokens; all active files under 500 physical lines does not establish the token recommendation. [Inventory](evidence/inventory.json) measures words/lines only. Measure with a supported tokenizer or label approximation, then move native dispatch mechanics into on-demand adapters (UA-30). Do not undo RV16's already-completed shortening as if it never happened.
- Existing [model facts:92](../../../skills/meta/model-adaptation/SKILL.md#L92) and [DeepSeek reference:31](../../../skills/meta/model-adaptation/references/deepseek-adaptation.md#L31) assert 1M/384K windows. Their current vendor/model accuracy is **UNVERIFIED here**; neither an unknown model nor a large advertised window licenses reading the whole repo. Detect model/endpoint limits if exposed; use small packets and revision-bound continuation.
- Long “pushy” descriptions/all-caps warnings are **not demonstrated trigger improvements**. [CLAUDE:60](../../../CLAUDE.md#L60) is house authoring guidance; [performance-notes:14](../../../skills/meta/skill-writer/references/performance-notes.md#L14) already scopes encouragement to prior generations. Test positive and near-miss prompts against baseline; use short direct requirements before adding emphasis. No blanket XML removal, no assumption that every current GPT needs the older `Formatting re-enabled` workaround.
- Model-native opaque reasoning/signature metadata must be preserved by the transport. A Markdown handoff stores task state, not those wire objects or hidden reasoning. Gemini APIs have distinct signature representations; see [Gemini draft](04-model-adaptation-drafts/gemini-adaptation.md).
- Wikis are discovery aids, not current-code certification: [wiki-research:75](../../../skills/workflows/wiki-research/SKILL.md#L75), UA-28. Carry revision/date and verify touched boundaries now.

## Spec/eval-driven development: tiny cross-model harness

This is an **extension of existing F3/F5**, not a new untracked platform: [FUTURE:15–31](../../../docs/FUTURE.md#L15), [split hygiene standard](../../../docs/standards/eval-split-hygiene.md#L1). Current CI checks shape/fixtures, not live skill retrieval or task efficacy; creator's current runner cannot establish either because of UA-17/18. Source for evaluator-optimizer: Anthropic agent patterns above; grading/split requirements already live in this repository's F5/HE doctrine.

### Separate four tests

| Layer | What it tests | Cheap falsifier |
|---|---|---|
| Resource/load smoke | Correct discovered skill, description and resource closure on installed host | Script/template not found; stale skill hash; treatment not loaded |
| Trigger selection | Would normal unforced retrieval select the skill on positive prompts and reject near-misses? | Forced `-s` loading or stdout name mention is not retrieval evidence |
| Efficacy | Same task/authority/tools/model with vs without the skill improves accepted artifact | Wrong candidate bytes, changed model midway, easier verifier or single lucky rollout |
| Safety/degradation | Missing capability, checker error, budget breach and harmful action are refused/paused correctly | Model reports PASS on unread files; loop exceeds wrapper limits; hidden global install |

### Minimal task suite and selection

Begin with local deterministic fixtures, then explicitly approved small paid/host smoke runs:

- Frontend: four authored pages, copied chrome, inline HTML/JSX, hashed duplicate declarations, dynamic-variable exception, two widths. Outcome = correct reusable source layout; proof = guard receipts and visible UI; architecture = owning shared shell unchanged.
- Core: tiny dependency DAG; failed objective test; independent review finding; interruption/resume after revision change. Acceptance must not precede exact-revision proof.
- Loop: pinned failing test, fake checker crash and fixed max attempts/time. Measure refusal and cap enforcement, not just eventual green.
- Git: offline `gh` fixture validating supported arguments and unresolved-thread follow-up. No real PR/tag mutation.
- Delivery: fake HOME install/dry-run, nested resources, executable bit, stale hash, destination escape and native Claude byte/activation invariants.
- Creator: known retrieval traces, two different descriptions, worker timeout and unseen final set. Failure cannot score as a correct negative.

Every skill eventually has a success contract: objective scripts for build/guard/git, blinded rubric + artifact for analysis/design/interviews. Read-only skills should not be forced into code-changing benchmarks. Matrix identifies purpose and output but **does not claim a runtime success check was empirically exercised for every row**.

### Record and grade

Example record (proposed, not a current interface):

```json
{
  "run_id": "audit-example",
  "skill_hash": "sha256-of-installed-candidate",
  "host": {"name": "observed-host", "version": "observed-version", "mode": "attended"},
  "model": {"provider": "observed", "endpoint": "approved", "id": "observed", "effort": "supported-value"},
  "split": "dev",
  "task_id": "frontend-reuse-01",
  "retrieval_proof": "trace-path",
  "outcome": "pass",
  "proof": "pass",
  "architecture": "pass",
  "execution": "valid",
  "trajectory": {"calls": 3, "seconds": 90, "cost": null},
  "budget_status": "within-approved-call-and-time-caps"
}
```

`null` cost means unknown, **not zero**; no paid unattended run with an unknown monetary liability. Acceptance requires outcome + proof + architecture; cost/latency/retries/human attention are separate diagnostics. Pre-register a falsifying result and immutable verifier hash. Use multiple seeds/rollouts where stochastic behavior matters; report sample size/uncertainty and blocked/skipped cells, never an aggregate “universal” percentage from structural lint.

Keep train/dev/held-out split, tune and choose on dev, touch final held-out once. Never give its outcomes to optimizer or repeatedly select max test score. Redact secrets/session cookies; trace tool calls and retrieval metadata, not hidden reasoning. Differential treatment compares same model/host/resource/authority; host comparisons require a separately reported capability condition. Use serial jobs and cached fixtures before paying for N-model parallelism.

Budget: explicit approved total/cell call/runtime/spend caps, model IDs checked against endpoint catalog, reserve before dispatch and cancel on cap. Deterministic no-model checks first; cheapest consented worker that meets contract; escalate once on documented failure class; independent strong reviewer only for high-value ambiguity. [Cost draft](04-model-adaptation-drafts/cross-vendor-tiering.md) does not invent current prices.

## Open standards: portable envelope, not automatic execution or safety

| Standard / source | What pays here | What it does not prove | Proposed application |
|---|---|---|---|
| [AGENTS.md](https://agents.md/) | Common project-instruction discovery, with nearer nested instructions | Host tool availability, paid identity or sandbox | Preserve CLAUDE native instructions; project-neutral policy source and generated host projections. Check nesting and scoped authority |
| [Agent Skills](https://agentskills.io/specification) | SKILL.md progressive loading, relative scripts/references/assets | Hooks, team scheduling, forced invocation or native tool arrays on every loader | Self-contained resource closure + export serialization; current PSFS allowed-tools array/metadata type adapters, UA-25 |
| [MCP 2026-07-28](https://modelcontextprotocol.io/specification/2026-07-28) | Shared tools/resources/prompts; optional Tasks/Skills/Apps surfaces may support adapters | Context isolation, hard budgets, permissions, durable scheduler or acceptance independence merely because a server exists | Trusted scoped executor/browser/state tools after semantic probe; annotations/content remain untrusted. Exact server implements needed contract or mark missing |

MCP can expose a verifier, queue, file store or browser across hosts; it cannot make a bare model execute tools without a harness, nor replace independent reviewers with a tool name. No need to write a new MCP server skill now (F10 already parked). Start with existing shell/JSON verifier interfaces; add MCP only when it removes actual duplicated host integration work.

## Adoption order and non-goals

UA-08/12 safety fixtures → frontend invariant gates → resource closure → tiny capability/graph adapter → creator measurement repair → approved F3/F5 cells. Do not add LangGraph, an autonomous router, a second handoff system or a general hook-forge because a pattern is fashionable. Native Claude execution remains intact; inexpensive attended paths become first-class, explicitly honest modes.
