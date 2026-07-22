---
name: repo-deep-dive
version: 1.5.1
description: >-
  Perform a comprehensive technical deep dive on an open-source repository, combining
  a deep-research markdown document with hands-on codebase analysis to produce a structured
  12-14 document reference series. Use this skill whenever the user wants to deeply analyze
  a repo, do a deep dive on a project, reverse-engineer a codebase, create a technical
  reference for an open-source tool, understand how a project works inside and out, or
  compare another project's architecture against a reference project. Also trigger when the
  user mentions "deep dive", "deep research", "analyze this repo", "break down this codebase",
  "technical reference", "how does this project work", or has a deep-research markdown
  alongside a cloned repo ready for analysis.
requires_agent_teams: false
requires_claude_code: true
min_plan: starter
owns:
  directories: []
  patterns: []
  shared_read: ["*"]
allowed-tools: ["Read", "Write", "Edit", "Bash", "Glob", "Grep", "Agent"]
composes_with: ["project-profiler", "plan-builder", "mermaid-charts", "wiki-research", "llm-wiki"]
spawned_by: []
---

# Repo Deep Dive

> **Tradeoff:** Biases toward exhaustive documentation. For quick familiarization, use Explore subagent or grep instead.

Turn a Claude Deep Research document and a locally cloned repository into a comprehensive, structured technical reference — the kind of document set that lets someone understand a 100k+ LoC codebase in an afternoon.

## First: the repo you're in IS the target — dive in, don't go hunting

You were launched in a specific working directory for a reason: that repo is the one to deep-dive. Read that context **before asking a single question** — interrogating the user for what you could have read yourself is the friction to avoid, and interrogating the *filesystem* to guess is worse.

- **Check the working directory: run `git rev-parse --show-toplevel`.** If it succeeds, that repo is the target. Words like "this", "this repo", "this codebase", "the lessons in this", "another repo from `<person>`", or no explicit target at all — all mean *the repo you're in*. Take it literally and proceed.
- **State the assumption in one line and keep going** — e.g. "Deep-diving the repo you're in: `<name>` — tell me if you meant a different one." A single correctable statement respects the user's time; a blocking multiple-choice menu does not.
- **Never scan the filesystem to guess a target.** If the user's words seem to gesture at some other repo but give you no path, that is *not* license to `find`/`ls`/`git log` across their other repos hunting for a match — that machine-interrogation is the same friction as menu-interrogation, and it burns a turn guessing. You have exactly two resolutions: the repo you're in, or a *specific* path/URL the user actually named. Nothing concrete to resolve means nothing to hunt for.
- **Only one situation earns a question:** the user names a *different* project you cannot resolve to a path, or the working directory isn't a git repo at all. Then ask **once** — a single direct question with the current repo pre-filled as the default — rather than going and guessing.
- **"Compare against X" / "what can Y learn from this" is a lens, not a second target to find.** A deep dive may compare the target against a reference project, but that reference is the *framing goal*, not a repo you go looking for — and it never demotes the repo you're in to "the reference" and sends you elsewhere for "the real target." The repo you're in is the target; the comparison is what you do with it.

The rule of thumb: the current repo is the target — state that assumption and proceed. Reserve a question for the one situation above; never a filesystem scavenger hunt.

## What You Need

1. **A deep-research document** — markdown from any deep-research session about the project (Claude Deep Research, ChatGPT Deep Research, Gemini Deep Research, or a hand-written brief). This provides landscape context, community perspective, and high-level understanding that code analysis alone can't give you.

2. **A locally cloned repo** — the actual source code to trace, measure, and analyze. **Default to the repo you're invoked in** (see the section above); only ask when the target is genuinely elsewhere.

3. **An output directory** — where the deep dive's document series should land. There is no built-in default — naming the location explicitly keeps deep dives from accumulating in a folder the user forgets about. **But don't just ask blind: first run vault detection (Phase 0).** Many users keep a dedicated deep-research / Obsidian "second-brain" vault with an established convention for where deep dives live. If one exists, offer it as the *recommended* target rather than asking from scratch. You still ask — detection sets a smart default, it doesn't override the user.

The deep-research document is critical — it grounds the analysis in why the project exists and where it sits in the landscape, not just what the code does. **But look before you ask:** check whether one already exists — scan the repo's own `docs/` and any detected vault's research/sources area (see Phase 0) for a matching markdown brief. Ask the user only if none turns up. If the user doesn't have one, suggest they run a deep-research session first (it takes ~5 minutes and dramatically improves the output quality).

## The Process

Six phases (Phase 0 and Phase 5 are conditional). Read `references/phases.md` for the detailed instructions and code snippets, and `references/vault-integration.md` for the Phase 0 detection heuristic + the Phase 5 wiki page schema.

0. **Phase 0 — Locate the vault (before asking for output_dir).** Detect whether the user keeps a deep-research / Obsidian knowledge vault. If so, propose its convention as the recommended output target. See `references/vault-integration.md`.
1. **Phase 1 — Orient.** Read the deep-research doc, extract claims, gather hard numbers from the repo (LoC, commits, contributors).
2. **Phase 2 — Map the Architecture.** Trace from entry points inward. Use parallel subagents to explore subsystems concurrently. Produce a mermaid architecture diagram.
3. **Phase 3 — Deep Dive Each Subsystem.** One focused document per major subsystem (6-10 typical). Read the actual code, not just docs.
4. **Phase 4 — Compare and Assess.** Comparison + convergence/frontier documents. This is the strategic payoff.
5. **Phase 5 — Wiki integration (only if the target is a knowledge vault).** Synthesize the deep dive into the vault's wiki layer — source page, entity/concept pages, a comparison page — and update the vault's index/log per its own conventions. This is what makes `composes_with: llm-wiki` real. See `references/vault-integration.md`.

## Output Structure

All output goes in `{output_dir}/{project}_deepdive/source-material/`.

`{output_dir}` is required. Phase 0 detection sets a recommended default (a detected vault's deep-dive convention); otherwise the user supplies it. Either way, confirm the location before generating any files — silently dropping a 12-document series into a location the user didn't confirm wastes their time finding it later. **If the target is a detected vault, also run Phase 5** to integrate the series into its wiki layer rather than leaving it as an unlinked island.

### Document Progression

Read `references/document-template.md` for the full template with per-document guidance.

The consistent structure across all deep dives:

| # | Document | Purpose |
|---|----------|---------|
| 00 | INDEX.md | Table of contents, generation metadata, reading guide |
| 01 | project-overview.md | What it is, by the numbers, landscape position |
| 02 | architecture.md | High-level system design, layers, key decisions |
| 03-09 | [subsystem docs] | Deep technical dives — one per major subsystem |
| 10+ | comparison.md | How it compares to a reference project and related tools |
| 11+ | convergence-analysis.md | What each project has that the other lacks |
| 12+ | frontier-assessment.md | What's novel, what's table stakes, what to build |

The exact number and naming of subsystem docs (03-09) varies by project. A project with a complex agent system gets `agent-system.md`. A project with a custom database gets `storage-engine.md`. Name them for what they cover, not by a fixed template.

### Document Quality Standards

- **80-300 lines per document** — long enough to be thorough, short enough to read in one sitting
- **Code paths, not code dumps** — reference specific files and functions, don't paste large blocks
- **"By the numbers" tables** — readers love hard data, give them precise counts
- **Mermaid architecture diagrams** — use the `mermaid-charts` skill for flowcharts, sequence diagrams, and system maps instead of ASCII art. Prefer `flowchart TB` with subgraphs for layer-cake architectures, `sequenceDiagram` for request flows
- **Cross-references** — link between documents when one subsystem touches another
- **Honest assessments** — note gaps, limitations, and production readiness issues candidly

## Parallelization, Scope, and Working With the Research Doc

Read `references/parallelization.md` for: the subagent strategy across phases, how to adapt scope to codebase size (6-8 / 10-12 / 12-14 docs), how to reconcile contradictions between the research doc and the code, and what makes a great deep dive vs a mediocre one.

## Anti-Pattern

> **Forbidden:** Generating a deep dive into an unconfirmed location. Phase 0 may *propose* a detected vault as the default, but you still confirm before writing. Silently dropping a 12-doc series anywhere — default folder or detected vault — without confirmation wastes the user's time.

> **Forbidden:** Dropping the series into a detected knowledge vault but skipping Phase 5. An unlinked deep-dive folder inside a wiki is an orphan — if the target is a vault, integrate it (source/entity/concept/comparison pages + index + log) per the vault's own conventions.

## Final step: feed findings into the living plan

After producing the reference series, if the target project has a living plan/ledger
(look for `START-HERE.md`, `BUILD-PLAN.md`, or `docs/REMAINING-WORK.md`), invoke the
`plan-intake` skill on the integration/gap findings so they become tracked entries
rather than a static report. Skip only if the project has no ledger.
(For skill-creator / skill-review reports, run `plan-intake` manually on the report — same loop.)

## Reference Files

- `references/phases.md` — detailed instructions for Phases 1-4 with measurement commands and subagent dispatch patterns
- `references/document-template.md` — full per-document template (INDEX, overview, architecture, subsystem skeletons, comparison, convergence, frontier)
- `references/parallelization.md` — subagent strategy, scope adaptation, reconciling research vs code, hallmarks of a great deep dive
- `references/vault-integration.md` — Phase 0 vault-detection heuristic + Phase 5 wiki integration (page schema, index/log updates)
