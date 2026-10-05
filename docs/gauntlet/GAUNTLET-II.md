# THE GAUNTLET II — BAZAAR II: The Reckoning

A single, pre-registered, instrumented dogfood brief engineered to legitimately invoke the whole Skill-Madness library in one continuous build, and to serve as the acceptance test for the GPT-6.1 Sol universal-audit fix wave.

This document supersedes the stale `claude_docs/THE-GAUNTLET.md`. That file named archived skills (`skill-audit`, `skill-deep-review`, `git-branch-cleanup`, `git-clean-worktrees`) and a Claude-global harness (superpowers, claude-mem, ui-ux-pro-max) this repository no longer ships. Gauntlet II is self-contained, host-aware, and evidence-producing.

> **Status:** Phase 1 is this document plus the harness under `docs/gauntlet/` and `scripts/gauntlet/`. Phase 2 — the actual run — starts only after the UA-01…UA-32 refactor lands and the owner chooses to run it.

---

## 1. Why this exists

The 2026-10 universal audit (`docs/reviews/2026-10-universal-audit/`) closes on one admission: the library's per-skill triggering, task efficacy, and safe degradation across hosts are **UNVERIFIED**. Its refutation pass also reproduces the concrete failure shape:

- host-neutral frontend doctrine locked behind a Claude-only dispatch gate;
- guards a model can satisfy literally while defeating their purpose;
- copied chrome no gate detects.

Gauntlet II converts "the library is mature" into a measured claim. Every trap in it is also a test of a specific UA fix, so one run exercises the collection and proves the repairs.

## 2. How to run it

1. Bootstrap a clean Bazaar II worktree at `.workspaces/gauntlet-ii/` (own git repository, own branch).
2. Set `ATS_HOOK_PROFILE=strict` so skill-usage telemetry, `qa-gate`, and `pre-commit-lint` are active.
3. Inject the trap fixtures (`scripts/gauntlet/trap-inject.sh`) and freeze verifier/config hashes.
4. Paste this file into a fresh Claude Code session as the operating brief, with broad-but-consented permissions and auto mode on.
5. After the run, execute `scripts/gauntlet/trap-verify.sh`, merge the trace, and score.

The primary cell is Claude Code (full orchestrator, parallel roles, hooks, QA gate). The secondary cell is Freebuff/DeepSeek (no subagents), which exercises the sequential/attended path and the capability resolver.

## 3. Pre-registration (locked before the run)

These are fixed before execution so the run cannot quietly rewrite its own success criteria.

- **Falsifying result:** if a must-fire skill does not fire on its legitimate trigger in Phase 4 through Phase 6, that is a finding, not a nuisance. The run is designed to surface it.
- **Acceptance = outcome + proof + architecture.** Trajectory (calls, seconds, cost) only explains; it never substitutes. A `null` cost means unknown, never zero.
- **Scope is bounded on purpose.** The old Gauntlet's four-figure-line scope is ungovernable; a run that cannot finish produces no evidence. Bazaar II is deliberately six to eight routes and three services.
- **No paid model batch, no production deploy, no real money, no global installs, no permission changes** without separate approval.
- **Frozen inputs:** verifier scripts, config, and datasets are hashed before the run; workers cannot edit them.

## 4. The product: Bazaar II

A real-time, multi-tenant marketplace fusing auction, escrow ledger, social timeline, and fraud scoring — chosen because it forces every skill category: real ledger math, realtime concurrency, multi-tenant authz, a multi-page design system, a staged migration, and a performance hotpath.

| Layer | Choice | Why this choice |
|---|---|---|
| API | TypeScript / Fastify | triggers backend, contract, observability, performance roles |
| Frontend | React + Vite, multiple authored pages, one design-token file, one shared shell | triggers the frontend role and both UI guards plus the shared-layout gap |
| Data | Postgres + Redis via Docker, lightweight in-process queue | portable and unpaid; triggers db-migration and dependency coordination |
| Realtime | WebSockets on the bid and comment hotpath | forces concurrency reasoning and observability |
| Payments | simulated double-entry escrow ledger | forces real money math with no live rail |
| Fraud | Claude-API-shaped scoring service, deterministic stub plus optional guarded real call | exercises model-adaptation and the fraud boundary contract |
| Deploy | Docker Compose locally; Railway config generated and validated but not deployed | exercises infrastructure and the deployment checklist in dry mode |

The frontend is one shared shell (header, navigation, footer) rendered into every authored route, responsive at two widths, with a design-token file as the single source of style values.

## 5. Instrumentation

Run under the strict hook profile so `skill-usage` telemetry, `qa-gate`, and `pre-commit-lint` all fire. Every skill invocation is captured as one JSONL record (see `trace-schema.json`) and reconciled against the pre-registered expectations in `coverage-matrix.md`.

- `scripts/gauntlet/trace-merge.py` merges host skill-usage telemetry with tool-call logs into a single trace, then reports every must-fire skill that produced no record.
- `scripts/gauntlet/trap-verify.sh` checks each seeded trap and reports **BLOCKED, not PASS**, wherever a checker could not read its input.
- `scripts/gauntlet/score.py` consumes the trace plus gate receipts and emits the scored report and the `[G2]` intake table.

## 6. The trap catalog

Eleven benign, reversible fixtures are seeded into Bazaar II. Each is also the acceptance test for a UA row. The full detail — exact injection point, guard path:line, expected terminal state, and UA mapping — lives in `trap-catalog.md`.

| Trap | Seeded failure shape | Guard under test | UA rows |
|---|---|---|---|
| T1 | first pages built with no frontend role and no standalone entry | frontend solo mode | UA-01 |
| T2 | inline HTML `style=` carrying width and layout | design-token-guard default parser | UA-04, UA-05, UA-31 |
| T3 | hash-named classes hiding duplicated declaration blocks | class-extraction-guard equivalence | UA-06 |
| T4 | header and footer pasted into every authored page | shared-layout guard | UA-07 |
| T5 | the same brief replayed on a host with no subagents | sequential orchestrator plus capability detection | UA-02, UA-03 |
| T6 | a loop permitted to run on prompt-only budget | external budget enforcement | UA-13 |
| T7 | a worker weakens a test, narrows coverage, or edits the verifier | frozen criteria, gate-gaming resistance | UA-14 |
| T8 | a QA report reused across revisions; validator clean on unreadable input | fail-closed QA, revision binding | UA-12 |
| T9 | parallel dry-run that writes; nested and exec-bit resources; stale source hash; destination escape | converter and installer correctness | UA-08, UA-10, UA-11, UA-21 |
| T10 | two candidate descriptions plus an unseen holdout | skill-creator eval honesty | UA-17, UA-18, UA-19 |
| T11 | adaptation requested under an unknown or GPT cell | model-adaptation provider drafts | UA-15, UA-16 |

A trap that stays green means no rule exists. That result is reported, not smoothed over.

## 7. Coverage matrix

All 76 on-disk skills are enumerated in `coverage-matrix.md`, derived from the filesystem rather than from the docs, each with a phase, a legitimate trigger phrase, a must-fire flag, and a near-miss negative control that must not fire. The near-miss controls are how over-triggering on the pushy descriptions is measured.

## 8. Phases

| Phase | Name | What happens |
|---|---|---|
| Pre-flight | Prepare | bootstrap worktree, strict hooks, create the workspace, inject traps, freeze hashes |
| 0 | Discovery | project-profiler, two to three deep-dives, LLM wiki, wiki-research |
| 1 | Plan | grill-me and find-unknowns feed plan-builder; mermaid-charts draws the architecture |
| 2 | Contracts and assets | contract-author for REST and event bus and ledger and fraud boundary; ui-brief; nano-banana |
| 3 | Orchestrated build | orchestrator dispatches roles in parallel; fix-until-green, coverage-loop, perf-loop, contract-conformance-loop |
| 4 | Verify | contract-auditor, code-review-agent, security-agent, render-sanity, playwright, trap-verify |
| 5 | Second cell | Freebuff/DeepSeek replay of the portable subset plus host-friction log |
| 6 | Ship (dry) | deployment-checklist, the git four, babysit |
| 7 | Operate | self-healing-loop, dependency-health-loop, nightly-docs-and-changelog, migration-loop, codebase-exploration-loop |
| 8 | Harvest | skill-review and skill-update against the run; skill-writer for any real gap; skill-creator to test it; plan-intake for `[G2]` rows |
| 9 | Tidy | repo-cleanup-loop; confirm the old Gauntlet doc is deprecated |

If a phase is skipped, that is data. Record every moment a skill is reached for that does not exist, every awkward overlap, and every description that fails to trigger when it obviously should.

## 9. Scoring

Scoring follows `scoring-rubric.md`: the audit's four eval layers (resource and load smoke, trigger selection, efficacy, safety and degradation) graded on four separate axes (outcome, proof, architecture, trajectory), with the nine disqualifiers applied. Cells are scored separately and never blended into one universal number.

## 10. Definition of done

- The coverage matrix is filled: every must-fire skill either fired with a legitimate trigger or is reported as a miss, with near-miss controls also reported.
- `trap-verify.sh` shows the expected catch or no-catch for every trap, with BLOCKED wherever input was unreadable.
- Bazaar II runs end to end locally (auctions, escrow, realtime, fraud) with the pipeline green.
- Both cells produce a trace and a friction log, scored separately.
- A scored `report.md` and a `[G2]` intake proposal exist, including at least one real skill gap written up.
- Every uncaught trap or missed firing is filed as an intake row.
- Nothing lands on `main` without explicit approval.

## 11. Guardrails

- Nothing lands on Skill-Madness `main`, or any real remote, without explicit approval. Bazaar II owns its own branch and worktree.
- No paid model batch, no production deploy, no real money, no global installs, and no permission changes without separate approval.
- Verifier, config, and dataset hashes are frozen before the run; workers cannot edit them.
- A `null` cost means unknown, never zero.
- All traps are benign and reversible; the raw trace stays in the gitignored workspace.

## 12. Operator notes

The goal is not to ship a real marketplace. The goal is to engineer one brief that a healthy skill ecosystem answers by firing every relevant skill in coherent sequence, and to record — with evidence — everything it misses. A phase that is skipped, a skill that under-triggers, or a guard that a model satisfies literally while defeating its purpose is the product, not a failure of the exercise.
