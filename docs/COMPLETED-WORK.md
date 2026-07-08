# Completed Work — Tactical Archive

**Last updated:** 2026-07-07
**Companions:** [`docs/REMAINING-WORK.md`](REMAINING-WORK.md) (open ledger — the to-do list), [`PLAN.md`](../PLAN.md) (strategic roadmap + closure log)

> **What this is.** The append-only tactical archive: every ledger item that reached
> `done`, relocated here verbatim so the open ledger stays lean and cheap to load. This
> is the *tactical* record (per-ID detail); it **complements** — does not duplicate — the
> strategic **closure log** in [`PLAN.md`](../PLAN.md) (one line per wave/milestone close).
> Rows arrive here via the **completion sweep** (see the `living-plan` skill). Never
> summarized on the way in, never deleted — trimming happens by relocation only.
>
> ID prefixes (stable, never reused): `RF` reference-file gaps · `TM` thinking-move
> additions · `PR` process additions · `CL` cleanup · `FA` functional-audit findings ·
> `SR` full-library review findings · `MT` model & effort tiering · `UF` user-feedback
> findings.

---

## Closed 2026-07-07 — plan-intake human-readability + over-build pass (`UF-1`)

User feedback from a live `plan-intake` run on PetriDishOfMadness, hand-added to the open ledger 2026-07-06 and shipped 2026-07-07 on branch `feat/plan-intake-human-readable` (`version 1.1.1 → 1.2.0`). **What shipped:** `plan-intake` Step 4's review table now carries a required jargon-free "What it does / what you'd notice" column written *for the approver*, separate from the terse ledger-native summary written on approval; Step 5 ties the fail-closed gate to that plain-language sentence (shorthand-only rows aren't ready to propose); Step 6 clarifies the ledger-native summary is what lands; and a **YAGNI over-build pass** flags speculative candidates `[speculative]` or routes them to `docs/FUTURE.md` instead of filing them at equal weight. Two new behavior rules ("approver-readable proposals", "filter for over-build"). The `orchestrator role-agent report output` extension noted in the finding was left out of scope. Source: user, 2026-07-06.

- **UF-1** `[done · P1]` — **plan-intake's review table (Step 4/5) is written in the target ledger's insider shorthand, so the human approving it can't tell what the items do.** On the PDoM research-v5 intake the proposed rows read as commit-message jargon ("pure `computeBuildingMesh(recipe,id_hash)` CGA split", "off-replay seam", "EM-155-gated"); the approver's verbatim response was *"none of those are human readable… not sure what any of this would do or change."* That makes the fail-closed approval gate (Step 5) theater — you can only rubber-stamp or bounce. **Fix:** the **review** table must carry a plain-language "what it does / what you'd see change" column written *for the approver*, kept separate from the terse ledger-native summary that gets *written* on approval (Step 6 still adopts the project's format). Require each proposed entry to state, in one jargon-free sentence, the observable change. **Bonus (YAGNI pass):** the user surfaced `DietrichGebert/ponytail` (a 75k-star "lazy senior dev / YAGNI" skill; a sibling `caveman` skill already ships in this library) as the lens — add an over-build check to intake so speculative shortlist directions are flagged *"does this need to exist yet?"* instead of filed at equal weight. The same run proposed 11 items where ~2 were cheap+committed and 4 overlapped already-tracked work. Affects `skills/workflows/plan-intake/SKILL.md` (Steps 4–6); the same readability gap likely applies to orchestrator role-agent report output.

## Closed 2026-07-04 — full-library review (`SR`) + model & effort tiering (`MT`)

The 2026-07-03 full-library review (skill-review Mode A + five parallel review agents) and the approved model & effort tiering proposal, implemented 2026-07-04 by a nine-agent parallel sweep (branch `fix/sr-mt-backlog-sweep`) across three waves + a QE/adversarial gate. Source: `[SRR]` = `skill-review-report.{md,json}` (repo root); `[METP]` = `docs/proposals/2026-07-03-model-effort-tiering-policy.md`. All 25 items gate-verified: catalog 71, lint 0 errors, 343/343 bats, 0 version-drift.

| ID | Finding | What shipped | Closed by |
|----|---------|--------------|-----------|
| **SR1** | H1 — portability claim contradicts frontmatter | Audited all 57 `requires_claude_code:true` flags; flipped 20 host-portable skills (14→**34 of 71** convert); rewrote README claims to match; `convert.sh` now excludes `archive/`+`in-progress/` so the count is exactly right | `fix/sr-mt-backlog-sweep` |
| **SR2** | H2 — CI ran 128 of 317 bats tests | CI installer job runs the full suite via `tests/run-all.sh`; `tests/installer` (172) + `tests/skill-health` now gate merges; five required Ubuntu job names preserved | `fix/sr-mt-backlog-sweep` |
| **SR3** | M1 — skill-health telemetry inert | `install.sh --wire-hooks` opt-in merges the emitter into settings.json (backup, idempotent, refuses malformed JSON); report banners "telemetry inactive" when unwired | `fix/sr-mt-backlog-sweep` |
| **SR4** | M2 — python3 spawned per frontmatter field | `frontmatter.sh` parses each SKILL.md once per process (on-disk cache); full convert ~90s → ~25s (3.7×), byte-identical output on bash 3.2 | `fix/sr-mt-backlog-sweep` |
| **SR5** | M3 — plan/apply under-installs Copilot | plan/apply emit + record the `~/.copilot/agents/` mirror alongside `~/.github/agents/`; uninstall/drift cover both | `fix/sr-mt-backlog-sweep` |
| **SR6** | M4 — `bats tests/` runs zero tests | New `tests/run-all.sh` (`bats -r tests/`); the `1..0` footgun documented in `scripts/README.md` | `fix/sr-mt-backlog-sweep` |
| **SR7** | M5 — skill-explorer omits `loops` | Added `loops` to the location-map brace list + eval fixture | `fix/sr-mt-backlog-sweep` |
| **SR8** | M6 — skill-writer dead link ×2 (×3 found) | Repointed all three `validation-checklist.md` refs by context (SKILL.md:88/:102 + quick-checklist.md:62) | `fix/sr-mt-backlog-sweep` |
| **SR9** | M7 — README documents nonexistent CLI flags | Synced README CLI reference to real script flags (`--tool`, positional path) verified against the scripts | `fix/sr-mt-backlog-sweep` |
| **SR10** | M8 — README "four hooks" undercounts six | Renamed to six hooks + fixed the per-profile map (standard 5, strict 6) from the manifest | `fix/sr-mt-backlog-sweep` |
| **SR11** | M9 — START-HERE/PLAN narrative stale | PLAN closure-log + START-HERE status table record artifact-publish (#42) + find-unknowns (#43) as skills 70/71 | `fix/sr-mt-backlog-sweep` |
| **SR12** | M10 — no lint warn band before the 1024 ceiling | `lint-skills.sh` WARNs >950 chars; orchestrator description trimmed 1023→935 | `fix/sr-mt-backlog-sweep` |
| **SR13** | L1 — version-bump drift ×3 | Bumped interactive-doc, mermaid-charts, model-adaptation; added opt-in `lint-skills.sh --changed` body-diff-without-bump guard | `fix/sr-mt-backlog-sweep` |
| **SR14** | L2 — orphan `body-template.md` | Added to skill-writer's Reference Files list | `fix/sr-mt-backlog-sweep` |
| **SR15** | L3 — madness stale "60 skills" | Count-free phrasing in SKILL.md + eval fixture | `fix/sr-mt-backlog-sweep` |
| **SR16** | L4 — cross-skill paths drop `skills/` prefix | Prefixed context-manager + orchestrator SKILL.md + workflow-orchestration.md + phase-guide.md refs | `fix/sr-mt-backlog-sweep` |
| **SR17** | L5 — self-healing-loop bare `primitives.md` | Added the `loop-controller`'s qualifier every sibling uses | `fix/sr-mt-backlog-sweep` |
| **SR18** | L6 — frontend/qe glob intersection | Tiebreak stated in the ownership map + a glob-intersection WARN check with a documented allowlist | `fix/sr-mt-backlog-sweep` |
| **SR19** | L7 — mermaid-charts eval stale count | Count-free phrasing in the eval fixture | `fix/sr-mt-backlog-sweep` |
| **SR20** | L8 — README "bash ≥4" vs bash-3.2 support | Lowered to bash 3.2+ (matches the macOS CI job + the scripts' idioms) | `fix/sr-mt-backlog-sweep` |
| **SR21** | L9 — README tree omits `hooks/`+`spec/` | Added both to the project-structure tree | `fix/sr-mt-backlog-sweep` |
| **SR22** | L10 — plan-apply contract lags code | Contract's `full` profile updated to 7 categories (added `loops`) | `fix/sr-mt-backlog-sweep` |
| **SR23** | L11 — install-plan silent on missing sources | Warns loudly per missing tool; exits non-zero when all sources absent; success path byte-identical | `fix/sr-mt-backlog-sweep` |
| **SR24** | L12 — no `known_external` allowlist for composes_with | Extended the existing bare-externals allowlist to composes_with/spawned_by (+ artifact-design, dataviz) | `fix/sr-mt-backlog-sweep` |
| **MT-1** | METP — model & effort tiering policy | Canonical section + `references/model-effort-tiering.md` in model-adaptation (priced Anthropic ladder, task→tier map, provider-relativity, guardrails); orchestrator dispatch + workflow-orchestration + loop-controller Step 6 + use-freellmapi all point at it; absorbs the review's `model-router` idea | `fix/sr-mt-backlog-sweep` |

---

## Closed 2026-06-24 — pre-loops backlog clear

The final pre-loops backlog, cleared across the FA-fidelity sweep (PR #32), the class-extraction-guard feature (PR #33), and the backlog-clear pass (PR #34):

| ID | What | Closed by |
|----|------|-----------|
| **FA1** | Doc↔script truth-up (nano-banana `.env` order, sync-skills link-replace claim, security-agent `scan-skills.sh` invocation, deployment-checklist `grep -oP`→`-oE`; mermaid/playwright/living-plan/orchestrator verified accurate) | PR #32 |
| **FA2** | `allowed-tools` + `compatibility` — repo found ~95% already backfilled; completed `design-token-guard` + `class-extraction-guard` | PR #32 / #33 |
| **FA4** | Disambiguation clauses (ui-brief, plan-builder↔living-plan, interactive-doc tokens, skill-explorer↔siblings, git-commit trailer, diagnose-loop↔systematic-debugging, qe-agent↔contract-auditor) | PR #32 |
| **FA5** | Cosmetics (caveman exit phrases, claude-design-brief 13→12, render-sanity phase wording, interactive-doc `conversation_search`) | PR #32 |
| **FA7** | **Decision: drop the `metadata:` block.** Removed from all 14 skills that carried it; routing relies on directory category + description | PR #34 |
| **FA8** | **Decision: keep observability/performance scores advisory.** P0 already reworded them to non-gating "input QE may cite"; no schema/gate change | closed as-is |
| **CL1** | Stale `skill-audit` examples in sync-skills → `skill-review` | PR #32 |
| **CL2** | **Stale-premise: closed not-actionable.** The ledger's "canonical copy moved to `hermes-agent/.claude/skills/`" never happened; the global `~/.claude/skills/fly-hermes` symlink points at a live, populated `claude_docs/fly-hermes` — removing it would orphan a live skill, not tidy. Nothing to remove in-repo | closed (decision) |
| **CL3** | `catalog.sh --check` now validates the README skill-table (one row per disk skill) + reconciled the table to 68 and the per-category prose counts | PR #34 |
| **PR1** | B2/B3/B4 process guidance — iterate-one-change-at-a-time, a required triggering-test, an optional perf-comparison — added to skill-writer + skill-review | PR #34 |
| **PR2** | Changelog discipline — guardrail in contract-author (history → `CHANGELOG.md`, one-line `// — vX.Y.Z` marker only) + `typescript-template.ts` pointer; orchestrator already carried the matching anti-pattern (from #24), cross-linked | PR #34 |

## Closed 2026-05-26 → 2026-06-01 — earlier in this backlog

Full detail in the [`PLAN.md`](../PLAN.md) closure log: **RF1–RF5** + **TM1–TM3** (reference files + thinking moves, 2026-05-26), **FA3** (catalog self-maintaining, PR #23), **FA6** (external namespace correctness, 2026-06-01).
