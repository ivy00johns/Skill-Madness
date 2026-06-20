# Agentic Loops and the `/loop` Command in Claude Code: A Build Guide for the "Skill Madness" Ecosystem

## TL;DR
- **Build loops as skills that wrap a verifiable "done" condition, not as raw bash `while` loops.** Claude Code now ships three native loop primitives — `/goal` (work until a model-verified condition holds), `/loop` (re-run a prompt on a schedule), and `/batch` / dynamic workflows (fan out one change across parallel worktree agents) — plus an official `ralph-loop` plugin. For "Skill Madness," the highest-leverage move is a thin **loop-controller meta-skill** that orchestrates these primitives with explicit exit conditions, iteration caps, and a separate-context evaluator, rather than reinventing the loop engine.
- **The single most important design rule, repeated by every authoritative source (Anthropic, Geoffrey Huntley, the Forward Future Loop Library), is: a loop is only as good as its verifiable stopping condition and its backpressure gate.** Loops converge when failures feed back as data (a failing test, a lint error, an evaluator score) and diverge/burn money when "done" is a subjective judgment the agent grades itself on. Your QE, contract-auditor, and observability skills are exactly the backpressure gates that make loops safe.
- **In a multi-agent ecosystem, loops belong at two levels: an inner loop per agent role (fix-until-green, refine-until-quality) and an outer orchestrator loop over the shared task list (loop until every task passes its quality gate).** Keep them flat where possible, use a fresh-context evaluator (the GAN/Plan-Generate-Evaluate pattern) so the grader never sees the build, and gate every loop with iteration limits, token budgets, and no-progress detection.

---

## Key Findings

1. **The native commands have crisp, distinct jobs.** `/goal` (Claude Code v2.1.139+) keeps a session working turn-after-turn until a Haiku-class evaluator confirms a condition; `/loop` (v2.1.71/72+) is a session-scoped cron scheduler that re-runs a prompt on an interval; `/batch` and dynamic workflows fan out across parallel worktree-isolated subagents. Conflating them is the "expensive mistake": a `/loop` on work with a finish line re-runs blindly on the clock; a `/goal` pointed at an external poll spins forever.
2. **The Ralph Wiggum pattern is the philosophical root, and Claude Code absorbed it natively.** Huntley's "Ralph is a Bash loop" (`while :; do cat PROMPT.md | claude ; done`, July 2025) became the official `ralph-loop` plugin (Stop-hook re-feeds the same prompt until a completion promise), then the native `/goal`. The key Ralph insights — fresh context each loop, file-system-as-memory, one task per iteration, "deterministically bad in an undeterministic world," tune-like-a-guitar — are directly portable to skills.
3. **Anthropic's own harness research converges on two patterns you should build into Skill Madness:** (a) the **initializer + coding agent** split with a feature-list JSON, progress file, and `init.sh`; and (b) the **Plan → Generate → Evaluate (PGE)** GAN-style loop with a fresh-context evaluator, because "agents are pathological optimists" about their own work.
4. **Loop safety is a solved-but-mandatory checklist:** unambiguous exit condition, max-iteration cap, token/cost budget, no-progress/oscillation detection, human-in-the-loop checkpoints before irreversible actions, and git checkpoints for rollback. Real incidents (a 4-agent loop that ran 11 days and burned tens of thousands of dollars) show what happens without enforcement (not just alerting).
5. **Loops integrate with your orchestrator via hooks and the shared task list.** Stop / SubagentStop / TaskCompleted hooks are the native re-trigger mechanism (block the stop → keep working). Agent Teams' shared task list is the natural substrate for an orchestrator-level loop.

---

## Details

### 1. The Forward Future "Loop Library"

The Loop Library (signals.forwardfuture.ai/loop-library, updated June 18, 2026; curated by Forward Future, most loops attributed to Matthew Berman, one to Peter Steinberger) is a catalog of **15 copy-paste agentic loops**. It is best treated as a **prompt cookbook**, not an architecture — its real value is its taxonomy statement and its insistence on stopping conditions.

**The library's core design principle (verbatim):** *"A useful loop specifies: trigger, action, proof, memory, and a stopping condition."* This five-part schema is the single most useful thing on the page and should become the required frontmatter contract for every loop skill you build. Every entry pairs a **Loop** (the action prompt) with an explicit **Verify / stop** condition.

**Full catalog (name → purpose → stop condition):**

| # | Loop | Purpose | Stop condition |
|---|------|---------|----------------|
| 001 | Overnight docs sweep | Nightly: review codebase, update docs to match latest changes, open PR | Documentation matches current implementation; finish with reviewable PR |
| 002 | Architecture satisfaction loop (Steinberger) | Refactor until architecture is satisfactory; live-test + autoreview + commit each step; track in `/tmp/refactor-{project}.md` | Architecture satisfactory and checks pass |
| 003 | Sub-50ms page-load loop | Optimize, measure page load across every page under repeatable conditions | Every page loads under 50 ms, no regressions |
| 004 | Production error sweep | Review prod logs, trace root cause, fix, verify, open PR, ping Slack | Actionable errors fixed and verified, or clean-log confirmation |
| 005 | 100% test coverage loop | Add tests until 100% coverage | Full suite passes at 100% coverage (coverage report = source of truth) |
| 006 | SEO/GEO visibility loop | Audit crawlability/indexation/structured data, fix highest-leverage gap, re-crawl | No remaining high-impact gaps; every priority query maps to an answer-ready page |
| 007 | Logging coverage loop | Add logging until every important path has useful, tested logs | Every important path emits useful, tested logs without exposing sensitive data |
| 008 | Nightly changelog loop | Nightly: update changelog with user-relevant changes | Every user-relevant change accounted for, or no-change recorded |
| 009 | Quality streak loop | Test realistic scenarios; on failure document + add regression/benchmark coverage + fix + restart streak | Latest [N] realistic cases pass in a row |
| 010 | Full product evaluation loop | Create [N] scenarios with predefined success criteria + scoring method, run all, fix causes, rerun | Every scenario meets the defined quality bar |
| 011 | Test-suite speed loop | Optimize test suite speed without reducing coverage or changing behavior | Faster suite, no coverage/behavior regression |
| 012 | Repository cleanup loop | Inspect branches/PRs/commits/worktrees, recover valuable work, clean stale | Repo state intentional; everything current, owned, or safely removed with evidence |
| 013 | Stale-safe batch release loop | Combine valid pending changes, exclude stale/unfinished, release together | Only current/complete changes ship; released revision = latest integrated main |
| 014 | Production data cleanup loop | Review prod records, remove invalid, improve classification logic, verify | Every remaining record meets the allowed definition |
| 015 | Post-release baseline loop | After releases finish, run standard benchmarks, record as new baseline | New baseline recorded with revision/environment/conditions |

**Taxonomy they use:** the library buckets loops into **engineering, research, evaluation, and operations**, but in practice nearly all 15 are *engineering/ops with a measurable proof*. **Design patterns advocated:** (1) every loop names its proof artifact (coverage report, benchmark, PR, audit); (2) "restart the streak" / "rerun the complete set" appears repeatedly — loops re-verify the *whole* after each fix, not just the changed unit; (3) nightly/scheduled cadence is treated as first-class (loops 001, 008); (4) loops end with a human-facing artifact (a PR, a Slack ping). **What it lacks** (and where Skill Madness must go further): no iteration caps, no token budgets, no non-convergence handling, no multi-agent orchestration — it is single-agent prompt-level guidance.

### 2. The native `/loop`, `/goal`, and `/batch` commands

There are now **four native autonomous mechanisms**, and you should treat them as separate primitives:

**`/goal` (the real "loop until done") — Claude Code v2.1.139+.** Sets a completion condition; after each turn a **small fast model (defaults to Haiku)** judges whether the condition holds from the transcript, returning yes/no + a reason. "No" feeds the reason back as guidance for the next turn; "yes" clears the goal and records an achieved entry. It is *"a wrapper around a session-scoped prompt-based Stop hook."* Critical constraints:
- The evaluator **does not run tools or read files** — it only judges *what Claude has surfaced in the conversation*. So conditions must be phrased as things Claude's own output can demonstrate (`"npm test exits 0"`, `"git status is clean"`).
- Condition up to **4,000 characters**; **one goal per session**; a new `/goal` replaces the old.
- **No built-in token budget** — it runs until the condition is met or you Ctrl+C / `/goal clear`. Anthropic's docs recommend embedding a bound directly in the condition (e.g., `"or stop after 20 turns"`).
- Anthropic's four canonical use cases: migrate a module until every call site compiles and tests pass; implement a design doc until all acceptance criteria hold; split a large file until each module is under a size budget; work through a labeled issue backlog until empty.
- Requires accepting the workspace trust dialog; unavailable if `disableAllHooks` or `allowManagedHooksOnly` is set.
- Works in interactive, `claude -p` headless (`claude -p "/goal ..."`), desktop, and Remote Control modes. The recommended unattended combo is **auto mode + /goal**: auto mode removes per-tool prompts, `/goal` removes per-turn prompts.

**`/loop` (the scheduler) — v2.1.71/72+.** A bundled skill that re-runs a prompt or slash command on a cron interval. `/loop 5m check if the deploy finished`. Key mechanics:
- Interval = number + unit (`s` rounds up to 1 min, `m`, `h`, `d`); **default 10 minutes**; omit the interval and Claude picks a **dynamic self-paced delay (1 min–1 hour)** based on what it observed, or runs `loop.md` if present.
- **Session-scoped**: dies when you close the terminal; **no catch-up** for missed fires (fires once when idle, not once per missed interval); **auto-expires after 3 days** (some docs say 7 — version-dependent; treat 3 days as the safe assumption); max **50 scheduled tasks** per session; **Esc** clears the pending wakeup.
- You can schedule **any slash command or skill**: `/loop 20m /review-pr 1234`. This is the key composition point — *skills + loops*. Boris Cherny (Claude Code creator) runs `/loop 5m /babysit` (auto-address review comments, auto-rebase PRs) and `/loop 30m /slack-feedback`.
- It does **not** automate Claude's internal agentic loop — it is "a thin scheduler that periodically restarts that loop from the outside." Disable entirely with `CLAUDE_CODE_DISABLE_CRON=1`.

**`/batch` and dynamic workflows (fan-out).** `/batch` spreads one large change across **5–30 parallel worktree-isolated subagents**, each opening a PR. **Dynamic workflows** (research preview, CLI v2.1.154+, Opus 4.8 era) go further: Claude writes a **JavaScript orchestration script** that fans out across up to **1,000 subagents (16 concurrent cap)**, keeping intermediate results in script variables (not context). Primitives: `agent()` (one subagent, optional JSON-schema validated output), `parallel()` (barrier — waits for all), `pipeline()` (stream items through stages, no barrier), with `isolation: 'worktree'` and a token budget. Reusable patterns named by the Claude Code team: **fan-out → reduce → synthesize**, **judge panel** (N attempts, parallel judges, synthesize winner), and **loop-until-dry** (keep spawning finders until K consecutive rounds find nothing new). Canonical proof point: Jarred Sumner's Bun port (~750,000 lines Zig→Rust, 99.8% of tests passing, 11 days), built with parallel port agents + two adversarial reviewers per file + a fix loop driving build/test until clean. **Caveat:** workflows are "meaningfully more usage" — one developer spawned 90 review agents and hit monthly token limits.

**Decision rule:** *Are you pushing work to a finish line, or watching for something to change?* Finish line → `/goal`. Watch → `/loop`. One big mechanical change across many files → `/batch`/workflows.

### 3. The Ralph Wiggum pattern and its descendants

**Origin (Geoffrey Huntley, "Ralph Wiggum as a 'software engineer'," July 14 2025).** *"Ralph is a technique. In its purest form, Ralph is a Bash loop": `while :; do cat PROMPT.md | claude-code ; done`.* Named for the Simpsons character — dumb, cheerful, persistent. Huntley's hard-won principles, all directly applicable:
- **"Deterministically bad in an undeterministic world"** — failures are predictable and informative; tune the prompt ("erect a sign") each time Ralph falls off the slide.
- **One thing per loop.** "Only one thing… trust Ralph to decide what's the most important thing."
- **~170k usable context; use as little as possible.** Primary context window should act as a **scheduler** that spawns subagents for expensive allocation (search, summarizing test results); cap parallelism (e.g., "up to 500 subagents for search, but only **1 subagent for build/tests**" to avoid bad backpressure).
- **File-system-as-memory:** `fix_plan.md` (the live TODO, watched "like a hawk" and thrown out often), `@AGENT.md` (how to build/run — Ralph self-updates it), and `specs/*` (one per file). State survives between fresh-context iterations through files + git history.
- **Backpressure is the engineering:** "code generation is easy now; what is hard is ensuring Ralph generated the right thing." Wire in type checkers, static analysers, tests, security scanners — "the wheel has got to turn fast."
- **No cheating:** Claude has an inherent bias toward placeholder/minimal implementations; Huntley uses emphatic anti-placeholder prompts and runs separate Ralphs to hunt down stubs.
- Reported results (anecdotal, from Huntley, covered by The Register & VentureBeat): 6 repos overnight at a YC hackathon; a $50k contract delivered for **$297** in API cost (Huntley on X, July 11 2025, verbatim: *"Cost of a $50k USD contract, delivered, MVP, tested + reviewed with @ampcode. $297 USD."*); the **CURSED** programming language built over 3 months.
- **Huntley's caveat:** "There's no way in heck would I use Ralph in an existing code base" — it's a greenfield bootstrapping technique that gets "90% done." Senior engineering judgment is still required.

**Official `ralph-loop` plugin (anthropics/claude-code).** Implements Ralph via a **Stop hook** that intercepts exit: run `/ralph-loop "<prompt>" --completion-promise "DONE" --max-iterations 50`; Claude works → tries to exit → Stop hook blocks → re-feeds the *same* prompt → repeat until the promise string appears or iterations run out. `--completion-promise` uses **exact string matching** (can't express SUCCESS vs BLOCKED), so **`--max-iterations` is the primary safety mechanism**. `/cancel-ralph` stops it.

**Community descendants:**
- **frankbria/ralph-claude-code** (Bash): 784 tests; **dual-condition exit gate** (requires BOTH completion indicators AND an explicit `EXIT_SIGNAL`); **rate limiting at 100 calls/hour** (configurable, hourly reset); **circuit breaker** with two-stage error filtering; **24h session expiration**; tmux monitoring; Docker sandbox (`ralph --sandbox docker`). *(These specific numbers are frankbria's, not ralph-orchestrator's.)*
- **mikeyobrien/ralph-orchestrator** (Rust, 2.9k stars / 280 forks, latest release v2.9.3 dated May 8 2026; docs self-describe it as a "functional, early-stage (alpha) implementation"): a **hat-based** event-driven orchestrator — the closest analog to your role-based ecosystem (see §7). Default completion token **`LOOP_COMPLETE`** (README, verbatim: *"Ralph iterates until it outputs LOOP_COMPLETE or hits the iteration limit"*); default caps `max_iterations: 100`, `max_runtime_seconds: 14400` (4h), cost limit $10, consecutive-failure limit 5, **loop detection at ≥90% output similarity**. Its AGENTS.md tenets, verbatim: *"Fresh Context Is Reliability — Each iteration clears context. Re-read specs, plan, code every cycle. Optimize for the 'smart zone' (40-60% of ~176K usable tokens). Backpressure Over Prescription — Don't prescribe how; create gates that reject bad work."* Its governing tenet, verbatim: *"The orchestrator is a thin coordination layer, not a platform. Ralph is smart; let Ralph do the work."*
- **Wiggum CLI**, **fstandhartinger/ralph-wiggum** (SpecKit-style, terminates+restarts each task for clean context), **Th0rgal/open-ralph-wiggum** (multi-agent-CLI agnostic), **agenticloops-ai/ralph-loop** (PRD + progress scaffold, "one task per iteration").
- **Huntley's evolution:** he now runs agents that push to master with no branches/CI on a NixOS box, with feedback loops that self-repair; he calls his research **"Loom"** (infrastructure for evolutionary software), Steve Yegge calls his **"Gas Town"** ("Kubernetes for agents"). Direction of travel: from single Ralph → fleets of coordinated loops.

### 4. Goal-oriented / objective-driven patterns and the canonical agent loops

The shift is from single-shot prompting to **giving the LLM a goal + a verifier and letting it loop**. Anthropic's own best-practice guidance (paraphrased): *the highest-leverage thing you can do is give Claude a way to verify its work — without clear success criteria, you become the only feedback loop.* The canonical academic loops, and where each fits Skill Madness:

- **ReAct (Reason+Act, Yao et al. 2022):** interleave Thought → Action (tool) → Observation until done. The baseline tool-using loop; lowest overhead; "short-term thinking" is its weakness. *Use for: research/explore skills, single-field fixes.*
- **Reflexion / Self-Refine (Shinn et al. 2023; Madaan et al.):** generate → critic reviews → feed critique back → regenerate; stop when the critic signs off or after N rounds. **Failure mode = self-bias:** a critic that is the same model as the drafter rubber-stamps its own work (measured in Panickssery et al. 2024). **Fix: distinct evaluator + an external signal (tests).** Per Ridnik et al. 2024, "Code Generation with AlphaCodium: From Prompt Engineering to Flow Engineering" (arXiv:2401.08500), GPT-4 accuracy *"increased from 19% with a single well-designed direct prompt to 44% with the AlphaCodium flow"* (pass@5, CodeContests validation set) — the tests are what stop the rubber-stamp. *Use for: refine-until-quality, fix-until-green.*
- **Plan-and-Execute / ReWOO:** plan the whole strategy upfront, then execute; efficient but brittle to stale plans. *Use for: migrations, well-understood multi-step work.*
- **Anthropic Plan-Generate-Evaluate (PGE) / GAN-style harness** (Harness Design for Long-Running Application Development, Mar 2026): a **Planner** expands a 1–4 sentence brief into a spec (deliberately under-specifying implementation), a **Generator** builds in sprints, and a **fresh-context Evaluator** (with Playwright MCP, no Write/Edit tools) clicks through the live app and grades each sprint against a rubric with **hard thresholds** — any criterion below threshold fails the sprint and returns detailed feedback. Before each sprint they negotiate a **sprint contract** (a shared, testable definition of "done"). 5–15 iterations, up to ~4 hours. In Anthropic's retro-game-maker test, the solo agent produced a barely-functional prototype in 20 min for ~$9; the full harness ran ~6 hours, cost ~$200, and delivered a polished, playable app. This is the architecture that maps most directly onto your contract-author/auditor meta-skills.

**Completion detection** in practice uses one (ideally several) of: an explicit emitted sigil grep'd from output (`<promise>COMPLETE</promise>`, `LOOP_COMPLETE`); a mechanical check (test exit 0, lint clean, coverage %, empty queue); a fresh-model evaluator (`/goal`'s Haiku judge, the PGE evaluator); or a **default-FAIL contract** (every criterion starts false; the agent can't flip it without opening evidence — from Anthropic's `cwc-long-running-agents` repo). **Convergence vs divergence:** loops converge when the proof signal is external and can't be argued with; they diverge/oscillate when "done" is subjective or when the agent grades itself.

### 5. Loop Types and Taxonomy (core deliverable)

For each type below: **purpose / structure / entry / exit / concrete use case**. These are the loop *archetypes* Skill Madness should support; §10 maps them to specific skills.

1. **Fix-until-green** — *Purpose:* drive a failing build/test suite to passing. *Structure:* run tests → parse failures → fix one → re-run (Reflexion + external signal). *Entry:* failing suite or red CI. *Exit:* `test command exits 0` AND lint/typecheck clean; cap at N iterations. *Use:* `/goal all tests in test/auth pass and lint is clean`. **Owner: QE.**
2. **Build-until-spec / contract-conformance** — *Purpose:* implement until a contract/spec is satisfied. *Structure:* PGE — generator builds one feature, evaluator checks against the contract. *Entry:* a written contract/feature-list (your contract-author output). *Exit:* every contract criterion passes its evidence check (default-FAIL). *Use:* implement a design doc until all acceptance criteria hold. **Owners: role agent + contract-auditor.**
3. **Refine-until-quality (LLM-judge)** — *Purpose:* iterate until a quality bar / rubric score is met. *Structure:* generate → fresh-context judge scores against rubric with hard thresholds → feedback → regenerate. *Entry:* draft + rubric. *Exit:* all rubric dimensions ≥ threshold, or max rounds (5–15). *Use:* frontend polish, doc quality, API-design review. **Owners: any role + a dedicated evaluator subagent.**
4. **Research-until-answered** — *Purpose:* gather info until a question is fully answered. *Structure:* fan-out searches → adversarially verify each claim against sources → synthesize (the `/deep-research` workflow shape). *Entry:* a question + success criteria ("every claim cited"). *Exit:* loop-until-dry (K rounds surface nothing new) or all sub-questions answered. *Use:* spike a new library, codebase Q&A. **Owner: docs/research role.**
5. **Review-and-revise** — *Purpose:* code review → fix → re-review until clean. *Structure:* reviewer subagent (fresh context) produces findings → author fixes → re-review. *Entry:* a diff/PR. *Exit:* reviewer returns zero blocking findings. *Use:* `/loop 5m /babysit` auto-addressing review comments. **Owners: security/QE reviewer + author role.**
6. **Migration loop** — *Purpose:* transform files one at a time until all are done. *Structure:* enumerate targets → one file per iteration (or fan-out worktree agents) → verify behavior-identical → commit. *Entry:* a mapping doc + target set. *Exit:* every target migrated, full suite green, no legacy pattern remains. *Use:* Jest→Vitest, API version bump, framework swap. **Owners: orchestrator + role agents (parallel).**
7. **Coverage loop** — *Purpose:* add tests until a coverage target. *Structure:* run coverage → find lowest-covered unit → add tests → re-measure. *Entry:* coverage below target. *Exit:* coverage report ≥ target (e.g., 100% or 80%), suite green. *Use:* Loop Library #005. **Owner: QE.**
8. **Performance loop** — *Purpose:* profile → optimize → re-profile until target. *Structure:* benchmark under repeatable conditions → optimize highest-leverage → re-benchmark, check for regressions. *Entry:* metric above budget. *Exit:* metric under target on every measured path, no functional regression. *Use:* Loop Library #003 (sub-50ms), #011 (test-suite speed). **Owner: performance role.**
9. **Self-healing loop** — *Purpose:* detect error → diagnose → fix → verify. *Structure:* watch logs/CI (often a `/loop` poller or a Channel push) → on actionable error, trace root cause → fix → verify → PR. *Entry:* an error signal. *Exit:* error resolved and verified, or clean-log confirmation. *Use:* Loop Library #004 production error sweep. **Owners: observability + role agent.**
10. **Exploration/understanding loop** — *Purpose:* build a mental model of an unfamiliar codebase. *Structure:* fan-out read-only subagents mapping subsystems → synthesize → identify gaps → repeat. *Entry:* "I don't understand X." *Exit:* a written architecture summary that answers the seed questions. *Use:* onboarding to a new repo. **Owner: project-profiler.**

### 6. Loop safety, control, and convergence

The mandatory guardrail stack (synthesized from Anthropic, ralph-orchestrator, and production agent-loop engineering):
- **Unambiguous exit condition.** Phrase "done" as a mechanical, observable proof (test exit code, file count, empty queue, coverage %). Use a **default-FAIL contract** so criteria can't be marked passing without evidence. Avoid subjective conditions ("looks good") for the model-evaluator path.
- **Iteration limit / circuit breaker.** Always set `--max-iterations`; ralph-orchestrator defaults to `max_iterations: 100`, a 4-hour runtime cap, and a **consecutive-failure limit of 5**. Stop-hook loops MUST check `stop_hook_active` to avoid infinite loops.
- **Token / cost budget.** `/goal` has *no* built-in budget — embed a turn cap in the condition and monitor with `/cost`. Dynamic workflows accept an explicit token budget. ralph-orchestrator's Overview docs warn verbatim: *"Autonomous loops consume significant tokens. A 50-iteration cycle on large codebases can cost $50-100+ in API credits, quickly exhausting subscription limits."* The lesson from the documented 11-day / multi-thousand-dollar runaway: **enforcement (terminate at threshold), not just alerting.** Set per-agent budget caps.
- **Non-convergence / oscillation detection.** Watch for output repeating (ralph-orchestrator trips at **≥90% similarity** to recent history), no state change across iterations (no-progress detection), or token growth that's quadratic rather than linear. One documented system repeated the same answer 58 times without these guards. In one benchmark of incomplete agent runs, **~36% of non-convergence was "looping/thrashing" and ~29% budget exhaustion** — these two failure modes dominate.
- **Human-in-the-loop checkpoints.** Mandatory review before irreversible actions (DB writes, deploys, external API calls, force-push). Implement via a checkpoint that pauses the loop (ralph-orchestrator uses a `human.interact` event with a default 300s timeout).
- **Rollback / checkpoints.** Commit working state every iteration with descriptive messages (Anthropic's coding-agent recipe). On a broken codebase, `git reset --hard` and re-loop is often cheaper than rescuing it (Huntley). Worktree isolation lets parallel agents fail without contaminating each other.
- **Guardrails against making things worse.** Run validation on only the changed unit each loop; forbid editing/deleting tests to make them pass (Anthropic uses *"It is unacceptable to remove or edit tests"* and stores the feature list as JSON because the model is less likely to overwrite JSON than Markdown); use a fresh-context evaluator with **no Write/Edit tools** so the grader can't "fix" by lowering the bar.

### 7. Loops + multi-agent orchestration (critical integration)

This is where Skill Madness differs from a single-prompt loop. Four integration layers:

**(a) Loop-per-agent (inner loops).** Each role skill runs its own internal verify loop: the QE agent runs fix-until-green, the performance agent runs profile-optimize-reprofile, the docs agent runs research-until-answered. This matches Huntley's "primary context as scheduler" and Anthropic's open question ("specialized agents like a testing agent or code-cleanup agent could do an even better job at sub-tasks").

**(b) Orchestrator-level loop (outer loop).** The lead loops over **task assignment until all tasks pass their gate**. The cleanest native substrate is **Agent Teams' shared task list** (experimental; `CLAUDE_CODE_EXPERIMENTAL_AGENT_TEAMS=1`): tasks have states pending → in_progress → completed with `blockedBy` dependencies; teammates claim tasks, work in their own context windows, and coordinate via the shared file + peer messaging (no central bottleneck). The orchestrator's loop = "while any task is not `completed` and passing its quality gate, (re)assign and supervise." This is exactly ralph-orchestrator's model, generalized.

**(c) The hat/event model (a blueprint for your role ecosystem).** ralph-orchestrator formalizes role-based looping in a way you should mirror conceptually. A **"hat"** is a specialized persona defined in YAML with `triggers` (events that activate it), `publishes` (events it may emit), and `instructions`. Default builtins: **planner, builder** (fallback pair) plus shipped patterns `code-assist`, `debug`, `research`, `review`, `pdd-to-code-assist`. A real 4-hat pipeline: **📋 Planner** (`triggers: [build.start]` → `publishes: [tasks.ready]`, explicitly *"MUST NOT start implementing"*) → **⚙️ Builder** (TDD, one task, `triggers: [tasks.ready, validation.failed]`) → **✅ Validator** (runs tests/clippy/fmt/build; emits `validation.passed`/`validation.failed`) → **📦 Committer** (`triggers: [validation.passed]`). The **EventBus** routes each emitted event to the hat whose triggers match; the loop continues until **`LOOP_COMPLETE`**. Crucially, **`validation.failed` is a Builder trigger** — that's the backpressure feedback edge. **This maps 1:1 onto your existing roles** (orchestrator=event router, backend/frontend/infra=builders, QE=validator, security=an adversarial validator hat, contract-auditor=the gate that emits pass/fail). Termination is a **dual-condition gate: no open tasks AND consecutive `LOOP_COMPLETE`**, optionally plus a `required_events` check so the agent can't shortcut the workflow.

**(d) Hooks as the re-trigger and gate mechanism.** Native lifecycle events wire loops into the team:
- **Stop / SubagentStop** hooks (exit 2 or `decision: "block"`) force continuation until a real condition clears — "don't stop until tests pass." A Stop hook declared in an agent/skill's frontmatter is **automatically converted to SubagentStop** when that agent runs as a subagent — so a loop gate ships *with* the skill.
- **TaskCompleted** hook (experimental) = a **validation gate** fired when a task is marked complete; exit 2 rolls it back. This is the orchestrator-loop's per-task quality gate.
- **TeammateIdle** hook = "assign new work" — the natural hook to keep the outer loop fed.
- **Prompt-type and agent-type hooks** let the gate itself be an LLM/subagent evaluation (`{"type":"prompt","prompt":"Evaluate if Claude should stop: $ARGUMENTS"}`), which is how `/goal` is implemented under the hood.

**Production examples of looped multi-agent systems:** Anthropic's PGE harness (planner/generator/evaluator, file-based handoffs); dynamic workflows (Bun's 750k-line port with parallel agents + adversarial reviewers + a fix loop); Gas Town / Multiclaude / Agent Teams (orchestrator decomposes → spawns workers → loops over the task board).

### 8. Practical implementation in Claude Code skills

**As a SKILL.md skill.** A skill = a directory with `SKILL.md` (YAML frontmatter + markdown body). Frontmatter fields relevant to loops: `name`, `description` (drives auto-discovery — write it third-person, "This skill should be used when…"), `disable-model-invocation: true` (for loops with consequences — you want to type `/fix-loop` deliberately, not have Claude start it), `allowed-tools`, `context: fork` + `agent:` (run the loop in a subagent to keep the main conversation clean), `model`, `hooks` (ship a Stop-hook gate with the skill), and `argument-hint`. Use **dynamic context injection** (`` !`command` `` lines run before Claude sees the skill) to inject live state (test results, coverage, git status) each invocation. Keep the body lean (~1,500–2,000 words); push detail to `references/`; put deterministic steps in `scripts/`.

**Implementation approaches and tradeoffs:**

| Approach | Mechanism | Best for | Tradeoff |
|---|---|---|---|
| **`/goal` from a skill** | Skill sets a verifiable condition; Haiku evaluator loops turns | "work until correct" with transcript-provable done | No file/tool verification by evaluator; no built-in budget |
| **Stop/SubagentStop hook** | Hook blocks exit until a script/prompt condition passes | deterministic gates ("tests must pass"); ships with skill | must guard `stop_hook_active`; always-block = infinite loop |
| **Slash command + `/loop`** | Package workflow as skill, schedule with `/loop 20m /skill` | recurring/poll workflows (babysit PRs, nightly sweeps) | session-scoped, 3-day expiry, no catch-up |
| **External bash (Ralph)** | `while :; do claude -p < PROMPT.md ; done` | greenfield, full fresh-context per iteration, runs across context windows | needs `--dangerously-skip-permissions` → sandbox required; no native budget |
| **Dynamic workflow** | Claude writes JS orchestration, fans out subagents | large parallel migrations/research/review | token-hungry; research preview |

**Fresh-context vs same-session:** the Ralph community split is real. Stop-hook plugins force the *same* session to continue (risking context overflow + lossy compaction); the fstandhartinger/ralph-orchestrator school **terminates and restarts each iteration with clean context**, reading state from disk. For long migrations, prefer fresh-context-per-task; for short refine loops, same-session is fine.

**State management across iterations (project-agnostic).** This is what makes a loop skill reusable. Externalize state to **path-addressable files** (Anthropic's term): a progress file (`claude-progress.txt` / `PROGRESS.md`), a feature-list/task JSON (default-FAIL), `fix_plan.md` (the live TODO), an `init.sh` (how to build/run), and git history. Anthropic's **initializer agent** writes these on first run; every subsequent **coding agent** starts by reading them, runs a basic smoke test, picks the highest-priority not-done item, works one increment, then commits + updates the progress file. Read these paths from `.claude/profile.yaml` so the same loop skill works across projects.

### 9. Day-to-day loop workflows (how to actually use loops)

**Morning (triage):** `/loop` or a Desktop scheduled task at 9am that runs production-error-sweep (#004), reviews overnight CI, and posts a Slack summary. A `/goal` to clear the labeled-issue backlog to empty.

**During active work (babysitters):** `/loop 5m /babysit` (auto-address review comments, auto-rebase) and `/loop 30m` to poll a long build/deploy — Boris Cherny's documented daily setup. A fix-until-green `/goal` running in auto mode while you do design work in another worktree.

**End-of-day / overnight (unattended, sandboxed):** overnight-docs-sweep (#001) and nightly-changelog (#008); a Ralph/dynamic-workflow build on a greenfield feature in an isolated worktree. **Only run unattended what has a hard verifier and is reversible** — coverage loops, lint/type-error fixes, dependency-update-then-test, docs. Never unattended: production data changes, deploys, anything without a test gate. Always sandbox (`--sandbox`/Docker) since unattended Ralph needs `--dangerously-skip-permissions`.

**Codebase health (recurring):** dependency-audit `/loop every 30m` during a sprint; type-error and lint-fix loops; repository-cleanup (#012) weekly.

**Learning a new codebase:** the exploration loop (fan-out read-only subagents → architecture summary), run once via your project-profiler.

**Solo power-user regular set:** fix-until-green (on demand), babysit (continuous), nightly docs+changelog, weekly repo cleanup, dependency audit during sprints, performance baseline post-release.

---

## Recommendations

### Concrete loop skills to build (prioritized) — §10 deliverable

**Build now (P0 — high value, hard verifier, low risk):**

1. **`loop-controller` (meta-skill, the foundation).** *Purpose:* a reusable harness that wraps any task in the Loop Library's 5-part contract (trigger, action, proof, memory, stop) plus the guardrail stack (max-iterations, token budget, no-progress detection, checkpoint commits). *Entry:* invoked by orchestrator or user with a goal + proof spec. *Exit:* proof passes or a cap trips. *Roles:* all (it's infrastructure). *Integration:* the orchestrator calls it to wrap any role's work; reads caps from `.claude/profile.yaml`. *Form:* **standalone skill** (`disable-model-invocation: true`) that internally chooses `/goal`, a Stop-hook, or `claude -p` based on the proof type. **Build first — everything else composes on it.**

2. **`fix-until-green` (QE).** *Purpose:* drive tests+lint+typecheck to passing. *Entry:* red suite/CI. *Exit:* `test exits 0 AND lint clean AND typecheck clean`, cap N. *Role:* QE. *Integration:* orchestrator dispatches after any role's build task; also a **Stop-hook gate** that other role skills inherit. *Form:* **skill + Stop hook** (gate ships with it). P0 — directly leverages John's QE background.

3. **`contract-conformance-loop` (build-until-spec).** *Purpose:* PGE loop — implement until the authored contract's criteria all pass, graded by a **fresh-context evaluator subagent with no Write/Edit tools** (default-FAIL). *Entry:* a contract from contract-author. *Exit:* every criterion has passing evidence. *Roles:* any builder + contract-auditor (as evaluator). *Integration:* this is the loop form of your existing contract-author/auditor pair. *Form:* **skill** orchestrating a generator + an evaluator subagent. P0 — uniquely fits the existing meta-skills.

4. **`babysit` (review-and-revise, scheduled).** *Purpose:* auto-address review comments + rebase PRs. *Entry:* open PR. *Exit:* zero blocking review findings. *Roles:* author role + security/QE reviewer. *Integration:* run via `/loop 5m /babysit`. *Form:* **slash command/skill scheduled with `/loop`.** P0 — proven daily-driver pattern.

**Build next (P1 — high value, needs a metric or guarded autonomy):**

5. **`coverage-loop` (QE)** — add tests to a coverage target; exit on coverage report ≥ target. **skill.**
6. **`self-healing-loop` (observability + role)** — poll logs/CI (or consume a Channel push) → root-cause → fix → verify → PR; HITL checkpoint before any prod-touching fix. **skill + `/loop` poller.**
7. **`migration-loop` (orchestrator + roles)** — mapping-doc-driven, one-file-per-iteration or `/batch` fan-out with worktree isolation; exit when all targets migrated + suite green + no legacy pattern. **skill that may invoke `/batch`/dynamic workflow.**
8. **`perf-loop` (performance role)** — profile→optimize→re-profile against a budget under repeatable conditions; exit on metric-under-target, no regression. **skill.**
9. **`orchestrator-task-loop` (the outer loop)** — lead loops over the Agent Teams shared task list until every task is `completed` and passes its **TaskCompleted gate**; uses TeammateIdle to keep workers fed. **skill + TaskCompleted/TeammateIdle hooks.** (P1 because Agent Teams is experimental — prototype behind a flag.)

**Build later (P2 — lower frequency or higher risk):**

10. **`nightly-docs-and-changelog` (docs)** — scheduled sweep (#001 + #008). **Desktop scheduled task / cloud routine** (survives laptop-off) rather than `/loop` (3-day expiry).
11. **`dependency-health-loop` (infra/security)** — audit + update + test; HITL before merging majors. **skill + scheduled.**
12. **`codebase-exploration-loop` (project-profiler)** — fan-out understanding loop; one-shot on new-repo onboarding. **dynamic workflow / `/deep-research` style.**
13. **`repo-cleanup-loop` (infra)** — Loop Library #012, weekly. **skill.**

### Staged adoption plan and the thresholds that change it
- **Stage 1 (week 1):** build `loop-controller` + `fix-until-green`; run them attended in one repo. **Promote to Stage 2 when** a fix-until-green loop completes 5 consecutive runs with no human intervention and no oscillation.
- **Stage 2:** add `contract-conformance-loop` + `babysit`; introduce the fresh-context evaluator. **Promote when** the evaluator's pass/fail agrees with your judgment ≥90% of the time (tune its prompt against divergences, exactly as Anthropic did).
- **Stage 3:** wire the `orchestrator-task-loop` over Agent Teams behind `CLAUDE_CODE_EXPERIMENTAL_AGENT_TEAMS=1`; add migration/perf/self-healing loops. **Promote to unattended/overnight only when** every loop has: a hard external verifier, a token budget with enforcement, no-progress detection, checkpoint commits, and a sandbox.
- **Roll back a loop to attended (or kill it) when** any of: token spend grows non-linearly, output similarity >90% across iterations, the evaluator and you disagree, or it touches an irreversible resource without a checkpoint.

### Design rules to encode in every loop skill
- Require the **5-part contract** (trigger, action, proof, memory, stop) in frontmatter/body.
- **Externalize state** to profile-defined paths (progress file, task JSON, fix_plan); never rely on conversation memory across iterations.
- **One task per iteration**; spawn subagents for expensive search/verification; cap parallelism on build/test to 1.
- **Separate the grader from the doer** (fresh context, no write tools) for any subjective bar.
- **Default-FAIL**: criteria start false; evidence required to flip.
- Make caps **project-agnostic** by reading them from `.claude/profile.yaml`.

---

## Caveats
- **Version- and experiment-dependent.** `/goal` requires v2.1.139+; `/loop` v2.1.71/72+; dynamic workflows v2.1.154+ (research preview); **Agent Teams is experimental and disabled by default** with known limitations (no session resumption for in-process teammates, lagging task-state propagation, slow shutdown). `/loop` expiry is reported as 3 days in some docs and 7 in others — treat 3 days as the safe assumption and verify on your version. There were March 2026 reports of `/loop` returning "Unknown skill" on some v2.1.71 installs.
- **Attribution care on Ralph clones.** The "100 calls/hour," "30-min circuit-breaker cooldown," and `MAX_TOKENS_PER_HOUR` numbers are **frankbria/ralph-claude-code's**, NOT mikeyobrien/ralph-orchestrator's. ralph-orchestrator's documented defaults (`max_iterations: 100`, 4h runtime, $10 cost, 5-failure limit, 90%-similarity loop detection) come partly from its legacy v1 (Python) "Overview" page; the v2 (Rust) project (v2.9.3, May 2026) may differ. Verify before hard-coding.
- **Anecdotal results.** Huntley's $297-for-$50k contract, "6 repos overnight," and CURSED are self-reported and not independently benchmarked (his own framing: Ralph is greenfield-only and gets "90% done"; senior engineers remain essential). The Bun port's "99.8% tests passing / 11 days" is Anthropic/Jarred Sumner's account.
- **Evaluator blind spots are real.** Anthropic found Claude is "out of the box a poor QA agent" — it approves its own mediocre work and tests superficially; the evaluator needed several rounds of prompt-tuning against human judgment before it graded reasonably, and even then missed deeply-nested bugs. Budget for evaluator tuning.
- **Cost is the dominant footgun.** `/goal` has no native budget; dynamic workflows and Agent Teams use 3–5x+ the tokens of a single session; one documented multi-agent loop ran 11 days and burned tens of thousands of dollars because it had observability but no *enforcement*. Per-loop budget caps with hard termination are non-negotiable for unattended runs.
- **The Forward Future Loop Library is one input, as instructed** — a single-agent prompt cookbook with no caps, budgets, or orchestration. Its lasting contribution is the 5-part loop contract; the rest of this report's safety and multi-agent guidance comes from Anthropic's harness research, Huntley's writing, and production agent-loop engineering.
