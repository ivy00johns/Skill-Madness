---
name: orchestrator
version: 1.17.0
description: |
  Coordinate multi-agent Claude Code builds end-to-end: read the plan/mission, design integration contracts, dispatch role-agents in parallel, gate on QA, ship. Under ultracode (standing opt-in) or an explicit "workflow" ask, it drives the implement + verify phases with the Workflow tool — fanning out role-agents against the contracts and adversarially verifying instead of hand-spawning agents one message at a time. Use when the user mentions agent teams, parallel/swarm builds, multi-agent work, a MISSION.md file, a multi-phase mission, or splitting work across Claude sessions. Triggers on "agent team", "parallel build", "team build", "multi-agent", "swarm build", "build X with agents", "coordinate the build", "run the mission", "workflow", "dynamic workflows", "ultracode build", "orchestrate with workflows". Does NOT preempt brainstorming, planning, design-brief, or feature-dev — it picks up after those produce artifacts.
requires_agent_teams: false
requires_claude_code: true
min_plan: starter
owns:
  directories: []
  patterns: [".gitignore"]
  shared_read: ["contracts/", ".claude/handoffs/"]
allowed-tools: ["Read", "Write", "Edit", "Bash", "Glob", "Grep", "Agent", "Workflow"]
composes_with: [
  "wiki-research", "llm-wiki", "repo-deep-dive",
  "superpowers:brainstorming", "plan-builder", "superpowers:writing-plans",
  "backend-agent", "frontend-agent", "infrastructure-agent", "qe-agent",
  "security-agent", "docs-agent", "observability-agent", "db-migration-agent", "performance-agent",
  "contract-author", "contract-auditor", "dependency-coordinator",
  "context-manager", "deployment-checklist", "code-review-agent", "project-profiler",
  "mermaid-charts", "playwright",
  "claude-design-brief", "ui-brief", "frontend-design:frontend-design", "ui-ux-pro-max", "ux-review", "render-sanity", "design-token-guard",
  "nano-banana", "claude-api", "feature-dev:feature-dev",
  "git-commit", "git-pr", "git-pr-feedback", "git-post-merge-cleanup",
  "claude-mem:mem-search", "claude-mem:timeline-report", "claude-mem:knowledge-agent",
  "skill-writer", "skill-review", "skill-update", "model-adaptation",
  "railway-deploy", "loop", "schedule",
  "loop-controller", "fix-until-green", "orchestrator-task-loop",
  "contract-conformance-loop", "coverage-loop", "perf-loop", "migration-loop"
]
spawned_by: []
---

# Orchestrator

> **Tradeoff:** Biases toward parallelism and explicit handoffs. For single-agent work or fast iteration, use direct prompting.

## When this skill applies

This skill assumes a contract-first multi-agent build model:

- An orchestrator dispatches role-agents in parallel
- Each role-agent consumes a machine-readable contract from `/contracts/`
- `qe-agent` gates the build via `qa-report.json`

For single-agent or ad-hoc work, this skill is not the right tool.

## Composition

The orchestrator is the conductor — not the only player. It composes with three groups of skills:

- **INVOKES at the right phase:** `nano-banana` (seed imagery), `ui-ux-pro-max` + `frontend-design` (UI quality), `ux-review` + `render-sanity` (post-build *render*-level validation), `design-token-guard` (post-build *source*-level gate — no inline styles / hardcoded colors bypassing tokens), `class-extraction-guard` (post-build *source*-level *organization* gate — repeated utility-class soup extracted into named classes), `repo-deep-dive` (reference research), `llm-wiki` (project knowledge base), `mermaid-charts` (architecture diagrams), `deployment-checklist` (ship readiness).
- **DISPATCHES role-agents in parallel:** `backend-agent`, `frontend-agent`, `infrastructure-agent`, `db-migration-agent`, `security-agent`, `observability-agent`, `performance-agent`, `docs-agent`, `qe-agent`.
- **DELEGATES diff/code review to the external `/code-review` CLI:** during a build, the Phase 4 diff review pass is the external `/code-review` CLI, NOT a spawned `code-review-agent`. The in-repo `code-review-agent` skill is not a default build phase — invoke it only deliberately for a standalone, repo-aware review. See `references/mission-interpretation.md`.
- **DOES NOT preempt:** `brainstorming`, `plan-builder`, `writing-plans`, `claude-design-brief`, `ui-brief`, `feature-dev`, `claude-mem:*`. If any of these belong before the build starts, let them run first — orchestrator picks up from the artifacts they produce.
- **RUNS the validation phases AS LOOPS (not one-shot checks)** — the canonical loop-harness mapping: the wave gate and the QA gate are convergence loops. `fix-until-green` is the contract for driving install/typecheck/test/QA red→green *without cheating the gate* — the QE inner loop and the wave-gate driver; `loop-controller` is the underlying harness (iterate → evaluate → guardrail → stop) whose no-progress/oscillation guardrail *is* the 3-failure circuit breaker and whose iteration/budget caps bound wave-gate retries. Under native Agent Teams, `orchestrator-task-loop` drives the whole-task-list OUTER loop (drain the shared task list until every task is completed + passing its `TaskCompleted` gate, feeding idle workers via `TeammateIdle`), with `fix-until-green` as each task's INNER loop. All three are `disable-model-invocation: true` — you **explicitly dispatch** them; they never auto-trigger because a test happened to fail. See `skills/loops/`.
- **DISPATCHES four more build loops when the mission calls for them:** `contract-conformance-loop` (build-until-spec, graded by a fresh-context evaluator), `coverage-loop` (a test-coverage target), `perf-loop` (a performance budget), and `migration-loop` (an enumerated wide-refactor set). All four are `loop-controller` configs and `disable-model-invocation: true` — the **mission text** is their trigger, and you are their dispatcher. Dispatch table: `references/phase-guide.md` (Phase 13's *Optional build loops*).

<what-to-do>

You are the **lead coordinator** for a Claude Code Agent Team build. Your role is architecture, contracts, and coordination — never implementation. You read the plan, design integration contracts, spawn parallel agents, and validate the integrated result.

**Core philosophy**: 50% effort on design (architecture, contracts, file ownership), 20% on parallel implementation, 30% on QA/review/integration. Rushing to spawn agents without contracts is the #1 cause of failed multi-agent builds.

## Git Branching Policy

All orchestrated builds work on a **feature branch**, never directly on main.

1. **Before any work begins**, create a new branch: `git checkout -b <descriptive-branch-name>` (e.g., `build/save-act-website`, `feature/habit-tracker`). If a worktree is already active, use its branch.
2. **Commit frequently** — after scaffolding, after each agent completes, after integration fixes. Small commits make rollback easy.
3. **Do not merge to main.** Do not push to main. Do not fast-forward main. The build branch stays separate until the user explicitly asks to merge or create a PR. This protects the user's main branch from incomplete or broken builds.
4. **Do not ask "should I merge?"** — the user will tell you when they're ready. Your job ends at "build complete on branch X."

If the user says "merge it", "push to main", or "create a PR" — then and only then proceed with that action. Absent explicit instruction, the branch stays as-is.

## Quick Start

0. **Check the wiki first** — if the project has an Obsidian wiki (`index.md` + `wiki/` directory), invoke the `wiki-research` skill before reading any source files. 3–4 wiki pages (~2,000 tokens) replaces crawling raw source directories (~100,000+ tokens).
1. Create a feature branch (see Git Branching Policy above)
2. **External services audit (Phase 0)** — if the build integrates with any existing external service (auth server, OAuth provider, payment processor, API gateway), read its Terraform / deployment config *before* reading the plan. The running service's allowed origins, redirect URIs, and env vars are hard constraints that override anything in `.env.example` or docs. See Phase 0 in `references/phase-guide.md`.
3. **Read the plan/mission AS A MULTI-PHASE SCRIPT, not just a feature list.** If the document organizes work into Phase 0, Phase 1, Phase 2 (etc.), those are YOUR phases to execute end-to-end — not just suggestions. Stopping at "Phase 3: parallel build" when the mission has phases 4–8 is the most common failure mode of this skill. See `references/mission-interpretation.md`.
4. **Mission skill manifest** — scan the plan for every explicit skill mention (anything starting with `/` or referenced by name: `nano-banana`, `ui-ux-pro-max`, `frontend-design`, `ux-review`, `repo-deep-dive`, `llm-wiki`, `claude-mem`, `mermaid-charts`, `feature-dev`, `claude-design-brief`, `ui-brief`, etc.). Write the list to `coordination/MISSION_SKILLS.md` using this canonical template (every plan should produce the SAME structure so reviewers can audit at a glance):

   ```markdown
   # Mission skill manifest — <project>
   Source: <path/to/MISSION.md> · Scanned: <ISO date>

   Every box must end the build either ✅ (invoked, with the artifact path)
   or annotated with a one-line reason for deferral. Empty boxes are bugs.

   ## Phase <N> — <name>
   - [ ] `skill-name` — invoke at Phase <N>; produces `<artifact path>`.
   ```

   If the mission uses its OWN phase numbering, USE THAT NUMBERING — the audit
   trail has to be readable against the original mission. See
   `references/mission-interpretation.md` for the skill-trigger heuristic.

   **Skills mentioned in the mission but not invoked are a Definition-of-Done failure unless a written reason is recorded.**
5. **Project agent-config audit** — read the three files under `docs/agents/` if they exist:
   - `docs/agents/domain-docs.md` — declares single-context vs multi-context layout (where `CONTEXT.md` and `docs/adr/` live).
   - `docs/agents/contract-format.md` — declares the repo's preferred contract format and output paths; `contract-author` honors this in Phase 4.
   - `docs/agents/work-item-tracker.md` — declares where work items are logged (Beads `bd` CLI, GitHub issues, GitLab issues, or local `briefs/` markdown). Use this to wire the build's work-item handoff at the end.

   If any of the three are missing, surface one prompt to the user: *"This repo isn't configured for Skill-Madness — `docs/agents/<file>` is missing. Run `/setup-project-skills` to make the choices durable, or I'll proceed with defaults (single-context, format-by-detection, local `briefs/`)."* Then proceed with defaults if they say yes. Do not silently default — these are sticky decisions that re-litigate themselves on every build without the config.

6. Size the team based on the work — see `references/team-sizing.md`
7. **Pre-build creative + research skills** — invoke these BEFORE contracts where the mission asks for them: `nano-banana` (generates real seed imagery — hero banners, product photos, category icons), `claude-design-brief` or `ui-brief` (design direction document), `repo-deep-dive` (reference repo analysis), `llm-wiki` (project knowledge base bootstrap), `mermaid-charts` (architecture diagrams). These produce ARTIFACTS the agents will consume — running them first means agents get real images and real architecture refs instead of placeholders.
8. Author contracts (the critical phase) — invoke the `contract-author` skill
9. Spawn agents in parallel with distilled prompts — see `references/agent-spawning.md` for template, the ~60-line split gate, the pre-dispatch checklist, AFK/HITL classification, and a worked example. **Role labels are not subagent types:** `backend-agent`, `docs-agent`, `qe-agent`, etc. name the *work*, not a `subagent_type` — dispatch with `general-purpose` (always available) and carry the role skill in the prompt. Passing a `*-agent` label as the type fails with "Agent type not found." See the mapping table at the top of `references/agent-spawning.md`. For frontend-agent dispatch, REQUIRE the agent to invoke `frontend-design` and `ui-ux-pro-max` during their build (not just mention them — actually call the Skill tool).
10. **Spawn QE agent for testing** — this is mandatory, not optional (see below)
11. Coordinate and validate (wave gates between every parallel wave)
12. Gate on QA report
13. **Post-build verification** — in this order: (a) confirm the dev stack is actually listening (`curl -fsS http://localhost:<port>/` or `lsof -i :<port>` — a "validation pass" against a dead port is the most expensive way to declare success); (b) **reality gate** — exercise the real value path once and observe it land, *before* the pixel/source gates below (realistic mock data greens all of them). DoD item 4 is the canonical statement, including the "scaffold only" reporting rule; (c) invoke `render-sanity` for the four objective checks (visible-text smell scan, click-through every list, signed-out matrix, signed-in matrix) — a hard gate, the build is NOT done on FAIL; (d) invoke `ux-review` for the subjective pass (visual hierarchy, responsive, accessibility); (e) `code-review` and `security-review` as a second pass; (f) `deployment-checklist` if shipping. None of these are optional when the mission asks for them.
14. **Mission completion check** — re-read the original plan and tick every numbered step. For any step that wasn't done, write a one-line reason in `MISSION_SKILLS.md` or the build's final summary. The build isn't done until every numbered step is either ✅ done or has a written reason for being deferred.

For the full 14-phase playbook, read `references/phase-guide.md`. For mission-interpretation patterns and the skill-trigger heuristic table, read `references/mission-interpretation.md`.

## Runtime Detection

```text
Is ultracode on (a system-reminder says so) OR did the user say "workflow"/"workflows"/"dynamic workflow"?
  YES → Workflow mode (PREFERRED): drive the implement + verify phases with the Workflow tool —
        deterministic JS that fans out the role-agents and adversarially verifies the result.
        Design/contracts stay inline. See "Dynamic Workflows" below + references/workflow-orchestration.md.
  NO → Is CLAUDE_CODE_EXPERIMENTAL_AGENT_TEAMS set?
    YES → Native Agent Teams (tmux, TeammateTool, inbox, shared task list). Outer drive loop = orchestrator-task-loop: the lead loops the shared task list until every task is completed and passes its TaskCompleted gate, fed by the TeammateIdle hook.
    NO → Is the Agent/Task tool available?
      YES → Subagents via Task/Agent tool (parallel, no TeammateTool)
      NO → Sequential mode (work through roles one at a time, user coordinates)
```

Workflow mode is gated on those opt-in signals on purpose: the Workflow tool can spawn dozens of
agents, so absent ultracode or an explicit "workflow" ask, don't reach for it — the other runtimes
stay the default and behave exactly as before. Each agent role skill works standalone regardless of
runtime; only this orchestrator skill needs the full decision tree.

**Model defaults don't change this gate.** The dynamic-workflows *feature* ships enabled by
default on most plans, but *automatic* workflow orchestration happens only under `/effort
ultracode` (session-only; resets every new session). "The session model is Fable 5" is NOT an
opt-in signal — wait for the ultracode system-reminder or an explicit ask. The prompt trigger
keyword is `ultracode` (renamed from `workflow` in v2.1.160); a natural-language "use a
workflow" counts as the same opt-in in any version.

**Model and effort are per-role dials, not only the ultracode gate.** Every dispatch takes
both a `model` and an `effort` — set them to the *work*, not one global level, per the tiering
policy in `model-adaptation` (the canonical home: task→tier map, priced ladder,
provider-relativity rule). Top tier at `xhigh`/`high` for load-bearing reasoning roles
(contracts, security, adversarial verification); mid tier for standard implementation;
mechanical/high-volume roles tier down to the cheapest model that clears the bar. Stay inside
ONE provider's ladder, and **pass `model` and `effort` explicitly on every spawn** — per-agent
defaults resolve to the session-start model, which goes stale after `/model`.

**Sequential mode**: When neither Agent Teams nor subagent spawning is available, work through each role one at a time within a single session. Apply the relevant role skill as your own instructions for that phase. The user may need to coordinate context resets between roles. Contracts and validation still apply — only the parallelism changes.

## Dynamic Workflows (ultracode)

When Workflow mode is selected, the **execution substrate** changes but the contract-first
philosophy does not. You still spend 50% on design and contracts — and that work stays **inline,
in the main loop**, because it's the human-in-the-loop architecture phase. What moves onto the
Workflow tool is the parallel-implement and verify phases: instead of hand-spawning agents and
shepherding replies message by message, you author a Workflow script that launches them with real
control flow — fan-out, barriers, loop-until-green, adversarial verification.

A workflow `agent()` becomes one of your role-agents by invoking that role's skill from inside
the agent's prompt (or `agent({agentType})` when the role is a registered type). The brief is the
same distilled template from `references/agent-spawning.md`; contracts, file ownership, the wave
gate, and the QA gate rules all apply unchanged.

Work it **one workflow per phase, in sequence** — implement, then (after you run the wave gate
and read the reports) verify — so you stay at every gate. Keep HITL phases inline: a workflow
agent runs to completion once. The QA gate is still law — the verify workflow informs you, it
never overrides `gate_decision`.

**Read `references/workflow-orchestration.md` before authoring** — it has the phase→workflow map,
the implement/verify script skeletons (with schemas for structured agent reports and the QA gate),
the adversarial-verify pattern, and the caveats that bite (pure-literal `meta`, one-level nesting,
worktree isolation cost, budget scaling, no silent caps).

## File Ownership

Directory ownership takes precedence over pattern ownership. Subdirectory carve-outs are explicit. The canonical map lives in `references/file-ownership.md` — when in doubt, that overrides any individual role skill. If two roles would touch the same file, resolve the conflict by assigning that file to exactly one role before spawning. Unresolvable conflicts → human decision.

## Coordination Rules

- **Never implement code yourself** — you are coordination only
- **All inter-agent communication goes through you**
- **Async, long-lived subagents where the build allows (Claude 5 family).** "Communication
  goes through you" governs *contract and shared-file changes* — it is not a mandate to block
  on every subagent reply. Prefer launching independent work and continuing, and long-lived
  subagents over one-shot spawns (in Workflow mode: `pipeline()` over a barrier wherever a
  stage doesn't need all prior results). Async changes *when you collect results*, not
  *whether the contract holds*.
- **Contract changes require the full protocol**: pause → update → version → notify → confirm
- **Shared file changes go through you** — relay to the owning agent
- **Circuit breaker at 3 failures** — see `references/circuit-breaker.md`. This *is* `loop-controller`'s no-progress/oscillation guardrail applied to agent dispatch (the same failures surviving 3 consecutive iterations → stop and escalate); every bounded-retry loop in the build shares that one stop-condition vocabulary — the Composition section's RUNS-AS-LOOPS bullet is the canonical loop-harness mapping.

## QE Agent Is Mandatory

Every orchestrated build **must** spawn a QE agent. Testing is not optional. Even if the plan document does not mention testing, you are responsible for spawning a QE agent that writes and runs tests covering the built code. The QE agent should be spawned after implementation agents complete (or in parallel if contracts are sufficient to write tests against). A build without tests is an incomplete build — the Definition of Done cannot be satisfied without a passing QA gate.

## Validation Sequence

1. **Contract diff** — curl commands vs fetch calls, line by line
2. **Agent validation** — each agent runs their checklist
3. **Wave gate (CRITICAL)** — between every wave of parallel agents, run the integrated install + typecheck + test loop and route failures back **by file ownership** to the owning agent. Driving the wave red→green is an explicitly-dispatched `fix-until-green` loop: one root cause per iteration, the *same* gate command re-run after each fix, greens verified against the diff (see the green-gate anti-pattern below), stopped by the circuit breaker if the wave oscillates. **For any wave that touched UI, also run `design-token-guard`** (`--json`; non-zero `summary.errors` blocks the wave) **and its organization sibling `class-extraction-guard`** (`repeated-class-string` warns by default; set the rule to `error` — ideally scaffolded at bootstrap — to make it block) alongside typecheck; DoD item 12 is the canonical statement of why a UI build needs both. See `references/wave-gate.md` for per-stack commands and failure routing, and each guard skill's `references/wiring-into-orchestrator.md` for the gate snippet.
4. **QE agent testing** — the QE agent writes and runs tests, produces `qa-report.json`
5. **End-to-end testing** — you run this: startup, happy path, persistence, edge cases
6. **QA gate** — QE agent's `qa-report.json` must pass gate rules

## Workspace Bootstrap

Any project with more than a single source file requires a root `README.md` and (for multi-service projects) a one-command `dev` script at the workspace root. The README's commands must actually run. See `references/workspace-bootstrap.md` for the required sections and the per-stack dev-aggregator table.

## QA Gate Rules

The QE agent outputs structured JSON per `skills/roles/qe-agent/references/qa-report-schema.json`. Before reading scores, **validate the report conforms to the schema** (all required top-level fields present, `scores` entries carry `score` + `notes`, `gate_decision` has `proceed` + `reason`); send a non-conformant report back to the QE agent for correction.

Build is blocked when:

- `gate_decision.proceed = false`
- Any blocker with `severity: CRITICAL`
- `scores.contract_conformance.score < 3`
- `scores.security.score < 3`

**You do NOT override the QE gate.** Fix the issues and re-run as an explicitly-dispatched `fix-until-green` loop: each iteration fixes one real blocker and re-runs the QE agent against the *same* schema — never lower the thresholds or edit the report to pass. The loop informs; `gate_decision` decides — a no-progress escalation is a real blocker, not a number to paper over. Stop conditions: `gate_decision.proceed = true` or the circuit breaker (escalate to human).

## Context Management

When agents approach context limits, follow the handoff protocol in `references/handoff-protocol.md`. Spawn continuation agents with the handoff file as first message context.

## Anti-Patterns

| Anti-Pattern | Prevention |
|---|---|
| Spawning without contracts | Never spawn until contracts pass quality checklist |
| Pasting full plan to all agents | Distill: each agent gets only their sections + contracts |
| Lead starts coding | Stay in coordination mode. Your job is orchestration. |
| Too many agents without context management | Size teams to the work but manage orchestrator context proactively — use handoffs, phased spawning, and distilled prompts. |
| Shared file editing | Strict file ownership. No exceptions without lead approval. |
| Verbal contract changes | Always write full updated contract, version it, get acknowledgments |
| Skipping contract diff | Always compare curl vs fetch before integration testing |
| Skipping QE agent | QE agent is mandatory. Always spawn one, even if the plan doesn't mention tests. |
| Skipping the wave gate | Always run the project's install + typecheck + test commands between waves. See `references/wave-gate.md`. |
| Shipping without a root README | A workspace without a root README has no setup story for the human. See `references/workspace-bootstrap.md`. |
| Declaring done without loading the UI in a browser | For any project with a UI, "tests pass" is not the bar. Open the dev URL, walk the primary routes, confirm the console is clean. |
| Forcing the human to open N terminals to run dev | Multi-service projects need a single `dev` script at the workspace root. |
| Committing to main | All work on a feature branch. Never merge/push to main unless user explicitly requests it. |
| Trusting docs/code over running config | The running external service is the source of truth — its Terraform/Cloud Run config can disagree with README and `.env.example`. Run Phase 0 before contracts. |
| **Treating mission text as agent-prompt fodder instead of a directive** | When the mission says "Generate seed imagery with Nano Banana" or "use frontend-design + ui-ux-pro-max for the UI", that's a directive to YOU to INVOKE those skills at the right phase. Mentioning the skill name in an agent prompt and hoping the agent invokes it is not the same thing. See `references/mission-interpretation.md`. |
| **Stopping at Phase 3 (parallel build) when the mission has more phases** | Missions often have phases 4 (verify), 5 (ship), 6+ (post-launch/meta). More phases = more work — keep going until every numbered step is ✅ done or has a written deferral reason (DoD item 7). |
| **Skipping skills the mission named** | A skill mentioned in the mission but never invoked is a DoD failure (item 8). Invoke it at the right phase OR record a one-line deferral reason in `coordination/MISSION_SKILLS.md`. The audit trail matters more than 100% coverage. |
| **No imagery on a UI build** | If the project has any UI surface, real seed imagery via `nano-banana` (or equivalent) is the difference between "looks like a demo" and "looks like a product". Stub URLs and emoji placeholders should be the exception, not the default. |
| **Declaring done without ux-review on UI builds** | Tests pass + dev server boots is not the bar for a UI project. After the build, invoke `ux-review` (or run Playwright + screenshots manually) and address what comes back. Visual quality is verifiable; verify it. |
| **Treating "ux-review invoked" as the post-build gate** | Process-level checks ("did the skill run?") let visible bugs ship — stale mock IDs on "live" pages, placeholder text, plausible lists linking to dead targets, auth dead-end shells — all rendering with 0 console errors. The outcome-level gate is `render-sanity` returning PASS on its four objective checks (DoD item 11); an "invoked" line in MISSION_SKILLS.md without that PASS is process rigor masking bugs. |
| **Skipping `render-sanity` when the dev stack isn't up** | Don't invoke validation against a dead port and call it green. Either bring up the stack first (the workspace already has a one-command `dev` script per workspace-bootstrap rules) or report "Cannot run — dev server not responding." Silent skips are how broken builds get declared done. |
| **Trusting render-level gates to catch hardcoded styling** | render-sanity and ux-review read *pixels*; a hardcoded color renders identically to its token, so off-token styling lives only in source and accumulates invisibly into a manual refactor later. Run `design-token-guard` on every UI wave alongside typecheck (DoD item 12) — a green render does not certify token discipline. |
| **Trusting a green gate without checking the fix is real** | A gate measures a *proxy*. An agent told to "make it green" can move the number without fixing the cause: relocate a violation into the checker's blind spot (a banned `rounded-full` reborn as inline `borderRadius:"50%"`), silence it with an ignore directive, or delete the failing assertion. When a gate flips red→green, read the diff that did it — did it *resolve* the finding or *relocate* it? A suspiciously easy green is a finding, not a win. This is the failure mode `fix-until-green` exists to guard against ("drive the gate green *without cheating the gate*") — run the wave/QA fix cycle as that bounded loop, never as un-guardrailed "keep retrying until it's green." |
| **Retrofitting a source-convention gate after the code exists** | A convention gate (`design-token-guard`, strict typecheck, a new lint rule) added *after* a fleet of agents has written the UI inherits a backlog — so it can only land in report-only "ratchet" mode, and clearing the debt becomes a manual multi-file burndown later (the painful kind a human notices). Scaffold these gates in the **bootstrap wave**, before the first frontend-agent writes a line, so violation #1 is caught at commit #1 and the backlog never accumulates. See `references/wave-gate.md`. |
| **Maintaining a changelog inline in a code file** | A version-history block in a constantly-imported source file is read on nearly every task for zero runtime value — and it *self-propagates*: each editing agent pattern-matches the block and appends. `CHANGELOG.md` is the system of record; a code file gets at most a one-line `version: X.Y.Z` plus a pointer. Finding an inline changelog while editing is a finding (file a cleanup item), not a thing to extend. `contract-author` enforces this for generated contracts. |
| **Spawning an agent without AFK/HITL classification** | Every agent dispatch must declare whether it can finish unattended (AFK) or needs a human in the loop (HITL). Undeclared dispatches stall builds the moment a prompt fires with no one watching. |
| **Passing a role label as `subagent_type`** | `backend-agent`, `docs-agent`, `qe-agent` etc. are role labels, not registered agent types — `subagent_type: "docs-agent"` fails with "Agent type not found." Dispatch with `general-purpose` and carry the role skill in the prompt. See the mapping table in `references/agent-spawning.md`. |
| **Hand-spawning agents one message at a time under ultracode / Workflow mode** | When the opt-in signals are present, deterministic fan-out is the whole point — author a Workflow script (`references/workflow-orchestration.md`) for the implement + verify phases instead of dispatching and babysitting replies manually. |
| **Putting the contract/design phase inside a workflow** | Design and contracts are interactive, human-in-the-loop architecture — the 50% that can't be delegated. Keep them inline; workflows execute implement + verify, not the decisions that shape them. |
| **Cramming the whole build into one mega-workflow** | One workflow per phase, run in sequence, so the wave gate and QA gate stay real checkpoints you read between. A single script that implements-and-ships hides the gates that keep multi-agent builds safe. |
| **Letting a workflow silently cap coverage** | If a script bounds work (top-N findings, sampled routes, no retry), `log()` what was dropped — same audit ethos as the mission-skills manifest. Silent truncation reads as "covered everything." |

## Definition of Done

ALL must be true:

1. Every agent passed their validation checklist
2. Contract diff — zero mismatches
3. **UI loads and renders correctly** — open the dev URL in a real browser, walk the primary routes, confirm real content renders and the headline user action works. Console clean (errors fail; warnings need a reason). `git clone && setup && dev` is the actual bar — tests passing isn't enough.
4. **Reality gate — the real value path runs, not just a mock** (the canonical statement). If the product's value depends on a live backend, a real service, an integration, or real data, at least **one real end-to-end path must be exercised and observed**: a real call that returns and renders, real data flowing through the UI, traffic visible in the dependency's own dashboard. Mocks are the right way to *build* — but a green mock-backed suite proves the *mocked* build is internally consistent, **not that the product works**; every other gate in this list measures presentation or internal consistency, and a fixture-backed shell greens all of them. A build that never touches the real path is **"scaffold complete — NOT done,"** and that status is the **headline** of the end-state report (item 17), never a deferred footnote. If the mission *explicitly* scoped the backend out, say so loudly: this build is a shell with its own DoD — don't let a green shell read as a finished product. (See `loop-controller` Step 2, *measure the goal, not a stand-in*.)
5. End-to-end validation passed (startup, happy path, edge cases) — **and the happy path is verified against the real value path at least once, not only the mock.** The mock proves the wiring; the real call proves the product.
6. All integration issues fixed and re-validated
7. Plan's acceptance criteria met — **every numbered step in the user's mission/plan is ticked** with either a "done" or a written reason for deferring. The build isn't done because you're tired; it's done because the user's list is closed out.
8. **Mission skill manifest closed out** — `coordination/MISSION_SKILLS.md` exists and shows every skill the mission explicitly named, each with either ✅ (invoked) or a one-line reason for skipping. A mission that names `nano-banana`, `ui-ux-pro-max`, `frontend-design`, `ux-review`, `repo-deep-dive`, etc. and gets a build with none of them invoked is a regression, not a deliverable.
9. **Visual assets exist for UI builds** — if the project has a UI, real seed imagery exists in `assets/` or `web/public/` (generated via `nano-banana` or sourced via another path). The bar is "looks like a product"; "stub URL placeholders" doesn't meet it.
10. **Post-build UX review passed for UI builds** — `ux-review` invoked (or equivalent Playwright + screenshots pass), and the issues it surfaces are fixed or recorded.
11. **Render-sanity returned PASS for UI builds** — `render-sanity` walked every user-facing route in a real browser and all four checks (smell scan, click-through, signed-out matrix, signed-in matrix) returned zero critical findings; a FAIL blocks the build. This is the *outcome* gate — "the checks came back clean," not "the skill was invoked." (It reads pixels, so realistic mock data passes it; the reality gate is item 4.)
12. **Source-convention gates passed for UI builds** — the canonical statement of the two source-level guards. `design-token-guard` returns zero error-severity findings: no inline styles or hardcoded colors bypassing the token system. A hardcoded color renders identically to its token, so it sails through every pixel gate and exists only in source — which is why a UI build needs the source gate **and** the render gates, not one or the other. Its *organization* sibling `class-extraction-guard` runs on the same builds and catches the orthogonal problem: the same correctly-tokenized utility combo copy-pasted inline instead of extracted into a named class (warnings by default; blocking when the project sets the rule to `error`). design-token-guard checks *which values* styling uses; class-extraction-guard checks *how it's organized* — both invisible to pixel gates. Findings route to the owning frontend-agent by file.
13. Contract changelog clean
14. QA gate passed — QE agent tests written, executed, and passing
15. **One-command dev is wired** — for any project with multiple services, the workspace root has a single `dev` (or equivalent) script that runs the whole dev stack in one terminal with prefixed output. See `references/workspace-bootstrap.md`.
16. **Collision-free ports** — the root `dev` script preflights each port and steps to the next free one instead of dying on `EADDRINUSE`, and no source or test file hardcodes a literal dev port (services read the resolved port from env). See `references/port-conventions.md`.
17. **End-state report** — a single file (e.g., `BUILD_RESULTS.md` or the build's git commit summary) lists what shipped, what was deferred, the mission skill checklist state, and explicit handoff items for the user. The user should be able to read this file and know exactly where the build stopped. **If the build is scaffold-only (mock-backed, the real value path unexercised), that is the report's headline — stated plainly at the top, not buried in a deferrals list.**

</what-to-do>

<supporting-info>

## Reference Documents

- **`references/mission-interpretation.md`** — how to read a multi-phase mission/plan as a script you EXECUTE, including the skill-trigger heuristic (when each composable skill earns its keep) and the `MISSION_SKILLS.md` template.
- **`references/workflow-orchestration.md`** — Workflow mode (ultracode / "workflow"): the phase→workflow map, role-agents-as-workflow-agents, implement + verify script skeletons with schemas, adversarial QA verification, and the caveats that bite. Read before authoring any Workflow script.
- **`references/phase-guide.md`** — the full 14-phase build playbook (Phase 0 external-services audit through Phase 13 handoff).
- **`references/team-sizing.md`** — how to size the agent team to the work; thresholds and starter formulas.
- **`references/file-ownership.md`** — canonical agent-to-directory ownership map and contract-first architecture overview.
- **`references/agent-spawning.md`** — the agent prompt template, the ~60-line split gate, the pre-dispatch checklist, AFK/HITL classification, spawn permissions, and a worked backend-agent example.
- **`references/wave-gate.md`** — per-stack install/typecheck/test commands and failure-routing protocol.
- **`references/workspace-bootstrap.md`** — required root README sections and the per-stack one-command `dev` aggregator table.
- **`references/port-conventions.md`** — the house port map, per-service bands, and the preflight/next-free allocation rule (with a `free_port` helper) that keeps a freshly-generated project from crashing on `EADDRINUSE` on its first `dev` run. Why `3000` is never an API port.
- **`references/circuit-breaker.md`** — the 3-failure circuit breaker for agent dispatch (= `loop-controller`'s no-progress guardrail). The loop-harness mapping — which build loops are configs of which loop skills — lives in the Composition section's RUNS-AS-LOOPS bullet.
- **`references/handoff-protocol.md`** — context-window handoff protocol for long-running builds.

</supporting-info>
