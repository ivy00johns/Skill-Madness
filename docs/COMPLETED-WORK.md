# Completed Work — Tactical Archive

**Last updated:** 2026-07-09
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
> findings · `RV` offline-window review findings · `MR` maxed-out-window review findings.

---

## Closed 2026-07-09 — maxed-out-window review fixes (`MR-1`–`MR-4`) + nano-banana key resolution (`RV6`)

The 2026-07-08 maxed-out-window review's four P1/P2 fix rows plus one earlier offline-window residual, shipped 2026-07-09 across PRs **#49** (nano-banana v1.4.0 key resolution → RV6), **#51** (loop dispatch wiring + intent→loop routing → MR-1/MR-2; orchestrator 1.15.0→1.16.0, loop-controller 1.1.1→1.2.0, skill-explorer 1.1.1→1.2.0), and **#52** (allowed-tools tooling blind spot + signing-safe fixture → MR-3/MR-4; qwen conversions carry `tools:` in 32/34 files where before 0, copilot fires 34 strip warnings where before 0, lint drops 10 false role WARNs, local suite 344/344 with commit-signing config present). Source: `[MWR]` / `[REV]`.

- **RV6** `[done · P3]` — **nano-banana `.env` lookup order misdescribed.** `SKILL.md:45` documents process env → repo-root `.env` → skill-local `.env`, but `generate_image.py` breaks after the FIRST existing `.env` file, so the skill-local fallback is never read when a repo-root `.env` exists. Drop the per-file `break` (the per-key `os.environ` guard already preserves precedence) or fix the doc. *(Closed by PR #49's broader rewrite: the script now walks every ancestor of the resolved script dir + cwd nearest-first until the key is found, and SKILL.md v1.4.0 documents the real behavior.)*
- **MR-1** `[done · P1]` — **Four build loops claim orchestrator parentage the orchestrator never honors.** `contract-conformance-loop`, `coverage-loop`, `perf-loop`, and `migration-loop` declare `spawned_by: ["orchestrator"]` and their bodies say "or have the orchestrator dispatch it", but zero mentions exist anywhere in `skills/orchestrator/` (SKILL.md + all 11 references) — unlike fix-until-green / loop-controller / orchestrator-task-loop, which are fully wired. Since `disable-model-invocation` hides them from model invocation, an orchestrated build following the playbook never reaches them. Add dispatch text where each earns its keep (contract-conformance at the QA gate, coverage/perf in post-build validation, migration in phase-guide decomposition — the inner-loop story `loop-controller` already tells). Observable change: an orchestrated build can actually dispatch its QE/perf/migration inner loops.
- **MR-2** `[done · P1]` — **No intent→loop routing table backs the front-door promise.** `madness` routes loop intents to `loop-controller` claiming "(it picks the specific loop + primitive)", but loop-controller's contract picks only the *primitive*, and `skill-explorer/references/routing-table.md` — which madness leans on for the long tail — has zero rows for any of the 13 loops. With trigger descriptions hidden by `disable-model-invocation`, roughly two-thirds of the library triggers only if the user already knows the slash name ("keep my PR green" has no documented path to `babysit`). Add a 12-row intent→loop table to loop-controller + matching rows in routing-table.md. Observable change: front-door loop requests land on the right concrete loop without the user knowing its name.
- **MR-3** `[done · P1]` — **The canonical `allowed-tools` frontmatter form is invisible to the shell tooling**, which reads only the deprecated `allowed_tools` alias (all 71 skills use the hyphen). Verified: `convert.sh:526`'s qwen `tools:` mapping is dead code (0 of 34 converted qwen files carry a whitelist); `convert.sh:244`'s copilot strip-warning never fires (field-name mismatch, plus `fm_has_field "owns"` always false — dicts never cached as scalars); `lint-skills.sh:461` false-WARNs all 10 role skills on every run; the README FAQ (~:680) + `scripts/README.md:61` document stderr that cannot occur. Pre-existing since PR #6 — the SR sweep rewrote code on both sides without catching it. Read hyphen-canonical (accept the underscore alias), then truth the docs. Observable change: qwen conversions keep their tool whitelists; lint stops false-warning the roles.
- **MR-4** `[done · P2]` — **SR13's test fixture breaks under commit signing** — the only defect the maxed-out window actually introduced. `tests/installer/bats/05-lint-rules.bats:356` (`_mk_changed_fixture`) sets `user.email`/`user.name` but never `commit.gpgsign false`, so a global 1Password signing config fails `git commit` non-interactively and all 5 `lint --changed` tests (261–265) fail locally (338/343); all 5 pass with `GIT_CONFIG_GLOBAL=/dev/null`. CI unaffected. One-line fixture fix. Observable change: local bats reads 343/343 on signing-configured machines.

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

---

## Closed 2026-07-21 — overnight drain (RV + MA + PF + CB + MR + SO)

The user-authorized overnight run (scope: full drain minus human-gated RV2/CB-10; PRs open for morning review, nothing self-merged). 31 rows closed across six PRs — **#55** (doc polish + MR-8 + CB-2), **#56** (RV16), **#57** (PF1/PF4 + converter hardening), **#58** (MR-5/CB-9), **#59** (MR-6/MR-7/SO-4), **#60** (CB-1). CB-3 deferred with a written reason (new-skill catalog ripple + cross-PR conflicts + review-debt economics — deserves a focused session). Rows verbatim below, status updated:

- **MA-1** `[done · PR #55]` — **`skill-writer/references/performance-notes.md` still teaches the prior-model "anti-laziness" tactic as a broadly-recommended default.** Reframed: prior-model tactic, apply only on a measured truncation failure for the specific skill on the current model; examples marked illustrative-only.
- **MA-2** `[done · PR #55]` — **`model-adaptation`'s model/effort tiering lacks the optimizer/target split evidence.** Optimizer/target split + SkillOpt's ~2× weaker-executor evidence added to the SKILL.md task→tier map and `references/model-effort-tiering.md`; v1.3.0.
- **RV1** `[done · PR #55]` — **living-plan's Reference Implementation misattributes the archive convention.** PetriDishOfMadness now the canonical full-convention example; The Hive re-scoped to front door + strategic doc + intake (predates the two-file split).
- **RV3** `[done · PR #55]` — **README emoji-heading anchors don't resolve.** Nav + inline anchors normalized to GitHub's `#-slug` form; the two double-space emoji headings single-spaced.
- **RV4** `[done · PR #55]` — **reality-gate proposal cites uncommitted evidence.** Workspace paths marked local/gitignored, the 4-run A/B eval outcome inlined, status line reconciled with the two open checkboxes.
- **RV5** `[done · PR #55]` — **claude-design-brief 13→12 sweep incomplete.** Remaining four "13 categories" mentions fixed ("13 frames" artboard math kept); v1.4.2.
- **RV7** `[done · PR #55]` — **use-freellmapi lost its only upstream URL.** Repo URL restored in the body's Local-development pointer; v1.2.1.
- **RV8** `[done · PR #55]` — **PR #34's behavior additions shipped without version bumps.** contract-author → 1.5.0, skill-writer → 1.4.0, skill-review → 1.3.0 (the latter two also carry CB-2's additions under the same bump).
- **RV9** `[done · PR #55]` — **living-plan leaks the `EM-###` prefix.** Now "(every ID'd row)".
- **RV10** `[done · PR #55]` — **living-plan Setup never creates the archive.** Step 2 names `docs/COMPLETED-WORK.md` with the lazy-creation rule.
- **RV11** `[done · PR #55]` — **START-HERE points at the wrong doc for closed-item detail.** Repointed to `docs/COMPLETED-WORK.md`.
- **RV12** `[done · PR #55]` — **PLAN.md's editing note prescribes the pre-sweep procedure.** Rewritten to the completion-sweep relocation rule.
- **RV13** `[done · PR #55]` — **COMPLETED-WORK date range excludes its own row.** Range extended to 2026-06-02.
- **RV14** `[done · PR #55]` — **README references a nonexistent template.** Repointed to `body-template.md`.
- **RV15** `[done · PR #55]` — **living-plan description missing sweep triggers.** Sweep vocabulary added at 1012/1024 chars; v1.2.0 (with RV1/9/10).
- **RV16** `[done · PR #56]` — **orchestrator body over the word guideline.** 6,180 → 5,298 words by giving each triplicated concept one canonical seat (reality gate → DoD 4, source guards → DoD 12, loop mapping → Composition); v1.16.1.
- **PF1** `[done · PR #57]` — **`convert.sh` never ships skills' `scripts/` dirs.** `copy_scripts` wired into all nine per-skill converters (exec bits kept; `__pycache__`/`node_modules`/`.DS_Store` stripped); nano-banana flipped convertible (34→35). website-walkthrough-video's flip deferred: its SKILL.md carries an unrelated uncommitted foreign edit.
- **PF2** `[done · PR #55]` — **`frontmatter-spec.md` defines `requires_claude_code` by the wrong criterion.** Redefined by the runtime-machinery test convert.sh implements; table row matched.
- **PF3** `[done · PR #55]` — **Two hand-maintained "34 of 71" numbers in README drift on any flag change.** `catalog.sh --check/--sync` now compute + guard/rewrite the convertible-subset count (both numbers per phrase).
- **PF4** `[done · PR #57]` — **`madness` converts to non-CC hosts but routes to skills absent there.** On-other-hosts routing note added (route only to skills present; name missing CC-only front doors rather than dead-ending); v1.1.0.
- **PF5** `[done · PR #55]` — **CLAUDE.md "role skills work standalone" reads oddly.** Clarified: standalone *of the runtime*, still orchestrator-dispatched.
- **CB-1** `[done · PR #60]` — **`roles/code-review-agent` is single-lens; give it mattpocock's two-axis structure.** Standards + Spec lanes as isolated sub-agents, twelve named Fowler smells in `references/standards-baseline.md`, never-merge + fail-fast binding rules, QE/security handoffs remapped; v1.4.0.
- **CB-2** `[done · PR #55]` — **Fold mattpocock's `writing-great-skills` craft doctrine into skill-writer + skill-review as checked rules.** Leading-word anchor, delete-no-op-sentences-whole, positive-prompting lint (with the Forbidden:-naming exception) added to skill-writer Step 3 and skill-review's audit checklist.
- **CB-9** `[done · PR #58]` — **Expand–contract sequencing for wide refactors, into `migration-loop` + orchestrator decomposition.** Three-stage mode (expand → migrate in blast-radius batches → contract) with the integration-branch fallback in migration-loop; matching decomposition note in the orchestrator phase-guide.
- **MR-5** `[done · PR #58]` — **Long-run hygiene is inherited only transitively, not wired per-loop.** babysit / self-healing-loop / migration-loop each carry a wired "Long-run hygiene (per loop-controller Step 6)" section; all → 1.1.0.
- **MR-6** `[done · PR #59]` — **Record the caveman/zoom-out keep-despite-upstream-deletion decision durably in-repo.** `docs/adr/0001-keep-caveman-zoom-out.md` is the first ADR (CB-5 convention unparked); ACKNOWLEDGMENTS rows point at it.
- **MR-7** `[done · PRs #58/#59]` — **Doc-drift batch.** (a) disable-model-invocation count 13→27 + disk-truth grep; (b) FUTURE.md CB-7 → `to-spec`/`to-tickets`; (c) caveman lineage contradiction resolved (concept karpathy, implementation mattpocock); (d) stale ACKNOWLEDGMENTS paths annotated + "examples reused" corrected; (e) all five near-ceiling loop descriptions trimmed for headroom.
- **MR-8** `[done · PR #55]` — **Integrate the fable-handoff artifacts into `model-adaptation`.** `scripts/extract_operating_manual.py` + `references/operating-manual.md` + new `references/capability-handoff.md`; trigger keywords added; the three unconfirmed API claims resolved against live docs (adaptive-on-Opus confirmed, stop_details shape confirmed, flat 4,096 cache minimum refuted — Opus 4.8 is 1,024); model-adaptation v1.3.0.
- **SO-4** `[done · PR #59]` — **No split-hygiene standard for any future skill scoring.** Shipped as `docs/standards/eval-split-hygiene.md` (stable hashing, touch-once test set, synthetic-train-only, multi-trial deltas); F5 points at it.
- **SO-5** `[done · PR #55]` — **`loop-controller` guardrail docs lack the strongest cautionary case for accept/reject gates.** The −52.8pt ungated SearchQA collapse added as a named example in `references/safety.md`; v1.2.1.
- **SO-6** `[done · PR #55]` — **Portability docs assert single-source-is-better without a cautionary counter-example.** SkillOpt's five-bespoke-integrations sprawl cited in the README portability section.
