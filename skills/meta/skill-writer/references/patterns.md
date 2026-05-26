# Skill Patterns

Five architectural patterns from Anthropic's Agent Skills guide (Ch.5, pp.21-24). Use these as named templates when deciding how a new skill should be structured. Each pattern has a distinct shape, trigger profile, and failure mode.

## 1. Sequential Workflow

**Shape:** A fixed sequence of steps where each step's output feeds the next.

**Use when:** The task has a natural pipeline — the order of operations is determined in advance, not by the model mid-run. Examples: code-review (read diff → categorize findings → produce report), deployment-checklist (run checks → score → sign off).

**In-repo example:** `deployment-checklist` — runs a defined sequence of readiness checks before declaring a build ready.

**Watch out for:** Steps that silently skip on empty input. Each step should assert its prerequisites; don't let a failed step pass a blank artifact to the next one.

---

## 2. Multi-MCP Coordination

**Shape:** The skill orchestrates two or more MCP servers or external tool categories, merging their outputs.

**Use when:** The task genuinely requires data from multiple tool surfaces — e.g., reading a file via `Read`, querying a database via a database MCP, and posting a result via a notification MCP. The skill's job is to coordinate the calls and normalize the outputs.

**In-repo example:** `playwright` — drives a browser MCP alongside `Read`/`Bash` to capture screenshots and run accessibility audits in one pass.

**Watch out for:** Treating multi-tool use as automatically requiring this pattern. Most skills just call several tools inline. This pattern applies when the coordination logic (retries, aggregation, normalization) is the main value of the skill.

---

## 3. Iterative Refinement

**Shape:** The skill produces a draft, evaluates it against a rubric, and revises until the rubric is met or a step limit is hit.

**Use when:** Quality is hard to specify up front but easy to evaluate — UI copy, architecture documents, skill descriptions. The rubric might be explicit (the frontmatter validation rules) or heuristic (does this trigger reliably?).

**In-repo example:** `skill-review` — scores a skill, produces findings, and expects the author (or `skill-update`) to iterate until findings are resolved.

**Watch out for:** Infinite loops. Always set an explicit iteration cap. Surface each iteration's rubric score so the user can decide to stop. Do not silently discard the draft and restart.

---

## 4. Context-Aware Tool Selection

**Shape:** The skill inspects the current environment at runtime and selects different tools or strategies based on what it finds.

**Use when:** The same goal is achieved by different means depending on context — local dev vs. CI, Claude Code vs. Claude.ai, single-agent vs. agent-team runtime. The skill reads environment signals and branches.

**In-repo example:** `orchestrator` — degrades across three runtime tiers (Agent Teams → subagents → sequential), picking the dispatch strategy based on what `CLAUDE_CODE_EXPERIMENTAL_AGENT_TEAMS` and other signals report at invocation time.

**Watch out for:** Branching on too many dimensions. Capture the key runtime variables at the start of the skill and make a single decision. Late branching (inside individual steps) makes the logic hard to trace.

---

## 5. Domain-Specific Intelligence

**Shape:** The skill embeds a narrow expert model — specialized rules, heuristics, vocabularies, and failure modes — for a specific technical domain.

**Use when:** Generic Claude instruction-following produces mediocre output, but a skill that knows the domain's idioms produces good output. The "expert knowledge" can't be inferred from first principles; it has to be encoded.

**In-repo example:** `contract-author` — knows the specific contract fields, invariant rules, and cross-package dependency conventions of this repo's integration contracts. A generic "write contracts" prompt would miss all of it.

**Watch out for:** Overfitting. Domain intelligence is an asset when the domain is stable. If the domain is changing rapidly, keep the volatile parts in `references/` so they can be updated without touching the skill body.

---

## Combining Patterns

Patterns compose. `repo-deep-dive` is Sequential Workflow (phased research phases) + Domain-Specific Intelligence (knows how to read a codebase, what to look for, how to produce the 12-14 document output). `orchestrator` is Context-Aware Tool Selection + Multi-MCP Coordination (spawns agents, reads their outputs, gates on QA).

Name the pattern you're using in the skill's design comments — it makes future reviewers' jobs easier.
