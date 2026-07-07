# Future — Frontier (out of scope)

**Last updated:** 2026-07-03 (F5–F18 intaken from the full-library review's ideas appendix)
**Companions:** [`PLAN.md`](../PLAN.md), [`docs/REMAINING-WORK.md`](REMAINING-WORK.md)

Items explicitly out of scope for the current plan. Kept here so they aren't lost; pulled into the ledger only if a future cycle prioritizes them.

## F1 — Multi-host installer reach ("convergence frontier")
The `agency-agents` comparison (184 agents, 11-tool install reach) sketches a ~10-day roadmap to broaden where skills can install (Copilot, Cursor-native, and other hosts) while preserving Skill-Madness's moats (contract layer, QA gate). Aspirational, not committed.
Source: `../DeepResearch/AllTheSkills/agency-agents_deepdive/source-material/11-convergence-frontier.md`.

## F2 — Skill marketplace / registry
A discoverable registry for publishing/pulling skills with remote version pinning (the `source` field reserved in `skills-lock.json` hints at this). No design committed.

## F3 — Per-host CI smoke tests
End-to-end verification that converted skills actually load and run on each non-Claude-Code host (not just that conversion produces a file). Today CI validates frontmatter, lint, catalog, hooks, and scan — but not live execution per host.

## F4 — README / docs image assets
Hero image, architecture diagram, and host-fidelity matrix graphic for the README. Cosmetic; deferred until the doc-polish backlog (M4) clears.

---

F5–F18 below are the new-skill ideas from the **2026-07-03 full-library review** (two independent ideation agents — a Claude Code platform-surface audit and an external-ecosystem/lifecycle scan — deduped against all 71 skills). Full pitches with triggers, DoD, and difficulty live in the report's appendix: [`skill-review-report.md`](../skill-review-report.md) § "Fresh Build Ideas". Suggested first wave: F5 + F8 + F13; identity-defining second wave: F6 + F7 + F9. The review's idea #20 (`model-router`) is absorbed by ledger entry MT-1, not listed here.

## F5 — `skill-eval` (meta, M/L)
Measured trigger-precision/recall harness for the library's own skills: generated should-trigger / should-NOT-trigger prompt sets run in clean-context subagents, rubric-scored behavior, description A/B, threshold gate. Both ideation agents' independent #1 — skill-review currently punts evals to external `/skill-creator` "if available", so the "pushy descriptions" value prop is never measured. Closes the loop: skill-writer authors → skill-eval scores → skill-update fixes.

## F6 — `mock-from-contract` (contracts, M)
Serve a runnable, schema-faithful mock server (deterministic seeded responses) from an authored OpenAPI/AsyncAPI contract, so consumer agents build against a live fake before the backend exists. Completes the owned pipeline: contract-author → mock → parallel build → contract-conformance-loop. Would be `contracts/`' first addition since v1.

## F7 — `hook-forge` (meta, L)
Author, install, and test hooks across ALL event types (PreToolUse/PostToolUse/Stop/SessionStart/Teammate/Task): matcher + script, dry-run, settings.json wiring, verify-it-fires. Every gate in the library today is advisory/skippable — this is the deterministic-enforcement layer ("make render-sanity a non-bypassable Stop hook"). Also fixes SR3's class of problem (hooks that exist but never get wired).

## F8 — `release-cut` (git, M)
Infer the semver bump from conventional commits, bump version fields everywhere (including skill frontmatter + manifests), generate release notes, tag, open the GitHub release. Triple-evidenced internally: RV8 + the three new drift instances in SR13 + the recurring-pain rule. Root-cause companion to SR13's lint check.

## F9 — `autonomy-profile` (loops, M)
Design the scoped permission allowlist + sandbox profile a given loop needs to run unattended: enumerate exact tools/paths, generate the settings block, verify a dry pass never prompts. All 13 loops currently hand-wave this inline; the single biggest unblock for the loops category's walk-away promise.

## F10 — `mcp-server-author` (workflows, M/L)
Scaffold, implement, and smoke-test a stdio MCP server exposing a project's own capabilities to Claude Code, then register it. The toolkit consumes a dozen MCPs and can't build one; natural companion to contract-author (a tool schema is a contract).

## F11 — `incident-response` + `postmortem` (workflows, M + S)
The operate-end pair: a HITL live-incident harness (severity, running timeline, mitigate-before-RCA, approval before prod-touching actions) and the blameless retro whose action items feed plan-intake. Today the only operate-stage skill is autonomous (self-healing-loop) — no human coordination layer, no retro artifact.

## F12 — `memory-curator` (meta, M)
Set up + maintain the auto-memory convention (one-fact-per-file, MEMORY.md index, frontmatter types): dedupe, lint stale entries, verify referenced files/flags still exist. The maintainer already runs exactly this workflow by hand with zero tooling.

## F13 — `notify-on-event` (workflows, S)
Wire PushNotification / SendMessage so long builds and loops ping the user on completion or at HITL gates. Zero PushNotification references exist in the library, yet the loop identity depends on reaching you when it matters. Smallest idea on the list; best effort-to-value ratio.

## F14 — `worktree-fanout` (workflows, M)
Per-agent worktree isolation on the Agent-Teams build path (+ merge-back protocol), upgrading the orchestrator's exclusive-file-ownership from convention to physical impossibility. (`/batch` auto-fanout + repo-cleanup teardown exist; the gap is the manual build path.)

## F15 — `headless-runner` (workflows, M/L)
Package a loop as a non-interactive job: `claude -p` streaming-JSON, exit codes, result parsing, or a thin Agent SDK app — so fix-until-green/self-healing-loop can run in GitHub Actions/cron instead of an open terminal.

## F16 — `routine-manager` (loops, M)
Author/list/monitor scheduled cloud agents generally: routine catalog, "did last night's run actually fire", failure drift. nightly-docs, dependency-health, and self-healing each re-derive scheduling ad hoc; this is the shared substrate.

## F17 — Quality-gates family (bundle)
Seven sibling gate/audit skills, each S–M, pick by appetite: `a11y-audit` (WCAG 2.2/axe — note ux-review/playwright *mention* "accessibility audit" but never run one), `secret-scan-gate` (staged-diff secrets before commit/PR), `license-audit` (SBOM + copyleft + declared-license check — RV2-evidenced), `flake-hunter` (N reruns under jitter; a gate that protects the gates), `threat-model` (pre-build STRIDE), `adr-author` (write/supersede/index ADRs), `load-test` (k6/Locust vs an SLO).

## F18 — Remaining tier-3 ideas (bundle)
`browser-authed-flows` (claude-in-chrome for logged-in testing — all current browser skills are unauthed Playwright), `plugin-packager` (concrete packaging step under F2), `cache-optimizer` (prompt-cache-aware agent prompts + measured cost delta), `feature-flag`, `seed-data-forge`, `human-onboarding`, `i18n-audit`.

---

## Deferred borrows from the 2026-07-06 skills-comparative refresh (`CB-4`–`CB-8`)

The lower-confidence tail of the skills-comparative intake (the committed borrows CB-1–CB-3 live in [`docs/REMAINING-WORK.md`](REMAINING-WORK.md)). Parked here — pulled into the ledger only if a future cycle prioritizes them. Source: the 2026-07-06 skills-comparative refresh (`../DeepResearch/skills-comparative_deepdive/source-material/11-delta-2026-07.md`).

- **CB-4** — **`.out-of-scope/` tombstone KB for Skill-Madness itself.** One note per idea considered and rejected (with reasoning), checked during future intake for dedup-by-concept so rejected ideas aren't re-litigated. Cheap; low urgency. The concrete first step of the "anti-corpus" frontier (F5-adjacent).
- **CB-5** — **ADRs about the library itself** (`.agents/adr/` or `docs/adr/`). `maintain-context` writes ADRs for *target* projects; Skill-Madness keeps none for its *own* design decisions (why 71 skills not 20, why the loops library, why exclusive file-ownership, why PSFS over a 100-line rule). Backfill the load-bearing ones. Overlaps F17's `adr-author` idea.
- **CB-6** — **Enrich `madness` with `ask-matt`-style context-hygiene rules** — keep an alignment→dispatch flow in one unbroken window, name the "smart zone" token budget, distinguish fork (handoff) vs continue-in-place compaction. Minor router polish.
- **CB-7** — **Full issue-tracker abstraction + `to-prd` (chat→PRD) + `to-issues` (vertical slices) + triage state machine** (mattpocock's daily-engineer flow). Big, and our tracker is Beads/Hive; we already have `work-item-brief` + `plan-intake`, so it's speculative — "does this need to exist yet?" If pursued, the tracker-indirection layer + vertical-slicing are the parts that compose with the orchestrator.
- **CB-8** — **Distribution polish: changesets + a published docs site + `npx`-style installer.** Only matters if Skill-Madness goes public; consider publishing to the existing `skills.sh` registry rather than building our own. mattpocock's near-2× star growth rode partly on frictionless install.
