# Host-capability model — W2

## Separate four axes

A **model** reasons and emits tool requests. A **host** executes them. An **installation** exposes skill resources. An **authority policy** permits actions and spend. DeepSeek can run inside Claude Code; GPT can run inside Codex or a bare harness. Neither model identity proves a scheduler, filesystem, browser, or subagent exists.

Current evidence: [converter filter:711](../../../scripts/convert.sh#L711) excludes 37 skills for every non-Claude target; [orchestrator runtime:119](../../../skills/orchestrator/SKILL.md#L119) already distinguishes Workflow, teams, subagents and sequential. [PSFS:126](../../../spec/PSFS.md#L126) encodes binary host/plan flags instead. Preserve the native tree; make its alternatives explicit.

## Capability vocabulary and fallback contract

Capabilities are semantic contracts, not aliases for a similarly named tool. Resolver output records supported, enabled, permitted, observed/probed, quality, and evidence. Unknown is not unsupported, but cannot satisfy a required safety capability. Probes must be read-only/no-cost by default; ask before executing a billed model, launching a browser with logged-in cookies, installing anything, or modifying schedules.

| Capability | Required semantics | Fallback ladder | Rating / refusal rule |
|---|---|---|---|
| `read_files` | Paths scoped to project; bounded reads; missing-file status | Native file tools → read-only shell → user-provided files | Equivalent with scope; pasted snippets degraded; refuse claims about unread files |
| `write_files` | Scoped edits; prior read; atomic replace and failure | Native edit → approved shell/file API → patch for human | Equivalent scoped API; human apply degraded; no applied-change claims before confirmation |
| `run_shell` | cwd, stdin, exit status, deadline, cancellation | Native terminal → trusted MCP executor → user runs bounded command | Equivalent only with exit evidence; human run safe degraded; no autonomous loop without runtime control |
| `web_fetch` | URL, status, text, provenance; untrusted content | Fetch/search → browser → supplied dated source | Degraded if not current; mark vendor/current facts UNVERIFIED |
| `spawn_subagent` | Separate context, scoped tools, identifiable result | Native child → approved separate CLI/API session → human launches second session | Equivalent only after verified isolation; same-session roleplay is not a child |
| `parallel_subagents` | Independent workers, limits, barrier/cancel | Parallel native → independent sequential sessions | Safe degraded: loses speed, retains independent context; do not share overlapping writes |
| `team_messaging` | Addressed messages, delivery acknowledgement | Native inbox → orchestrator relay → file inbox + polling | Safe degraded if messages/version acknowledgements recorded; no acknowledgement means block dependent work |
| `shared_task_list` | Stable IDs, dependency DAG, ownership, status and proof | Native tasks → locked file queue → attended checklist | Safe degraded sequential; unsafe concurrent claims without locks |
| `schedule_recurring` | Durable cadence, timezone, run locks, cancellation | Native scheduler → approved OS cron/CI → attended one-shot | OS/CI equivalent only with execution and overlap guarantees; attended one-shot degraded; never infinite Ralph as substitute |
| `completion_gate` | External proof verifier and fail-closed decision | Native stop hook → wrapper/CI script → independent reviewer + explicit checklist | Script can be equivalent for objective criteria; self-check alone not equivalent; refuse unattended subjective acceptance |
| `ask_user_structured` | Real human reply/approval, not model-generated answer | Native choices → numbered plain question → file approval packet | Equivalent if explicit authorization preserved; absence of reply means paused |
| `persistent_memory` | Durable scoped state, provenance and revision | Native memory → handoff/JSON files → human-copied packet | Files equivalent for task state; lossy compaction degraded; secrets never in public handoff |
| `browser_automation` | Navigate/interact, screenshot, console/network; declared visible/auth state | Native browser → approved browser MCP → visible Playwright → human browser evidence | Equivalent only for required observations; screenshots alone cannot prove interaction; unavailable UI validation is BLOCKED |
| `artifact_publish` | Output, access policy, owner, URL, retention | Native Artifact → approved hosting → local complete HTML | Local file safe degraded, not a private hosted link; never silently publish public |
| `lifecycle_hooks` | Documented event/I/O, bounded invocation, tested wiring | Native hooks → wrapper stage callbacks → explicit attended stages | Safe degraded; “hook file exists” is not “hook fired” |
| `independent_evaluator` | No builder history, read-only artifacts, frozen rubric, fresh tools | Native isolated reviewer → separate session/model → human + objective verifier | Same model can be independent context; different vendor optional, not proof of independence. Same-session selfgrade unsafe for final subjective gate |
| `budget_enforcement` | Reserve then account spend; external max calls/tokens/runtime/cost | Native hard cap → harness wrapper → human attended cap | Equivalent wrapper; monitoring alone degraded only attended; refuse unattended without cancellation |
| `permission_scope` | Paths/actions/network/account allowlist; human approvals | Native sandbox/permissions → container/restricted executor → human applied patch | Safe only after explicit scope; broad allowlist is not containment |
| `workflow_graph` | Explicit states/transitions/checkpoints/idempotency | Workflow engine → small JSON/file-backed state runner → attended state checklist | Engine choice optional; transition/proof integrity required |

## Verified host map

**N** = documented native feature, not exercised here. **H** = shell/file/harness adapter proposed. **U** = UNVERIFIED in current host documentation or current installation. **D** = deliberate human-assisted degradation. This is not a vendor marketing capability comparison. All runtime flags/version/permissions must still be probed. Claude mappings are repository-declared, not re-certified against every current Claude API; non-Claude mappings below use live official pages fetched during this session.

| Host | Files / shell / web | Isolated and parallel workers | Teams / tasks | Schedule | Completion / lifecycle | Questions / memory | Browser / publication |
|---|---|---|---|---|---|---|---|
| Claude Code | Repo uses Read/Write/Edit/Bash/WebFetch | Agent; Workflow `agent/parallel`; teams when enabled | TeammateTool/inbox + native task list | Repo declares `/loop`, CronCreate/ScheduleWakeup; version/plan probe | Stop/SubagentStop; event adapters; manifest currently six hooks | AskUserQuestion/TodoWrite; handoff files / native memory | Playwright MCP or visible shell browser; Artifact if exposed |
| Codex CLI | Host file/shell; exact current wire names U | **N:** parallel subagent workflows, `/agent`, custom agent model/effort | Claude-style inbox/task events U; H queue/relay | Native recurring CLI mechanism U; H cron/CI | Native stop contract U; H wrapper/CI | D questions; AGENTS + H handoffs | Browser/MCP provider U here; H Playwright; H local HTML |
| Gemini CLI | Host tools; settings adapter | **N:** independent context specialized subagents; parallel semantics require probe | Claude team task events U; H queue | Native cron U; H cron/CI | **N:** Before/AfterAgent, Before/AfterTool, SessionStart etc; AfterAgent retry/halt | D questions; config + H task memory | **N:** browser agent disabled by default, visible by default; publication H |
| Cursor | Host files/shell; tools enabled by mode | **N:** isolated foreground/background and parallel subagents | H queue/relay; Claude team equivalence U | Native recurring interface U; H schedule | **N:** stop, pre/post tool, subagent hooks; cloud source/event restrictions | D questions; project rules + H memory | **N:** Browser subagent via MCP; local/approved-host HTML H |
| OpenCode | **N:** Build full tools; Plan asks edit/bash | **N:** general/explore/scout; general parallel work | H queue/relay | U; H schedule | Native stop-gate semantics U; H wrapper/plugin after verification | Agent switching is not independent review; H disk memory | MCP/browser integration requires configured tool; publication H |
| Aider | Read/write chat files; shell automation details U | Native isolated delegation U; D separate sessions | D checklist | H cron/CI | H external lint/test runner; native loop hook U | Plain questions; `/read` and configuration files | H Playwright/human; H local HTML |
| Hermes | Child terminal/tool inheritance documented | **N:** `delegate_task`, isolated children and batch; default up to ten concurrent | H queue/messages unless live probe proves stronger | **N:** `cronjob_manage`, fresh sessions, no-agent scripts, recursion disabled | Exact stop/lifecycle contract U; H external verifier | User-owned model pins; H handoffs; native memory U here | Browser/publication surface U; H approved adapters |
| Devin | Skill docs demonstrate files, shell, browser | Session orchestration mentioned, exact delegation/independence U | H review packets/queue | U; approved external scheduling H | Native completion-gate contract U; H CI | Repository `.agents/skills`, user questions; H task memory | Browser examples N; exact Artifact equivalent U; H hosting |
| Freebuff / generic DeepSeek/GPT harness | **Observed here:** read/edit/shell/search/fetch, structured questions, todo tracking | **Not exposed here:** spawn/team/Workflow; tool-call parallelism is NOT agent parallelism | H disk task graph | No scheduler exposed in this session | No blocking Stop/lifecycle authority exposed; file-change hooks are optional checks | Native structured question tool; disk reports and managed context summaries | Native browser panel tools exposed; no Claude Artifact; local HTML preview is not publication |
| Bare API loop | None unless application supplies executors | H separate inference contexts; never implied by model | H queue/lock/relay | H external timer | H deterministic controller with cancellation | Application question queue and storage | H browser/MCP and approved object hosting |

### Live host source register

- [Codex subagents](https://learn.chatgpt.com/docs/agent-configuration/subagents): current releases default-enabled; subagents spend additional tokens; model/effort inheritance unless explicitly selected.
- [Gemini subagents](https://geminicli.com/docs/core/subagents/) and [hooks](https://geminicli.com/docs/hooks/): independent context; browser enable/consent; stdout must be JSON, pollution can fail open. Never copy Claude's success log to Gemini stdout.
- [Cursor subagents](https://cursor.com/docs/subagents), [hooks](https://cursor.com/docs/hooks): parallel contexts; cloud hooks differ from local and user-level hooks do not transfer to cloud VMs.
- [OpenCode agents](https://opencode.ai/docs/agents/): global `~/.config/opencode/agents/`, project `.opencode/agents/`; this differs from [plan installer destination:192](../../../scripts/install-plan.sh#L192).
- [Hermes delegation](https://hermes-agent.nousresearch.com/docs/user-guide/features/delegation), [cron](https://hermes-agent.nousresearch.com/docs/user-guide/features/cron): child background processes die on child teardown; completion admission is not proof of successful downstream model turn.
- [Devin skills](https://docs.devin.ai/product-guides/skills), [Aider conventions](https://aider.chat/docs/usage/conventions.html): Devin `.agents/skills`; Aider file copy requires `/read`, `--read`, or config activation.

The converter comment “Only Claude Code has a native lifecycle-hook system” at [convert:934](../../../scripts/convert.sh#L934) is **refuted by Gemini and Cursor official docs**. Lack of a shipped adapter is real; lack of host capability is not.

## PSFS proposal — additive migration, not immediate rewrite

These examples are **draft future schema**, not valid additions under today's closed `additionalProperties:false` [schema:113](../../../spec/frontmatter.schema.json#L113). Keep legacy fields until all loaders/converters support the version; native Claude exports retain native allowed-tools/hooks/model-invocation behavior. Frontmatter metadata is not a permission grant.

```yaml
name: orchestrator
version: 2.0.0
requires_claude_code: true  # compatibility during transition, not final resolver input
requires_agent_teams: false
min_plan: starter          # deprecated informational legacy field
requires_capabilities: [read_files, write_files, run_shell, ask_user_structured]
execution_modes:
  claude-native:
    requires: [spawn_subagent, completion_gate]
    adapter: references/hosts/claude-code.md
  parallel:
    requires: [parallel_subagents, independent_evaluator, completion_gate]
    adapter: references/hosts/parallel.md
  attended-sequential:
    requires: [ask_user_structured, independent_evaluator]
    adapter: references/hosts/sequential.md
    quality: degraded-safe
optional_capabilities: [team_messaging, shared_task_list, workflow_graph]
refuse_if: [unattended_without_budget_enforcement, subjective_gate_without_independent_evaluator]
```

Today: orchestrator `requires_claude_code:true` plus [one paragraph sequential:153](../../../skills/orchestrator/SKILL.md#L153). After: shared design/contracts/ownership/QE body; semantic execution modes above; native teams/Workflow selected only by existing opt-in signals, never silently by model identity. An attended-sequential adapter can involve human launching reviewer sessions; if that is unavailable, report unverified/BLOCKED rather than claiming equivalent completion.

```yaml
name: fix-until-green
version: 2.0.0
requires_capabilities: [read_files, write_files, run_shell]
execution_modes:
  claude-native:
    requires: [completion_gate]
    adapter: references/hosts/claude-code.md
  bounded-wrapper:
    requires: [budget_enforcement, permission_scope, completion_gate]
    adapter: references/hosts/wrapper.md
  attended:
    requires: [ask_user_structured]
    adapter: references/hosts/sequential.md
    quality: degraded-safe
optional_capabilities: [spawn_subagent, persistent_memory]
refuse_if: [unattended_without_budget_enforcement]
```

Today: [fix-until-green:4–9](../../../skills/loops/fix-until-green/SKILL.md#L4) dispatch-only and host-gated. After: exact test/lint/typecheck command set immutable; one root cause per pass; full proof on finish; bounded controller rather than “stop after N” in prose.

### Body convention

Each canonical skill begins with Purpose, Inputs, Output/proof, Host adapters, Authority/limits, and common doctrine. `Host adapters` declares selected mode and rating in one sentence, loads only relevant `references/hosts/*.md`, states missing capabilities, and lists what will be blocked/deferred. Heavy skill native plumbing moves into host refs; small skill uses a short inline ladder. Paths resolve through explicit `SKILL_ROOT`, not `~/.claude` guessing. Don't inline all adapters into every prompt.

### Toolchain migration and Claude regression conditions

1. PSFS spec/schema/linter gain enumerated capabilities, mode requirements, unique names, resolvable adapter paths, refusal predicates, and documented unknown-field loader policy. Separate tolerant load from strict author lint; Agent Skills export maps tools to its experimental string format and metadata to string-map.
2. Add one resolver receiving observed host capabilities/version, model wire capabilities, authority and installed resource manifest. It outputs mode, missing prerequisites and evidence. No inferred paid plan or model ID from unknown session metadata.
3. Converter emits canonical doctrine plus selected adapter/resources, not blanket deletion; unsupported feature logs are truthful. Codex/Hermes/Devin targets must be explicit before claiming install reach. Keep Windsurf: already implemented.
4. Sync becomes delivery mode of the same projection, with owned-link manifest; raw-native CC symlinks remain an allowed fast path. No raw non-Claude link bypasses compatibility resolution.
5. Install verifies resource closure, checks bytes/modes, owns only its files, and preserves hooks' host-specific event contracts and opt-in wiring.
6. Regression fixtures assert unchanged native Claude outputs and activation semantics for teams/subagents/Workflow, fixed resource completeness, QE nonoverride, ownership, refused actions and cost cap. Compare semantic output excluding timestamp, not just counts.

Do not add a giant dependency framework to implement this vocabulary. Start with files/JSON and a small resolver, preserving the already-working native controller. F1/WC3 broad declarative-host refactor is parked; the immediate case-study adapters have demonstrated demand.
