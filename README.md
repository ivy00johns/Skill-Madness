<div align="center">

# 🧰 Skill Madness

### *All the skills, all the agents, all the chaos — coordinated.*

**Most AI coding setups give you one agent, one context window, one shot. Skill Madness gives you a coordinated fleet — plus the autonomous loops to keep it working until the job is provably done.**

A multi-agent orchestration toolkit for Claude Code: **71 skills, seven categories** — turn a one-line ask into a contract-first parallel build, run **autonomous loops** until your tests are actually green, and author everything once in a portable `SKILL.md` format whose converters feed **eleven AI coding tools** (Claude Code runs the full library; the ten other hosts get its portable subset).

<p align="center">
  <a href="https://github.com/ivy00johns/Skill-Madness/actions/workflows/lint-skills.yml"><img src="https://github.com/ivy00johns/Skill-Madness/actions/workflows/lint-skills.yml/badge.svg" alt="Skill Lint" /></a>
  <a href="LICENSE"><img src="https://img.shields.io/badge/license-MIT-blue.svg" alt="License: MIT" /></a>
  <img src="https://img.shields.io/badge/skills-71-success.svg" alt="71 skills" />
  <img src="https://img.shields.io/badge/role%20agents-10-blueviolet.svg" alt="10 role agents" />
  <img src="https://img.shields.io/badge/autonomous%20loops-13-9cf.svg" alt="13 autonomous loops" />
  <img src="https://img.shields.io/badge/orchestrator-14%20phases-success.svg" alt="14-phase orchestrator" />
  <img src="https://img.shields.io/badge/hosts-11-orange.svg" alt="11 hosts" />
  <img src="https://img.shields.io/badge/format-SKILL.md-3178c6.svg" alt="SKILL.md format" />
  <img src="https://img.shields.io/badge/PRs-welcome-ff69b4.svg" alt="PRs welcome" />
</p>

<p align="center">
  <a href="#-quick-start">Quick Start</a> ·
  <a href="#-why-this-exists">Why this exists</a> ·
  <a href="#-autonomous-loops">Loops</a> ·
  <a href="#-architecture">Architecture</a> ·
  <a href="#-skill-catalog">Skill catalog</a> ·
  <a href="#-also-works-on-ten-other-hosts">Other hosts</a> ·
  <a href="#-roadmap">Roadmap</a>
</p>

</div>

---

<table>
<tr>
<td width="33%" valign="top">

**🪄 Orchestrate**

Turn a one-line ask into a coordinated multi-agent build. The `orchestrator` decomposes the work into a 14-phase plan, authors machine-readable contracts **before** any code, dispatches role agents in parallel with exclusive file ownership, and blocks the merge on a structured QA report.

</td>
<td width="33%" valign="top">

**🔁 Loop**

Point Claude at a goal and walk away. **13 autonomous loops** drive tests to green, coverage to target, a contract to conformance, or a PR to merged — each on a guardrail stack so it converges instead of thrashing or burning your budget.

</td>
<td width="33%" valign="top">

**🌐 Port**

Author once in `SKILL.md`; install into **eleven** AI coding tools — Claude Code gets the full library, and the portable subset converts for Copilot, Cursor, Aider, Windsurf, OpenCode, Qwen, OpenClaw, Gemini CLI, Antigravity, and Kimi.

</td>
</tr>
</table>

> 🚪 **New here, or not sure which skill to reach for?** Type **`/madness`** in Claude Code and just say what you want. It reads your intent, picks the right starting skill out of all 71, confirms before anything expensive, and launches it — so you never have to memorize the catalog. One front door for the whole toolkit.

<sub><b>Maintainers / agents:</b> see <a href="START-HERE.md"><code>START-HERE.md</code></a> for current status and which docs are canonical.</sub>

---

## ✨ Why this exists

Every AI coding tool ships the same traps. **One agent, one context window, one set of files** — fine for a small project, brittle for anything bigger than a single context can hold. They **stop at the first draft** — when the tests are still red, *you're* the one re-prompting "still failing, try again" until it finally goes green. And **every tool reinvents the same wheel** — Cursor wants `.mdc`, Aider wants `CONVENTIONS.md`, Windsurf wants `.windsurfrules`, Claude Code wants `SKILL.md` — so any prompt library you build gets stranded on whichever host you wrote it for.

**Skill Madness attacks all three.** The `orchestrator` decomposes a complex build into a 14-phase plan, makes integration surfaces machine-readable *before* anyone writes code, dispatches role agents in parallel with strict file ownership, and refuses to ship until a separate QE agent signs off via a structured report. **Autonomous loops** then keep the work going after that first pass — driving tests to green, coverage to a target, or a contract to conformance, with guardrails that make them converge instead of thrash. And the skill library underneath authors once in the canonical `SKILL.md` format — the same skills install into eleven different AI coding tools without copy-paste drift.

- 👑 **The orchestrator is the entry point** — a single 14-phase playbook covering team sizing, runtime detection, contract authoring, parallel dispatch, integration validation, QA gate, and handoff. It's the skill that turns a one-line ask into a coordinated multi-agent build.
- 📜 **Contract-first** — `contract-author` writes OpenAPI / AsyncAPI / Pydantic / TypeScript / JSON Schema *before* a line of implementation. `contract-auditor` verifies every shipped module against the spec. Agents can't drift; the contract is the truth.
- 🤖 **Ten role agents, exclusive ownership** — backend, frontend, infrastructure, QE, security, docs, observability, db-migration, performance, code-review. Each declares `owns.directories` / `owns.files` in its frontmatter. No two agents touch the same path. Conflicts get resolved before spawn, not after.
- 🛡️ **QA gate that blocks** — `qe-agent` emits a `qa-report.json` with critical / high / medium / low findings plus contract-conformance and security scores. The orchestrator gates the merge on the report. Agents can't self-declare "done."
- 🔁 **Autonomous loops that converge** — 13 loop skills keep Claude working until something is *provably* true: `fix-until-green` won't stop until tests + lint + typecheck pass (and can't cheat the gate), `coverage-loop` grows the suite to a target without gaming it, `contract-conformance-loop` builds until a fresh-context evaluator agrees the spec is met, and `babysit` / `self-healing-loop` / `nightly-docs-and-changelog` run on a schedule. Every one is a configuration of `loop-controller`'s guardrail stack — iteration cap, token budget, no-progress breaker, stop condition — so they finish instead of thrashing. [See the loops →](#-autonomous-loops)
- 🪄 **One front door** — `madness` is the router: type `/madness`, describe the task, and it picks the right starting skill out of all 71 and launches it. The cure for "which skill was that again?" across a 71-skill library.
- 🪜 **Progressive disclosure** — frontmatter (~100 tokens) always loaded, body loaded on trigger, references loaded on demand. A 71-skill library stays cheap to host.
- 🔁 **Two-runtime degradation** — Agent Teams (parallel tmux) → subagents (Task tool) → sequential. The orchestrator picks the highest mode the host supports; role skills work standalone in any of them.
- 🧰 **71 skills, seven categories, all CI-linted** — the `orchestrator`, 10 role agents, 2 contract skills, 7 meta-skills (including `madness`, the front-door router, and `model-adaptation`), 4 git-workflow skills, 34 cross-cutting workflow skills (plan-builder, repo-deep-dive, ui-brief, mermaid-charts, …), and 13 autonomous-loop skills. Frontmatter, body length, and cross-skill ownership are all gated on every push.
- 🌐 **Portable format, honest subset** — `SKILL.md` is the canonical source; converters emit Claude Code, Copilot, Cursor, Aider, Windsurf, OpenCode, Qwen, OpenClaw, Gemini CLI, Antigravity, and Kimi formats. The multi-agent core — the orchestrator, the role agents, and the autonomous loops, whose contracts *are* Claude Code's runtime primitives — stays Claude-Code-only by design; the standalone conventions and workflows (git, planning, docs, review, debugging, contract authoring, and more) convert to all ten other hosts. See [Also works on ten other hosts](#-also-works-on-ten-other-hosts).

> **Status — read before you pitch this to anyone:**
> - **The orchestrator + 71-skill library is the mature part.** All bodies under 500 lines, zero ownership conflicts, zero broken cross-references, full Ubuntu + macOS lint matrix on every push.
> - **The 13 autonomous loops are the newest layer.** All built on one `loop-controller` guardrail harness and CI-linted. The build/verify loops (`fix-until-green`, `coverage-loop`, `contract-conformance-loop`) are the most exercised; the scheduled ones (`self-healing-loop`, `dependency-health-loop`) are powerful but younger — keep a human in the loop on anything irreversible.
> - **Claude Code is the end-to-end-verified host.** Multi-agent dispatch with file-ownership exclusivity and the `qa-report.json` gate runs live on Claude Code today. The other ten hosts receive the library's portable subset and don't run the orchestrator's parallel dispatch.
> - **Lossy conversion is announced.** When a skill is converted to a non-Claude-Code host, orchestration-only fields (`allowed_tools`, `owns`, `composes_with`, `spawned_by`, `requires_agent_teams`) are stripped with a stderr line per skill. Skills marked `requires_claude_code: true` are skipped entirely for those targets. See `contracts/installer/per-tool-output-spec.md`.

---

## 🚀 Quick Start

### Prerequisites

| You need | Why |
|----------|-----|
| **bash 3.2+** + standard POSIX tools | The installer is pure shell, written bash-3.2-safe — stock macOS bash works, no upgrade needed (CI runs a macOS job to keep it that way) |
| **python3** | Frontmatter parsing in `lint-skills.sh` |
| **git** | Cloning the repo and (optionally) symlinking into your global skills dir |
| **Claude Code** (recommended) | Where the orchestrator + multi-agent QA gate actually run end-to-end |
| **(optional) any of ten other hosts** | Copilot, Cursor, Aider, Windsurf, OpenCode, Qwen, OpenClaw, Gemini CLI, Antigravity, Kimi — see [Also works on ten other hosts](#-also-works-on-ten-other-hosts) |

### Install for Claude Code

Two install paths. Pick one.

#### Option A — Claude Code plugin manager (recommended for users)

From inside Claude Code:

```text
/plugin marketplace add ivy00johns/Skill-Madness
/plugin install skill-madness@skill-madness
```

That installs all 71 skills into Claude Code's plugin storage. No clone, no symlink, no edits-to-the-repo workflow. Use this if you just want the skills.

To update later: `/plugin update skill-madness`.

#### Option B — Clone + `/sync-skills` (recommended for contributors)

Clone, then run `/sync-skills` from inside Claude Code. It creates flattened symlinks at `~/.claude/skills/<skill-name>` so edits in the repo are live in every session — no rebuild step.

```bash
git clone https://github.com/ivy00johns/Skill-Madness.git
cd Skill-Madness

# Inside Claude Code:
/sync-skills
```

If you'd rather copy than symlink, the underlying script accepts `--copy` instead of `--link`. See `skills/workflows/sync-skills/SKILL.md`.

Use this if you want to author skills, iterate on them, or contribute upstream.

### Install for any of the other ten hosts

Two scripts. The first translates the canonical `SKILL.md` files into eleven host-native shapes; the second installs the converted artifacts into whichever hosts it detects on your machine.

```bash
./scripts/convert.sh   # skills/**/SKILL.md  →  integrations/<host>/...
./scripts/install.sh   # integrations/<host> →  ~/.<host>/, .cursor/rules/, etc.
```

`install.sh` is interactive when run in a TTY and auto-detects from environment variables in CI. See [Also works on ten other hosts](#-also-works-on-ten-other-hosts) for the per-host format matrix and what gets stripped on conversion, and `scripts/README.md` for flag-level docs.

### Use it

Tell Claude Code to build something with multiple agents:

```text
"Build a chat app with React frontend and FastAPI backend — use an agent team."
```

The `orchestrator` skill triggers automatically: it sizes the team, generates contracts, spawns parallel agents in isolated worktrees, gates the build on `qa-report.json`, and returns when QE signs off.

Or set it loose on a goal and let a loop converge on its own:

```text
"Fix the failing tests and don't stop until everything's green."  → fix-until-green
"Get test coverage up to 85% without gaming the metric."          → coverage-loop
"Keep this PR rebased and green while review comes in."           → /loop 5m /babysit
"Map this whole codebase and write me the architecture."         → codebase-exploration-loop
```

Or invoke any skill standalone:

```text
"Review this code for security vulnerabilities."   → security-agent
"Set up Docker and CI/CD for this project."        → infrastructure-agent
"Write k6 load tests for the /search endpoint."    → performance-agent
"Profile this codebase and write me a CLAUDE.md."  → project-profiler
"Generate a UI brief for a refresh of /settings."  → ui-brief
```

Not sure which skill fits? Don't guess — let the front door route you:

```text
/madness build a CLI that syncs two folders, with tests
```

`madness` reads the intent, picks the right starting skill, confirms before anything expensive (a swarm, an overnight loop, a full build), and hands off.

---

## 🧬 Architecture

The orchestrator sits above seven skill categories — every build pulls from this library, every category lints clean, and the library's portable subset converts to the ten non-Claude-Code hosts.

```mermaid
flowchart TB
    orch["👑 <b>orchestrator</b><br/><sub>14-phase build playbook · runtime detection<br/>team sizing · circuit breaker · handoff protocol</sub>"]:::entry

    subgraph contracts["📜 contracts/ — 2 skills"]
        direction TB
        ca[contract-author]
        cau[contract-auditor]
    end

    subgraph roles["🤖 roles/ — 10 agents · exclusive file ownership"]
        direction TB
        be[backend]
        fe[frontend]
        infra[infrastructure]
        qe["qe<br/><sub>(QA gate)</sub>"]:::gate
        sec[security]
        rdocs[docs]
        obs[observability]
        dbm[db-migration]
        perf[performance]
        cra[code-review]
    end

    subgraph meta["🧠 meta/ — 7 skills"]
        direction TB
        md["madness<br/><sub>(front door)</sub>"]:::entry
        sx[skill-explorer]
        sw[skill-writer]
        sr[skill-review]
        su[skill-update]
        mda[model-adaptation]
        sc[skill-catalog]
    end

    subgraph gitcat["🔁 git/ — 4 skills"]
        direction TB
        gcm[git-commit]
        gpr[git-pr]
        gpf[git-pr-feedback]
        gpmc[git-post-merge-cleanup]
    end

    subgraph workflows["⚙️ workflows/ — 34 skills"]
        direction TB
        pb[plan-builder]
        cm[context-manager]
        dc[dependency-coordinator]
        dch[deployment-checklist]
        pp[project-profiler]
        wr[wiki-research]
        rdd[repo-deep-dive]
        lw[llm-wiki]
        ub[ui-brief]
        cdb[claude-design-brief]
        mc[mermaid-charts]
        rs[render-sanity]
        dl[diagnose-loop]
        more["+ 21 more"]
    end

    subgraph loops["🔁 loops/ — 13 skills"]
        direction TB
        lc[loop-controller]
        fug[fix-until-green]
        otl[orchestrator-task-loop]
        ccl[contract-conformance-loop]
        bs[babysit]
        cov[coverage-loop]
        pfl[perf-loop]
        shl[self-healing-loop]
        mig[migration-loop]
        ndc[nightly-docs-and-changelog]
        dhl[dependency-health-loop]
        cel[codebase-exploration-loop]
        rcl[repo-cleanup-loop]
    end

    orch --> contracts
    orch --> roles
    orch --> meta
    orch --> gitcat
    orch --> workflows
    orch --> loops

    classDef entry fill:#7c3aed,stroke:#4c1d95,color:#fff,stroke-width:2px
    classDef gate fill:#dc2626,stroke:#7f1d1d,color:#fff,stroke-width:1.5px
```

### How a build flows

A one-line build request enters the orchestrator and exits as a shipped artifact only after the `qe-agent` writes a passing `qa-report.json`. Every other path blocks the merge.

```mermaid
flowchart TB
    user(["🧑 You"]) -->|"build X — use an agent team"| orch[👑 orchestrator]
    orch --> detect[/"detect runtime<br/><sub>Agent Teams · subagents · sequential</sub>"/]
    detect --> size[/"size team"/]
    size --> contracts["📜 <b>contract-author</b><br/><sub>OpenAPI · Pydantic · TypeScript<br/>written BEFORE any implementation</sub>"]:::contract

    contracts --> dispatch{{"⚡ parallel dispatch<br/><sub>exclusive file ownership · no overlapping writes</sub>"}}

    subgraph parallel["isolated worktrees"]
        direction LR
        be["🛠 backend<br/><sub>owns api/</sub>"]
        fe["🎨 frontend<br/><sub>owns web/</sub>"]
        infra["📦 infrastructure<br/><sub>owns infra/</sub>"]
        docs["📚 docs<br/><sub>owns docs/</sub>"]
    end

    dispatch --> be
    dispatch --> fe
    dispatch --> infra
    dispatch --> docs

    be --> validate
    fe --> validate
    infra --> validate
    docs --> validate

    validate["🔬 contract-auditor<br/>+ qe-agent + security-agent"]:::validate
    validate --> gate{"🚦 qa-report.json<br/>gate"}:::gate
    gate -- "CRITICAL findings" --> block[/"⛔ block merge"/]:::fail
    gate -- "all checks pass" --> ship[/"🚀 ship"/]:::pass

    classDef contract fill:#1e40af,stroke:#1e3a8a,color:#fff,stroke-width:2px
    classDef validate fill:#7c3aed,stroke:#5b21b6,color:#fff
    classDef gate fill:#f59e0b,stroke:#b45309,color:#fff,stroke-width:2px
    classDef fail fill:#dc2626,stroke:#7f1d1d,color:#fff
    classDef pass fill:#16a34a,stroke:#14532d,color:#fff
```

---

## 🔁 Autonomous loops

The newest part of Skill Madness — and the fastest way to feel why it exists. A loop points Claude at a goal with a **verifiable stop condition** and a **mandatory guardrail stack**, then lets it run until the goal is provably met. No more babysitting "still failing, try again."

Every loop is a configuration of **`loop-controller`**, the foundation harness that picks the right primitive for the job — `/goal`, `/loop`, a Stop-hook, a bash "Ralph" loop, or a dynamic workflow — and wires in the guardrails so the loop *converges* instead of thrashing or running up the bill.

**🟢 Build & verify — run until it's green:**

| Loop | What it drives to "done" | Kick it off with |
|------|--------------------------|------------------|
| `fix-until-green` | tests + lint + typecheck all passing — and it can't cheat the gate | *"fix until the tests are green"* |
| `contract-conformance-loop` | every authored-contract criterion holds, graded by a fresh-context evaluator | *"build until the contract is met"* |
| `coverage-loop` | a coverage target, without gaming the metric | *"get coverage to 85%"* |
| `perf-loop` | a metric under its budget, with no functional regression | *"optimize until p95 < 200ms"* |
| `migration-loop` | an enumerated target set migrated, suite green, no legacy pattern left | *"migrate every file off the old API"* |

**🗓️ Operate & maintain — run on a schedule:**

| Loop | What it keeps healthy | Kick it off with |
|------|-----------------------|------------------|
| `babysit` | a PR rebased + green, auto-addressing review comments (HITL on anything irreversible) | `/loop 5m /babysit` |
| `self-healing-loop` | logs/CI watched → root-caused → fixed → verified → PR (HITL before prod) | *"watch CI and self-heal"* |
| `nightly-docs-and-changelog` | docs + changelog that don't rot after a release | `/schedule` nightly |
| `dependency-health-loop` | dependencies audited + one gated bump per pass (HITL on majors) | `/schedule` weekly |
| `repo-cleanup-loop` | branches / PRs / worktrees tidy — recover valuable work *before* deleting | `/schedule` weekly |

**🔎 Understand & coordinate:**

| Loop | What it produces | Kick it off with |
|------|------------------|------------------|
| `codebase-exploration-loop` | a written architecture summary that answers every seed question | *"map this codebase for me"* |
| `orchestrator-task-loop` | the Agent Teams shared task board drained until every task passes its gate *(experimental)* | *"drain the task board"* |

> 🛡️ **Loops are gated by design.** Every loop inherits `loop-controller`'s guardrails: a hard iteration cap, a token budget, a no-progress circuit breaker, and a stop condition checked by a *separate* fresh-context evaluator so the worker can't grade its own homework. Anything irreversible — pushing to prod, force-deleting work — pauses for a human. Read the harness: [`skills/loops/loop-controller/SKILL.md`](skills/loops/loop-controller/SKILL.md).

---

## 🧰 Skill catalog

71 skills organized into seven categories. All bodies under 500 lines, all frontmatter validated, zero ownership conflicts, zero broken cross-references.

<details>
<summary><b>📚 Full skill table</b> (click to expand)</summary>

| # | Skill | Category | What it does |
|---|-------|----------|--------------|
| 1 | `orchestrator` | coordinator | 14-phase multi-agent build playbook (the entry point) |
| 2 | `backend-agent` | role | API servers, business logic, data layers |
| 3 | `frontend-agent` | role | UI, client-side state, presentation |
| 4 | `infrastructure-agent` | role | Docker, CI/CD, deployment configs |
| 5 | `qe-agent` | role | Contract conformance, integration testing, QA gate report |
| 6 | `security-agent` | role | OWASP audits, dependency + auth review |
| 7 | `docs-agent` | role | READMEs, API docs, changelogs |
| 8 | `observability-agent` | role | Logging, metrics, health checks, alerting |
| 9 | `db-migration-agent` | role | Schema migrations, seed data |
| 10 | `performance-agent` | role | Load testing (k6 default; Locust / JMeter / Artillery) |
| 11 | `code-review-agent` | role | Orchestrator-dispatched code review with scoring rubric |
| 12 | `contract-author` | contract | Generates API / data / event contracts before any build |
| 13 | `contract-auditor` | contract | Verifies implementations match contracts (static audit) |
| 14 | `madness` | meta | The front-door router — reads intent, launches the right starting skill |
| 15 | `skill-writer` | meta | Generates new SKILL.md files with proper frontmatter |
| 16 | `skill-explorer` | meta | Discover, recall, and route across the skill toolkit |
| 17 | `skill-review` | meta | Bulk audit or single-skill deep review with scoring |
| 18 | `skill-update` | meta | Apply a skill-review report — edit, lint, ship |
| 19 | `model-adaptation` | meta | Adapt prompts/skills/scaffolding across model generations (Fable 5 / Mythos 5) — prune, refusal-audit, long-run hygiene |
| 20 | `skill-catalog` | meta | Catalog-as-CI-invariant — counts derived from disk, gated on every push |
| 21 | `git-commit` | git | Conventional commits + branch naming |
| 22 | `git-pr` | git | PR title/body format and gh CLI workflow |
| 23 | `git-pr-feedback` | git | Triage and address PR review comments |
| 24 | `git-post-merge-cleanup` | git | Prune merged branches, dead remote refs, stale worktrees |
| 25 | `plan-builder` | workflow | Research / PRDs → orchestrator-ready build plans |
| 26 | `plan-intake` | workflow | Turn any report into tracked living-plan ledger entries |
| 27 | `living-plan` | workflow | Set up the living-plan convention (front door + strategic / tactical / frontier docs) |
| 28 | `context-manager` | workflow | Compaction strategy, handoffs, token budgets |
| 29 | `dependency-coordinator` | workflow | Cross-package dependency manifest before parallel dispatch |
| 30 | `deployment-checklist` | workflow | Pre-deploy verification gates |
| 31 | `project-profiler` | workflow | Codebase analysis → CLAUDE.md + profile.yaml |
| 32 | `wiki-research` | workflow | Wiki-first protocol — read 3 pages before crawling source |
| 33 | `setup-project-skills` | workflow | Bootstrap per-repo config that other Skill-Madness skills consume |
| 34 | `work-item-brief` | workflow | Durable, agent-ready ticket — no paths, just acceptance criteria |
| 35 | `maintain-context` | workflow | Keep CONTEXT.md glossary + ADR records up to date inline |
| 36 | `zoom-out` | workflow | Step back — which modules are touched, what am I missing |
| 37 | `grill-me` | workflow | Depth-first design interview — one question at a time |
| 38 | `find-unknowns` | workflow | Blindspot pass + comprehension quiz — surface unknown-unknowns before, verify understanding after |
| 39 | `diagnose-loop` | workflow | Build the fast feedback loop first, then debug |
| 40 | `architecture-rescue` | workflow | Find shallow modules + missing seams; deletion + two-adapter test |
| 41 | `caveman` | workflow | Ultra-compressed responses, ~75% token cut, full accuracy |
| 42 | `render-sanity` | workflow | "Tests pass but UI is broken" gate — click-through + stale-data scan |
| 43 | `design-token-guard` | workflow | Block inline styles / hardcoded CSS from bypassing the design-token system |
| 44 | `class-extraction-guard` | workflow | Catch utility-class soup — repeated inline class runs that should be extracted |
| 45 | `sync-skills` | workflow | Symlink/copy skills to `~/.claude/skills/` and Cursor |
| 46 | `settings-consolidator` | workflow | Merge Claude Code permissions across projects |
| 47 | `repo-deep-dive` | workflow | OSS repo → 12–14 doc technical reference series |
| 48 | `llm-wiki` | workflow | Bootstrap + maintain LLM-powered knowledge bases |
| 49 | `interactive-doc` | workflow | Paired Obsidian `.md` + self-contained `.html` companion |
| 50 | `ui-brief` | workflow | Opinionated UI design briefs (greenfield + rebuild) |
| 51 | `claude-design-brief` | workflow | Paste-ready prompts for Claude Design mockup canvas |
| 52 | `mermaid-charts` | workflow | Expert-quality diagrams (15–30+ node systems) |
| 53 | `nano-banana` | workflow | Google Gemini image generation + batch ops |
| 54 | `artifact-publish` | workflow | Publish a visual/interactive deliverable as a shareable, hosted claude.ai Artifact page |
| 55 | `playwright` | workflow | Browser-based E2E + screenshots with visible Chrome |
| 56 | `website-walkthrough-video` | workflow | Smooth scrolling walkthrough mp4 of a whole site (desktop + mobile) |
| 57 | `railway-deploy` | workflow | Deploy to Railway (Dockerfile, multi-service, GraphQL API) |
| 58 | `use-freellmapi` | workflow | Wire a project to FreeLLMAPI — a local free-model OpenAI-compatible proxy |
| 59 | `loop-controller` | loop | Foundation harness: 5-part contract + guardrail stack every loop composes on |
| 60 | `fix-until-green` | loop | Drive tests+lint+typecheck green without cheating the gate |
| 61 | `contract-conformance-loop` | loop | Build-until-spec: implement until contract criteria hold, fresh-context evaluator |
| 62 | `coverage-loop` | loop | Grow the test suite to a coverage target without gaming the metric |
| 63 | `perf-loop` | loop | Profile → optimize → re-benchmark a metric under budget, no regression |
| 64 | `migration-loop` | loop | Migrate an enumerated target set until done + suite green + no legacy pattern |
| 65 | `babysit` | loop | Scheduled review-and-revise: keep a PR rebased + green via `/loop` |
| 66 | `self-healing-loop` | loop | Watch logs/CI → root-cause → fix → verify → PR on a poll cadence |
| 67 | `nightly-docs-and-changelog` | loop | Nightly `/schedule` sweep keeping docs + changelog from rotting |
| 68 | `dependency-health-loop` | loop | Scheduled audit + gated update + green gate; HITL on majors |
| 69 | `codebase-exploration-loop` | loop | Fan-out read-only mappers until seed questions are answered |
| 70 | `orchestrator-task-loop` | loop | Outer loop draining the Agent Teams shared task board (experimental) |
| 71 | `repo-cleanup-loop` | loop | Weekly evidence-gated branch/PR/worktree hygiene, recover-before-delete |

</details>

---

## 📂 Project structure

```
.
├── README.md                         # this file
├── CLAUDE.md                         # project guidance for Claude Code
├── AGENTS.md                         # shared instructions for AI agents
│
├── skills/                           # the canonical skill library (71)
│   ├── orchestrator/                 # 1 — entry point
│   ├── roles/                        # 10 — implementation agents
│   ├── contracts/                    # 2 — contract-author / contract-auditor
│   ├── meta/                         # 7 — skills that manage skills (incl. madness, model-adaptation)
│   ├── git/                          # 4 — git workflow conventions
│   ├── workflows/                    # 34 — cross-cutting process skills
│   └── loops/                        # 13 — autonomous-loop skills
│
├── scripts/                          # multi-tool installer
│   ├── convert.sh                    # SKILL.md → 11 host-native formats
│   ├── install.sh                    # integrations/ → host install dirs
│   ├── lint-skills.sh                # frontmatter + cross-skill validation
│   ├── lib/                          # frontmatter / platform / slug / term helpers
│   └── README.md                     # per-host destinations and flags
│
├── hooks/                            # lifecycle-hook layer (Claude Code only, 6 hooks)
│   ├── hooks.manifest.json           # registry: hook id, event, profiles, blocking
│   ├── run-with-flags.sh             # single entrypoint; dispatches scripts/<hook-id>.sh
│   ├── scripts/                      # per-hook implementations (qa-gate, catalog-sync, …)
│   └── lib/                          # shared hook helpers
│
├── integrations/                     # generated outputs (one dir per host)
│   ├── claude-code/  copilot/  cursor/  aider/  windsurf/
│   ├── opencode/  qwen/  openclaw/  gemini-cli/  antigravity/  kimi/
│
├── contracts/installer/              # installer specs
│   ├── skill-source-format.md        # canonical SKILL.md schema
│   ├── per-tool-output-spec.md       # per-host fidelity matrix
│   ├── install-locations.md          # where each host expects skills
│   └── lint-rules.md                 # what the linter enforces
│
├── spec/                             # the portable frontmatter standard
│   ├── PSFS.md                       # Portable Skill Frontmatter Spec v1.1.0
│   └── frontmatter.schema.json       # JSON Schema 2020-12 reference validator
│
├── tests/installer/                  # bats-core tests for convert/install/lint
└── .github/workflows/lint-skills.yml # Ubuntu + macOS CI matrix
```

---

## 🎁 Also works on ten other hosts

The orchestrator and the multi-agent QA gate are Claude-Code-native — that's the headline feature, and it stays home: skills whose contract *is* Claude Code's runtime (the orchestrator, the 10 role agents, all 13 loops, and the workflows bound to the Artifact tool, subagent dispatch, or `~/.claude` config) are marked `requires_claude_code: true` and are never converted. The canonical `SKILL.md` *format* is platform-agnostic, though, so the rest of the library — **34 of the 71 skills** today: the git conventions and the planning, docs, review, debugging, and contract-authoring workflows — converts to ten other AI coding tools. Broadening that subset is tracked as F1 in [`docs/FUTURE.md`](docs/FUTURE.md).

The single-source model is deliberate, and there's a concrete counter-example for why: microsoft/SkillOpt shipped the opposite design — five bespoke per-host integrations (claude-code, codex, copilot, devin, openclaw) — and was already drifting within months of release: backend-enum mismatches between plugins, and an openclaw adapter broken-by-design against its own engine. One canonical `SKILL.md` plus converters means a fix lands once instead of five times.

Two scripts handle it:

```bash
./scripts/convert.sh   # skills/**/SKILL.md  →  integrations/<host>/...
./scripts/install.sh   # integrations/<host> →  ~/.<host>/, .cursor/rules/, etc.
```

`install.sh` is interactive when run in a TTY and auto-detects from environment variables in CI. See `scripts/README.md` for per-host destinations, scopes, and flags.

| Host | Scope | Output format | Source strategy |
|------|-------|---------------|-----------------|
| 🟣 **Claude Code** | user | `SKILL.md` (passthrough) | direct symlink |
| 🐙 **GitHub Copilot** | user | `.md` (passthrough) | direct copy |
| 🌀 **Cursor** | project | `.mdc` with metadata | generated |
| 🤝 **Aider** | project | single `CONVENTIONS.md` | accumulated |
| 🪁 **Windsurf** | project | single `.windsurfrules` | accumulated |
| 🧱 **OpenCode** | project | `.md` with `mode` field | generated |
| 🧮 **Qwen Code** | project | `.md` with optional `tools` | generated |
| 🦾 **OpenClaw** | user | 3-file split (SOUL / AGENTS / IDENTITY) | generated |
| 💎 **Gemini CLI** | user | extension manifest + `SKILL.md` | generated |
| 🛰️  **Antigravity** | user | community-skill `SKILL.md` | generated |
| 🌙 **Kimi Code** | user | YAML config + `system.md` | generated |

**Lossy by design.** Claude-Code-specific orchestration fields (`allowed-tools`, `owns`, `composes_with`, `spawned_by`, `requires_agent_teams`) are stripped on conversion to the other ten hosts — those hosts don't run multi-agent dispatch with file-ownership exclusivity, so the metadata would be noise. You'll see one `[host] stripped allowed-tools/owns from <slug>` line per affected skill on stderr. Skills marked `requires_claude_code: true` are skipped entirely for non-Claude-Code targets.

> **Credit where it's due.** The eleven-host installer pattern, the `detect_<tool>()` probes, the interactive selection UI, the slug pipeline, and the OpenClaw soul/agents split are all adapted from [`msitarzewski/agency-agents`](https://github.com/msitarzewski/agency-agents) (MIT). Full attribution and the list of pieces that came across vs. were rewritten lives in [`ACKNOWLEDGMENTS.md`](ACKNOWLEDGMENTS.md). The orchestrator, role agents, contracts, QA gate, and the rest of the skill library are independent.

---

## 💻 CLI / scripts reference

<details>
<summary><b>📖 Full script reference</b> (click to expand)</summary>

### `scripts/convert.sh`

Reads `skills/**/SKILL.md` and writes host-specific artifacts to `integrations/<host>/`. Idempotent. Lossy-by-design — orchestration metadata is stripped per the per-tool spec, with stderr warnings on every strip.

```bash
./scripts/convert.sh                     # all hosts
./scripts/convert.sh --tool cursor       # one host
./scripts/convert.sh --parallel --jobs 8 # all hosts, concurrently
```

### `scripts/install.sh`

Reads `integrations/<host>/` and copies into the host's expected install location. Detects which hosts are present on the machine (presence of `~/.cursor`, `~/.config/aider`, etc.). Interactive when run in a TTY; auto-confirms in CI.

```bash
./scripts/install.sh                     # interactive TUI (TTY) or detected hosts (non-TTY)
./scripts/install.sh --tool claude-code  # one host
./scripts/install.sh --dry-run           # show what would happen
```

### `scripts/lint-skills.sh`

Runs on every push to every branch (Ubuntu + macOS) via `.github/workflows/lint-skills.yml`. Validates:

- Frontmatter schema (required fields, valid `version` semver, kebab-case `name`)
- Body length under 500 lines
- Cross-skill invariants (no ownership conflicts in `owns.directories` / `owns.files`)
- Reference link integrity within each skill's `references/`

Outputs JUnit XML for GitHub Actions test results.

```bash
./scripts/lint-skills.sh                          # full lint
./scripts/lint-skills.sh skills/orchestrator/     # one skill (positional path, not a flag)
./scripts/lint-skills.sh --standard               # report the frontmatter standard it validates
```

### Frontmatter standard — PSFS v1.1.0

The frontmatter convention is published as a named, versioned standard: the **Portable Skill Frontmatter Spec (PSFS) v1.1.0** at [`spec/PSFS.md`](spec/PSFS.md). It defines two conformance tiers — **Core** (Anthropic-aligned, vendor-neutral; the tier any collection can adopt) and **Extended** (Core plus the multi-agent fields `owns` / `composes_with` / `spawned_by` / `requires_*`). The portable, tool-agnostic reference validator is [`spec/frontmatter.schema.json`](spec/frontmatter.schema.json) (JSON Schema 2020-12 — runnable in any language); `scripts/lint-skills.sh` is the bash reference implementation and adds the cross-file checks (name uniqueness, name-matches-directory, `owns` non-overlap) that a per-file schema can't express.

### `/sync-skills` (Claude Code slash command)

The recommended path on Claude Code. Symlinks `skills/<category>/<skill>/` to `~/.claude/skills/<skill>/` so Claude Code sees them globally and edits stay live.

</details>

---

## 🪝 Hooks

Skill Madness ships a small **hooks layer** under `hooks/` that turns the orchestrator's doctrine — the QA gate, formatting, profile injection — into enforcement. Hooks are modeled on the gated-hook design but built in the repo's own bash + `python3` (stdlib-only) idiom. Today only **Claude Code** has a native lifecycle-hook runtime, so hooks are emitted for Claude Code and skipped (logged `unsupported`) for the other ten hosts.

### The six hooks

| Hook | Event | Profiles | Blocks? | What it does |
|------|-------|----------|---------|--------------|
| `qa-gate` | `Stop` | all | **yes** | Validates `qa-report.json` against the QE schema and applies the orchestrator gate rules; blocks the Stop on a gate failure. **(marquee)** |
| `post-edit-format` | `PostToolUse(Edit\|Write)` | standard, strict | no | Formats the just-edited file if a matching formatter (prettier/black/shfmt/gofmt/rustfmt) is on `PATH`. |
| `session-start-profile` | `SessionStart` | standard, strict | no | Injects a ≤8 KB summary of `CLAUDE.md` / `.claude/profile.yaml` into the session. |
| `catalog-sync` | `PreToolUse(Bash git commit)` | standard, strict | no | If the skill catalog (README/CLAUDE/PLAN/START-HERE/plugin.json/marketplace.json counts) has drifted from disk, runs `catalog.sh --sync` and re-stages the corrected files; acts only on real drift, never blocks. |
| `skill-usage` | `PostToolUse(Skill)` | standard, strict | no | Appends a coarse, best-effort usage-telemetry event via `skill-health.sh record`; degrades silently, never blocks. |
| `pre-commit-lint` | `PreToolUse(Bash git commit)` | strict | no (warn) | Runs `lint-skills.sh` on staged skills and warns; never blocks the commit. |

Everything routes through one entrypoint — `hooks/run-with-flags.sh <hook-id>` — which reads the gating env vars and `hooks.manifest.json`, then dispatches `hooks/scripts/<hook-id>.sh` (or no-ops `exit 0` if disabled).

### Profiles & disabling

Two env vars tune the whole graph:

- `ATS_HOOK_PROFILE` ∈ `{minimal, standard, strict}` (default `standard`).
  - `minimal` → `qa-gate` only (1 hook).
  - `standard` → `qa-gate` + `post-edit-format` + `session-start-profile` + `catalog-sync` + `skill-usage` (5 hooks).
  - `strict` → all six; `qa-gate` also treats a **missing** report as a block.
- `ATS_DISABLED_HOOKS` → comma-separated hook ids to force-off, e.g. `post-edit-format,pre-commit-lint`.

Only `qa-gate` ever blocks, and only on a real gate failure. It signals a block the Claude Code way — printing `{"decision":"block","reason":"…"}` to stdout and exiting `0`.

### Install & enable

`scripts/convert.sh --tool claude-code` copies `hooks/` into `integrations/claude-code/hooks/` and generates `integrations/claude-code/hooks.json` (Claude Code settings-hook format). `scripts/install.sh` then copies that tree to a **namespaced** target — `~/.claude/ats-hooks/` — and writes `hooks.json` there. Install is **non-destructive**: it never auto-merges your `~/.claude/settings.json`. Instead it prints the exact snippet to merge into the `"hooks"` key. The wrapper is invoked as:

```text
"$CLAUDE_PROJECT_DIR"/.claude/ats-hooks/run-with-flags.sh <hook-id>
```

### Lint & test

```bash
./scripts/lint-hooks.sh          # validate the hooks tree (manifest, exec bits, headers, profiles)
bash tests/hooks/run-tests.sh    # the bats suite (wrapper gating, qa-gate, convert, lint)
```

Both run in CI via the `Hooks Layer (Ubuntu)` job in `.github/workflows/lint-skills.yml`.

---

## 🛠️ Development

### Run the lint locally

```bash
./scripts/lint-skills.sh
```

That's the same command CI runs. If it's green locally on macOS or Linux, the PR will be green.

### Add a new skill

1. Use the `skill-writer` skill: `"Generate a new skill for X."` — it scaffolds frontmatter + body in the right category dir.
2. Or copy `skills/meta/skill-writer/references/body-template.md` and fill in by hand.
3. Run `./scripts/lint-skills.sh skills/<category>/<your-skill>/` until clean.
4. Run `/sync-skills` (or `./scripts/install.sh --tool claude-code`) so Claude Code picks it up.
5. PR — CI gates on full-ecosystem lint.

### Edit an existing skill

If you used `/sync-skills`, the symlinks make edits in `skills/` live in `~/.claude/skills/` immediately — no resync needed.

> **Keep skill bodies under 500 lines.** When detail spills over, move it to `references/` — that's what progressive disclosure is for.

---

## 🩺 Troubleshooting

<details>
<summary><b>"<code>/sync-skills</code> says skills already exist"</b></summary>

Existing files in `~/.claude/skills/<name>/` block the symlink. Either delete the existing dir or run with `--force` to overwrite. The `sync-skills` skill body documents the safe paths.
</details>

<details>
<summary><b>"Linter fails on macOS but passes on Linux (or vice versa)"</b></summary>

Almost always a `pyyaml` version skew. CI installs `pyyaml` explicitly on macOS — replicate locally with `python3 -m pip install pyyaml`. Linux runners include it preinstalled.
</details>

<details>
<summary><b>"My non-Claude-Code host doesn't see all 71 skills"</b></summary>

Expected. Skills with `requires_claude_code: true` — the `orchestrator`, all of `roles/`, all of `loops/`, and the workflows bound to Claude Code's runtime or `~/.claude` config — are skipped for the other hosts; 34 of the 71 skills convert today. `./scripts/convert.sh` prints one `[convert] skipping <category>/<slug> for <tool> (requires_claude_code: true)` line to stderr per skipped skill — no extra flag needed.
</details>

<details>
<summary><b>"Stderr is full of <code>stripped allowed-tools/owns</code> lines"</b></summary>

That's by design — every Claude-Code-only frontmatter field that gets stripped on conversion to another host is announced. It's not an error; it's the installer being honest. Pipe stderr to a log file if it's noisy: `./scripts/convert.sh 2> convert.log`.
</details>

<details>
<summary><b>"Orchestrator complains about file-ownership conflicts"</b></summary>

Two skills declare `owns.directories` or `owns.files` on overlapping paths. The lint output prints the offending pair — open both SKILL.md files and pick which one truly owns it. The orchestrator's canonical ownership map (in `skills/orchestrator/SKILL.md`) is the tiebreaker.
</details>

<details>
<summary><b>"<code>install.sh</code> can't find my host's install directory"</b></summary>

Set the override env var documented in `scripts/README.md` (e.g. `CURSOR_RULES_DIR=...`, `AIDER_CONVENTIONS_PATH=...`) before running. The defaults assume each host's standard location.
</details>

---

## 🗺️ Roadmap

- [x] **Skill library** — 71 skills, seven categories, all linted
- [x] **Multi-tool installer** — convert / install / lint, eleven host adapters
- [x] **CI matrix** — Ubuntu + macOS lint on every push
- [x] **Contract-first specs** — OpenAPI / AsyncAPI / Pydantic / TypeScript / JSON Schema templates
- [x] **QA gate** — `qa-report.json` schema with critical / high / medium / low blockers
- [x] **Two-runtime degradation** — Agent Teams → subagents → sequential, host-detected
- [x] **Autonomous-loop library** — 13 loops on one `loop-controller` guardrail harness
- [x] **`/madness` front door** — one router that reads intent and launches the right skill
- [ ] **Image assets** — README hero, architecture diagram, host matrix illustration ⏳
- [ ] **End-to-end multi-agent verification on non-Claude-Code hosts** ⏳
- [ ] **Skill marketplace / registry** — discoverable installs, version pinning ⏳
- [ ] **Per-host CI smoke tests** — actually exercise each adapter's converted skills against a sample host ⏳

---

## 🧭 Key design decisions

- 📜 **One canonical format** — `SKILL.md` with YAML frontmatter is the source of truth; everything else is generated.
- 🚫 **Exclusive file ownership** — no two role agents own the same file. Conflicts resolved before spawn, not after.
- 🚦 **QA gate blocks** — critical issues or sub-threshold contract / security scores in `qa-report.json` fail the build. Self-declared "done" is not accepted.
- 🪜 **Progressive disclosure** — frontmatter (always loaded) → body (loaded on trigger) → references (loaded on demand). Big libraries, small contexts.
- 🪞 **Lossy conversion is announced** — every stripped field gets a stderr line per skill per host. The installer never silently drops content.
- 🛡️ **Fail loud, fail early** — frontmatter schema, ownership conflicts, broken cross-refs are all CI errors, not warnings.
- 🔁 **Symlinks > copies** — `/sync-skills` defaults to symlinking so edits in the repo are instantly live in every Claude Code session.
- 📣 **Pushy descriptions** — skill `description` fields intentionally over-enumerate trigger contexts. Under-triggering is a worse failure than over-triggering.

---

## 🤝 Contributing

PRs welcome — new skills, host adapter improvements, lint rules, examples, bug reports.

- New skill? Use `skill-writer` to scaffold it, then run `./scripts/lint-skills.sh` until clean.
- New host adapter? Add the converter to `scripts/convert.sh`, the installer destination to `scripts/install.sh`, and a fidelity row to `contracts/installer/per-tool-output-spec.md`.
- Bug report? Include the failing skill name and the lint output verbatim.

---

## 📜 License & attribution

[MIT](LICENSE) — fork, embed, ship commercial products on top, just keep the notice.

The multi-tool installer (`scripts/convert.sh`, `scripts/install.sh`, `scripts/lib/`) adapts code from [`msitarzewski/agency-agents`](https://github.com/msitarzewski/agency-agents) (also MIT). Full credits, the list of adapted pieces, and the upstream MIT notice live in [`ACKNOWLEDGMENTS.md`](ACKNOWLEDGMENTS.md).

---

<div align="center">

### ⭐ Star History

<a href="https://star-history.com/#ivy00johns/Skill-Madness&Date">
  <img src="https://api.star-history.com/svg?repos=ivy00johns/Skill-Madness&type=Date" alt="Star History Chart" width="640" />
</a>

<br/><br/>

<sub>🧰 Built by humans + the agents they coordinate.</sub>

</div>
