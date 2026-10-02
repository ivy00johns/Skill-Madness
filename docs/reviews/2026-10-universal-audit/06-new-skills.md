# Gap proposals and new-skill decisions — W6

## Avoid skill-count inflation

The best fixes mostly belong in existing skills or runtime adapters. Names below are **design candidates only**: not installed, not catalog entries, and no authority to implement. Frontmatter uses only today's [PSFS v1.1.0 fields](../../../spec/frontmatter.schema.json#L8); future capability declarations belong in body prose until the schema is approved. `requires_claude_code:false` alone does not establish portable execution. All consequential actions remain explicitly approved.

Rank = value to a solo low-budget developer given this audit's demonstrated failure, not a model-performance prediction. Deduplication: [completed work](../../../docs/COMPLETED-WORK.md#L1), [parked F1/F3/F5/F7/F9/F15/F16](../../../docs/FUTURE.md#L8), [32 proposed UA rows](09-ledger-intake.md).

| Rank | Candidate | Decision | Why / overlap | Candidate linkage |
|---|---|---|---|---|
| 1 | duplicate-declaration check | **Accept extension**, not new skill | Four hash-class pages pass current organization checks; extend class-extraction-guard | UA-06 |
| 2 | shared-layout-guard | **Accept small new guard** | No generic source-chrome ownership verifier; Payload globals already cover one stack | UA-07 |
| 3 | host-adapter / capability-detect | **Accept small resolver + discoverable entry**, not two skills | Needed to choose safe standalone mode; extends madness/model capability handoff, overlaps parked F1/WC3 | UA-02 |
| 4 | budget-guard | **Accept runtime extension**, reject prose-only new skill | Unattended budget needs controller/harness enforcement, not another reminder; F9/F15/F16 overlap | UA-13/16 |
| 5 | cross-model-eval | **Accept scoped F3/F5 extension after runner repairs**, not parallel platform | Existing FUTURE proposal already includes triggering/efficacy/grading; current creator invalidates those measures | UA-17–19 |
| 6 | session-handoff | **Extend context-manager**, reject duplicate skill | Handoff schema and restart protocol already exist, but host-gated/Claude paths | UA-01/03/26 |
| 7 | sequential-orchestrator | **Reject separate skill**, accept orchestrator mode | One contracts/ownership/QE source prevents divergence; existing fallback insufficient, not absent | UA-03 |
| 8 | model-router | **Reject autonomous new skill**, extend current tiering/router | MT1/MA2 already absorbed router; unknown prices/privacy/capabilities must not be inferred | UA-15/16 |
| 9 | gate-gaming resistance | **Accept cross-cutting protocol/fixtures**, reject universal mega-guard | Every verifier has a distinct invariant; shared fail-closed/provenance mechanics can be reused | UA-12/14/31 |
| 10 | resource-closure-check (additional) | **Accept toolchain gate**, not user skill initially | Source resources disappear between convert/install; better deterministic CI than another triggered workflow | UA-10/11/26 |

## 1. Duplicate CSS declaration check — extend class-extraction-guard

**Purpose:** detect repeated declaration blocks even when selectors are unique/hash-named. **Trigger:** CSS organization/reuse audit, conversion of inline styles into classes, frontend build bootstrap. Existing [class-extraction implementation:60](../../../skills/workflows/class-extraction-guard/scripts/check_class_extraction.py#L60) measures repeated utility runs, not CSS equivalence. [Four-page receipt](evidence/adversarial-results.txt#L33) proves the new gap. This is complementary to design-token values/policy, not a replacement.

Hypothetical separate packaging frontmatter (do **not** create this skill unless extension proves unworkable):

```yaml
---
name: duplicate-declaration-check
version: 1.0.0
description: Detect duplicated CSS declarations hidden by unique selectors. Use when extracting inline styles, reviewing CSS reuse, or checking repeated page styling.
compatibility: Requires project read access and an approved CSS parser or local checker.
requires_claude_code: false
composes_with: [class-extraction-guard, design-token-guard, frontend-agent]
---
```

**Acceptance:** compare normalized declarations within equal media/supports/container/layer contexts; respect fallback order, duplicate properties, custom properties, cascade/specificity and intentional variations. Require extraction only where a shared class/component preserves behavior. Report exact selector/file/line/equivalence group plus approved, justified exceptions. Cheap escape = reordering/whitespace/hash rename or splitting the block; normalize safe forms and compare substantial overlap without auto-merging semantically distinct rules. CI config/exception baseline controlled by reviewer, not worker. Guard must catch fixture while allowing two identical blocks under genuinely different conditions where consolidation changes cascade semantics. Parser/package choice remains undecided; no library dependency added in this audit.

## 2. Shared-layout guard — new small workflow

**Purpose:** enforce one owning source for header/footer/nav/site shell shared by multiple authored routes. **Triggers:** multipage static site, repeated chrome, “update all headers,” copied layout/component cleanup. **Overlap:** frontend/mobile outside-in doctrine; class extraction only class strings; design guard only style policy; Payload globals/shared content solve their stack but not static HTML generally. Evidence: [frontend reference](../../../skills/roles/frontend-agent/references/mobile-responsive.md#L1), [Payload:46](../../../skills/workflows/payload-cms/SKILL.md#L46), [copied-chrome fixture](evidence/adversarial-results.txt#L51).

```yaml
---
name: shared-layout-guard
version: 1.0.0
description: Check that repeated site chrome has one owning partial, include, or component. Use for multipage site builds, duplicated headers or footers, and shared-layout changes.
compatibility: Requires project source access and a local layout checker; never scans generated output as authored source.
requires_claude_code: false
composes_with: [frontend-agent, class-extraction-guard, design-token-guard, payload-cms]
---
```

**Capabilities in body:** read_files, run_shell for deterministic verifier; write_files only for approved scaffold/fix; browser_automation for rendered regression. **Output:** source-root/stack map, repeated subtree groups, owning template/component, per-route variation contract and checker receipt.

**Acceptance:** infer or ask source/generated roots; AST/subtree similarity for semantic header/nav/footer, ignoring whitespace and approved active-link/data differences. Rendered repetition from one template is PASS. Several separately authored copies are FAIL/explicit exception requiring owner approval. Cheap escape = rename IDs/classes or inject trivial per-page text; normalized structure and source dependency graph must still detect common chrome. Do not mandate a heavyweight React migration: a small build-time include/partial is enough. Dynamic CSS/custom properties not banned. Representative pages at mobile/desktop and an owner-source change must update every built route; generated hashes/dates alone are not proof.

## 3. Capability-detect — entry to one resolver

**Purpose:** describe current host/model/installation/authority separately and choose a supported mode without spending money. **Triggers:** session start when configured, model/host switch, skill prerequisite failure, install verification. **Overlap:** [madness fallback:231](../../../skills/meta/madness/SKILL.md#L231), [capability handoff](../../../skills/meta/model-adaptation/references/capability-handoff.md#L1), setup-project-skills asks project preferences rather than runtime features. UA-02 is an evidence-backed subset of parked F1/WC3, not approval of broad generator rewrite.

```yaml
---
name: capability-detect
version: 1.0.0
description: Identify available host capabilities and safe skill modes. Use at a configured session start, after changing host or model, or when a skill prerequisite is missing.
compatibility: Read-only local probes by default; paid calls, browser sessions, installs, and scheduling require explicit approval.
requires_claude_code: false
composes_with: [madness, model-adaptation, setup-project-skills]
---
```

**Acceptance:** output supported/enabled/permitted/observed evidence with freshness/version, missing capabilities, equivalence rating and chosen mode. Unknown stays unknown; no assumption that a model supplies tools. No plugin install, global permissions, scheduler creation, billed call, secrets dump or cookie access during “detection.” Cheap escape = cached stale report or tool names masquerading as semantics; invalidate on host/version/session/permission change and probe only read-only contracts. Claude native opt-ins retained; absence of teams cannot silently activate a different paid mode. Deterministic resolver must be reusable by converter/install/sync, not separately reimplemented inside every model prompt.

## 4. Budget guard — external enforcement, not a new reminder

**Purpose:** reserve and enforce approved time/calls/tokens/cost across retries/workers/models. **Triggers:** any unattended loop, paid fan-out, benchmark batch; attended run when the owner requests a budget. **Overlap:** existing [controller budget:195](../../../skills/loops/loop-controller/SKILL.md#L195), model-effort-tiering and F9/F15/F16. Favor wrapper/controller extension; candidate frontmatter only if a user-facing configuration skill later pays its maintenance cost.

```yaml
---
name: budget-guard
version: 1.0.0
description: Configure and verify external run ceilings. Use before unattended loops, paid model batches, or parallel workers with an approved spending limit.
compatibility: Requires a harness with measurable usage, reservations, deadlines, and cancellation; otherwise attended-only or refuse.
requires_claude_code: false
disable-model-invocation: true
composes_with: [loop-controller, model-adaptation, use-freellmapi]
---
```

**Acceptance:** independent controller reserves worst-case in-flight liability before each dispatch, locks shared counters, accounts retries/failed calls/delayed usage and cancels process tree at limit. A run stopping due to budget is STOPPED, never falsely accepted. Unknown price/usage means no paid unattended authorization; free may have quotas and nonmonetary limits. Cheap escape = prompt ignores ceiling, child jobs escape parent, concurrent jobs oversubscribe, or `null` means unlimited; wrapper cancellation/locked reservation tests close those paths. [Cost ladder draft](04-model-adaptation-drafts/cross-vendor-tiering.md) is the policy companion, not proof an enforcement backend exists.

## 5. Cross-model eval — existing F3/F5 scope

**Purpose:** distinguish resource load, unforced trigger selection, task efficacy and safety across selected hosts/models. **Triggers:** skill release/change, model change, claimed portability regression; never every routine skill invocation. **Overlap:** skill-review static quality, writer drafting, creator optimization; [F3/F5](../../../docs/FUTURE.md#L15) already owns this scope. Repair creator first; don't fork a second broken evaluator.

```yaml
---
name: cross-model-eval
version: 1.0.0
description: Measure skill retrieval, task outcomes, and safe degradation across approved model and host cells. Use to validate portability or compare a skill revision against a frozen baseline.
compatibility: Requires isolated task snapshots and host traces; paid execution requires explicit per-batch limits and provider approval.
requires_claude_code: false
disable-model-invocation: true
composes_with: [skill-creator, skill-review, skill-update, model-adaptation]
---
```

**Acceptance:** no-model deterministic fixtures first; actual candidate hash/model pin/retrieval trace; immutable train/dev/final split; execution-error distinct from nontrigger; outcome/proof/architecture independent of cost. Cheap escape = forced load, text mention, selecting max repeated test score, changed model/tool/authority, disclosed benchmark target; exclude invalid comparisons, test once held-out and report sample size/uncertainty. Definition and initial suite: [patterns](05-patterns.md). Universal claims remain UNVERIFIED until measured. No paid run was performed here.

## 6. Session handoff — extend context-manager

**Purpose:** carry portable revision-bound task/contract/proof/budget/authority state between sessions/hosts, not hidden reasoning. **Triggers:** compaction, switching provider/host, pause/resume, context saturation. **Overlap:** [context-manager](../../../skills/workflows/context-manager/SKILL.md#L20), [handoff startup:71](../../../skills/orchestrator/references/handoff-protocol.md#L71), maintain-context glossary, wiki durable knowledge; those are distinct lifetimes. Candidate frontmatter expresses proposed behavior only, preferred packaging is existing context-manager standalone mode.

```yaml
---
name: session-handoff
version: 1.0.0
description: Produce and verify a portable task-state handoff. Use when pausing work, changing host or model, or resuming after compaction.
compatibility: Requires local state files; does not export credentials, hidden reasoning, or model-native transport tokens.
requires_claude_code: false
composes_with: [context-manager, model-adaptation, orchestrator]
---
```

**Acceptance:** goal/non-goals, exact revision, ownership, last valid proof, rejected attempts, next action, remaining approved budget and unresolved human decisions. Receiver rereads current boundaries and marks old proof invalid after revision change. Cheap escape = assert last session passed without receipt or carry stale approval; required artifact digests/source revision and explicit approval scope prevent self-certification. One SKILL_ROOT/project-neutral path contract, with Claude handoff path adapter intact. No new memory service required.

## 7. Sequential orchestrator — reject fork, specify mode

**Purpose:** bounded contracts-first build on hosts without workers. **Triggers:** approved coordinated build with no spawn_subagent; user requests solo mode. **Overlap:** exactly orchestrator. Existing [sequential:153](../../../skills/orchestrator/SKILL.md#L153) is not a complete execution plan, but duplicating plan/contracts/QE doctrine creates new drift.

```yaml
---
name: sequential-orchestrator
version: 1.0.0
description: Run a contracts-first build in attended sequential role passes. Use when an approved coordinated build has no isolated workers and a human or separate session can provide final review.
compatibility: Requires files and shell plus independent acceptance; same-session self-review cannot certify subjective completion.
requires_claude_code: false
disable-model-invocation: true
composes_with: [orchestrator, contract-author, qe-agent, loop-controller]
---
```

**Acceptance if proposed mode ships:** dependency queue, file ownership, role packet, objective proof, fresh independent reviewer and bounded failure/escalation transitions as in [core](03-multi-agent-core.md). Cheap escape = same agent changes persona and declares independent QE; retain same-context review as useful precheck but label degraded and require external acceptance. Mandatory subjective gate without independent evaluator is BLOCKED, not waived. Native Claude never-implement coordinator rule remains intact; only explicit attended adapter permits role-pass implementation.

## 8. Model router — reject autonomous sibling

**Purpose:** choose cheapest approved model that meets task quality/capability/privacy constraints. **Triggers:** configured tiering before dispatch, measured repeated failure, requested cost optimization. **Overlap:** MT1/MA2 current tiering plus madness and use-freellmapi; [FUTURE:24](../../../docs/FUTURE.md#L24) explicitly absorbed this proposal. Candidate frontmatter for clarity, not a new catalog entry.

```yaml
---
name: model-router
version: 1.0.0
description: Select an approved model tier using task requirements and measured outcomes. Use for requested cost optimization or bounded escalation after a documented failure.
compatibility: Requires an observed endpoint catalog and owner-approved providers, data scope, and budget; unknown identity never defaults Claude.
requires_claude_code: false
composes_with: [madness, model-adaptation, use-freellmapi]
---
```

**Acceptance:** no-model → cheap mechanical → implementation → reasoning → independent review; once strong author/optimizer where useful. Keep single-provider default and explicit cross-provider consent. Cheap escape = inexpensive-per-token but expensive repeated failure, stale prices or disallowed data egress; score cost per accepted result and verify catalog/units/reservations. Current GPT/Gemini/Qwen/Kimi prices and exact session identities are UNVERIFIED. Never treat host tools as model features, or replace unsupported refusal with deceptive prompt circumvention.

## 9. Gate-gaming protocol — reference and fixtures, not mega-skill

**Purpose:** state owning invariant, cheapest literal escape and mechanical countermeasure for every verifier. **Triggers:** guard/loop authoring and review, adding exemptions/baselines, checker failure. **Overlap:** [safety anti-cheat:97](../../../skills/loops/loop-controller/references/safety.md#L97), contract-auditor/QE, skill-review; comprehensive guard cases in [core](03-multi-agent-core.md).

```yaml
---
name: gate-gaming-review
version: 1.0.0
description: Review whether a verifier can be satisfied while defeating its invariant. Use when adding a guard, changing a metric or exemption, or investigating a falsely green result.
compatibility: Read-only review and isolated local fixtures; any verifier-policy change requires independent approval.
requires_claude_code: false
composes_with: [skill-review, loop-controller, contract-auditor, qe-agent]
---
```

**Acceptance:** coverage exclusions, removed assertions, reduced workloads, empty scan, mock data, stale QA, hash CSS, copied source chrome, prose markup exemptions, mutable criteria, first-route-only UI sampling and unsupported skip all have negative controls. Config/verifier/dataset digest immutable for workers; error/blocked/skipped distinct from pass. Standard should be loaded by each existing author/reviewer, not automatically run every guard in every repository. An LLM-only “looks hard to game” judgment is not gate proof.

## 10. Resource closure — deterministic release gate

**Purpose:** prove the installed skill can resolve every declared needed resource without canonical checkout or Claude home assumptions. **Triggers:** convert/install change or release; source resource addition. **Overlap:** catalog counts/lint structural checks; PF1 copied scripts but did not establish installed closure. [Resource summary](evidence/resource-delivery-summary.json): zero Copilot script operations, zero Gemini manifest operations, zero generated asset files in exercised paths.

```yaml
---
name: resource-closure-check
version: 1.0.0
description: Verify that generated and installed skills retain their declared runnable resources. Use when changing skill delivery or preparing a skill release.
compatibility: Requires shell and fake install roots; never uses the real home directory or copies credentials.
requires_claude_code: false
composes_with: [skill-catalog, skill-review, sync-skills]
---
```

**Acceptance:** source→generated→fake-installed manifests agree on hashes/modes/relative paths; references/assets/scripts/agents/eval-viewer/templates accounted for; root helpers either bundled or declared checkout prerequisite; native hook wiring checked separately. Cheap escape = count files instead of resolve references, inline only top-level refs, rely on canonical repo accidentally on PATH; run with isolated HOME/cwd/PATH and fixtures for nested/omitted classes. Read root credential variable names only; never distribute root environment values. Prefer CI script/contract change first, adding a user-facing skill only if users repeatedly need interactive diagnosis.

## Shared constraints for every accepted design

- Preserve current Claude dispatch/teams/Workflow/hook activation and explicit opt-ins; new standalone modes additive.
- Reference commands runnable through available semantic capability, with cwd/exit/deadline evidence; missing tool does not mean invent PASS.
- Fixed source roots and reviewer-owned exemptions. Scanning generated artifacts and finding duplication from a shared template must not force busywork refactors.
- Cheapest deterministic checks before paid model review; no unapproved installs/global permission changes/deploys/publication.
- All frontmatter blocks are proposal examples, validated locally for today's known schema structure; full jsonschema validation is unavailable locally and is **UNVERIFIED**, not asserted by these drafts.
