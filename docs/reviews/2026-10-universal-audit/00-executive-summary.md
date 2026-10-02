# Skill Madness universality audit — executive summary

**Date:** 2026-10-02. **Audited HEAD:** `51106e1762205ab5a0b06b0d77ad8c69e8e33aba`. **Disposition:** report only; no skill/toolchain fixes, ledger intake, commit, installation into real HOME, or paid model runs.

## Bottom line

The library has strong engineering doctrine, but **portable doctrine, native execution plumbing, resource delivery and enforcement are conflated**. The solution is not to flatten Claude Code into a lowest-common-denominator checklist. Keep its teams, isolated agents, Workflow, hooks and explicit opt-ins; expose the same doctrine through capability-selected standalone and bounded execution adapters.

The measured baseline is **76 active skills: 37 Claude-gated and 39 exportable**, not the supplied approximately 79/41. All 76 bodies were inspected; the [matrix](01-skill-matrix.md) records value, overlap, static trigger assessment, size, dependencies and verdict for each. This is **not an empirical success rate**: per-skill triggering and efficacy across models remain **UNVERIFIED**. No present evidence justifies archiving a specialization merely because it overlaps another stage.

Evidence: [baseline identity/counts](evidence/baseline.txt), [hashed inventory](evidence/inventory.json), [complete numbered bodies](evidence/all-active-skills-numbered.txt). The user's main worktree is at a different HEAD (`d06cc28…`); this report does not describe its newer cloudflare skill or delivery changes.

## Ten most important findings

| Rank | Severity / candidates | Finding and evidence | Recommended fix, preserving Claude |
|---|---|---|---|
| 1 | **P0 · UA-08** | Parallel installer worker resets `DRY_RUN` before argument parsing. Direct worker-entry repro with exported dry-run wrote 39 Gemini skills to audit-local fake HOME, exit 0. [reset:47](../../../scripts/install.sh#L47), [receipt](evidence/refutation-checks.txt#L156) | Propagate parsed immutable worker context; prove both serial/parallel dry-runs write nothing. Never remove preview support. |
| 2 | **P0 · UA-12** | Strict QA permits a missing validator, exit 0; unexpected validator statuses also allow. Reports lack run/revision binding. [hook:85](../../../hooks/scripts/qa-gate.sh#L85), [receipt](evidence/adversarial-results.txt#L64) | Fail closed on enforcement-path checker failure; revision-bound proof and bounded hook reentry. Preserve intentional standard-profile missing-report behavior and DV1 TTY fix. |
| 3 | **P1 · UA-01/02** | Converter drops all ten roles, all thirteen loops, orchestrator and other useful doctrine. [filter:711](../../../scripts/convert.sh#L711), [frontend gate:8](../../../skills/roles/frontend-agent/SKILL.md#L8) | Add standalone roles and one capability resolver with native adapters. Do not merely flip flags and ship impossible instructions. |
| 4 | **P1/P2 · UA-04–07/31** | Luna failure is a chain: role unavailable → bootstrap not invoked → default inline policy nonblocking/misses HTML → hash-class and copied-chrome escapes. Four authored pages passed both guards. [receipts](evidence/adversarial-results.txt#L2), [strict counter-test](evidence/refutation-checks.txt#L105) | Portable frontend entry; consented strict layout gate/CI bootstrap; duplicate CSS equivalence and source shared-layout gate. Preserve dynamic CSS-property exceptions. |
| 5 | **P1 · UA-03/13/14** | Sequential orchestrator exists but conflicts with never-implement/mandatory-agent/QE instructions; prompt budgets are not universal external kill switches. [sequential:153](../../../skills/orchestrator/SKILL.md#L153), [prohibition:186](../../../skills/orchestrator/SKILL.md#L186), [budget:195](../../../skills/loops/loop-controller/SKILL.md#L195) | Specify attended state transitions and independent evaluator; require externally enforced limits for unattended work. Same-context roleplay cannot certify independence. |
| 6 | **P1/P2 · UA-09–11/26** | Generation and install are not resource-closed: assets/creator helper dirs omitted, nested inline references missed, installers drop resources/metadata. Parallel conversion loses worker context. [resource totals](evidence/resource-delivery-summary.json), [worker code:790](../../../scripts/convert.sh#L790) | One resource/ownership manifest through generation, install and sync; SKILL_ROOT; sequential/parallel equivalence tests. Preserve script-copy work already shipped in PF1. |
| 7 | **P1/P2 · UA-17/18** | Creator accepts but does not apply candidate description; forces skill loading and infers trigger from stdout; errors become negative results. Selection repeatedly uses held-out test scores. [eval:75/125](../../../skills/workflows/skill-creator/scripts/run_eval.py#L75), [selection:207](../../../skills/workflows/skill-creator/scripts/run_loop.py#L207), [mock receipt](evidence/refutation-checks.txt#L338) | Isolated candidate snapshot, actual retrieval trace, tri-state outcomes and pinned worker model; train/dev selection, touch-once held-out final test. Preserve SO4 standard. |
| 8 | **P1/P2 · UA-15/16** | Only Anthropic/DeepSeek adaptation; unknown runtime defaults Anthropic. Existing cost tiering is useful but lacks missing vendor instantiations and approved cross-vendor reviewer policy. [defaults:83](../../../skills/meta/model-adaptation/references/model-effort-tiering.md#L83), [provider policy:96](../../../skills/meta/model-adaptation/references/model-effort-tiering.md#L96) | Adopt GPT/Gemini/unknown drafts; conservative measured cost-per-accepted-result ladder; single-provider default plus explicit privacy/budget consent. No invented prices/IDs/plan entitlements. |
| 9 | **P1/P2 · UA-20/21** | Baseline raw CC/Cursor sync contradicts filtered conversion; flat subset ignored, copies may be removed on collision. Apply trusts stale source bytes/destinations and loses executable modes. [sync:393/412](../../../skills/workflows/sync-skills/scripts/sync-skills.sh#L393), [apply:92](../../../scripts/install-apply.sh#L92), [repro](evidence/adversarial-results.txt) | Shared projection, owned-only cleanup and approval/backups; schema/digest/containment/mode validation and atomic state. Sync collision itself was source-inspected, not executed. |
| 10 | **P2 · UA-19/24/25/30** | Green structural tests do not establish universal behavior. Role blurbs name nonexistent QE dimensions; current PSFS export types differ from live Agent Skills; a few scoped docs claims lag reality. [CI:117](../../../.github/workflows/lint-skills.yml#L117), [frontend:21](../../../skills/roles/frontend-agent/SKILL.md#L21), [PSFS:113](../../../spec/frontmatter.schema.json#L113) | Repair precise claims; extend existing F3/F5 smoke/eval proposals rather than duplicate them. Preserve native tool arrays with an export adapter and keep tolerant loading distinct from strict author lint. |

## Luna case: what is established

The owner's 40+ page incident and exact runtime/model identity are **user-reported; independently UNVERIFIED**. The repo mechanism and smaller four-page escape were reproduced without a model. Thus the audit establishes an architectural failure shape, not that a particular model is inherently incapable.

- **Inline CSS:** host-neutral frontend doctrine was hidden by dispatch/export gates; neither correct doctrine nor an invoked strict guard was guaranteed. Default HTML dimensions returned no finding; JSX dimensions returned WARN/exit 0. Strict configuration caught both, exit 1.
- **Unique hash classes:** utility-combination extraction is not declaration deduplication. Four different selectors with identical CSS passed; simply forbidding inline syntax does not require reuse.
- **Copied header/footer:** neither current guard examines shared source-layout ownership. Payload globals/shared content already address a stack-specific form, so “no shared-content doctrine anywhere” is false. A generic source-template gate remains missing.
- **Fix order:** shared shell/tokens/one owning chrome source → representative routes and two-width proof → generate/build remaining pages → independent final UI proof. Do not lint repeated generated HTML as an authoring defect.

Full causal analysis, whole-library recurrence sweep and gate-gaming register: [multi-agent core](03-multi-agent-core.md).

## Universality scorecard — delivery and static execution, not efficacy

**Works** = static documented route exists for the stated slice, not live host certification. **Degraded** = usable portions with missing resources/adapters/evidence. **Broken** = core excluded, no shipped route, or reproduced unsafe path. Runtime universality for every host is **UNVERIFIED**; no numeric universal-support percentage is warranted.

| Host | Routine portable doctrine | Roles/orchestrator/loops via shipped converter | Delivery / safety verdict |
|---|---|---|---|
| Claude Code | Works, static native design | Works by native design; sequential/QA caveats | **Degraded:** incomplete resources and P0 installer/strict-checker paths; actual native load/hook smoke UNVERIFIED |
| Codex CLI | Degraded: manual skill load possible per live host docs | **Broken delivery:** no converter target in baseline | Current CLI documents subagents; host inability is not the cause. No baseline multihost sync route |
| Gemini CLI | Degraded: 39 exported | **Broken:** 37 excluded despite documented subagents/hooks | Classic path preserves extension shape; plan path omits manifest/skills prefix; dry-run worker unsafe |
| Cursor | Degraded: 39 converted rules; raw sync exposes different content | **Broken conversion:** core excluded | Subagents/hooks documented; raw skill activation not certified; subset/collision risks |
| OpenCode | Degraded: 39 flat agents | **Broken:** core excluded | Resource install losses; global path differs from current official docs |
| Aider | Degraded: consolidated 39 bodies | **Broken:** core excluded | References deliberately omitted; conventions require explicit read/config activation |
| Hermes | Degraded: manual route; creator runner specifically targets Hermes | **Broken delivery:** no converter target | Delegation/cron documented, but no library adapter or host smoke here |
| Devin | Degraded: manual `.agents/skills` route documented | **Broken delivery:** no converter target | Exact delegation/gate equivalence UNVERIFIED; not baseline sync target |
| Freebuff / bare API | Works for report-only read/edit/shell/search doctrine observed here | **Broken native path; degraded attended proposal** | No spawn/teams/Workflow/Stop/scheduler here; browser/questions/todos available; unattended must refuse without external limits |
| Windsurf / other converter targets | Degraded: 39 bodies exported | **Broken:** core excluded | Windsurf exists, not dead; detailed current host execution UNVERIFIED |

Host facts and safe fallback ratings: [capability map and source register](02-capability-model.md).

| Category | Active / gated | Claude static design | Non-Claude converter baseline |
|---|---:|---|---|
| contracts | 2 / 1 | Works, static/runtime distinction useful | Degraded: author exported but body excludes solo; auditor blocked |
| git | 4 / 0 | Degraded: CLI/feedback/approval defects | Degraded: all four export; same semantic defects |
| loops | 13 / 13 | Degraded: sound contracts, external enforcement not guaranteed | Broken delivery; attended one-shot adapter possible, not shipped |
| meta | 7 / 1 | Degraded: useful routing/tiering, missing provider baseline | Degraded: six exported; gated destinations/resource assumptions |
| orchestrator | 1 / 1 | Works native design; degraded sequential specification | Broken delivery |
| roles | 10 / 10 | Works native design; residual gate/schema blurbs | Broken delivery of portable discipline |
| workflows | 39 / 11 | Degraded: useful specialization plus scoped defects | Degraded: 28 exported; missing resources/invocation/adapters |

Counts are filesystem-derived [baseline](evidence/baseline.txt), not current-main or historical documentation counts.

## Actual gate results

- Skill lint: **exit 0, 0 errors, 120 warnings across 82 files** (76 active + six archives), [full output](evidence/lint-skills.txt).
- Catalog: **exit 0, 76**, [full output](evidence/catalog-check.txt).
- Corrected full Bats run: **plan 346; 339 passed, seven jsonschema skips, zero failures, exit 0**, [summary](evidence/corrected-test-summary.json), [full TAP](evidence/tests-run-all-corrected.txt).
- Initial snapshot run had one scanner failure because this auditor omitted tracked ignore input. Restoring that input in the audit-only snapshot made scanner **15/15** and full suite green; initial receipt retained, not blamed on repo. [correction](evidence/refutation-checks.txt#L2).
- Sequential generation: **466 processed, 370 skipped, zero errors, exit 0** across eleven targets. Parallel attempt: **exit 1, macOS xargs command-length failure**. [sequential](evidence/convert-sequential.txt), [parallel](evidence/convert-parallel.txt).

Seven local schema skips are not seven passes. CI explicitly installs jsonschema; no claim that CI schema enforcement is broken. Final Markdown/link/scope checks are recorded in [validation receipt](evidence/report-validation.txt).

## Default-refute pass — top fifteen propositions

Counter-evidence was sought before final ranking. A narrower surviving finding replaces each overbroad starting claim.

| # | Proposition challenged | Attempt to disprove / evidence | Final disposition |
|---|---|---|---|
| 1 | Approximately 41 of 79 gated; doc counts drift | Filesystem inventory 76/37/39; catalog check clean | **REFUTED** counts/drift as supplied; retain 37 blocked skills, no count ticket |
| 2 | Frontend doctrine unusable off-Claude | Read role gate/filter versus neutral mobile/cascade rules | **CONFIRMED delivery/entry blockage**, not inherent model incapacity; UA-01 |
| 3 | All roles lack standalone wording | Code-review already explicitly standalone and has sequential Standards→Spec at [113](../../../skills/roles/code-review-agent/SKILL.md#L113) | **NARROWED:** preserve existing standalone lanes; host gate and independence gap remain |
| 4 | Guards cannot catch inline CSS | Strict configuration catches both HTML/JSX, exit 1 | **NARROWED:** default policy/HTML matching/invocation defect, not total inability; UA-04/05 |
| 5 | Hash renaming closes organization issue | Four unique selectors with repeated declaration blocks pass both guards | **CONFIRMED escape**, not utility extraction malfunction; UA-06 |
| 6 | No shared-content doctrine exists | Payload globals/reusable content [46](../../../skills/workflows/payload-cms/SKILL.md#L46) | **NARROWED:** generic shared-source chrome verifier missing; UA-07 |
| 7 | Orchestrator has no sequential fallback | Explicit paragraph [153](../../../skills/orchestrator/SKILL.md#L153); handoff user relay exists | **NARROWED:** insufficient/conflicting plan, not absent fallback; UA-03 |
| 8 | Loops have no safety doctrine | Five-part contracts, caps, anti-cheat and Ralph wrapper requirement exist | **NARROWED:** proof of external runtime enforcement missing on fallback paths; UA-13/14 |
| 9 | Strict QA always enforces correctness | Missing-validator fixture allows; unexpected status path also allows | **CONFIRMED P0** enforcement hole; DV1 hang fix not regressed; UA-12 |
| 10 | Installer dry-run is read-only | Direct parallel-worker entry reset ignores exported dry-run; fake HOME gains files | **CONFIRMED P0** worker path; serial dry-run not accused; UA-08 |
| 11 | Integrations stale / Windsurf dead / cloudflare missing | Integrations absent/ignored; fresh eleven-target output; Windsurf implemented; cloudflare absent baseline source | **REFUTED at this HEAD**; fresh resource/parallel defects retained instead |
| 12 | Scripts never ship | Converter copies scripts since PF1; assets/helpers missing and install paths drop scripts | **NARROWED:** resource closure/install regression, not missing script converter; UA-10/11 |
| 13 | Sync reaches seven hosts and Codex 97 | Baseline source only CC/Cursor; main different revision | **UNVERIFIED supplied installation count; REFUTED baseline route**; raw/filter divergence still real, UA-20 |
| 14 | Creator candidate/holdout eval is valid | Different candidate strings produce identical mocked calls; direct test-detail leak refuted by blinding code, but repeated test-based selection present | **CONFIRMED candidate/control and selection defects**, no paid efficacy claim; UA-17/18 |
| 15 | Full tests fail / CI is missing | Initial scanner failure caused by audit setup; corrected 339 pass + seven skip; recursive CI suite present | **REFUTED repo test-failure claim**; uncovered adversarial gaps are new tests needed, UA-19 |

Additional discarded suspicions: Docs Phase 14 really exists in [phase guide](../../../skills/orchestrator/references/phase-guide.md); CSS scanning is configurable, not absolutely unsupported; PSFS tolerant parser versus strict author schema are different layers, not automatically a contradiction. Native Claude nested discovery and actual installed hook-wrapper execution remain UNVERIFIED.

## Recommended order of work — subject to approval

1. **Safety first:** UA-08/12; add fake-HOME dry-run and fail-closed/reentry/revision proof fixtures. No host expansion should precede trust in preview/verification.
2. **Close the demonstrated frontend incident:** UA-01/04–07/31; standalone role entry, two existing guard extensions and one small generic layout guard. Preserve native dispatched mode and dynamic exceptions.
3. **Make delivered resources executable:** UA-09–11/20/21/26; single resource/ownership manifest, safe apply, projection parity, native Claude output regressions.
4. **Capability/solo core:** UA-02/03/13/14/24; small resolver and explicit state plan; independent reviewer and external caps before unattended mode. No compulsory LangGraph dependency.
5. **Low-budget model path and honest evaluation:** UA-15–19; missing drafts, optional approved reviewer routing, fix creator measurements, tiny F3/F5 eval matrix before universal claims.
6. **Scoped hygiene:** remaining UA rows; precise CLI/docs/schema/config/freshness/authority/capture fixes. Do not reopen historic counts or closed work without regression evidence.

The [32 candidate rows](09-ledger-intake.md) flag completed-work overlap and parked FUTURE scope. They are proposals, not commitments. Stop here for owner review; no automatic intake.

## Report navigation

- [01 · every skill](01-skill-matrix.md)
- [02 · capabilities, host mappings and PSFS migration](02-capability-model.md)
- [03 · core, solo plans and Luna/gaming sweep](03-multi-agent-core.md)
- [04 · GPT](04-model-adaptation-drafts/gpt-adaptation.md), [Gemini](04-model-adaptation-drafts/gemini-adaptation.md), [unknown](04-model-adaptation-drafts/unknown-model-adaptation.md), [cost ladder](04-model-adaptation-drafts/cross-vendor-tiering.md)
- [05 · patterns and eval design](05-patterns.md)
- [06 · new-skill decisions and frontmatter](06-new-skills.md)
- [07 · toolchain and real receipts](07-toolchain.md)
- [08 · actual host friction](08-host-friction-log.md)
- [09 · approval-ready candidate intake](09-ledger-intake.md)
