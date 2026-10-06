# Gauntlet II — Coverage Matrix

All 76 active skills, derived from the filesystem (`skills/**/SKILL.md`, excluding `skills/archive/`), not from the docs. Each row lists the phase it should fire in, the legitimate trigger context that must select it, a must-fire flag, and a near-miss control that must **not** select it.

The near-miss controls are how over-triggering on the pushy descriptions is measured. A must-fire miss and a near-miss false positive are both findings.

The **Must-fire** cell has three values. `yes` means the model must select the skill unforced on the legitimate trigger — an unsatisfied `yes` is a finding. `explicit` means the skill ships `disable-model-invocation: true` (or is otherwise dispatched only by a lead), so it is *deliberately* not model-selectable: the acceptance is that it is reached and its work happens once invoked, and a natural-language prompt that fails to auto-select it is not a finding. `yes (optional)` is a must-fire row whose need is conditional.

> **Phase key:** P0 pre-flight · P1 plan · P2 contracts/assets · P3 build · P4 verify · P5 second cell · P6 ship · P7 operate · P8 harvest · P9 tidy.

---

## Orchestrator

| Skill | Phase | Legitimate trigger | Must-fire | Near-miss control (must not fire) |
|---|---|---|---|---|
| orchestrator | P3 | "run the approved plan with an agent team" | yes | "what does the orchestrator skill do?" |

## Role agents

| Skill | Phase | Legitimate trigger | Must-fire | Near-miss control (must not fire) |
|---|---|---|---|---|
| backend-agent | P3 | "implement the Fastify auction and ledger endpoints" | yes | "explain how Fastify routing works" |
| frontend-agent | P3 | "build the item, auction, and checkout pages" | explicit | "list React state libraries" |
| infrastructure-agent | P3 | "write the Dockerfile, compose file, and CI workflow" | yes | "what is CI?" |
| db-migration-agent | P3 | "add the staged Postgres migration for the ledger tables" | yes | "what is a migration?" |
| qe-agent | P4 | "verify the build against the contracts and emit qa-report.json" | yes | "write one unit test" |
| security-agent | P4 | "audit authz and run the OWASP top-ten sweep" | yes | "is OAuth2 secure?" |
| docs-agent | P4 | "write the README, API reference, and runbook" | yes | "fix this typo" |
| observability-agent | P3 | "add structured logs, metrics, and health checks" | yes | "what is a metric?" |
| performance-agent | P3 | "write k6 load scripts for the bid and fraud endpoints" | yes | "why does performance matter?" |
| code-review-agent | P4 | "review this diff for correctness and conventions" | explicit | "read me this function" |

## Contract skills

| Skill | Phase | Legitimate trigger | Must-fire | Near-miss control (must not fire) |
|---|---|---|---|---|
| contract-author | P2 | "author the REST and event contracts before any code" | yes | "show me an example OpenAPI snippet" |
| contract-auditor | P4 | "audit the implementation against the ledger contract" | yes | "what is an OpenAPI file?" |

## Meta skills

| Skill | Phase | Legitimate trigger | Must-fire | Near-miss control (must not fire) |
|---|---|---|---|---|
| madness | P0 | "/madness kick off the Bazaar II build" | yes | "what skills do I have for testing?" |
| skill-explorer | P8 | "which skill handles dependency freshness?" | yes | "use dependency-health-loop now" (must route, not launch) |
| skill-writer | P8 | "write a new skill for shared-layout enforcement" | yes | "edit an existing skill's description" |
| skill-review | P8 | "audit the four skills that under-triggered in this run" | yes | "review this product code" |
| skill-update | P8 | "apply the skill-review report to frontend-agent" | yes | "explain the report" |
| model-adaptation | P5 | "adapt the brief for the Freebuff/DeepSeek cell" | yes | "what model am I?" |
| skill-catalog | P8 | "reconcile the catalog after adding a skill" | yes | "what does the catalog file look like?" |

## Git skills

| Skill | Phase | Legitimate trigger | Must-fire | Near-miss control (must not fire) |
|---|---|---|---|---|
| git-commit | P6 | "commit the auction service with a conventional message" | yes | "what is a commit?" |
| git-pr | P6 | "open a PR with a structured body" | yes | "what is a PR?" |
| git-pr-feedback | P6 | "triage the review comments on the PR" | yes | "what is a code review?" |
| git-post-merge-cleanup | P9 | "prune the merged build branch and stale worktrees" | yes | "what is a worktree?" |

## Loop skills

| Skill | Phase | Legitimate trigger | Must-fire | Near-miss control (must not fire) |
|---|---|---|---|---|
| loop-controller | P3 | "keep the ledger suite green until it passes" (routes to a primitive) | explicit | "what is a loop?" |
| fix-until-green | P3 | "do not stop until tests, lint, and typecheck are green" | yes | "run the tests once" |
| contract-conformance-loop | P3 | "build until every ledger contract criterion holds" | yes | "explain the contract" |
| coverage-loop | P3 | "get coverage of the ledger module to 85%" | yes | "what is coverage?" |
| perf-loop | P3 | "optimize the bid endpoint until p95 is under 200ms" | explicit | "what is p95?" |
| migration-loop | P7 | "migrate every module off the legacy pricing API" | yes | "what is a migration?" |
| babysit | P6 | "keep the open PR rebased and green while review comes in" | yes | "what does a PR do?" |
| self-healing-loop | P7 | "watch CI and self-heal the failures" | yes | "what is CI?" |
| nightly-docs-and-changelog | P7 | "run the nightly docs and changelog sweep" | yes | "write the changelog once" |
| dependency-health-loop | P7 | "audit dependencies and propose one gated bump" | yes | "list our dependencies" |
| codebase-exploration-loop | P7 | "map the Bazaar II codebase and answer the seed questions" | yes | "what is a module?" |
| orchestrator-task-loop | P3 | "drain the shared task board until every task passes its gate" | yes | "make a todo list" |
| repo-cleanup-loop | P9 | "weekly branch and worktree hygiene, recover before deleting" | yes | "delete this branch" |

## Workflow skills

| Skill | Phase | Legitimate trigger | Must-fire | Near-miss control (must not fire) |
|---|---|---|---|---|
| plan-builder | P1 | "turn the research into a build plan" | yes | "what is a plan?" |
| plan-intake | P8 | "intake the run report into the ledger" | yes | "read the ledger" |
| living-plan | P0 | "set up the living-plan convention for Bazaar II" | yes | "what is a plan?" |
| grill-me | P1 | "interview me about the escrow design, one question at a time" | yes | "give me a design doc" |
| find-unknowns | P1 | "run a blindspot pass before we commit to the plan" | yes | "what are requirements?" |
| zoom-out | P1 | "step back — which modules does this change touch?" | explicit | "list the files" |
| architecture-rescue | P1 | "find the shallow modules and missing seams in the ledger" | yes | "what is architecture?" |
| work-item-brief | P1 | "write an agent-ready ticket for the fraud service" | yes | "make a todo" |
| yagni-gate | P2 | "before we build the fraud service, climb the reuse ladder" | yes | "what is YAGNI?" |
| dependency-coordinator | P2 | "build the cross-package dependency manifest before dispatch" | yes | "what is a dependency?" |
| context-manager | P3 | "the orchestrator context is filling — plan the handoff" | yes | "what is context?" |
| maintain-context | P3 | "update the CONTEXT glossary and ADR for the escrow decision" | yes | "what is a glossary?" |
| project-profiler | P0 | "profile the skeleton and emit profile.yaml" | yes | "what is a profile?" |
| setup-project-skills | P0 | "bootstrap the per-repo config for Bazaar II" | yes | "what is a config?" |
| diagnose-loop | P4 | "the bid race is flaky — build the fast feedback loop first" | yes | "fix this bug" |
| repo-deep-dive | P0 | "deep-dive the Stripe SDK for the payments architecture" | yes | "summarize this repo" |
| wiki-research | P0 | "read the relevant wiki pages before crawling source" | yes | "what is a wiki?" |
| llm-wiki | P0 | "stand up the Bazaar II knowledge wiki" | yes | "what is a wiki?" |
| ui-brief | P2 | "write the UI brief for the marketplace refresh" | yes | "pick a color palette" |
| claude-design-brief | P2 | "produce the paste-ready Claude Design prompt for the auction page" | yes | "describe the auction page" |
| mermaid-charts | P1 | "draw the service and escrow architecture as a diagram" | yes | "what is mermaid?" |
| render-sanity | P4 | "tests pass but the checkout UI is broken — click-through and stale-data scan" | yes | "what is the DOM?" |
| design-token-guard | P3 | "verify no inline styles bypass the design tokens" | yes | "what is a design token?" |
| class-extraction-guard | P3 | "check for utility-class soup that should be extracted" | yes | "what is a CSS class?" |
| playwright | P4 | "run the end-to-end signup to bid to pay journey with screenshots" | yes | "what is a browser?" |
| website-walkthrough-video | P4 | "capture a scrolling walkthrough video of the built site" | yes | "what is a video?" |
| nano-banana | P2 | "generate the eight listing photos and the hero banner" | yes | "what is an image model?" |
| artifact-publish | P4 | "publish the run report as a shareable artifact page" | yes | "what is a report?" |
| railway-deploy | P6 | "prepare the multi-service Railway deployment config" | yes | "what is a deploy?" |
| deployment-checklist | P6 | "run the pre-deploy verification gates" | yes | "what is a deploy?" |
| use-freellmapi | P5 | "wire Bazaar II to the FreeLLMAPI proxy for the fraud stub" | yes | "what is an API proxy?" |
| use-pxpipe | P3 | "wire the token-saver proxy for this long run" | yes | "what is a proxy?" |
| caveman | P3 | "give me the ultra-compressed summary of the diff" | yes | "summarize the diff normally" |
| prose-slop-guard | P4 | "check the docs for AI-slop prose before they ship" | yes | "fix this sentence" |
| interactive-doc | P8 | "produce the paired Obsidian and HTML companion for the ledger doc" | yes | "write a doc" |
| payload-cms | P2 | "optionally rebuild the storefront on Payload CMS" | yes (optional) | "what is a CMS?" |
| skill-creator | P8 | "test that the new shared-layout guard triggers, then run a variance benchmark" | yes | "write a skill" |
| sync-skills | P0 | "sync the repo skills globally so the session can see them" | yes | "what is a symlink?" |
| settings-consolidator | P0 | "consolidate the permissions into one project allowlist" | yes | "what is a permission?" |

---

## Roll-up

| Category | Count |
|---|---|
| orchestrator | 1 |
| roles | 10 |
| contracts | 2 |
| meta | 7 |
| git | 4 |
| loops | 13 |
| workflows | 39 |
| **Total** | **76** |

A `yes` skill that produces no trace record is reported as a miss. A near-miss control that fires is reported as a false positive. An `explicit` skill is reported separately: it is graded on whether it was reached and did its work when invoked, never on unsolicited model selection. Misses, false positives, and unreached `explicit` skills all feed the `[G2]` intake proposal.
