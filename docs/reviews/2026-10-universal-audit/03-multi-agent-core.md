# Multi-agent core and frontend failure — W3

## What is worth preserving

Contract-first interfaces, single file ownership, read-before-edit, actual service/browser proof, a QE gate the coordinator cannot override, and a three-failure circuit breaker are valuable regardless of host. [Orchestrator:85–114](../../../skills/orchestrator/SKILL.md#L85), [phase guide:174–204](../../../skills/orchestrator/references/phase-guide.md#L174), [ownership:5–29](../../../skills/orchestrator/references/file-ownership.md#L5), and [loop-controller:109–220](../../../skills/loops/loop-controller/SKILL.md#L109) encode them already. No recommendation removes Claude teams/Workflow, native task events, or its opt-in semantics.

Plumbing to abstract: Workflow `agent/parallel/pipeline`, native Agent/Task types, teams/inbox/message acknowledgements, TaskCompleted/TeammateIdle, `/goal`, `/loop`, `/batch`, schedules, Stop/SubagentStop, settings/env/model/effort flags, Skill invocation, and `.claude` handoffs/profiles. [Runtime detection:119–153](../../../skills/orchestrator/SKILL.md#L119) and [primitive mechanics](../../../skills/loops/loop-controller/references/primitives.md#L1) locate these dependencies.

## Default-refute: is sequential already enough?

**No, but not absent.** The runtime tree ends in sequential, and [line 153](../../../skills/orchestrator/SKILL.md#L153) explicitly says apply each role in one session, with the user coordinating resets. [Handoff:12](../../../skills/orchestrator/references/handoff-protocol.md#L12) has user relay. [Code review:113](../../../skills/roles/code-review-agent/SKILL.md#L113) already specifies Standards then Spec if no subagents. Those refute “no fallback at all.”

They do not resolve the conflicting [“never implement yourself”:186](../../../skills/orchestrator/SKILL.md#L186), [mandatory QE spawn:109](../../../skills/orchestrator/SKILL.md#L109), [single-agent exclusion:45](../../../skills/orchestrator/SKILL.md#L45), or role bodies that reject solo work. “Only parallelism changes” also overstates equivalence: context contamination, evaluator independence, physical ownership isolation, event enforcement, cancellation and budget execution change. Single-session role labels are not fresh agents.

### Concrete attended-sequential protocol (proposal)

1. **Discover and consent:** read current repo/host/skill resources; choose `attended-sequential`; declare no native scheduler/subagents/hook authority. Agree scope, allowed actions, runtime/call/spend limits. No automatic installs, commits, production calls or secrets copying.
2. **Resolve intent:** read mission/acceptance criteria; clarify only unresolved decisions. Keep small task direct; do not force all ten roles.
3. **Checkpoint state:** file packet records run ID, source revision/diff hash, mission criteria, dependencies, ownership, contract versions, selected adapter, commands, budget, pending human decisions and evidence paths. Default criteria false. Store no secrets.
4. **Author contracts and manifests:** shared types → API/data/events; dependency coordinator for multiple manifests; validate syntax and version. User approves consequential interfaces. Freeze the acceptance contract and verifier policy.
5. **Implement in dependency order:** data/schema → backend → frontend → infra/instrumentation; exact role scope. One role pass at a time, distinct output packets. Read actual files first. Single ownership still useful even without concurrency.
6. **Wave verification:** run permitted install/typecheck/tests/source guards; record exit/output plus revision. A failure routes to one owner; after three same failure/no-progress passes, pause for architectural/contract review. Test execution may be filtered for fast feedback, but full final verifier is unchanged.
7. **Independent review:** build a packet containing requirements/contracts/current artifacts/commands, **not builder narrative**, for a second clean session or human. Reviewer gets read-only production files, isolated test outputs, frozen criteria. Same vendor/model acceptable; second vendor requires explicit privacy/budget approval. Without it, mechanical tests can pass but subjective QA remains `NOT INDEPENDENT / BLOCKED`.
8. **Runtime QE:** reviewer executes contract/integration/adversarial checks; unavailable services/UI are skipped/blocked, never green. Generate schema-valid report and re-derive gate decision externally. No lowering threshold or patching own report to proceed.
9. **UI/reality checks:** real requested value path, visible semantic route/auth checks, aesthetics separately, source style/DRY gates. Local mock success must be labelled scaffold-only; no expensive real API without authorization.
10. **Close:** verify full mission and full proof, bind report to final revision/contract, summarize deferred work and remaining budget. Human controls commit/PR/deploy/intake. Persist handoff so a new host resumes the next legal state.

### Minimal machine-checkable state graph

```text
DISCOVER → SCOPE_APPROVED → CONTRACTS_FROZEN → IMPLEMENTING
IMPLEMENTING → WAVE_VERIFY → REVIEW_PACKET → INDEPENDENT_QE
WAVE_VERIFY.fail → OWNER_FIX → WAVE_VERIFY  (bounded)
INDEPENDENT_QE.fail → OWNER_FIX            (bounded)
INDEPENDENT_QE.pass → REALITY_UI_SOURCE_GATES → COMPLETE
any → PAUSED_HUMAN | BLOCKED_CAPABILITY | STOP_BUDGET | STOP_NO_PROGRESS
```

Transition guard examples: no implementation before contracts; no completion without immutable verifier logs at current diff; no concurrent queue ownership without a lock; no subjective accepted verdict without evaluator separation. Resume compares contract/diff hash and invalidates stale downstream proof. Durable state is not a transcript summary. JSON plus atomic file writes is enough initially; LangGraph is a pattern, not a required dependency.

## Role-by-role decomposition and solo execution

All ten role files have host gates. The static review across every role is in [matrix](01-skill-matrix.md); citations below cover each body and its core seam. Reports-only roles may write findings but not production code. No invented role can override project authority.

| Role | Host-neutral purpose | Claude plumbing / retained native behavior | Safe solo execution and proof |
|---|---|---|---|
| [backend-agent:23](../../../skills/roles/backend-agent/SKILL.md#L23) | API/business/data implementation; typed errors, CORS, persistence | Orchestrator-only contract input/ownership/lead communication | Read authored contract, implement owned paths, curl/tests actual endpoints. Correct opening “produce contract” to “consume”; stop on contract change |
| [frontend-agent:21–37](../../../skills/roles/frontend-agent/SKILL.md#L21) | Central API client, shell-first layout, mobile-first styles, observed render | Orchestrator dispatch plus external frontend-design/ui-ux-pro-max | Solo inputs inferred/confirmed, token/layout/shared-shell bootstrap first, two-width visible proof, semantic/source gates |
| [infrastructure-agent:21](../../../skills/roles/infrastructure-agent/SKILL.md#L21) | Containers, CI, environment template, health wiring | Lead coordination/ownership; nonexistent deployment/observability score blurb | Build/health dry-run locally; validate config; approve deployment separately; feed real QE dimensions |
| [db-migration-agent:21](../../../skills/roles/db-migration-agent/SKILL.md#L21) | Schema/migration/seed consistency and rollback | Orchestrator spawn/lead requests | Disposable test database with approved scripts, migration/rollback evidence; refuse production writes without human |
| [observability-agent:21](../../../skills/roles/observability-agent/SKILL.md#L21) | Logging/metrics/health/alerts with exclusive ownership | Lead relays wiring; advisory QE input already correct | Local request/log/metric signal, security scrub; production alert activation approved separately |
| [performance-agent:21](../../../skills/roles/performance-agent/SKILL.md#L21) | Repeatable workload and bottleneck report | Role dispatch, ownership; advisory input not SLA gate | Freeze workload/config/environment; baseline/trial distributions; do not edit implementation while evaluating |
| [docs-agent:21](../../../skills/roles/docs-agent/SKILL.md#L21) | Accurate setup/API/system docs | Phase14 trigger exists in canonical phase guide; not drift | Read run commands and verify allowed local ones; respect ADR/agents carve-outs; docs completion cannot impersonate QE pass |
| [security-agent:21–39](../../../skills/roles/security-agent/SKILL.md#L21) | Read-only static security/auth/dependency audit | Dispatch-only, lead severity attribution; root scan helper | Run available manager-specific audit/scanner; report source evidence; missing tool is BLOCKED check, not PASS |
| [qe-agent:21–44](../../../skills/roles/qe-agent/SKILL.md#L21) | Runtime conformance/integration/adversarial gate | Mandatory spawn + report schema | Independent fresh reviewer session and runtime tools; static mode explicitly limited; prototype policy cannot rewrite canonical bar |
| [code-review-agent:21–114](../../../skills/roles/code-review-agent/SKILL.md#L21) | Standards/Spec independent lanes | Already standalone, not orchestrator default; Agent for parallel isolation | Preserve two lanes; separate sessions preferred. Sequential Standards→Spec exists, but disclose same-context contamination |

Contract-auditor is an additional read-only pre-QE static role ([body:21](../../../skills/contracts/contract-auditor/SKILL.md#L21)); expose solo scope/contract input, do not collapse it into runtime QE. Contract-author is portable in metadata but [solo exclusion:40](../../../skills/contracts/contract-author/SKILL.md#L40) defeats direct solo contract requests.

## Thirteen loops — per-loop execution without subagents/hooks/scheduler

Every concrete loop inherits controller contracts and safety. The following are **proposed safe modes**, not claims their current non-Claude export exists. Each citation points to its inspected canonical instructions.

| Loop | Host-neutral action/proof | Current native plumbing | Attended degradation / refusal boundary |
|---|---|---|---|
| [loop-controller:109](../../../skills/loops/loop-controller/SKILL.md#L109) | trigger/action/proof/memory/stop contract | Select /goal /loop /batch Workflow Stop or Claude Ralph | Write same contract, externally bounded runner or attended passes; refuse unbounded autonomous run |
| [fix-until-green:30](../../../skills/loops/fix-until-green/SKILL.md#L30) | One root-cause repair; full test/lint/typecheck zero | /goal or Stop gate | One repair pass + exact verifier; cap failures; never delete assertions/config to green |
| [contract-conformance-loop:29](../../../skills/loops/contract-conformance-loop/SKILL.md#L29) | Plan-generate-evaluate acceptance criteria | Fresh Agent evaluator /goal | Second clean read-only reviewer; no such reviewer means mechanical-only/BLOCKED subjective criteria |
| [coverage-loop:30](../../../skills/loops/coverage-loop/SKILL.md#L30) | Identify untested paths, add useful tests, target report | /goal / controller | Freeze denominator/exclusions, exercise behavior, reviewer approves test-policy change; cap accepted increments |
| [perf-loop:30](../../../skills/loops/perf-loop/SKILL.md#L30) | Profile→change→repeatable benchmark + functionality | /goal controller | Fixed dataset/environment/SLO, repeats and functional gate; unavailable benchmark is blocked |
| [migration-loop:30](../../../skills/loops/migration-loop/SKILL.md#L30) | Enumerated mapping; expand/migrate/contract; whole-suite and no legacy | /batch worktrees, Agent/Workflow, /goal | Sequential slices, fixed scope/patterns; count output separate from grep status; rc2 error not zero matches |
| [orchestrator-task-loop:30](../../../skills/loops/orchestrator-task-loop/SKILL.md#L30) | Dependency queue until tasks have passing proof | Tasks, Team idle/completion events, messages | Locked file queue, one worker, per-task proof before status; no autonomous reschedule without controller |
| [codebase-exploration-loop:29](../../../skills/loops/codebase-exploration-loop/SKILL.md#L29) | Question→subsystem read→new evidenced map; stop saturation | Agent/Workflow scouts | One subsystem per pass, provenance and novelty threshold; cap; no invented completeness |
| [babysit:29](../../../skills/loops/babysit/SKILL.md#L29) | Poll PR/CI/review; classify then address | /loop / schedule; gh action flows | One-shot read/triage; approved fixes; user-owned merge/rebase/push policy; recurring schedule requires lock/cancel |
| [dependency-health-loop:29](../../../skills/loops/dependency-health-loop/SKILL.md#L29) | Audit versions/security; minimal update/test | /loop scheduling | One lockfile-scoped audit/update; major changes approval; repeat only through bounded external scheduler |
| [nightly-docs-and-changelog:29](../../../skills/loops/nightly-docs-and-changelog/SKILL.md#L29) | Compare source/diff to docs, bounded maintenance PR | durable/session schedules | One-shot docs pass, exact change provenance, review before publish; no scheduler means no nightly promise |
| [repo-cleanup-loop:29](../../../skills/loops/repo-cleanup-loop/SKILL.md#L29) | Classify stale artifacts/branches and safe removal | /loop / controller | Read-only inventory then approved scoped cleanup; protected ignored files/worktrees; no unattended broad delete |
| [self-healing-loop:28](../../../skills/loops/self-healing-loop/SKILL.md#L28) | Observe health, diagnose, bounded recovery and recheck | /loop/schedules, healing commands | Read-only monitoring until action allowlist approved; localhost reversible actions only by default; prod intervention HITL |

### Which protections weaken and how to restore them

- **Builder cannot grade itself:** a same-session “now be QE” pass retains hypotheses and incentives. Restore clean read-only session/model or human; objective script gates are useful but not complete subjective review.
- **Ownership:** prompt restrictions aren't filesystem ACLs. Solo prevents simultaneous collision, but preserves ownership intent. Parallel non-Claude runs need isolated worktrees or enforced path allowlists, not merely role names.
- **Budget:** [controller:187–203](../../../skills/loops/loop-controller/SKILL.md#L187) promises enforcement, but `/cost` observation and an evaluator transcript turn cap are not an external kill. Ralph examples are unbounded templates. Keep attended native behavior; require wrapper termination before unattended promotion.
- **Task events:** [manifest](../../../hooks/hooks.manifest.json#L1) ships Stop and tool/session hooks, not TaskCompleted/TeammateIdle. [task-loop hook refs](../../../skills/loops/orchestrator-task-loop/references/hooks.md#L1) are instructions to wire, not proof that the current installer did so.
- **Stop safety:** [qa-gate:34–40](../../../hooks/scripts/qa-gate.sh#L34) drains payload; [safety:39](../../../skills/loops/loop-controller/references/safety.md#L39) says inspect `stop_hook_active`. Need bounded reentry policy that avoids both permanent wedges and unconditional bypass. Strict validator errors must block; standard missing report's warn policy is intentional, not a surprise bug.
- **Evidence freshness:** schema-valid reports don't bind source/contract hashes. Cache/state is navigation, not proof. A changed build invalidates old gate receipts.

## GPT Luna static-site case: causal trace

The owner's 40+ page incident and model transcript are **user-reported, UNVERIFIED independently**: no failing project/artifacts/session trace supplied here. The repository failure mechanisms and four-page escapes below **were reproduced**. No claim about Luna's inherent skill-following ability follows from static code.

| Field step | Verified library mechanism | Classification | Native-preserving fix |
|---|---|---|---|
| Frontend skill refused | [frontend metadata:4–8](../../../skills/roles/frontend-agent/SKILL.md#L4), [multi-agent exclusion:25–33](../../../skills/roles/frontend-agent/SKILL.md#L25), [converter:711–726](../../../scripts/convert.sh#L711) | Host-neutral doctrine gated off and body rejects solo; not evidence model is incapable | Solo frontend mode with user scope/contracts/ownership inferred; keep orchestrator-dispatched branch unchanged |
| All CSS inline | [mobile rules:13–17](../../../skills/roles/frontend-agent/references/mobile-responsive.md#L13) are sound but behind role. [Guard defaults:55–67](../../../skills/workflows/design-token-guard/scripts/check_design_tokens.py#L55) WARN inline; [DIM_RE:90](../../../skills/workflows/design-token-guard/scripts/check_design_tokens.py#L90) requires nested quotes, misses HTML `width:1200px` | Invocation gap plus gate/profile/parser weakness | Before first layout, adopt ERROR layout profile preserving legitimate dynamic custom properties; run standalone CI/precommit after explicit bootstrap consent |
| Hash classes after complaint | [class guard:60–76](../../../skills/workflows/class-extraction-guard/scripts/check_class_extraction.py#L60) groups class-token strings, requires ≥4 utilities / ≥3 sites. CSS excluded from token guard by default | Literal fix gamed purpose; duplicate declaration detector absent | Normalize CSS declaration blocks **within** media/support/layer/cascade context; require shared selector/component or explained scoped exception |
| Header/footer copied into every source HTML | Guard fixture scanned four HTML files, no class findings; library sweep found Payload globals/reusable content but no generic markup detector | Missing generic source shared-chrome gate | Detect repeated header/nav/footer/landmark blocks; require one template/component/include owner; static generated pages may repeat if generated from shared source |

[Adversarial output](evidence/adversarial-results.txt) shows four unique classes with identical CSS and repeated chrome pass both guards. [Refutation](evidence/refutation-checks.txt) shows default JSX dimensions WARN+exit0, HTML layout absent; strict inline policy catches both and exits1. Thus “neither guard can ever catch inline styles” is false. “Default policy prevents all inline layout” is also false.

Do not make source-gate adoption depend on the missing orchestrator. Suggested build order: one shared shell → shared token/style primitives → representative page at two widths → remaining routes generated through shared layout → independent render/source proof. At step2 reject rename-only “fixes”; measure maintained source duplication, not only rendered pixels.

## Whole-library sweep of the same failure shape

The [76-row matrix](01-skill-matrix.md) and [inventory](evidence/inventory.json) enumerate every instance, not grep-density guesses:

- **All ten roles + contract-auditor**: doctrine portable; roles overgated. Code-review already standalone in body, so distinguish host gate from orchestrator-only gate.
- **All thirteen loops + orchestrator**: convergence/queue/ownership/evaluator doctrine portable; execution needs safe adapters, not simply flipping metadata false.
- **context-manager, dependency-coordinator, deployment-checklist, project-profiler, skill-catalog, repo-deep-dive, render-sanity, sync-skills, website-walkthrough-video**: nine additional gated skills with file/shell/browser workflows that need host paths/capability branches. Catalog/scanner root tools require checkout or bundling. Sync is CC/Cursor only in this revision.
- **Three legitimate vendor-specialized gates**: settings-consolidator (Claude permissions), use-pxpipe (Claude harness proxy), artifact-publish (native hosted Artifact). Keep native adapter; local output alternative must not pretend equal privacy/publishing.
- **Portable-but-body-gated**: contract-author and plan-builder reject single-agent use; madness routes UI/build/review to unavailable leaves despite its fallback note; ui-brief and nano-banana hardcode Claude consumer/resource locations; llm-wiki/wiki-research depend on CLAUDE-only context discovery; skill-creator's runner depends on Hermes, not Claude, proving “host-neutral” needs more than deleting Claude names.

### Gate-gaming register (cross-cutting)

| Guard/proof family | Cheapest literal win that defeats intent | Closure / current good doctrine |
|---|---|---|
| Design tokens/inline | Move hex into excluded stylesheet/token-named file; HTML dimensions missed; dynamic layout allowed; Git failure yields empty list | Protected explicit token source; syntax-aware layout rule; true scanned count; error status; approved exceptions |
| Class extraction | Unique names or append unique utility token; regenerate baseline; dynamic interpolation ignored | Declaration/subset/source-component analysis; protected baseline/config; reviewer approves ratchet changes |
| Shared layout (missing) | Add data/class attributes to cloned markup or move copies to different files | Normalize landmarks ignoring irrelevant literals; source ownership graph; do not flag generated output as authored duplication |
| Prose lexical | Move original prose into quoted/fenced blocks or swap words without adding facts | Existing fresh-eyes/provenance layer [prose:80–120](../../../skills/workflows/prose-slop-guard/SKILL.md#L80); measure source scope and exception provenance |
| Test/fix-until-green | Skip/delete tests or loosen assertion/config; run only subset forever | Controller already forbids cheating; freeze commands/assertions and inspect diff; full final run |
| Coverage | Narrow denominator, exclusion patterns, meaningless execution-only tests | Freeze coverage scope; behavioral/mutation checks on changed paths; reviewer owns accepted policy |
| Performance | Smaller dataset, warm-cache-only run, fewer clients, change threshold | Frozen workload/env, repeated distributions, correctness gate, independent acceptance |
| Migration | Narrow grep/scope, delete legacy code without migration, interpret grep error as no matches | Immutable target list/patterns; parse rc1=no match vs rc2=error; whole-scope final proof |
| Contract/QA | Toggle passed boolean; fabricate score; reuse old report; validator missing | Read-only independent grader, real test logs bound to diff/contract; strict fail-closed wrapper |
| Render/UI | Show first working item; hide broken routes/auth; render mock value path | Enumerated routes/roles, stratified samples + coverage disclosure; reality proof separate; report BLOCKED for unavailable login |
| Deploy readiness | Validate local not target, use wrong account/env; stale QA report | Identity/target confirmation; current bound evidence; production actions human-approved |
| Skill eval | Force-load skill; detect its name in prose; infra error becomes negative success; select on test score | Actual retrieval traces, candidate bytes/model pin, tri-state outcomes, untouched final holdout |
| Catalog/schema/scan | Count files but lose resources; allowed ignore removes secrets; optional schema skip called pass | Resource closure/host load tests; ignore authorization; skipped≠executed; catalog already guards live counts |

The strongest anti-gaming prose already exists in [safety:97–119](../../../skills/loops/loop-controller/references/safety.md#L97). The gap is enforcement and loophole fixtures, not another exhortation to “try harder.”
