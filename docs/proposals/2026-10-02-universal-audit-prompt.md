# Prompt — Full universal-portability audit of Skill Madness

> Hand this to the auditing model (written for GPT-6.1 Sol). Run it from the repo root so it can
> read `AGENTS.md`. Facts in the "Starting evidence" section were measured on 2026-10-02 on
> branch `feat/cloudflare-pages-deploy-all-hosts`; the auditor is told to re-verify them.

---

## Role

You are a senior agent-systems engineer auditing **Skill Madness**, a library of ~79 agent skills
(`skills/**/SKILL.md`) plus an install/convert/sync toolchain that ships those skills to many AI
coding hosts. Your job has two parts. First, decide whether every skill makes sense and actually
works. Second, decide what it takes to make the library **model- and host-universal**. It must keep
working fully in Claude Code, and it must also run well on hosts that lack Claude Code's tooling.

This is the owner's most important project. Be thorough, be specific, and back every claim with
evidence.

## Why this audit exists

- The library was built inside Claude Code and leans on Claude-Code-only features: the Agent/subagent
  tool, Agent Teams (`TeamCreate`/`SendMessage`/`TaskCreate`, `TeammateIdle`/`TaskCompleted` hooks),
  the Workflow tool, `/loop`, `/goal`, `ScheduleWakeup`/`CronCreate`, Stop hooks, `AskUserQuestion`,
  `TodoWrite`, Artifacts, `.claude/settings.json`, and `CLAUDE_CODE_*` env flags.
- Running the skills under **DeepSeek** (via Freebuff) and **GPT Luna** broke some
  skills, agents, and workflows because they assumed that tooling.
- The owner has moved to a cheaper Claude plan and will rely more on other models and hosts. That
  makes **cost** a first-class requirement. Cheaper and non-Claude models have to be a supported
  path, not a degraded afterthought.

## Known field failure: case study (trace it to root cause)

On a static-site build, **GPT Luna** said it couldn't use `frontend-agent` because the skill was
too Claude-Code-specific. It then built the site with no frontend discipline:

1. It put **all CSS inline**.
2. When told to stop, it moved every inline style into a **unique hash-named class**
   (`.c-a91f`, …). That cleared the "no inline styles" complaint, but nothing was shared, so each
   rule was still one-off and duplicated.
3. It **hardcoded the header and footer into 40+ HTML files**. Fixing one copy left the other 39
   broken. Cleanup took more than a day.

Starting evidence (verify it):

- `skills/roles/frontend-agent/SKILL.md` declares `requires_claude_code: true`,
  `disable-model-invocation: true`, and "Orchestrator-dispatched only… Not user-invocable." So
  `convert.sh` never ships it to non-Claude hosts, and even where the file exists it presents
  itself as unusable without the orchestrator. Yet its *doctrine* (cascade-aware authoring,
  "classes in stylesheets, never inline `style=`", `references/mobile-responsive.md`, outside-in
  layout/shell first) is entirely host-neutral. **Portable rules are trapped behind a Claude-only
  dispatch gate.**
- `design-token-guard` and `class-extraction-guard` *are* exported to other hosts, but nothing
  invoked them, because the role that composes them never ran. Check whether either guard would
  have caught step 2: unique single-use classes with duplicated declaration blocks. As far as a
  grep shows, `class-extraction-guard` targets repeated utility-class runs, not duplicate
  declarations hidden behind unique names.
- No skill appears to detect **duplicated layout markup across files** (step 3). Nothing enforces
  "shared chrome lives in one partial/component/include."

What to deliver for this case: explain why each step happened. Was it a missing skill, a skill
that was gated off, a gate that was never invoked, or a gate that existed but could be gamed? Then
propose the fix at each layer: role skills that run **standalone** on any host (for example, a
"solo mode" section next to the orchestrator-dispatched mode), guards that run automatically
outside the orchestrator, a duplicate-declaration check, and a shared-layout/DRY-markup gate.
After that, **sweep the whole library for the same failure shape**: host-neutral doctrine locked
inside a Claude-only or orchestrator-only skill, and gates that a model can satisfy literally
while defeating their purpose. Report every other instance you find.

## Hard constraints

1. **Run read-only until the report is approved.** Do not edit, rename, move, or delete any
   existing file. Write only your audit outputs, and only to the location given under
   Deliverables.
2. **Claude Code must not regress.** Every recommendation has to preserve current Claude Code
   behavior. Where a host-neutral rewrite would weaken Claude Code, propose an adapter or a
   capability branch instead of flattening it.
3. **Verify, don't guess.** Every finding cites `path:line` or command output that you produced in
   this session. If you can't verify something, label it `UNVERIFIED`. Never state counts, routes,
   or file contents from memory.
4. **Be honest about your own tooling.** You are a non-Claude host, which makes you a live test
   subject. Whenever a skill or `AGENTS.md` tells you to use a tool you don't have, log it in the
   *Host-friction log* deliverable: the exact instruction, what you lacked, and what you did instead.
   This log is primary evidence, so don't smooth the problems over.
5. Respect repo conventions: `AGENTS.md` (markdownlint, `.workspaces/`, a single root `.env`) and
   the PSFS frontmatter spec (`spec/PSFS.md`, `spec/frontmatter.schema.json`).

## Orientation: read these first, in order

1. `START-HERE.md`, `AGENTS.md`, `CLAUDE.md`, `README.md`
2. `spec/PSFS.md` and `spec/frontmatter.schema.json` (the portable frontmatter standard)
3. `contracts/installer/*`, especially `per-tool-output-spec.md`, `install-locations.md`, and `skill-source-format.md`
4. `scripts/convert.sh`, `scripts/install*.sh`, `scripts/lint-skills.sh`, `scripts/catalog.sh`, `manifests/profiles.json`
5. `skills/workflows/sync-skills/SKILL.md` (symlinks raw skills into Claude, Cursor, Codex, Gemini, `~/.agents`, Devin, and Hermes)
6. `skills/meta/model-adaptation/` (SKILL.md and all `references/`). This is the current cross-model doctrine.
7. `skills/orchestrator/` and `skills/loops/loop-controller/`, the two most Claude-coupled foundations
8. `docs/REMAINING-WORK.md`, `docs/COMPLETED-WORK.md`, `docs/FUTURE.md`, `PLAN.md` (the living plan; don't re-propose work that is already closed)
9. `hooks/hooks.manifest.json` and `integrations/claude-code/hooks.json`

## Starting evidence (measured 2026-10-02; re-verify each item before you rely on it)

- **Half the library is gated off non-Claude hosts.** 41 of ~80 `SKILL.md` files declare
  `requires_claude_code: true`, and `scripts/convert.sh` (~line 711–726) skips those for every
  non-Claude host. The gated set covers the **orchestrator, all 10 roles, all 13 loops,**
  `contract-auditor`, `context-manager`, `repo-deep-dive`, `render-sanity`, and others. So the
  multi-agent core never reaches DeepSeek, GPT, or Gemini hosts through the converter.
- **The two delivery paths disagree.** `convert.sh` generates host-specific output into
  `integrations/<tool>/` and filters Claude-only skills. `sync-skills` symlinks the **raw,
  unconverted** Claude-flavored SKILL.md into Codex, Gemini, Devin, Hermes, and `~/.agents`
  (`~/.codex/skills` holds 97 entries). Work out which path each host actually uses and whether
  the two paths contradict each other.
- **Generated integrations look stale.** `integrations/{kimi,antigravity,openclaw,gemini-cli,cursor}`
  each hold 37 skills. They include archived or nonexistent skills (`git-branch-cleanup`,
  `git-clean-worktrees`, `deep-explainer`) and are missing recent ones (`cloudflare-pages-deploy`,
  `payload-cms`, `yagni-gate`, `use-pxpipe`). `integrations/windsurf/` is empty, and Codex has no
  converter target.
- **Counts drift.** `CLAUDE.md` says 77 skills, `START-HERE.md` says 77 in one place and narrates
  71–73 elsewhere, and the filesystem has ~79 non-archive SKILL.md files.
- **The cross-model doctrine covers two vendors.** `model-adaptation` covers Anthropic and DeepSeek.
  It has no OpenAI/GPT, Gemini, Qwen, or Kimi adaptation reference.
- **Plan gating is Claude-specific.** `min_plan: starter` or `pro` is a Claude subscription concept
  and has no meaning on other hosts.
- The highest density of Claude-only tool references (by grep count) is in `orchestrator-task-loop`,
  `orchestrator`, `loop-controller`, `babysit`, `artifact-publish`, `codebase-exploration-loop`,
  `self-healing-loop`, `contract-conformance-loop`, and `settings-consolidator`.

## Scope: seven workstreams

### W1. Skill-by-skill correctness and value

For **every** non-archive skill, fill in one row of the skill matrix (see Deliverables):

- Does it make sense? Is its purpose clear and distinct, or does it overlap with another skill? Name the overlaps.
- Does it work? Do the referenced files and scripts exist, do the cross-references resolve, can its steps actually be carried out, and are its gates real or rubber stamps?
- Does it trigger correctly? Look for a description that is too broad or too narrow, and for collisions with sibling skills.
- Is its size right for progressive disclosure (frontmatter, then body, then `references/`)?
- What does it depend on? List each dependency on a host capability (see W2).
- Verdict: **keep / fix / merge / split / archive**, with a reason.

### W2. Host-capability abstraction (the core of the universality work)

Inventory every host-specific mechanism the skills use, then design a **capability vocabulary**
that skills can declare in place of tool names. A starting set:

`read_files · write_files · run_shell · web_fetch · spawn_subagent · parallel_subagents ·
team_messaging · shared_task_list · schedule_recurring · stop_hook / completion_gate ·
ask_user_structured · persistent_memory · browser_automation (MCP) · artifact_publish ·
lifecycle_hooks`

For each capability, specify:

- The native mechanism on each host: Claude Code, Codex CLI, Gemini CLI, Cursor, OpenCode, Aider, Hermes, Devin, and a bare API loop such as Freebuff/DeepSeek or GPT through a generic harness.
- A **fallback ladder** for when it's missing. For example, `parallel_subagents` → sequential role passes in fresh context. `schedule_recurring` → cron, a CI schedule, or a bash Ralph loop. `ask_user_structured` → a numbered plain-text question. `stop_hook` → an explicit self-check checklist plus an external verifier script.
- Whether the fallback is *equivalent*, *degraded but safe*, or *unsafe* (the skill must refuse to run).

Then propose how skills should express this: a PSFS frontmatter extension (for example
`requires_capabilities: [...]` and `degrades_to: ...`) that replaces the binary
`requires_claude_code` and `min_plan`. Add a body convention, such as a "Host adapters" section or
a `references/hosts/<host>.md` per heavy skill, so one canonical skill body serves every host.
Spell out how `convert.sh`, `sync-skills`, PSFS, and `lint-skills.sh` would change. Prefer one
source of truth with generated adapters over forked copies.

### W3. The multi-agent core on non-Claude hosts

Go deep on `orchestrator`, `loop-controller`, `orchestrator-task-loop`, the 13 loops, and the 10
roles. For each, write down:

- what it's for, independent of the host;
- which parts are host-neutral doctrine (contracts-first, exclusive file ownership, QE gate, circuit breaker, fresh-context evaluator) and which parts are Claude plumbing;
- a concrete degraded execution plan for a single-agent host with no subagents, hooks, or scheduler. The orchestrator already claims a "Agent Teams → subagents → sequential" degradation path, so test whether the sequential path is actually specified well enough for another model to follow.
- which guardrails get *weaker* when subagents are unavailable (above all, "the builder can't grade itself") and how to restore them, for example a second model or session as the evaluator, or a script-based gate.

### W4. Model-level portability (separate from host tooling)

Some failures come from the model, not the tool: instruction-following style, verbosity,
refusal triggers, context-window size, tool-call formats, and thinking modes. Do the following:

- Audit the prose conventions that may be tuned to Claude, such as XML-tag usage, "pushy" descriptions, all-caps emphasis, and reliance on the 1M context window.
- Draft the missing `model-adaptation` references for **OpenAI/GPT** and **Gemini**, plus a general "unknown model" baseline, matched to the existing `deepseek-adaptation.md` format. Mark every vendor-specific fact `UNVERIFIED` unless you checked it against live vendor docs during this session.
- Extend the model and effort tiering policy (`references/model-effort-tiering.md`) into a cost-aware ladder across vendors that fits a low budget, including free and cheap tiers (see `use-freellmapi`).

### W5. Engineering-pattern review: proven approaches the library should adopt or fix

Assess the library against established agent-engineering patterns, and cite a source for each:

- **Workflow primitives** from Anthropic's "Building effective agents": prompt chaining, routing, parallelization, orchestrator-workers, and evaluator-optimizer. Does each skill pick the simplest pattern that works?
- **Graph and state-machine orchestration** (LangGraph-style explicit states, transitions, checkpoints, and resumability). Should orchestrator phases or loop contracts be expressed as an explicit, machine-checkable state graph?
- **Loop engineering**: Ralph loops, Reflexion, bounded retries, circuit breakers, verifier-gated termination, and anti-reward-hacking measures for coverage, test, and perf loops.
- **Context engineering**: progressive disclosure, just-in-time retrieval, compaction and handoff files, sub-agent context isolation, and memory files.
- **Spec- and eval-driven development**: does each skill have a measurable success check? Propose a lightweight **cross-model eval harness** that runs a small task suite per skill on N models and hosts, so that "universal" stays a tested claim and not an assertion.
- **Open standards**: the `AGENTS.md` convention, the Agent Skills / SKILL.md format, and MCP as the portable tool layer, including whether MCP servers could replace Claude-only built-ins.

For each pattern, say where the library already does it well (with file references), where it
falls short, and what concrete change to make. Don't recommend a pattern just because it's
popular. Say why it pays off *here*.

### W6. Gap analysis: missing skills

Propose new skills that would fill real gaps, ranked by value to a solo developer on a budget who
uses several models. Candidates to evaluate (accept or reject each with a reason, and add your
own):

- `host-adapter` / `capability-detect`: probes the current host at session start and selects the fallback ladder
- `cross-model-eval`: the eval harness from W5
- `model-router`: picks the cheapest model and host that meets a task's capability and quality needs
- `session-handoff`: portable state handoff between hosts and models mid-task
- `sequential-orchestrator`: the single-agent execution of the orchestrator, if W3 shows it needs its own skill
- `budget-guard`: token and cost ceilings per run, across vendors
- `shared-layout-guard` (or an extension of an existing guard): detects header, footer, nav, and
  other chrome duplicated across N files and requires a single partial, include, or component
- a duplicate-declaration check: flags identical CSS declaration blocks behind different
  (including hashed) class names, which closes the loophole from the case study
- **gate-gaming resistance** as a cross-cutting requirement: for every guard, name the cheapest
  way a model could satisfy it literally while defeating its intent, and say how the guard closes
  that path

For each one, give its purpose, its triggers, how it overlaps with existing skills, and a draft
frontmatter block that conforms to PSFS.

### W7. Toolchain and repo hygiene

Check `convert.sh`, `install*.sh`, `sync-skills`, the catalog, and the lints:

- Generation freshness: do the generated outputs match the source, and does CI catch drift?
- Missing converter targets (Codex, Windsurf) and any dead targets.
- Doc and count drift across `CLAUDE.md`, `START-HERE.md`, `README.md`, and the catalog.
- Whether tests run (`tests/run-all.sh`). Report the actual pass/fail output.
- Leftover `*-workspace/` directories inside `skills/`, which `AGENTS.md` says belong in `.workspaces/`.

## Method

1. Orient (reading list above), then build the skill inventory from the filesystem, not from the docs.
2. Run the existing gates (`scripts/lint-skills.sh`, `scripts/catalog.sh --check`, `tests/run-all.sh`) and record their real output.
3. Fill in the skill matrix (W1) and the capability inventory (W2) using grep plus reading the relevant sections.
4. Go deep on W3 and W4, then synthesize W5–W7.
5. Before writing recommendations, take a **default-refute pass** over your own top 15 findings. Try to disprove each one against the code, and drop or downgrade any that don't hold up.

## Severity rubric

- **P0**: broken on Claude Code today, or silently unsafe on another host (for example, a loop with no working termination gate).
- **P1**: blocks a non-Claude host from using a core capability (orchestrator, roles, loops).
- **P2**: degraded but workable; doc or count drift that misleads; triggering problems.
- **P3**: polish and speculative improvements.

## Deliverables

Write everything under `docs/reviews/2026-10-universal-audit/`. That's the only place you may write.

1. `00-executive-summary.md`: the 10 most important findings, a universality scorecard (per host and per skill category: works / degraded / broken), and the recommended order of work.
2. `01-skill-matrix.md`: one row per skill with category, purpose, verdict, capability deps, host status, issues (`path:line`), and severity.
3. `02-capability-model.md`: the capability vocabulary, per-host mapping table, fallback ladders, and the proposed PSFS extension and body convention, with before/after examples for `orchestrator` and one loop.
4. `03-multi-agent-core.md`: the W3 analysis and degraded execution plans.
5. `04-model-adaptation-drafts/`: the draft GPT, Gemini, and unknown-model references, plus the cross-vendor tiering ladder.
6. `05-patterns.md`: the W5 assessment with sources.
7. `06-new-skills.md`: the W6 proposals with PSFS frontmatter.
8. `07-toolchain.md`: the W7 findings, including the real command outputs.
9. `08-host-friction-log.md`: every point during this audit where your own host lacked an instruction's tooling.
10. `09-ledger-intake.md`: every actionable finding as a candidate ledger row (ID prefix `UA`, plus priority, one-line problem, fix, evidence, and size S/M/L), formatted so the repo's `plan-intake` skill can consume it directly.

Stop once the report is written. Don't implement fixes. The owner reviews the report and runs
intake into `docs/REMAINING-WORK.md` before any changes are made.

## Out of scope

- Rewriting skills during this pass. Drafts belong only in the deliverables folder.
- Re-litigating items already closed in `docs/COMPLETED-WORK.md`, unless you find they regressed (show the evidence).
- Generic advice that isn't tied to a specific file in this repo.
