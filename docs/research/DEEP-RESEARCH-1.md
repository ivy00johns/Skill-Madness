# What's New in Agent Engineering (Mid-2026 → Oct 2026): A Skill Madness / The Hive Update

The biggest change since mid-2026 is that skills now need tests. Claude Code shipped `claude plugin eval` on September 11, 2026, and Anthropic donated the Agent Skills standard to the Linux Foundation's Agentic AI Foundation on October 22, 2026. Over the same period the newest named engineering layer above harnesses became **loop engineering** (June 2026). The term practitioners keep returning to under it, though, is **verification**: evals, verifier agents and quality gates. For The Hive, that means its next version should treat every skill as a tested, portable, measured artifact. That suits an SDET background unusually well.

## TL;DR

- **Skills are now a neutral standard and a testable artifact.** Agent Skills (SKILL.md) moved to the Linux Foundation's AAIF on Oct 22, 2026. Claude Code v2.1.269 (Sept 11, 2026) added `claude plugin eval`, which scores a skill with and without the plugin loaded and reports the delta (Δ). Ship Skill Madness with an `evals/` suite per skill, and gate CI on Δ.
- **The vocabulary went prompt → context → harness (Feb 2026) → loop engineering (June 2026).** Pieces such as "graph engineering" and "eval engineering" came after; graph engineering is mostly a meme, while eval engineering is substantive. Loop engineering is real practice, but it is partly being absorbed into built-in `/loop` and `/goal` commands. A mining study of 36,710 repos found autonomous agent loops in only 217 of them.
- **The practical frontier is verification and context economy.** Skill descriptions are now a scarce, budgeted resource: Claude Code and Codex both truncate or drop descriptions when too many skills are installed. Newer models also need less scaffolding. Prune, measure triggering, and design skills to act as verifiers inside loops.

## Key Findings: What's New Since Mid-2026

| Date (2026) | Development | Why it matters for The Hive |
|---|---|---|
| Jun 2–7 | Boris Cherny ("My job is to write loops"), Peter Steinberger and Addy Osmani name **loop engineering** | Skills become building blocks inside unattended loops |
| Jun 30 | Dex Horthy (HumanLayer), "Harness Engineering is not Enough: Why Software Factories Fail" (AI Engineer World's Fair) | Counterweight: unread agent code degrades codebases |
| Jul 9 / Jul 20 / Aug 14 | Osmani: "Own the Outer Loop," "Software Factories, Light and Dark," "Practical Loop Engineering" | Humans own the verification boundary |
| Jul 15 | arXiv 2609.00006 source-code study of 11 coding harnesses: SKILL.md skills lead MCP in adoption (9/11 vs 8/11) | Skills are now the most widely implemented extension surface |
| Jul 18 | "Graph engineering" meme (Steinberger, Hamel Husain joke post; Carlos E. Perez essay) | Mostly hype; see below |
| Aug 22 | Lulla et al., "Loop Engineering: Building Blocks, Adoption, and Impact" (arXiv 2608.21884) | First empirical data on loops |
| Sept (5 or 11) | OpenAI's Eric Provencher, "Rethinking skills and prompts for GPT-6 Astra" | Shorter descriptions, leaner AGENTS.md |
| Sept 1 | Claude Code plugins can declare `defaultEnabled: false`; dependency auto-resolution | Better packaging for a large skill suite |
| Sept 11 | Claude Code v2.1.269: `claude plugin eval` | First-party skill/plugin test harness |
| Sept 23–25 | Claude Marketplace opens with 2,000+ connectors/plugins; plugin submission portal for paid-plan developers with safety scanning and usage analytics | New distribution channel |
| Oct | Claude Code adds `/doctor prompt-audit`, fork subagents by default, idle compaction, per-subagent auto-compact windows, `claude plugin install --marketplace` | Harness keeps absorbing patterns skills used to provide |
| Oct 22 | Agent Skills donated to the Agentic AI Foundation (Linux Foundation) | Spec governance is now vendor-neutral |

## Details

### 1. Skill harnesses: spec, Claude Code, cross-vendor adoption

**The spec itself has barely changed, and that is the point.** The agentskills.io specification still defines exactly six frontmatter fields:

- `name` (required): 1–64 chars, lowercase, hyphens, must match the directory.
- `description` (required): 1–1024 chars, saying what the skill does and when to use it.
- `license` (optional).
- `compatibility` (optional): ≤500 chars.
- `metadata` (optional): string→string map.
- `allowed-tools` (optional, experimental): a space-delimited string, *not* a YAML list.

One practitioner comparison found the frontmatter table identical in field set and requirements to the December 2025 original. The recommended progressive-disclosure budgets are unchanged:

- About 100 tokens of metadata per skill at startup.
- A SKILL.md body under 5,000 tokens / 500 lines.
- `scripts/`, `references/` and `assets/` loaded on demand, with references kept one level deep.

Two gaps matter for a distributor. The spec publishes no version identifier, and the repo had no tags or releases when checked in August 2026. Behaviour for unknown frontmatter keys is also unspecified. The Oct 22 donation to AAIF, the same foundation that hosts MCP, should eventually produce versioned governance. Until then, treat the six-field core as the only portable contract.

**Adoption is effectively universal.** The agentskills.io client showcase listed 46 products on Aug 18, 2026, including:

- Claude Code
- ChatGPT/Codex
- Cursor
- GitHub Copilot
- VS Code
- Gemini CLI
- OpenHands
- Goose
- Amp

Notable platform moves:

- **Google:** Gemini CLI is being replaced by **Antigravity CLI**. Gemini CLI stopped serving consumer (AI Pro/Ultra/free) requests on June 18, 2026. Google says Antigravity CLI keeps Agent Skills, Hooks, Subagents, and Extensions (now "Antigravity plugins"). Gemini CLI also honors a `.agents/skills/` alias that takes precedence over `.gemini/skills/`.
- **OpenAI Codex** uses `.agents/skills/` and `$skill` invocation and maintains `openai/skills`. Provencher's September guidance warns that "when you add too many skills, Codex starts shortening their descriptions to fit." It also warns that descriptions with "too much 'pick me' energy" make the model load instructions that don't help. OpenAI updated its `$skill-creator` accordingly. Sources disagree on the publication date (Sept 5 vs Sept 11).
- **Claude Code** now falls back to AGENTS.md when no CLAUDE.md exists (reported September 2026). It also syncs claude.ai account skills into terminal sessions (v2.1.273+).

**Claude Code-specific skill mechanics worth adopting or guarding against:**

- **Description budget.** Claude Code keeps every skill name in its listing. When the listing overflows its character budget, it drops descriptions, starting with the least-invoked skills. A large suite like Skill Madness can therefore silently lose triggering on its long-tail skills. Community tooling (`skill-trigger-bench`) lints for a combined description budget of roughly 15k chars and for TF-IDF overlap between descriptions.
- **Claude Code frontmatter extensions** (not portable): `when_to_use`, `disable-model-invocation`, `paths`, subagent execution, and `` !`cmd` `` dynamic context injection.
- **Bundled `/verify` and `/run-skill-generator`** write per-project recipe skills (`.claude/skills/verify/SKILL.md`). Since v2.1.286, a project skill named `verify` or `simplify` is automatically run before each commit. The harness is now *generating and consuming* skills as part of its own verification loop.
- **`/doctor`** compares unused skills, MCP servers and plugins against their context cost. **`/doctor prompt-audit`** (v2.1.283+) flags outdated or conflicting instructions across CLAUDE.md and skills.

**Plugins and marketplaces.** The Sept–Oct changelogs added:

- `defaultEnabled: false` in `plugin.json` or marketplace entries.
- Auto-resolution of missing plugin dependencies from configured marketplaces.
- `claude plugin configure` for plugin options.
- `--plugin-dir` loading a folder of plugins.
- `claude plugin install --marketplace`.
- Credential redaction in marketplace URLs.

Anthropic opened **Claude Marketplace** on Sept 23 with "more than 2,000" connectors and plugins. On Sept 25 it opened a directory submission portal where "each submission is checked and safety-scanned as soon as you submit," with usage analytics by surface and version. It also says "one discovery experience will roll out across Claude and Claude Code". That rollout is announced, not yet confirmed as complete.

### 2. Skill evaluation tooling: the QA moment

This is the most important development for John's background. Three layers now exist:

1. **`skill-creator` (Anthropic, `anthropics/skills`)** has eval, benchmark and description-optimization modes:
   - With-skill vs without-skill benchmarking (pass rate, time, tokens) into `benchmark.json`.
   - Description tuning that generates should-trigger and should-not-trigger prompts.
   - A key caveat from the skill itself: "Claude only consults skills for tasks it can't easily handle on its own." Trivial prompts are therefore poor trigger tests.
   - A reported bug (anthropics/skills#556) has the trigger eval reporting a 0% trigger rate.
2. **`claude plugin eval` (Claude Code ≥ v2.1.269, Sept 11, 2026)** is the first-party regression harness:
   - Each case is a directory under `evals/` with a `prompt.md` and a `graders/` folder.
   - There are six grader types. Four are deterministic and free; `llm` and `baseline` bill a judge model. A `tool_used` grader can assert that the Skill tool fired with a given skill name.
   - Each case runs several times in an isolated session with only the target plugin loaded, and by default again without it. The report shows WITH, W/OUT and Δ: "Their difference, Δ, is what the plugin contributed."
   - `--threshold`, `--max-cost-usd` and `--trust-plugin` make it a CI gate.
   - `claude plugin eval init` interviews you and scaffolds cases.
   - The eval directory is configurable via the manifest's `experimental.evals` key. The `experimental` prefix signals the format may still change.
3. **Community lint/bench tools** such as `skill-trigger-bench` check frontmatter, missing "when" language, description overlap, budget, body length and missing references. The `skills-ref validate` reference validator checks spec conformance.

Real-world migration is already under way. One large public plugin repo (melodic-software/claude-code-plugins) held 341 skill-creator `evals.json` files as of Oct 4, 2026 and is converting them to `case.yaml` plugin-eval suites plugin by plugin. The owner notes that each converted suite needs paid eval runs, so eval spend is now a budgeting decision.

Quality and security baselines are poor, which makes good testing a differentiator. A UC Irvine study (Hong, Imani & Ahmed, "From Anatomy to Smells," arXiv 2607.01456, July 2026) of 238 skills found that "over 99% of SKILL.md files contain at least one skill smell, and once introduced, skill smells rarely disappear as skills evolve." Snyk's ToxicSkills audit (Feb 5, 2026) found that 1,467 of 3,984 skills from ClawHub and skills.sh (36.82%) had at least one security flaw, 534 (13.4%) were critical and 76 were confirmed malicious.

### 3. Loop engineering and agentic loops

**Origin and definition.** In early June 2026 three statements landed within days of each other:

- Cherny (June 2 interview): "I don't prompt Claude anymore. I have loops that are running… My job is to write loops."
- Steinberger (June 7): "you shouldn't be prompting coding agents anymore. You should be designing loops that prompt your agents."
- Osmani (June 7) named it: "Loop engineering is replacing yourself as the person who prompts the agent. You design the system that does it instead."

Osmani's building blocks are automations, worktrees, **skills**, plugins/connectors and subagents, plus external state ("the agent forgets, the repo doesn't").

The peer-reviewed-track working definition (Lulla, Treude, Baltes et al., arXiv 2608.21884, Aug 22, 2026) is: automated control structures that repeatedly invoke coding agents, triggered on a schedule or by events, with each run bounded by a machine-checkable stop condition. The same definition requires persisted state, independent verification, bounded cost, restricted unattended changes and defined human escalation.

**Lineage.**

- Geoffrey Huntley's Ralph loop (July 2025): `while :; do cat PROMPT.md | claude-code ; done`, with a fresh context each iteration and progress persisted to disk.
- Claude Code's `/loop` (March 2026).
- Codex goal objects with machine-checkable completion (April).
- `/goal` in Claude Code, Hermes and others (May).

**Consensus building blocks** (largely traceable to Osmani's posts, so less independent than they look):

- A trigger plus a stop condition.
- Durable state outside the context window.
- Skills for project knowledge.
- Worktree isolation.
- A **maker/checker split with an independent verifier**. Cobus Greyling's verifier skill makes rejection the default.
- Budgets and a kill switch.
- Approval limits.
- Staged autonomy, e.g. Greyling's readiness levels: L0 documented intent, L1 report-only, L2 assisted fixes with verifier, L3 unattended.

**Evidence vs. claims.** The Lulla et al. mining study scanned 36,710 engineered repos and confirmed autonomous agent loops in 217 (0.59%). Most were event-triggered PR review in GitHub Actions. Almost none committed the state files, stop conditions, budgets or verifier subagents the discourse prescribes. Headline numbers are self-reported: Stripe engineers told InfoQ (March 2026) that Minions "now produce over 1,300 pull requests per week, up from 1,000 in earlier trials," all human-reviewed, and Osmani reports 423 Firefox security fixes in a month.

Documented failure modes include:

- Runaway cost (about 8M tokens in 48 hours from one CI-fixing loop).
- Infinite fix loops.
- "Verifier theater."
- Review fatigue that turns human gates into rubber stamps.
- "Comprehension debt."

Gergely Orosz concluded that after `/loop` and `/goal` became built-ins, loop engineering looked "as good as obsolete" for regular app engineers, while it remains important at the infra level.

**Long-running harness patterns (Anthropic).** Prithvi Rajasekaran's "Harness design for long-running application development" (Mar 24, 2026) is still the canonical primary source:

- A planner → generator → evaluator architecture, inspired by GANs.
- An evaluator that drives the live app with Playwright against explicit grading criteria.
- Structured handoff artifacts.
- The finding that context resets beat compaction alone for Sonnet 4.5.
- Crucially, scaffolding was *removed* (the sprint construct) once Opus 4.6 could sustain longer sessions. Every harness component encodes an assumption about model weakness, so re-test it per model.

**Software factories.** Osmani's "Software Factories, Light and Dark" (July 20) frames loop → harness → factory. A dark factory ships code no human reads; a light factory keeps humans at judgment points. Horthy reports that unread, agent-written codebases begin defeating their own agents after roughly 3–6 months. His proposed fix is human review at product, architecture, program-design and vertical-slice checkpoints, which he claims yields 2–3x throughput. That figure is self-reported. Ethan Mollick added "twilight factory" (August 2026) for agents that proactively pull humans in.

The scale context is real. Anthropic's engineering blog post "Redesigning source control at Anthropic" (Oct 13, 2026) reports that "In May 2026, Anthropic averaged around 2,500 code changes merged per day; as of September, we merged over 30,000 per day," peaking at 30,401 on Sept 9, and a team of seven built new source control (Scion) to cope.

### 4. Prompt and context engineering: what changed

- **Less instruction is now more.** Provencher's GPT-6 Astra guidance:
  - Trim AGENTS.md rules written for weaker models. "read architecture.md before every edit" burns context, and forced testing now causes redundant test runs because the model checks its own work.
  - Loosen over-strict permission language.
  - State explicit completion criteria.
  - Keep skill descriptions short.

  Anthropic's equivalent tooling is `/doctor prompt-audit` and `/claude-api prompt-audit`, which flag "instructions written for older models." One practitioner audit cut 143 skill descriptions from 56,560 to 12,392 characters (−78%).
- **Context budget heuristics.** Horthy's "dumb zone" heuristic: reasoning degrades past roughly 40% of the context window for beginners, while experienced users push to 60–70%. It is based on HumanLayer session data and has not been independently verified. His Research → Plan → Implement (RPI) workflow and "intentional compaction" remain the reference practitioner pattern.
- **Harness-level compaction keeps moving into the tool.** Claude Code added idle compaction (v2.1.299), per-subagent `autoCompactWindow` (v2.1.296), fork subagents on by default (v2.1.302) and an `effort` parameter for subagents (v2.1.292). Skills should not hand-roll what the harness now does.
- **Context files have mixed evidence.** An ETH Zurich study (Gloaguen et al., "Evaluating AGENTS.md," arXiv 2602.11988) found that "providing context files does not generally improve task success rates, while increasing inference cost by over 20% on average." Lulla et al. (arXiv 2601.20404) instead associated AGENTS.md with "lower median runtime (Δ28.64%) and reduced output token consumption (Δ16.58%)" at comparable task completion. Galster et al.'s study of 2,853 repos concluded "harness engineering in open source today is… mostly context engineering": developers adopt static context files and rarely use executable mechanisms such as hooks and skills.
- **Hooks are the deterministic layer.** October fixes made instruction-style prompt hooks on Stop/SubagentStop actually block. They also added an `onFailure: block` option and a `claude_code.safety_event` OpenTelemetry event. For verification, hooks beat prose instructions.

### 5. The "new engineering area": what's real and what's hype

| Term | Coined / popularized | What it means | Verdict |
|---|---|---|---|
| **Agentic engineering** | Andrej Karpathy, Feb 2026; formalized at Sequoia AI Ascent, Apr 2026 | Umbrella: "you are orchestrating agents who do [write code] and acting as oversight" | Real; the name of the whole field |
| **Harness engineering** | Mitchell Hashimoto (Feb 2026 blog); OpenAI/Ryan Lopopolo (Feb 11, 2026); LangChain's "Agent = Model + Harness" (Mar 2026) | Everything around the model: tools, AGENTS.md, skills, hooks, sandbox, feedback | Real and established; academically studied |
| **Loop engineering** | Cherny/Steinberger/Osmani, June 2026 | Systems that prompt agents on triggers, with stop conditions and verifiers | Real practice, contested novelty ("renamed cron jobs"); partly absorbed into `/loop`/`/goal` |
| **Graph engineering** | Steinberger quip + Hamel Husain joke post (July 18, 2026); Carlos E. Perez essay (July 18); Jilin Univ. survey arXiv 2608.21156 (Aug 21) | Perez: "not a better loop but a graph of loops"; survey: graph structures organizing task execution and multi-agent coordination | Mostly hype. Husain's post was reportedly a joke (essentially a GIF); only the academic survey is substantive |
| **Eval engineering** | Popularized by Galileo; SiliconANGLE (May 17, 2026) calls it vendor language | Lifecycle of building, calibrating and deploying evals and LLM judges; framed by blogs as "designing the bar the loop has to clear" | Substantive under any name; the most relevant to an SDET |
| **Intent engineering** | Paweł Huryn (Product Compass, Jan 2026), vendor blogs, a Forbes Council post (Apr 2026) | Specifying what the agent should *want*: goals, trade-offs, definition of done | Useful idea, not standardized. Sourcegraph: "no specification, no agreed definition" |
| **Software factories (light/dark/twilight)** | Dan Shapiro (Jan 2026), StrongDM (Feb), Osmani (July), Mollick (Aug) | Many loops at scale with gates into production | Real operating-model debate; dark factories contested by Horthy |

**My judgment.** The genuinely new engineering area is not another "X engineering" label. It is **verification as the binding constraint on autonomy.**

- Osmani's rule is that autonomy should grow only as far as output can be verified cheaply and reliably.
- Every loop source puts the verifier first.
- Anthropic shipped `/verify`, plugin evals and safety telemetry.
- The empirical paper found verifiers are the piece real repos *don't* commit.

Call it eval engineering or verification engineering: it is the evolution of QA/SDET work into agent systems. The naming treadmill (harness → loop → graph) is moving faster than practice. Expect "graph engineering" to fade or fold into multi-agent orchestration.

## Recommendations for Skill Madness / The Hive

**Structure and compatibility**

1. **Make the six-field spec core canonical.** Use only `name`, `description`, `license`, `compatibility`, `metadata` (strings only) and `allowed-tools` (a string) in the portable layer. Put Claude-only fields (`when_to_use`, `disable-model-invocation`, `paths`, `` !`cmd` `` injection) in clearly marked variants, or document graceful degradation. Put a version in `metadata.version` and in `plugin.json`, because the spec itself is unversioned.
2. **Dual-path layout.** Ship skills so they can be installed to `.agents/skills/` (read by Codex and Antigravity/Gemini, which gives the alias precedence) and to `.claude/skills/`, and also wrap them as a Claude Code plugin via a `.claude-plugin/marketplace.json`. Drop any Gemini CLI–specific assumptions; target Antigravity plugins for Google.
3. **Treat descriptions as a budget.** Lint every description for:
   - "Use when…" trigger language.
   - Under about 300–400 chars in practice (the hard limit is 1024).
   - No "pick me" superlatives.
   - Overlap below about 0.35 TF-IDF cosine with sibling skills.
   - Total suite description size under the roughly 15k-char community budget estimate.

   Split The Hive into themed plugins, and mark niche ones `defaultEnabled: false`, so the always-loaded listing stays small.
4. **Prune for current models.** Run `/doctor prompt-audit` and Provencher's checklist across the suite. Remove "always read X first," "always run tests" and over-strict ask-first language that Opus 5.5- and GPT-6-class models no longer need.

**Testing (lead with the SDET strength)**

5. **Every skill ships an `evals/` suite for `claude plugin eval`**, with at least:
   - One `tool_used` grader proving the skill fires.
   - One near-miss negative case proving it does *not* fire.
   - One deterministic result grader.
   - One negative-control task where Δ should be about 0.

   Require Δ > 0 on cases where a skill claims unique value. A skill with no measurable lift is a deletion candidate.
6. **Tier CI by cost.** On every PR, run free static lint (`skills-ref validate`, a trigger-bench-style overlap/budget lint) and one smoke eval case with `--max-cost-usd`. Run the full suites nightly or before release. Re-run on every Claude Code or model upgrade, because harness behaviour shifts weekly.
7. **Build a cross-harness compatibility matrix.** Smoke-test triggering in Claude Code, Codex CLI and at least one open-source harness (OpenCode or Goose), and publish the results in the README. Nobody else does this systematically, so it is a credible differentiator.
8. **Add security hygiene.** Scan bundled scripts, avoid angle brackets in frontmatter, keep `allowed-tools` minimal (it *grants* permissions, it does not restrict them), and document what each script executes. Marketplace submission already safety-scans; get ahead of it.

**Loop-readiness**

9. **Ship a "loop kit" of skills designed as loop components:**
   - A default-reject verifier skill (maker/checker).
   - A state-file convention (LOOP.md/progress log), which fills the gap the mining study found.
   - Stop-condition templates.
   - A budget/kill-switch checklist.
   - A `verify` project skill that plugs into Claude Code's pre-commit hook behaviour.

   Map them to readiness levels L0–L3 so users can adopt them gradually.
10. **Don't duplicate the harness.** Drop or slim any Hive skills that reimplement compaction, subagent forking, `/loop`, `/goal` or `/verify`. Wrap and configure the built-ins instead.

**Distribution**

11. **Distribute through three channels:** a GitHub marketplace repo (`claude plugin marketplace add`), the `npx skills add` / skills.sh cross-agent path, and a submission to the Claude directory portal for analytics. Watch AAIF for a versioned spec and for any signing or provenance requirement.

## Caveats

- Many dates and figures come from fast-moving secondary sources such as changelog mirrors, vendor blogs and X articles. The Claude Code changelog itself, Anthropic and OpenAI blogs, agentskills.io and arXiv papers are the primary anchors.
- Provencher's article date is inconsistent across sources (Sept 5 vs Sept 11). Perez's essay date is also inconsistent (Medium shows July 16; X shows July 18).
- Productivity claims (Stripe Minions, 423 Firefox fixes, Horthy's 2–3x, the "dumb zone" threshold) are self-reported and unreplicated.
- The arXiv papers cited are preprints. The loop engineering paper is under review at JAWs@ASE 2026.
- The marketplace's unified "one discovery experience" across Claude and Claude Code is announced, not confirmed shipped. `claude plugin eval`'s eval directory key is still under `experimental`.
- Gmail held no prior Skill Madness research threads, so this report could not diff against the earlier research baseline. Some items may not be new to you.
