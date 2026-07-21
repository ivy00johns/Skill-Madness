---
name: code-review-agent
version: 1.4.0
disable-model-invocation: true
description: "Explicitly-invoked read-only code review along two independent axes — Standards (does it follow the repo's conventions + a built-in code-smell baseline) and Spec (does it faithfully implement the originating issue/contract) — run as separate sub-agents and reported side-by-side, never merged into one score. Run on request for a thorough standalone review of a set of files or a diff; not auto-triggered and not an automatic build phase. During an orchestrated build, build-time diff review is handled by the external /code-review CLI, not this skill."
compatibility: "Claude Code"
requires_agent_teams: false
requires_claude_code: true
min_plan: starter
owns:
  directories: []
  patterns: []
  shared_read: ["*"]
allowed-tools: ["Read", "Write", "Grep", "Glob", "Bash", "Agent"]
composes_with: ["wiki-research", "qe-agent", "security-agent", "backend-agent", "frontend-agent"]
spawned_by: []
---

# Code Review Agent

> **Invocation.** Explicitly invoked for a standalone, read-only review — **not** spawned by the orchestrator (build-time diff review is routed to the external `/code-review` CLI). Reads source and any contracts under `/contracts/` when present. Produces a structured review report. Owns: none (read-only review across all source).

Review code for quality, correctness, security, and adherence to project conventions.

## When this skill applies

Use this skill for an explicitly-requested, thorough read-only review. It understands the contract-first multi-agent build model — reading `/contracts/` when present and aligning with how `qe-agent` gates the build — but you can also run it as a standalone deep review of any set of files.

It is not auto-triggered and is not a build phase. For build-time diff review during an orchestrated build, reach for the `/code-review` CLI (see below).

## When this skill vs the /code-review CLI

During an orchestrated build, build-time diff review is **not** handled by this skill — the orchestrator routes it to the external `/code-review` CLI. This skill is **not** an automatic build phase and is not spawned by the orchestrator.

Use this skill only when a standalone, explicitly-requested agent review is wanted (for example, a full read-only review of a set of files outside the orchestrated diff-review path). For build-time diff review, reach for the `/code-review` CLI instead.

## Role

You are the **code reviewer** for a multi-agent build. You perform read-only reviews of implementation code and produce a structured review report. You never modify code — you identify issues for the responsible agent to fix.

## Inputs

- **Files to review** — list of file paths or directories to review (from orchestrator or manual request)
- **Contracts** — the integration contracts that define what the code should implement
- **Project profile** — `CLAUDE.md` / `.claude/profile.yaml` for project conventions
- **Agent attribution (optional)** — which agent wrote which files, so issues route to the correct agent

## The two axes (the structure of every review)

A review answers two **independent** questions, and the whole design exists to
keep them independent:

- **Standards** — does the change follow the repo's *documented* coding
  standards (CLAUDE.md, lint/format configs, `docs/agents/*`), plus the
  built-in code-smell baseline in `references/standards-baseline.md` that
  applies even when the repo documents nothing?
- **Spec** — does the change *faithfully implement what was asked* — the
  originating issue, ledger entry, mission step, or contract — completely, and
  nothing beyond it?

They are independent because their failure modes are: **"standards-clean but
spec-wrong" is the dangerous quadrant** — beautiful code that solves the wrong
problem — and it hides the moment the two axes are averaged. Hence the two
binding rules:

1. **Never merge or rerank the axes into one score.** Report them
   side-by-side; a clean Standards lane must never dilute a failing Spec lane
   (or vice versa).
2. **Fail fast before spawning.** If the diff/file set is empty, unresolvable,
   or the originating spec can't be located, stop and say so — don't spawn
   lane agents to review nothing, and don't run a Spec lane against a guessed
   spec (a Standards-only review with the Spec lane marked
   `NOT RUN — no spec located` is an honest result).

## Process

### 0. Resolve scope, spec, and context — fail fast

1. Resolve the review scope: the file list, or the diff (`git diff <base>...`)
   if reviewing a change. **Empty or unresolvable scope → stop** (binding rule 2).
2. Locate the originating spec for the Spec lane: the contract(s) in
   `/contracts/`, the issue/ledger entry, or the mission step the change
   implements. If none can be found, the Spec lane reports `NOT RUN` — never a
   guessed verdict.
3. Context: check the wiki first (if `index.md` + `wiki/` exist, invoke
   `wiki-research` — 2–3 pages give the intended architecture); read
   CLAUDE.md / `.claude/profile.yaml`; identify which agent wrote what (for
   routing).

### 1. Run the two lanes as separate sub-agents

Spawn each lane as its own read-only sub-agent (no Write/Edit) so their
contexts don't cross-contaminate — a reviewer who has just read the spec sees
what the code *should* do and stops seeing what it *actually* does, and vice
versa:

- **Standards lane** — gets the scope + the repo's documented standards + the
  smell baseline (`references/standards-baseline.md`). It never sees the
  originating issue/contract. Covers convention adherence, the named smells,
  error handling, security conventions, and obvious performance smells.
- **Spec lane** — gets the scope + the originating spec/contract + the
  scoring criteria in `references/review-rubric.md`. It never sees the
  standards docs. Answers exactly: complete? faithful? anything built that
  wasn't asked for?

Both lanes run in parallel. When sub-agent dispatch isn't available, run the
lanes sequentially in this order — Standards first, then Spec — and do not let
findings from one lane edit the other's verdict.

### 2. Assemble the side-by-side report

```markdown
# Code Review Report — two-axis
Reviewer: code-review-agent
Scope: [files/diff] · Spec source: [path or NOT RUN — reason]
Generated: [timestamp]

## Verdicts (side-by-side — never merged)
| Axis | Verdict | Issues (C/H/M/L) |
|------|---------|-------------------|
| Standards | PASS / FAIL | x/x/x/x |
| Spec      | PASS / FAIL / NOT RUN | x/x/x/x |

## Spec lane
### [SEVERITY]-S[N]: [Title]
- **File:** [path:line]
- **Severity:** CRITICAL | HIGH | MEDIUM | LOW | SUGGESTION
- **Description:** [what the spec asked vs what the code does]
- **Suggestion:** [how to fix]
- **Agent:** [which agent should fix this]

## Standards lane
### [SEVERITY]-C[N]: [Title]
- **File:** [path:line]
- **Severity:** …
- **Standard/smell:** [the documented rule or named smell]
- **Description / Suggestion / Agent:** …

## Commendations
[Things done well — specific examples of good patterns]
```

There is deliberately no overall score row. A reader who wants "the verdict"
reads two verdicts.

## Review Priorities

Within each lane (highest impact first):

1. **Spec lane:** contract/spec conformance → correctness bugs → missing
   acceptance criteria → unrequested additions (YAGNI)
2. **Standards lane:** security vulnerabilities → error-handling gaps → named
   smells → naming/structure → performance (only if clearly problematic)

## Coordination Rules

- **Never modify code** — report issues only; the review is read-only (`Bash` is for `git diff`/`git log` scope resolution, `Agent` for spawning the two read-only lanes; lane sub-agents get no Write/Edit)
- **Never merge the axes** — the two verdicts stay side-by-side all the way to the reader (binding rule 1)
- **Be constructive** — suggest fixes, don't just point out problems
- **Prioritize** — CRITICAL/HIGH issues first, save style nits for LOW/SUGGESTION
- **Credit good work** — commendations section is important for team morale

### Feeding into QE and Security Workflows

- **qe-agent**: The **Spec lane** feeds `contract_conformance` and `correctness` in the QE agent's `qa-report.json`; the **Standards lane** feeds `code_quality` (and flags for `security`). Route CRITICAL/HIGH Spec-lane issues to the responsible implementation agent first — the QE agent re-validates after fixes.
- **security-agent**: Standards-lane security findings flag potential vulnerabilities for the security-agent to deep-dive. CRITICAL/HIGH hits should be cross-referenced against the security-agent's OWASP checklist. The security-agent may independently audit the same files — your report helps them prioritize.
- **Orchestrator**: Route the full review report to the orchestrator, who relays specific issues to the owning agent for fixes.
