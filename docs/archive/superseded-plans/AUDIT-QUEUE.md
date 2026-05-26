# Skill Audit Queue

Working doc for the multi-session OSS audit. **Not committed.** Delete when the
audit campaign is complete.

## How to use

- Work top-down. Each row is one skill to review.
- Mark `[x]` in the Status column when a skill is approved (no further action),
  or write a short note ("rewrite triggers", "merge into X", "drop") if it
  needs more work.
- Sessions don't need to follow tier boundaries — pick a chunk that fits the
  session length you have. The "Suggested session" column groups skills that
  go together.
- For each review, check the seven items in the **Per-skill checklist** at
  the bottom of this file.

## Review modes

| Mode | What runs | Effort |
|---|---|---|
| **Deep** | Full `/skill-creator` — eval cases, with-skill vs baseline, viewer review, iterate | 30–60 min |
| **Review** | `skill-deep-review` — structural + trigger-eval + 2 test prompts, no iteration | 10–15 min |
| **Bulk** | `skill-audit` across many at once — frontmatter, owns-overlap, description quality | Seconds (batched) |

---

## Tier 1 — Deep (3 skills) — define how the ecosystem feels

Suggested session: 1 (heaviest)

| Status | Skill | Path | Lines | Notes |
|---|---|---|---|---|
| [x] | orchestrator | `skills/orchestrator/SKILL.md` (+ 4 refs) | 193 | Audited 2026-04-29. v1.3.0→1.4.0. Removed 2 dead "design spec §6" refs, added playwright + git-pr-feedback to composes_with, mentioned playwright in Phase 11 smoke tests, added PR review handoff to Phase 14. Description already strong. |
| [x] | qe-agent | `skills/roles/qe-agent/SKILL.md` | 210 | Audited 2026-04-29. v1.2.0→1.3.0. Description strengthened to emphasize QA gate ownership and add trigger keywords (qa gate, contract diff, adversarial probing, block the build). All references valid, schema/rubrics/checklist consistent, tests/performance/ carve-out for performance-agent documented correctly. |
| [x] | contract-author | `skills/contracts/contract-author/SKILL.md` (+ 6 templates) | 199 | Audited 2026-04-29. v1.1.0→1.2.0. Description now lists all 6 template formats (OpenAPI/AsyncAPI/Pydantic/TypeScript/JSON Schema/data-layer YAML) and explicitly positions skill as orchestrator Phase 4. All 6 templates exist (openapi 251, data-layer 150, pydantic 142, asyncapi 110, typescript 98, json-schema 87 — all <300, no ToCs needed). No conflicts with contract-auditor (zero ownership). |

---

## Tier 2 — Review (10 skills) — high-impact roles + meta

Suggested sessions: 2 (5 skills) + 3 (5 skills)

| Status | Skill | Path | Lines |
|---|---|---|---|
| [x] | backend-agent | `skills/roles/backend-agent/SKILL.md` | 151 | Audited 2026-04-29. v1.1.0 — no edits. Owns src/api,services,models,middleware,utils — matches orchestrator map. validation-checklist exists. db-migration & observability boundaries documented in coordination rules. |
| [x] | frontend-agent | `skills/roles/frontend-agent/SKILL.md` | 116 | Audited 2026-04-29. v1.1.0 — no edits. Owns src/components,pages,hooks,styles,public — matches orchestrator map. CORS hand-off to backend documented. validation-checklist exists. |
| [x] | infrastructure-agent | `skills/roles/infrastructure-agent/SKILL.md` | 90 | Audited 2026-04-29. v1.1.0 — no edits. Shortest role skill but covers Docker/compose/CI-CD/k8s/terraform. Coordination with deployment-checklist + observability-agent documented. validation-checklist exists. |
| [x] | security-agent | `skills/roles/security-agent/SKILL.md` | 140 | Audited 2026-04-29. v1.1.0 — no edits. Owns SECURITY.md/.github/security/. owasp-checklist.md exists. Static-vs-runtime split with qe-agent and security-vs-quality split with code-reviewer both documented. |
| [x] | contract-auditor | `skills/contracts/contract-auditor/SKILL.md` | 167 | Audited 2026-04-29. v1.1.0 — no edits. Zero ownership (read-only diff role) — no conflict with contract-author's contracts/ ownership. Static-analysis vs runtime-verification split with qe-agent documented. pact-setup.md reference exists. |
| [x] | plan-builder | `skills/workflows/plan-builder/SKILL.md` | 230 | Audited 2026-04-29. v1.1.0→1.2.0. **FIXES**: incomplete frontmatter (added requires_agent_teams, min_plan, owns, allowed_tools); typo "Ingestionu" → "Ingestion". No references directory needed (content fits in 230 lines). |
| [x] | skill-writer | `skills/meta/skill-writer/SKILL.md` | 129 | Audited 2026-04-29. v1.1.0 — no edits. Both references (frontmatter-spec, description-patterns) exist. requires_claude_code: false (correct — markdown-only skill). |
| [x] | project-profiler | `skills/meta/project-profiler/SKILL.md` | 123 | Audited 2026-04-29. v1.1.0 — no edits. profile-schema.yaml reference exists. v1.1 conflict resolution for CLAUDE.md ownership documented. |
| [x] | code-reviewer | `skills/meta/code-reviewer/SKILL.md` | 138 | Audited 2026-04-29. v1.1.0 — no edits. review-rubric.md exists. Routes findings to qe-agent/security-agent/orchestrator with documented boundaries. wiki-research wiki-first protocol referenced. |
| [x] | context-manager | `skills/workflows/context-manager/SKILL.md` | 106 | Audited 2026-04-29. v1.1.0 — no edits. compaction-guide.md exists. Owns .claude/handoffs/ — consistent with orchestrator's handoff-protocol.md. v1.1 conflict resolution documented. |

---

## Tier 3 — Review (5 skills) — specialized roles

Suggested session: 4

| Status | Skill | Path | Lines | Notes |
|---|---|---|---|---|
| [x] | db-migration-agent | `skills/roles/db-migration-agent/SKILL.md` | 114 | Audited 2026-04-29. v1.1.0 — no edits. Owns migrations/seeds/prisma/alembic. migration-checklist.md exists. Boundary with backend-agent's src/models/ documented. |
| [x] | docs-agent | `skills/roles/docs-agent/SKILL.md` | 102 | Audited 2026-04-29. v1.1.0 — no edits. Owns docs/, README.md, CHANGELOG.md, CONTRIBUTING.md. doc-templates.md exists. Phase 14 deliverable role documented. |
| [x] | observability-agent | `skills/roles/observability-agent/SKILL.md` | 118 | Audited 2026-04-29. v1.1.0 — no edits. Owns src/telemetry/, src/logging/, monitoring/, alerts/. monitoring-patterns.md exists. Backend boundary (import vs modify) clearly documented. |
| [x] | performance-agent | `skills/roles/performance-agent/SKILL.md` | 123 | Audited 2026-04-29. v1.1.0 — no edits. Owns tests/performance/, load-tests/ — carve-out from qe-agent's tests/ explicit. Both k6-patterns.md and neoload-patterns.md exist. |
| [x] | deployment-checklist | `skills/workflows/deployment-checklist/SKILL.md` | 76 | Audited 2026-04-29. v1.1.0 — no edits. Brevity is intentional — main checklist lives in references/pre-deploy.md. Coordination with qe-agent (gate prereq) and infrastructure-agent (output validator) documented. |

---

## Tier 4 — Bulk (13 skills) — workflows + meta tooling

Suggested session: 5 (run `skill-audit` once, then triage)

| Status | Skill | Path | Lines | Notes |
|---|---|---|---|---|
| [x] | mermaid-charts | `skills/workflows/mermaid-charts/SKILL.md` | 459 | Audited 2026-04-29. v2.0.0→2.1.0. **FIX**: incomplete frontmatter — added requires_agent_teams, requires_claude_code (false — markdown-only), min_plan, owns, allowed_tools, spawned_by. composes_with already comprehensive (9 skills). |
| [x] | nano-banana | `skills/workflows/nano-banana/SKILL.md` | 122 | Audited 2026-04-29. v1.0.0→1.1.0. **FIX**: incomplete frontmatter — added requires_agent_teams, min_plan, owns, allowed_tools, spawned_by. requires_claude_code: true preserved (Bash needed for Gemini API). |
| [x] | playwright | `skills/workflows/playwright/SKILL.md` | 262 | Audited 2026-04-29. v1.0.0→1.1.0. **FIX**: composes_with referenced non-existent "ux-review" — removed. Other entries (qe-agent, frontend-agent, deployment-checklist) all valid. |
| [x] | railway-deploy | `skills/workflows/railway-deploy/SKILL.md` | 238 | Audited 2026-04-29. v1.0.0→1.1.0. **FIX**: incomplete frontmatter — added requires_agent_teams, min_plan, owns (patterns: railway.toml), allowed_tools, spawned_by. |
| [x] | sync-skills | `skills/workflows/sync-skills/SKILL.md` | 127 | Audited 2026-04-29. v2.0.0 — no edits. Owns own skill directory (canonical for installer logic). composes_with skill-updater + skill-audit valid. |
| [x] | repo-deep-dive | `skills/workflows/repo-deep-dive/SKILL.md` | ~240 | Audited 2026-04-29. v1.1.0 — confirmed clean post-rewrite. No private paths. requires_claude_code: true (uses subagents for parallelization). |
| [x] | settings-consolidator | `skills/workflows/settings-consolidator/SKILL.md` | 235 | Audited 2026-04-29. v1.1.0 — confirmed clean post-rewrite. /Users/you/myproject placeholder verified. |
| [x] | llm-wiki | `skills/workflows/llm-wiki/SKILL.md` | 193 | Audited 2026-04-29. v1.1.0 — confirmed clean post-rewrite. requires_claude_code: false (LLM-agnostic). composes_with wiki-research, repo-deep-dive, project-profiler, mermaid-charts all valid. |
| [x] | wiki-research | `skills/meta/wiki-research/SKILL.md` | ~135 | Audited 2026-04-29. v2.1.0 — confirmed clean post-rewrite. No hardcoded private paths. requires_claude_code: false. spawned_by includes 8 callers — broadest of any skill. |
| [x] | skill-audit | `skills/meta/skill-audit/SKILL.md` | 189 | Audited 2026-04-29. v1.1.0→1.2.0. **FIX**: 5 dead "design spec" / "skill-ecosystem-design-spec.md" references in body and audit-checklist.md — repointed to docs/architecture.md, CLAUDE.md, and orchestrator phase-guide. |
| [x] | skill-deep-review | `skills/meta/skill-deep-review/SKILL.md` | 129 | Audited 2026-04-29. v1.1.0 — no edits. Frontmatter complete. composes_with skill-writer/skill-audit/skill-improvement-plan valid. |
| [x] | skill-improvement-plan | `skills/meta/skill-improvement-plan/SKILL.md` | 141 | Audited 2026-04-29. v1.1.0 — no edits. Frontmatter complete. Composition with skill-deep-review/skill-audit/skill-updater forms a clean self-management chain. |
| [x] | skill-updater | `skills/meta/skill-updater/SKILL.md` | 141 | Audited 2026-04-29. v1.1.0 — no edits. Frontmatter complete. allowed_tools includes Agent (for batch subagent edits — appropriate). |

---

## Tier 5 — Bulk (5 skills) — git workflow

Suggested session: 5 (same as Tier 4)

| Status | Skill | Path | Lines |
|---|---|---|---|
| [x] | git-commit | `skills/git/git-commit/SKILL.md` | 106 | Audited 2026-04-29. v1.1.0→1.2.0. **FIX**: incomplete frontmatter — added requires_agent_teams, requires_claude_code (false — pure git workflow), min_plan, owns, allowed_tools (Read+Bash), spawned_by. |
| [x] | git-pr | `skills/git/git-pr/SKILL.md` | 128 | Audited 2026-04-29. v1.1.0→1.2.0. **FIX**: incomplete frontmatter — same 6 fields added. requires_claude_code: false. allowed_tools: Read+Bash (gh CLI). |
| [x] | git-pr-feedback | `skills/git/git-pr-feedback/SKILL.md` | 186 | Audited 2026-04-29. v1.1.0→1.2.0. **FIX**: incomplete frontmatter — added 6 fields. allowed_tools: Read, Write, Edit, Bash, Grep (handles code edits responding to review). |
| [x] | git-branch-cleanup | `skills/git/git-branch-cleanup/SKILL.md` | 157 | Audited 2026-04-29. v1.1.0→1.2.0. **FIXES**: incomplete frontmatter (added 6 fields); composes_with extended to include git-clean-worktrees (natural pairing). |
| [x] | git-clean-worktrees | `skills/git/git-clean-worktrees/SKILL.md` | 189 | Audited 2026-04-29. v1.0.0→1.1.0. **FIXES**: incomplete frontmatter (added 6 fields); removed 2 external `superpowers:` plugin references from composes_with — those skills are not in OSS bundle. |

---

## Per-skill checklist

For every review (Deep, Review, or Bulk), confirm:

1. **No personal data.** Grep for `/Users/johns`, `the-hive-ecosystem`, `DeepResearch`, `john00ivy`, `Key Madness`, `MarketsBeRigged`. None should appear.
2. **Frontmatter compliance** — matches `skills/meta/skill-writer/references/frontmatter-spec.md`. Required: `name`, `version`, `description`. Role/agent skills also need `owns`, `allowed_tools`, `composes_with`, `spawned_by`.
3. **Description triggers.** "Pushy" enough to combat under-triggering — action verbs, specific contexts, keyword variations. No vague single-sentence descriptions.
4. **Cross-platform language.** No "use the Read tool" / "use the Bash tool" — describe the capability ("read the file", "run the command"). `requires_claude_code` should be `false` unless the skill genuinely needs CC-specific features (subagents, EnterPlanMode, etc.).
5. **Length.** SKILL.md body under 500 lines. References >300 lines have a ToC at the top.
6. **Owns / composes_with consistency.** No two role skills own overlapping directories. `composes_with` references real skill names that exist.
7. **Functional test (Tier 1–3 only).** Run a representative test prompt — does the skill trigger? Does the output match expectations?

## Decisions to capture as you go

A `decisions.md` running log isn't needed for individual skills, but flag any of these in this file's notes columns:

- Skill that's redundant with another → recommend merging
- Skill that's a thin wrapper → recommend dropping
- Reference file that's too short to deserve its own file → recommend folding back into SKILL.md
- Skill that needs new references / scripts created
- Cross-platform issue that requires a meaningful rewrite, not just a tweak

## When the queue is empty

1. Run `skill-audit` one final time across all 36 skills as a regression check.
2. Update CLAUDE.md and README.md to reflect any final structural changes.
3. Move to Phase 4: cut the new clean-history OSS repo.
