# Skill-Madness Full Upgrade Plan — 2026-08-06

## 1. Executive Summary

The sweep returned 27 verdict rows against a 26-repo brief (the off-by-one is unreconciled — **unverified**): **12 CONFIRMED_LINEAGE, 15 NO_LINEAGE**. Real lineage is a minority, and two of the twelve are inverted — SM is *upstream* of The-Hive, and ECC was mis-tiered as noise when it is in fact the named design model for five shipped `contracts/` subsystems. The two decisions that matter most are upstream *reversals*, not new borrows: mattpocock retired `productivity/grill-me` to a stub and **reversed** "one question at a time" into a round-based frontier, and deleted `writing-great-skills` in favour of `writing-for-agents`, whose "context pointer" concept is a sharper restatement of SM's own pushy-description doctrine — SM currently ships a dead citation to the deleted skill and an ACKNOWLEDGMENTS row crediting a constraint upstream has since disowned. Three findings are functional, not cosmetic: SM installs Antigravity skills to a path Antigravity stopped reading on 2026-07-01, `use-freellmapi` Step 3 hands agents a CLI invocation that hard-fails in every non-TTY session, and `lint-skills.sh:450` pipes whole SKILL.md bodies into `grep -qF` under `pipefail` (the WC-1 `$ARGUMENTS` check — nondeterministically wrong today, not latent). ACKNOWLEDGMENTS.md omits **seven** upstreams that shipped code or standards into SM (freellmapi, pxpipe, SkillOpt, harness-engineering, ai-website-cloner-template, ponytail, ECC) while the four debts it *confesses* (orchestrator, contract-first architecture, role-agents, QA-gate) remain unanswerable from this corpus entirely. The pxpipe image-proxy matrix has now rotted twice; the fix is to stop mirroring it, not to refresh it. Three separately-scored "high" borrows (agency-agents `check-tools.sh`, last30days doc-contract test, ratel `--list`) are one mechanism against one target — CLAUDE.md's hand-maintained name lists, the class `catalog.sh --check` has now missed four times — and must be intaken as a single consolidated work item. Coverage is incomplete in two named ways: seven repos had dirty working trees (reviewed at stale HEAD or not at all), and `skills/contracts/` received **zero** of 72 borrows despite being the exact debt ACKNOWLEDGMENTS confesses.

## 2. Lineage Map

### CONFIRMED_LINEAGE (12)

| Repo | Evidence (short) | What SM owes it |
|---|---|---|
| **mattpocock/skills** | Dedicated ACKNOWLEDGMENTS section (`:67-124`) with MIT text + 8-row derivation table; inline credits in `caveman/SKILL.md:20`, `diagnose-loop/SKILL.md:20`, `code-review-agent/references/standards-baseline.md:9`, `migration-loop/SKILL.md:187`; ADR 0001; fidelity audit pinned to upstream `d574778` | Credited. Owes: 4 stale pointers/claims (C-1…C-4) and an adopt/decline on the grilling reversal |
| **anthropics/skills** | ACKNOWLEDGMENTS `:35-52`; runtime dependency — `skill-review/SKILL.md:15` composes with `skill-creator:skill-creator` and delegates trigger testing to it; `AGENTS.md:7` overrides its workspace behavior; `ui-brief`/`claude-design-brief` reference `frontend-design:frontend-design` | Credited. Owes: three PSFS misstatements (C-5…C-7) that misattribute non-Anthropic fields to the Anthropic spec |
| **multica-ai/andrej-karpathy-skills** | ACKNOWLEDGMENTS `:153-198` incl. lineage disambiguation; the "opening tradeoff caveat" pattern verifiably present in exactly the six named skills | Credited and accurate. Nothing owed |
| **msitarzewski/agency-agents** | Verbatim code survives: `get_body()` byte-identical, `slugify()` functionally identical, `detect_copilot()` character-for-character, redraw helper verbatim from pre-PR-#567; credited in 4 script headers + README `:532,:748` + ACKNOWLEDGMENTS `:205-260` | Credited. Owes: two functional regressions inherited from the fork point (C-9, C-10) |
| **teamchong/pxpipe** | `use-pxpipe/SKILL.md:30` links it; `PX` ledger prefix; PX-1/2/3 closed | Credited in-skill, **absent from ACKNOWLEDGMENTS**. Owes: 6 stale facts + a mirrored matrix that has rotted twice |
| **tashfeenahmed/freellmapi** | 983-line skill entirely about it; 6 more SM files depend on it; RV7 in the ledger | Credited in-skill, **absent from ACKNOWLEDGMENTS**. Owes: an invocation that fails for agents |
| **DietrichGebert/ponytail** | Credited 3× in `yagni-gate/SKILL.md` body; CB-3 row; rename logged in PLAN.md `:73` | Credited in-skill, **absent from ACKNOWLEDGMENTS**. Owes: an entry + the unbuilt marker harvest |
| **microsoft/SkillOpt** | `[SO]` ledger prefix; `docs/standards/eval-split-hygiene.md` ported from it; cited in 8+ files incl. `safety.md:104` and `README.md:505` | **Absent from ACKNOWLEDGMENTS** despite a ported standard. Owes: a corrected plugin count |
| **lopopolo/harness-engineering** | `HE` ledger prefix; HE-1/HE-2 closed; F5 prose sourced by filename. CC BY 4.0 with a published attribution string | **Absent from ACKNOWLEDGMENTS**, and CC BY asks for it. Owes: attribution + "changes were made" note |
| **The-Hive** | Derivation runs **SM → The-Hive** (SM first commit `16d6d64` 2026-03-10 vs Hive `93498ca` 2026-03-20; Hive commits name "ATSA"/"Skill-Madness" explicitly). SM's genuine narrow debt: `living-plan/SKILL.md:160` + `plan-intake/SKILL.md:58` | Already correctly scoped by RV1. **Do not credit as a general source** — that mistake was made once and fixed |
| **JCodesMore/ai-website-cloner-template** | `WC` ledger prefix; WC-1 shipped at `lint-skills.sh:441-451`, WC-2 at `agent-spawning.md:65,69` | **Absent from ACKNOWLEDGMENTS** (MIT © JCodesMore). Owes: a false `hosts.yaml` citation in FUTURE.md |
| **ECC (Everything Claude Code)** | Five `contracts/` files name ECC scripts as their model; derived SM code shipping (`install-plan.sh`, `catalog.sh`, `scan-skills.sh`, `skill-health.sh`, `hooks.manifest.json`); PRs #8/#9 | **Absent from ACKNOWLEDGMENTS** (MIT © Affaan Mustafa). Effectively tier-1, was mis-tiered as noise |

### NO_LINEAGE (15) — co-located clones, research subjects, or downstream

`davidondrej/skills`, `ratel`, `9router`, `OpenSwarm`, `last30days-skill`, `hermes-agent`, `Clauge`, `beads`, `gastown`, `gstack`, `overstory`, `multica-ai/multica`, `paperclip`, `ruflo-src`, `deer-flow`.

Notes worth keeping: `hermes-agent` and `Clauge` derive *from* the SM ecosystem, not into it (`fly-hermes` is SM-authored and copied into the hermes clone). `beads`, `gastown`, `gstack`, `overstory` appear only as **eval-prompt subjects** and deep-dive material — that is why four of the stale-artifact rows land in `mermaid-charts/evals/evals.json`. `davidondrej/skills` owes zero attribution *today*; taking its borrows creates the obligation (see Decision 7).

**Honest read:** 12 of 27 are real lineage, and only 4 of those (mattpocock, anthropics, karpathy, agency-agents) are currently credited. The remaining 15 are a research corpus that produced good borrows and zero derivation.

## 3. Corrections Required

Each row is ledger-ready. **C-1…C-8 are wrong statements in shipped/spec files. C-9…C-15 are functional. C-16…C-23 are stale facts in shipped skills. C-24…C-30 are attribution and record-keeping.**

| ID | File | What's wrong | Fix |
|---|---|---|---|
| C-1 | `skills/meta/skill-review/references/audit-checklist.md:119` | Cites `writing-great-skills`, deleted upstream (`D skills/productivity/writing-great-skills/SKILL.md` in `d574778..HEAD`). The three rules survive; only the pointer is dead | Repoint to `productivity/writing-for-agents`; land with UL-16 |
| C-2 | `ACKNOWLEDGMENTS.md:87` | Credits `productivity/grill-me` with "one question at a time … Depth-first design-tree walk". Upstream `grill-me` is now an 8-line alias; `productivity/grilling` asserts the opposite (round-based frontier) | Rewrite the row to cite `productivity/grilling`, state which constraints survived (recommend-then-ask, ask-code-not-user) and which upstream reversed. Gated on Decision 1 |
| C-3 | `skills/workflows/caveman/SKILL.md:20` | "Same behavior, same examples" — contradicted by `ACKNOWLEDGMENTS.md:90` ("Our examples are original") and by upstream's deletion of `productivity/caveman` (`7d3ada9`). MR-7d fixed only the acknowledgments side | Bring the skill body in line with the acknowledgments text |
| C-4 | `skills/workflows/architecture-rescue/references/architecture-language.md:5` | "modeled on mattpocock's `LANGUAGE.md`" — no such file at HEAD or at the v1.1.0 baseline | Repoint to `skills/engineering/codebase-design/SKILL.md:16-32`, where the seven-term glossary now lives |
| C-5 | `spec/PSFS.md:38-41` + `skill-writer/references/frontmatter-spec.md:72,74-79,130-136` | Lists `argument-hint` and `disable-model-invocation` as "Anthropic Agent Skills optional fields". Neither is one; upstream has zero occurrences in 46 commits and `quick_validate.py:42` rejects both. (`compatibility` IS legitimate) | Reclassify both as Claude-Code-runtime fields in the Extended tier |
| C-6 | `spec/PSFS.md:248-262` | Claims Core-conformant skills run "without modification" and that "spec-compliant parsers ignore unrecognized keys". Anthropic's only shipped validator hard-fails on unknown keys **including `version`**, which PSFS Core requires — both tested SM skills exited 1 | Restate as: loads on every runtime tested, but fails Anthropic's strict reference validator on `version` + Extended fields. See Decision 3 |
| C-7 | `spec/PSFS.md:113-117, 280` | Says PSFS metadata "mirrors Anthropic's nested-metadata form"; the deleted normative spec says string values only, and the PSFS example uses an array (`tags: [...]`) | Drop the mirroring claim; fix the example or mark it PSFS-only |
| C-8 | `docs/plans/2026-08-06-upstream-lineage-refresh-plan.md:28,64,216` | Inventories anthropics/skills as "18 skills + spec/ + template/"; there are 17 (the 18th SKILL.md is `template/SKILL.md`) and `spec/` is a 3-line redirect, so the planned spec-vs-spec diff cannot run as written | Retarget to the deleted-in-history `spec/skill-authoring.md` (`69c0b1a^`) + `scripts/quick_validate.py` |
| C-9 | `scripts/install.sh:133,167,571`, `scripts/install-plan.sh:172`, `scripts/lib/install-state.sh:128`, `contracts/installer/install-locations.md:18` | **Functional.** Antigravity skills install to `~/.gemini/antigravity/skills/`, which the app stopped reading. Upstream `309a8e7` (2026-07-01) moved user skills to `~/.gemini/config/skills/` and project skills to `<project>/.agents/skills/`. SM's detector probes the dead path, so Antigravity reports not-installed on machines that have it | Update detector + both dests + the contract table. *Upstream's fix and rationale verified; Google's docs **unverified*** |
| C-10 | `scripts/convert.sh:290-317`, `contracts/installer/per-tool-output-spec.md:266`, `tests/installer/README.md:74-86` | **Functional.** Antigravity output stamps `risk`/`source`/`date_added`, making it non-deterministic — paid for with a contract carve-out and golden-file normalization. Upstream deleted all three fields in the same commit | Emit name + description only; delete the carve-out and the normalization step |
| C-11 | `scripts/lint-skills.sh:386,406,**450**,679,688`, `scripts/convert.sh:441` | **Functional.** `grep -q` fed by a pipe under `set -o pipefail`; `:450` pipes an entire SKILL.md body (~500 lines) into `grep -qF '$ARGUMENTS'` — past the pipe-buffer threshold today, so the WC-1 fail-loud check is nondeterministic. Upstream measured 106/87/90 warnings across identical runs, stable at 59 after the fix | Convert all six sites to herestrings (`grep -qE -- "$pat" <<<"$body"`); record the rule in `contracts/installer/lint-rules.md`. Overlaps UL-20 |
| C-12 | `skills/workflows/use-freellmapi/SKILL.md:150-152` | **Functional.** Teaches `npx freellmapi setup-claude --url … --dry-run` with no key; `cli/src/index.ts:75-79` throws `'No API key supplied…'` whenever stdin is not a TTY — i.e. every agent invocation | Add `--api-key <key>` / `FREELLMAPI_API_KEY`; upstream corrected its own docs in `36eea7b` |
| C-13 | `skills/workflows/use-freellmapi/references/agent-clients.md:20-25,27-41` | Same keyless block; option table omits `--api-key`, `--model`, `--url`, the env fallbacks, and the `list` command. Do **not** re-add `--profile`/`--dry-run` — already present | Correct the block and the table |
| C-14 | `skills/workflows/setup-project-skills/references/templates/work-item-tracker-beads.md` | **Functional for consumers.** Every command uses a nonexistent `bd issue` subcommand (`create`/`list`/`show`/`ready`/`update`/`close` are top-level); the ID example implies sequential `bd-318` where beads uses hash IDs (`bd-a1b2`). A project that picks Beads gets a file where nothing works, silently. (`SKILL.md:62` detection via `.beads/` is still correct) | Rewrite to the flat surface — then convert the file to a stub per UL-13 so it cannot rot again |
| C-15 | `skills/workflows/use-pxpipe/SKILL.md:93-108,55` | Presents `export ANTHROPIC_BASE_URL` as *the* integration with no cost stated. Upstream documents that it fails client-side firstParty checks — hiding `/remote-control`, disabling claude.ai connectors — and ships `pxpipe warp` to avoid it | Teach `pxpipe warp -- <agent-cmd>` as the preferred wiring; keep the env var as the fallback with the cost named (was UL borrow #15) |
| C-16 | `skills/workflows/use-pxpipe/SKILL.md:56,68-70` | Says the default model scope is `claude-fable-5` only; upstream default is `['claude-fable-5','gemini-3.6-flash']` (`applicability.ts:41`) | Correct |
| C-17 | `skills/workflows/use-pxpipe/SKILL.md:47-49` | "~8 weeks of history, v0.8.x" — actual `package.json` is 0.11.1, first commit 2026-05-18, 404 commits | Correct or delete the age claim |
| C-18 | `skills/workflows/use-pxpipe/SKILL.md:137` + `references/verification.md:84-85` | Dashboard model-scope chips described as in-memory-only; they persist to `~/.config/pxpipe/config.json` and survive restart (`node.ts:100-104`, 0.10.0). Env is no longer the only persistence layer | Correct both files |
| C-19 | `skills/workflows/use-pxpipe/references/verification.md:92` | 4xx body capture described as the default posture; it is opt-in behind `PXPIPE_DEBUG_CAPTURE_4XX=1`, which upstream SECURITY.md warns against in production | Correct |
| C-20 | `skills/workflows/use-pxpipe/SKILL.md:88-91`, `verification.md:89-90` | Risk framed as "dashboard is unauthenticated — never bind 0.0.0.0". Since 0.10.0 dashboard routes are loopback-only and return 403; only the proxy API is exposed | Keep the caution, fix the mechanism |
| C-21 | `skills/meta/model-adaptation/references/model-effort-tiering.md:110-128` | Image-proxy matrix frozen at pxpipe v0.8.0: no `gemini-3.6-flash` row (14/15, now in the default set), no `claude-opus-5` row (2/15, added then removed as a default), Opus 4.8 at 6/15 vs upstream's current 0/15 | **Do not refresh — delete the mirrored matrix.** Keep the durable fail-closed rule; point at `src/core/applicability.ts` + upstream README with a re-derive instruction. See Decision 4 |
| C-22 | `README.md:505` | "five bespoke per-host integrations (claude-code, codex, copilot, devin, openclaw)" — there are six; `plugins/cursor/` is a full integration added `cd5ca48` (2026-07-19), one day before SM's dive. The rest of the sentence still verifies and the backend-enum mismatch has widened | Correct to six and name cursor |
| C-23 | `skills/workflows/mermaid-charts/evals/evals.json` + `repo-deep-dive/evals/evals.json` | Eval prompts assert stale facts: Gas Town "377k LoC" (now 474,723); gstack "13 skills" + eight nonexistent slash commands (59 SKILL.md, ~50 commands) and "NOT an orchestrator" (now arguable); Overstory "9 adapters" (11), "10 agent roles" (7 registered), tmux-by-default (headless now default), and the repo is archived as of 2026-05-28 | Low stakes — grading criteria are about diagram structure, not these facts. Refresh for accuracy in one pass |
| C-24 | `docs/COMPLETED-WORK.md:97` (CL2) | Premise wrong: says the migration to `hermes-agent/.claude/skills/` "never happened". A byte-identical copy exists there, untracked (`?? .claude/`). CL2's conclusion still stands | Amend the row; note the unsynchronized out-of-VCS duplicate as a live drift risk |
| C-25 | `docs/FUTURE.md:11` (WC-3) | Cites "the ai-website-cloner-template pattern — a declarative `hosts.yaml`". No such file exists or ever existed upstream; its converter is nine hand-written `write()` calls. The idea is still fine; the citation is false | Strip the citation, keep the idea as SM-originated |
| C-26 | `ACKNOWLEDGMENTS.md` | Missing sections for **freellmapi** (MIT © Tashfeen Ahmed), **pxpipe** (MIT), **SkillOpt**, **harness-engineering** (CC BY 4.0, published attribution string, "adaptations must identify that changes were made"), **ai-website-cloner-template** (MIT © 2025 JCodesMore), **ponytail** (MIT © 2026 DietrichGebert), **ECC** (MIT © Affaan Mustafa) | Back-fill seven sections. See Decision 8 |
| C-27 | `contracts/hooks/hooks-layer.md`, `contracts/installer/*.md`, `contracts/standards/psfs.md` | Still call the repo "AllTheSkills" (renamed 2026-05-07) and cite an unresolvable external vault path (`DeepResearch/The-Hive/ecc_deepdive/source-material/14-alltheskills-frontier.md`) that does not exist in a clone | Rename; replace with an in-repo citation per the HE-1 rule |
| C-28 | `skills/workflows/living-plan/SKILL.md:160` | Ships a literal `/Users/johns/...` absolute path in a published skill body — the only non-placeholder personal path under `skills/` | Fix, and land the guard (UL-7) so it cannot recur |
| C-29 | `claude_docs/hive-cli/` (SKILL.md + `references/cli-reference.md`, `rest-api.md`) | Five stale claims: three new command groups absent (`platform install`, `platform hook`, `platform steer-check`); `doctor --category` documented as 5 infra categories vs 13 actual; four `skill` subcommands + `tracker query` missing; REST table covers ~21 of 38 route modules and misses root `GET /metrics` | **Lower priority** — `claude_docs/` is untracked and outside the 73-skill published catalog. Fix or explicitly mark local-only-and-stale |
| C-30 | `ACKNOWLEDGMENTS.md:4-7` disclaimer | The blanket "credits will be back-filled" survives every fix, so it never converges | Replace with a named open list (the four confessed pre-May-2026 debts) once C-26 lands |

## 4. Decisions Needed From The User

**1. The grilling reversal — adopt round-based frontier, or keep depth-first?**
Upstream retired `productivity/grill-me` to a 4-line alias and rewrote the substance in `productivity/grilling`, which now works the design tree in **rounds**: ask the entire frontier (every decision whose prerequisites are settled) in one numbered batch with a recommendation per question, then wait; answers reshape the tree and push the frontier out. SM's `grill-me/SKILL.md` rule 1 is the exact inverse and its description sells "depth-first, one question at a time".
- *Keep depth-first:* no churn; the description stays true; but SM would be defending a constraint whose **only** source has retracted it, with no independent SM evidence — and ADR 0001 sets the precedent that keeping a diverged position requires a written justification.
- *Adopt rounds:* fewer round trips, better AFK/HITL batching, and it harmonizes with the zero-tool pre-build gate (UL-32), which is also batch-shaped ("list the 1-3 consequential choices, then stop"). Costs a description edit and an ADR.
**Recommendation: adopt rounds as the default; keep one-at-a-time as an explicit deep mode.** Write `docs/adr/0003-grilling-frontier-rounds.md` recording the reversal, and take the two strictly-additive sub-parts regardless of this vote — the numbered `❓ Q1 / ➡️ recommendation` output format and **non-blocking sub-agent fact-finding** (a running exploration is an unsettled prerequisite, so only its downstream questions wait). Then fix C-2.

**2. Adopt the `writing-for-agents` doctrine into skill-writer, or cite-only?**
Five concepts SM does not have anywhere (verified by grep across `skills/`): **context pointer** (a description and an AGENTS.md line are the same object; the pointer's *wording*, not its target, decides retrieval — a must-have target behind a weak pointer is a variance bug), **the two loads** (context load vs cognitive load, the latter being the price of human agency and not a thing to minimise), **information hierarchy** as a three-rung ladder with branching as the disclosure test (+ co-location, sprawl, sediment as named failure modes), **completion criteria** clarity/demand (premature completion pulled by visible post-completion steps), and **cache vs environment**.
- *Cite-only:* cheapest, closes the dead citation (C-1), leaves SM's "progressive disclosure" as a length rule only (`≤5,000 words / ≤500 lines`).
- *Adopt:* gives SM's pushy-description doctrine a mechanism instead of a heuristic, and gives skill-review something checkable beyond the three CB-2 rules.
**Recommendation: adopt (UL-16).** This is the highest-leverage doctrine borrow in the sweep and it is prose-only.

**3. PSFS conformance posture — restate honestly, or chase validator conformance?**
Every SM skill fails `anthropics/skills/skills/skill-creator/scripts/quick_validate.py` on `version` (which PSFS *requires*) plus all six Extended fields. The runtime tolerates extra keys; the strict validator does not.
- *(a) Restate:* fix C-5/C-6/C-7 to say "loads on every tested runtime; fails Anthropic's strict reference validator on `version` + Extended fields". Zero code churn, full honesty.
- *(b) Conform:* move `version` and Extended fields under `metadata`. Large ripple across 77 SKILL.md, `lint-skills.sh`, `frontmatter.schema.json`, `catalog.sh`, and every host converter — and Anthropic's metadata is string-valued, so `owns`/`composes_with` arrays do not fit cleanly.
**Recommendation: (a) now, park (b) as a FUTURE row.** This decision also **blocks any new frontmatter field** — see Decision 9.

**4. pxpipe image-proxy matrix — refresh it, or delete and point upstream?**
PX-3 shipped a "durable rule in the body, aging table in references/" split. The table has now rotted twice in six weeks (missing gemini-3.6-flash, missing opus-5, wrong opus-4.8 figure).
- *Refresh:* one edit, correct today, re-arms the identical failure at the next model release.
- *Delete and point:* keep the fail-closed rule (which is durable and correct), replace the table with a source-map pointer to `src/core/applicability.ts` + the upstream README matrix and a re-derive instruction.
**Recommendation: delete and point (C-21).** This is exactly the multica source-map discipline (UL-40) and the beads never-bundle-a-CLI-reference rule (UL-13) applied to a data table — three independent upstreams converged on it.

**5. Catalog authority — one consolidated work item, or three?**
`check-tools.sh`/`check-divisions.sh` (agency-agents), the doc-contract test (last30days), and `--list` + non-authoritative markers (ratel) are one mechanism: *stop hand-maintaining name lists; extract identifiers from prose and diff against disk*. `ALL_TOOLS` is duplicated verbatim in three scripts with zero cross-check; `catalog.sh --text` emits counts but no names; COMPLETED-WORK.md:22 records this class biting a fourth time.
- *Three rows:* looks like more progress, guarantees three partial implementations of the same set-comparison.
- *One row:* larger single unit, single contract bump on `catalog-invariant.md`.
**Recommendation: one row (UL-15), four sub-parts** — `--list` query mode, prose name-set extraction with a DOC_ONLY allowlist, disk-directory enumeration, and `tools.json` as the single host registry.

**6. The `wizard` borrow — what do we call it?**
Adopting it as `wizard` takes an upstream skill's identity, against SM policy (the `ponytail` → `yagni-gate` precedent).
- *Build it:* generates a staged bash script for the human-only steps (provisioning, CI secrets, third-party dashboards) — the artifact SM's deployment-checklist and railway-deploy never emit; HITL is prose-only across the library today.
- *Skip it:* one fewer skill in the catalog ripple.
**Recommendation: build it under an SM name** (e.g. `human-steps-script`), keeping `wizard` as a description trigger word only. Confirm the name before UL-28 starts.

**7. Take the davidondrej borrows and incur the attribution?**
Verdict is NO_LINEAGE — SM owes it nothing today. But four borrows survived the panel, including the highest-value safety item in the sweep (an executable PreToolUse guard: SM ships a 30-rule *declarative* deny list the user must opt into, and installs skills into eleven hosts and a guard into **none**), plus the irreversible-vs-recoverable design rule SM states nowhere and ~12 missing irreversible patterns.
- *Take:* creates a new ACKNOWLEDGMENTS obligation; must reconcile with F9 `autonomy-profile` (per-loop allowlists) rather than duplicate it.
- *Decline:* leaves SM with no mechanical block on `rm -rf /` for any host.
**Recommendation: take, and credit.** Headline finding #3 ("entirely uncredited") is *resolved* by the verdict — nothing was owed — but adopting creates the debt, so the section ships with the code.

**8. Attribution scope — the seven new, or also the confessed four?**
ACKNOWLEDGMENTS:4-7 confesses debt on the orchestrator, contract-first architecture, role-agents, and the QA-gate. Every uncredited upstream this sweep found is a 2026-07 intake — debt incurred *after* that confession. **This 26-repo corpus cannot close the original four**; none of these clones is plausibly a March-2026 ancestor.
- *Seven only:* honest and shippable now, but the disclaimer survives and looks unchanged.
- *Seven + open an archaeology row:* requires reading SM's own early history (`16d6d64` onward) and reconstructing what the author was reading in March 2026.
**Recommendation: both.** Ship C-26, then rewrite the disclaimer (C-30) to name the four specific open items rather than a blanket "incomplete", and open one ledger row for the early-history pass.

**9. Cognitive-pattern library — adopt, and whom do we credit?**
The candidate proposes 41 named thinking patterns as YAML + an optional `cognitive_patterns:` frontmatter field, and reassigns provenance from The-Hive to gstack based solely on a count match in SM's *own* eval prompt.
**Recommendation: decline both halves.** The reassignment is asserted with no gstack-side evidence, The-Hive is a demonstrated mis-attribution hazard (RV1), and the field requires a PSFS MINOR bump that *worsens* the confirmed validator defect in Decision 3. SM already ships stance-shaped skills (caveman, yagni-gate, grill-me, find-unknowns, zoom-out) as full skills.

## 5. Adoption Backlog

Value/effort as scored by the panel; effort is S (prose/single-file), M (multi-file or new reference), L (new skill or cross-cutting tooling). Rows already covered by §3 (pxpipe warp, freellmapi CLI, allowlist) are **not** repeated here.

### Band A — high value, ship first

| ID | Title | Source | SM target | Value | Effort |
|---|---|---|---|---|---|
| UL-1 | Loop retirement condition + durable end-state taxonomy (nothing needed / candidate proposed / change proved / approval requested / recovery required / policy obsolete) | harness-engineering | `loops/loop-controller/SKILL.md` — extend the 5-part contract with a `retirement` line | high | S |
| UL-2 | `not_established: []` on the QE report — say what the evidence did NOT prove | harness-engineering | `roles/qe-agent/references/qa-report-schema.json` + SKILL.md | high | S |
| UL-3 | Three-state gate exit codes: 0 ran/ok, 1 ran/rejected, 2 **did not run** — never a pass. Also kills `gate()`'s "(none — vacuous pass)" coercion | OpenSwarm | `loop-controller/references/safety.md` + `fix-until-green/references/{gate-commands,stop-hook}.md` | high | S |
| UL-4 | Shape ops vs outcome ops — a rubric of only formatting checks is not a grader | SkillOpt | `docs/standards/eval-split-hygiene.md` Rule 5 + `safety.md` | high | S |
| UL-5 | `reject_unverified` — a third gate outcome when the holdout leaked; stage but never certify. Ships with the paired test that the gate can still say yes | SkillOpt | `eval-split-hygiene.md` Rule 6 + `safety.md` | high | S |
| UL-6 | Harvest the `yagni:` markers — the debt ledger yagni-gate never built; hands off to plan-intake | ponytail | `workflows/yagni-gate/` new section | high | S |
| UL-7 | `personal-path` scan rule (HIGH) with a placeholder allowlist. **Note:** upstream ships only two hardcoded regexes for one username — SM designs the generic pattern itself | ECC | `scripts/scan-skills.sh` + `tests/scan-skills/`; fixes C-28 | high | S |
| UL-8 | Guard skills must prove teeth: reintroduce a violation → gate must exit non-zero → restore → must pass. A bad pattern staying green means no rule exists | deer-flow | `design-token-guard` Step 3 + `class-extraction-guard` + `skill-writer/references/validation-script-pattern.md` | high | S |
| UL-9 | Prior coverage suppresses duplicate **posting**, never duplicate **analysis**; plus self-idempotency on the skill's own replies | deer-flow | `git/git-pr-feedback/SKILL.md:68,188,72-92` + `loops/babysit/SKILL.md:47` | high | S |
| UL-10 | A when-not-to-parallelize gate before Phase 2 sizing (SM writes its own prose and name) | overstory | new `orchestrator/references/`, wired between phase-guide 1 and 2 | high | S/M |
| UL-11 | Container-networking triage: host-loopback proxy unreachable from the container, IPv6-only daemon config, and the one-line discriminating probe | freellmapi | `use-freellmapi/SKILL.md` Step 5 table + `references/capabilities.md` | high | S |
| UL-12 | Baseline-relative gate: record the checkout failure set; green becomes "no pass→fail regression". **Merges 9router `known-fails.txt` + OpenSwarm merge-base fingerprinting** incl. `baselineEnvironmentChanged` | 9router + OpenSwarm | `loops/fix-until-green/` Step 0 + new `references/baseline-gate.md`; extends to coverage-loop, perf-loop | high | M |
| UL-13 | Never bundle a third-party CLI's command surface — reference file becomes a stub naming live sources; lint rule | beads | `skill-writer/references/patterns.md` + `skill-review/references/audit-checklist.md`; applied first to the beads template (C-14) | high | M |
| UL-14 | Ownership-violation detection at the wave gate + a declared scope-expansion escape hatch (`expansion_reason:` in a commit body); named all-caps failure-modes block in role skills | overstory | `orchestrator/references/file-ownership.md` + `wave-gate.md` + `roles/*/SKILL.md` | high | M |
| UL-15 | **Catalog authority consolidation** (Decision 5): `catalog.sh --list`, prose name-set extraction with DOC_ONLY allowlist, on-disk category enumeration, root `tools.json` registry cross-checked against the three duplicated `ALL_TOOLS` | agency-agents + last30days + ratel | `scripts/catalog.sh`, new `scripts/check-tools.sh`, `tools.json`, `contracts/installer/catalog-invariant.md` bump, demotion lines in CLAUDE.md/README.md | high | L |
| UL-16 | `writing-for-agents` doctrine: context pointers, the two loads, information hierarchy + branching disclosure test, completion-criteria clarity/demand, cache vs environment (Decision 2) | mattpocock | new `skill-writer/references/` craft file + extend the CB-2 block; closes C-1 | high | M |
| UL-17 | Staged consequential-effects ladder (assess → prepare → canary → approve → cut over → verify → roll back) + a 7-field authority-grant record; "merge" never means bypass authority | harness-engineering | `loop-controller/references/safety.md` §HITL + `self-healing-loop` | high | M |
| UL-18 | Class A / Class B eval split as the evidence procedure for dropping a model tier (neutral role_context, grader stronger than every subject, temperature 0, `--repeat 3`) | gastown | `model-adaptation/references/model-effort-tiering.md` new section | high | M |
| UL-19 | Executable dangerous-command guard: PreToolUse exit-2 block + `test-guard.sh`, the irreversible-vs-recoverable design rule, ~12 missing irreversible patterns. **Seed from the existing settings-consolidator deny list; do not re-import it.** Reconcile with F9 | davidondrej | `hooks/scripts/deny-dangerous.sh`, `hooks/dangerous-patterns.txt`, `hooks.manifest.json` | high | M/L |
| UL-20 | SIGPIPE-safe `grep -q` rule (herestring, not pipe) recorded as a lint-rules row | agency-agents | `contracts/installer/lint-rules.md`; the code fix is C-11 | medium | S |
| UL-21 | Trust level **derived from files on disk** (markdown-only / assets / script-bearing); first script promotes a skill and fails CI until a human extends an expectation list. 7 SM skills ship `scripts/` today, none enumerated | paperclip | `spec/PSFS.md` (concept, **not** a frontmatter field — see Decision 3) + `catalog.sh` + `tests/` | high | M |

### Band B — medium value

| ID | Title | Source | SM target | Value | Effort |
|---|---|---|---|---|---|
| UL-22 | Discriminating-assertion rubric: fail superficial/coincidental evidence, burden of proof on the expectation; post-grading critique of non-discriminating assertions; cross-config analyzer pass | anthropics | `loop-controller/references/authoring.md` §Evaluator + `qe-agent/references/llm-judge-rubrics.md` | medium | S |
| UL-23 | Eval-prompt realism bar (concrete, messy, specific) + the mechanism constraint: trivial one-step prompts do not trigger skills and pushier wording cannot fix them | anthropics | `skill-writer/references/description-patterns.md` + `skill-review` §B2 | medium | S |
| UL-24 | Grade the claim, not the vocabulary: negation-aware lookbehinds, claim-regex instead of refusal keyword lists, refusal only counts when short | SkillOpt | `eval-split-hygiene.md` grading rules + fix-until-green / render-sanity gate language | medium | S |
| UL-25 | Two anti-cheat modes: the gate's **runner script** is read-only to the fixer, and a test the agent wrote cannot be evidence its own fix works | OpenSwarm | `fix-until-green/SKILL.md:121-128` + `coverage-loop/references/coverage.md` | medium | S |
| UL-26 | Completion-report guards: hedging tokens in the agent's own summary fail the report; whitespace-only diffs and >1200-line diffs flag scope creep | OpenSwarm | new reference under `qe-agent/` or `code-review-agent/`, consumed by loops' completion step | medium | S |
| UL-27 | Escalation = **re-diagnose with the strong model fed the failing patch + test output**, not retry the cheap one; plus "the test result outranks the plan" | OpenSwarm | `loop-controller` escalation ladder + `diagnose-loop`; trust line into `work-item-brief` + handoff protocol | medium | S |
| UL-28 | Verify-don't-trust handoff: state-not-instructions (narrative sections only — `suggested_first_action` stays SM's deliberate exception), reference-don't-duplicate, and a ready-to-paste closing prompt telling the fresh agent to verify every claim | davidondrej | `orchestrator/references/handoff-protocol.md` + `context-manager` | medium | S |
| UL-29 | Zero-tool instant pre-build gate: no tool use, 1-3 consequential choices with gut recommendations, then stop | davidondrej | fast-mode section in `grill-me` or `yagni-gate` | medium | S |
| UL-30 | Tail-slot instruction principle (position 0 reads as background after a long tool loop; harnesses re-emit at the tail) + durable-vs-session classification and hard pin bounds | pxpipe | `loop-controller` (long-run instruction hygiene) and/or `context-manager`; one line in `use-pxpipe` Step 5. **Not** maintain-context | medium | S |
| UL-31 | "What this skill cannot do" as a required body section — naming the sibling that covers the gap **and an operational tell**. 6 SM skills already do it ad hoc | ruflo-src | `skill-writer/references/body-template.md` + `skill-review/references/audit-checklist.md` | medium | S |
| UL-32 | Self-declaring staleness footer: name the upstream version the skill targets and what to do when `<tool> --version` is newer | beads | `body-template.md` + `audit-checklist.md` | medium | S |
| UL-33 | Every documented invariant names the test that enforces it; mark "unenforced (honor system)" explicitly | last30days | `CLAUDE.md` Key Design Decisions + `AGENTS.md` | medium | S |
| UL-34 | Record the expected gate **outcome**, not just the command (expected pass/fail counts, how to judge a regression, per-bucket cause of known-red); plus an inline stale-doc-section convention | 9router | `project-profiler/SKILL.md:110,122` + optional `test_expected_outcome` in the schema | medium | S |
| UL-35 | Interactive commands hang an unattended capture (editors, pagers, live monitors, nested ssh, TTY prompts) — hand the user a copyable block. Carry the anti-denylist rationale: static lists create false confidence | Clauge | `loop-controller/references/safety.md` §HITL subsection | low | S |
| UL-36 | No fabricated per-repo savings — route impact questions to the counted marker ledger (UL-6). Do **not** echo into use-pxpipe (real byte baseline there) | ponytail | `yagni-gate/SKILL.md` boundary note | low | S |
| UL-37 | Plain-HTTP LAN installs: `CSP_UPGRADE_INSECURE_REQUESTS` as the escape hatch on SM's existing `HOST_BIND=0.0.0.0` gotcha | freellmapi | `use-freellmapi/references/capabilities.md:278-279` | low | S |
| UL-38 | Written upstream-adaptation policy: keep-name vs rename test, strip branding, dependency policy (SM writes its own text — that is the policy's point) | ECC | `docs/adr/0002-upstream-adaptation-policy.md`, referenced from `skill-writer` + `plan-intake` | medium | S |
| UL-39 | Invocation-policy parity as an enforced invariant: emit each host's equivalent of `disable-model-invocation` (27 skills), fail loudly where none exists. Includes the Codex `agents/openai.yaml` mapping note in PSFS (cheap half) — emission needs a codex target first | mattpocock + davidondrej | `scripts/convert.sh` + `lint-skills.sh` + `contracts/installer/lint-rules.md` + `spec/PSFS.md:110` | medium | M |
| UL-40 | Source-map reference files: per-claim `Fact → path/file:line` tables with a re-derive header, plus a same-PR update rule | multica | `repo-deep-dive` (new deliverable) + `setup-project-skills` generated block | medium | M |
| UL-41 | Per-skill semantic anchors in CI (`mustContain` / `mustNotContain` phrases, deliberately not line citations). Keep cheap and orthogonal to F5 | multica | `lint-skills.sh` + `lint-skills.yml` + `skill-review` | medium | M |
| UL-42 | Deterministic resource-graph check: referenced-file-missing, reference-escapes-package, orphan resource file — with an evals-fixture allowlist. Reclassifies two LLM-judged checklist lines as deterministic | deer-flow | `scripts/lint-skills.sh` + `audit-checklist.md:40,43` | medium | M |
| UL-43 | Treat the reviewed skill's content as untrusted data + one injection eval fixture expecting "blocked + safety finding" | deer-flow | `skill-review` Mode B + new `evals/` case | medium | M |
| UL-44 | Second machine axis on skill-review: **assurance** (what was proven at runtime) beside readiness; SHIP must not imply behavior was verified when B2 was skipped | deer-flow | `skill-review/references/report-format.md` + rubric + SKILL.md Phase 4 | medium | M |
| UL-45 | Originality / near-duplicate guard (entity-neutralized 8-word shingle Jaccard). **SM must re-derive its own thresholds** — the 13 loops are deliberate structural siblings | agency-agents | new `scripts/check-skill-originality.sh` + bulk mode in `skill-review` | medium | M |
| UL-46 | Structural rules for the scanner: symlink escape (critical), broken/circular symlink, per-file size cap, total-size + file-count caps, checked-in binaries/executables. **Trust-tier install matrix excluded** — F2 parks registries | hermes-agent | `scripts/scan-skills.sh` + `security-agent/SKILL.md:151` | medium | M |
| UL-47 | PreToolUse `hookSpecificOutput` output-shape contract (top-level `additionalContext` is silently ignored) + a non-blocking "steer" tier **below** termination — must be framed as a cheaper tier, not a replacement, or it contradicts safety.md:6 | The-Hive | `contracts/hooks/hooks-layer.md` (the strong half) + `safety.md` Oscillation | medium | M |
| UL-48 | Bounded skill-name resolution with four outcomes (FOUND / MISSING / AMBIGUOUS / REJECTED); today `pull_from()` interpolates unnormalized names and `break`s on first match | SkillOpt | `sync-skills` SKILL.md + `scripts/sync-skills.sh` + `madness` router guidance | medium | M |
| UL-49 | Shape-aware output digest: declare a `render_as` shape up front, budget per shape, tell the model it sees a digest and to re-query narrowly | Clauge | new `context-manager/references/output-budgeting.md` + pointer from `safety.md` | medium | M |
| UL-50 | Diff-size review floor (skip specialists under N lines) + measured-yield specialist retirement **with a never-gate insurance list** (security, data-migration always run); optional `test_stub` on findings | gstack | `orchestrator/references/team-sizing.md` + `code-review-agent` + qa-report schema | medium | M |
| UL-51 | Five-tag over-engineering review taxonomy (`delete:`/`stdlib:`/`native:`/`yagni:`/`shrink:`) with a net-lines score; carries the "never flag the single smoke test" carve-out | ponytail | `yagni-gate` review-mode section, cross-referenced from `architecture-rescue` | medium | M |
| UL-52 | Stall triage as retry / terminate / **extend**, defaulting to extend, with a `fallback` flag so a default never reads as a judgment | overstory | `orchestrator/references/circuit-breaker.md` (new silence trigger) + `safety.md` | medium | M |
| UL-53 | Reap-vs-converge for a derived index: add orphan-row detection + a drop-and-rebuild-from-disk mode. **Not** living-plan — skill-catalog already has the mechanism | ruflo-src | `llm-wiki/references/operations.md` lint + a rebuild mode | medium | M |
| UL-54 | Knowledge records with classification tiers, shelf life, and hard entry caps (foundational never expires; tactical/observational do) | overstory | `maintain-context` + `llm-wiki` lint expiry check | medium | M |
| UL-55 | Diataxis quadrant coverage as the operational definition of "docs match the changed surface": score each new public entity across four quadrants; zero coverage = critical gap, reference-only = common gap | gstack | `loops/nightly-docs-and-changelog` + `roles/docs-agent/references/` | medium | M |
| UL-56 | Pin CI-green proof to the PR's latest head SHA (`headRefOid` refreshed every iteration and after every push; per-SHA check-runs + legacy status) | paperclip | `loops/babysit/SKILL.md:48` + `references/scheduling.md:55-72` | medium | M |
| UL-57 | FIND-before-MAKE: search **outside** the repo before authoring a new skill (`gh search code --filename SKILL.md`, `gh search repos`), with judging criteria and three outcomes | paperclip | `skill-writer/SKILL.md` + `references/quick-checklist.md` | medium | M |
| UL-58 | Mine local prior-session logs as trajectory evidence (repeated steering, rejected formulations, lessons with no durable owner) with its own guardrails | harness-engineering | new optional phase in `repo-deep-dive` or `project-profiler` | medium | M |
| UL-59 | Per-client inference keys with server-enforced system prompts — label **main-only** (feature commit `fedfdb8`, newest tag v0.6.8), same version-skew framing capabilities.md already uses | freellmapi | `use-freellmapi/references/capabilities.md:45-47,272` + `agent-clients.md:92-105` | medium | M |
| UL-60 | An agent-facing `llms.txt`: what Skill-Madness is **not**, strong-fit/weak-fit, install commands with a currency stamp, and an anti-hallucination block (77 on disk vs 73 allowlisted is a publication gate) | ratel | new root `llms.txt` + redirect callout in `AGENTS.md` | medium | M |
| UL-61 | `.skill` bundle target for Claude.ai upload + the update-in-place discipline (never `-v2`; copy read-only installs before editing). Fold into F18 if read as the same row | anthropics | `scripts/convert.sh` 12th target + a `sync-skills` publish note | low | S |
| UL-62 | Human-steps script generator — staged bash for provisioning / CI secrets / third-party dashboards; reads `.env*`, `docker-compose*`, `.github/workflows/*` instead of asking cold; `bash -n` + shellcheck, never run end-to-end. **SM name required (Decision 6)** | mattpocock | NEW `skills/workflows/`, composes with deployment-checklist + railway-deploy | medium | L |
| UL-63 | Grilling frontier rounds + numbered `Q/recommendation` format + non-blocking sub-agent fact-finding (**gated on Decision 1**; ADR either way) | mattpocock | `workflows/grill-me/SKILL.md` + ACKNOWLEDGMENTS (C-2) + `docs/adr/0003-*` | medium | M |

## 6. Explicitly Declined

Record these so they are never re-proposed.

1. **Installer v2 TUI primitives** (agency-agents) — REFUTED by the panel. SM's `interactive_select` (`install.sh:184-300`) plus `lib/term.sh` already work; this is a ~120-line rewrite of functioning code for alt-screen/raw-mode polish, on a path every bats test invokes with `--no-interactive`. It is precisely what `yagni-gate` exists to stop. *Only* the sub-part worth revisiting: a documented test hook so the selector is exercisable in CI — which does not require the rewrite.
2. **Cognitive-pattern library + `cognitive_patterns:` frontmatter field** (The-Hive/gstack) — declined per Decision 9. The gstack reassignment is unevidenced, The-Hive is a demonstrated mis-attribution hazard (RV1), and a new Extended field worsens the confirmed validator defect.
3. **Refreshing the pxpipe image-proxy matrix in place** — declined per Decision 4. The table is deleted and replaced with a pointer; refreshing re-arms a failure that has already fired twice.
4. **`wizard` as a skill name** — declined by SM policy (never take upstream identities). The capability is adopted under an SM name (UL-62).
5. **SkillOpt/hermes `INSTALL_POLICY` trust-tier install matrix** — declined; it presupposes installing third-party skills from a registry, which FUTURE.md F2 parks with no design committed and CB-8 suggests using an existing registry instead. Only the structural rule group is taken (UL-46).
6. **`$TMPDIR` out-of-tree handoff storage** (davidondrej) — declined; SM writes to `.claude/handoffs/` inside the repo by design. Deliberate divergence, not a gap.
7. **Upstream's 300-char description cap** (multica) — declined; contradicts SM's decided pushy-description policy.
8. **Upstream strict-YAML lesson** (multica) — already banked; `lint-skills.sh` does a real `yaml.safe_load` with an explicit `YAMLError` branch.
9. **Near-miss-negatives rule** (anthropics) — already shipped (`skill-review/SKILL.md:101`, `skill-writer/SKILL.md:127`).
10. **Codex-drops-symlinks-on-install** and the **plugin.json-tracks-package.json** invariant (mattpocock) — do not reach SM: SM's plugin ships real files and has no `package.json`.
11. **ADR 0001 (keep caveman + zoom-out)** — settled; not re-litigated by this plan, and unaffected by upstream's deletion of `productivity/caveman`.

**Reconcile-don't-duplicate** (FUTURE.md rows adjacent to backlog items, which must be updated rather than shadowed): F1 (installer reach) ← UL-15/UL-39; F2 (marketplace) ← declined trust-tier install; F3 (per-host smoke tests) ← UL-39; F5 (`skill-eval`) ← UL-4/UL-5/UL-18/UL-22/UL-24 land in *shipped* docs ahead of it, per the SO-4 precedent; F7 (`hook-forge`) ← UL-47's contract note is two paragraphs, not a skill build; F9 (`autonomy-profile`) ← UL-19 must extend, not duplicate; F17 (quality-gates bundle) ← UL-50 is gate *economics*, not a new gate; F18 (`plugin-packager`) ← UL-61; CB-4 (tombstone KB) ← UL-45 is content similarity across *shipped* skills, not rejected ideas.

## 7. Coverage Gaps

**Dirty working trees — seven repos reviewed at stale HEAD or not at all:** `space-agent`, `RuView`, `ECC`, `hermes-agent`, `Clauge`, `trinity`, `context-engineering-intro`. Of these, ECC, hermes-agent, and Clauge produced verdicts and borrows — **at a HEAD that may not be current** — and ECC in particular was upgraded to CONFIRMED_LINEAGE mid-review, meaning the repo SM names as the design model for five shipped subsystems was assessed against a dirty tree. `space-agent`, `RuView`, `trinity`, and `context-engineering-intro` produced no verdict row at all. Any re-run must stash-or-clone-clean first (see §8 step 2).

**Under-investigated per the completeness critic:**
- `ruflo-src` and `OpenSwarm` are direct structural peers of SM's orchestrator + role-agent + swarm design; both were mined only for **gate mechanics** and never for team composition, spawn policy, or role decomposition. `OpenSwarm` produced four borrows, all aimed at `fix-until-green`, none at the orchestrator whose name the repo carries.
- `ECC` yielded two borrows despite being the named model for five subsystems — it warrants a full re-diff, not a footnote.
- **`skills/contracts/` (contract-author, contract-auditor) received zero of 72 borrows.** That is the single largest hole, and it lands exactly on the contract-first-architecture debt ACKNOWLEDGMENTS confesses.
- `skills/git/` (4 skills) got one borrow. Of ten role skills, five borrows total, four of them to `qe-agent` alone — backend, frontend, infrastructure, observability, performance, db-migration, and docs got nothing.
- The orchestrator's four borrows are all peripheral (team-sizing, ownership, circuit-breaker, a parallelize gate); `phase-guide`'s 14 phases, mission interpretation, and workflow orchestration were untouched.
- Net effect: the sweep optimized for where SM already has dense prose to compare against, not where SM is thin.

**Attribution debt this sweep cannot close:** ACKNOWLEDGMENTS:4-7 confesses debt on the orchestrator, contract-first architecture, role-agents, and the QA-gate — all predating the May-2026 window. Every uncredited upstream found here is a 2026-07 intake. Closing the original four requires SM's own early git history (`16d6d64` onward, 2026-03-10) and whatever the author was reading then; **no repo in this 26-clone corpus is plausibly that ancestor.** Track as its own ledger row.

**Bookkeeping:** the sweep returned 27 verdict rows against a 26-repo brief. The off-by-one is **unreconciled/unverified** and should be resolved when `lineage.yml` is seeded.

## 8. The Repeatable Skill

**Name recommendation:** `upstream-lineage-sweep` (SM-original; `lineage`, `attribution`, `upstream drift` kept as trigger words only).

**Placement:** `skills/workflows/upstream-lineage-sweep/` — SKILL.md + `references/{lineage-manifest-schema.md, verdict-rubric.md, sweep-phases.md}` + `evals/evals.json`.

**Frontmatter** (PSFS-conforming; no `<`/`>` in field values; description under 1024 chars; `version` top-level; Extended fields declared):

```yaml
---
name: upstream-lineage-sweep
version: 1.0.0
description: >-
  Re-verify what this library borrowed from every upstream repo it tracks, and catch the
  moment an upstream changes out from under a shipped skill. Reads a lineage.yml manifest
  of upstreams with a last_reviewed commit ref per repo, runs git log since that ref
  instead of re-reading whole trees, and returns four things: verdicts (confirmed lineage
  vs none), stale artifacts (files in this repo that are now factually wrong because
  upstream moved), surviving borrows (patterns worth adopting, each with gap evidence
  proving this repo lacks it), and attribution gaps (credited in a skill body but missing
  from ACKNOWLEDGMENTS). Hands findings to plan-intake as ledger rows. Use when the user
  says check our upstreams, refresh attribution, did upstream change, are our borrows
  stale, audit lineage, who do we owe credit to, re-run the lineage sweep, or before
  publishing a release that claims derivation. Also use after cloning a new candidate
  repo to decide adopt, decline, or no lineage. Does not adopt anything itself.
allowed-tools: ["Read", "Grep", "Glob", "Bash", "Write", "Edit", "Task"]
composes_with: ["plan-intake", "skill-review", "repo-deep-dive", "skill-writer"]
---
```

**`lineage.yml` manifest schema** (repo root; the artifact that makes the next run cheap):

```yaml
version: 1
generated: 2026-08-06
sweep_ref: <SM commit at which this sweep ran>
upstreams:
  - id: mattpocock-skills                 # stable key, used as the ledger source tag
    url: https://github.com/mattpocock/skills
    clone_path: /Users/johns/Repos/...    # local path; may be absent
    license: MIT
    verdict: CONFIRMED_LINEAGE            # CONFIRMED_LINEAGE | NO_LINEAGE | UNREVIEWED
    verdict_date: 2026-08-06
    last_reviewed_ref: d574778            # THE load-bearing field: next run = git log last_reviewed_ref..HEAD
    tree_clean_at_review: true            # false => findings are provisional (the 7-repo gap)
    credited: true                        # is there an ACKNOWLEDGMENTS section?
    credit_anchor: "ACKNOWLEDGMENTS.md#mattpocockskills"
    attribution_required: true            # license/convention obligation
    derived_artifacts:                    # SM files whose claims depend on this upstream
      - path: skills/workflows/caveman/SKILL.md
        claim: "Adapted from mattpocock/skills caveman (MIT)"
      - path: skills/meta/skill-review/references/audit-checklist.md
        claim: "CB-2 writing-great-skills doctrine"
    watch_paths:                          # upstream paths whose change invalidates a claim
      - skills/productivity/grilling/SKILL.md
      - skills/engineering/codebase-design/SKILL.md
    ledger_prefix: CB                     # ID prefix in docs/REMAINING-WORK.md, if any
    notes: "Divergence recorded in docs/adr/0001-keep-caveman-zoom-out.md"
```

**Step list:**

1. **Load the manifest.** No `lineage.yml` → bootstrap mode: enumerate candidate clones, write `UNREVIEWED` rows, and run a full read for each. With a manifest, every repo is a delta pass.
2. **Clean-tree gate (blocking).** For each clone, `git status --porcelain`. Dirty → record `tree_clean_at_review: false`, mark all findings provisional, and surface the repo in the coverage-gaps section. **Never silently review a dirty tree** — that is the failure this sweep hit seven times.
3. **Delta enumeration.** `git log --oneline <last_reviewed_ref>..HEAD` plus `git diff --name-status <last_reviewed_ref>..HEAD -- <watch_paths>`, and `git log --diff-filter=D --name-only -- "*/SKILL.md"` to catch deletions (this is how `writing-great-skills` and `productivity/caveman` were caught).
4. **Verdict pass** — only for `UNREVIEWED` rows or when the manifest's verdict is challenged. Word-boundary grep for distinctive upstream tokens across SM (never substrings — `ratel` matched `deliberately` 63 times and `swarm` is ordinary English), then read every hit in context. Direction check: compare first-commit dates before asserting derivation (this is how The-Hive was correctly inverted).
5. **Stale-artifact pass.** For every `derived_artifacts` entry, re-verify the claim against upstream HEAD. Any claim whose watch path changed or was deleted becomes a correction row with file, wrong text, and the fix.
6. **Borrow pass with mandatory gap evidence.** A borrow is only reportable with a grep or file read proving SM lacks it, plus checks against `docs/COMPLETED-WORK.md` (already shipped?) and `docs/FUTURE.md` (already declined?). No gap evidence, no row.
7. **Dedup + adversarial panel.** Collapse borrows that are one mechanism against one target (Decision 5's three-into-one). Reject anything that rewrites working code for polish, takes an upstream identity, or requires a spec change with a known conflict.
8. **Attribution reconcile.** Any upstream with `attribution_required: true` and `credited: false`, or named in a skill body but absent from ACKNOWLEDGMENTS, becomes a correction row.
9. **Emit + hand off.** Write the four result sets, hand to `plan-intake` for ledger rows under each upstream's `ledger_prefix`, then **update `last_reviewed_ref` to each upstream's current HEAD and commit `lineage.yml`** — the step that makes run N+1 cheap.

## 9. Sequencing

**Wave 0 — corrections, no dependencies, parallelizable now.** C-1, C-3, C-4, C-8, C-16 through C-20, C-22, C-23, C-24, C-25, C-27, C-29 are independent single-file edits. C-9/C-10 (Antigravity) go together and touch installer + contract + golden tests. C-11 (SIGPIPE) is standalone and should land before any new lint work. C-12/C-13 (freellmapi) go together. C-15 lands with the pxpipe body edits. **Gate:** C-14 (beads commands) must land *before* UL-13 converts that file to a stub, or the stub replaces content nobody verified.

**Wave 1 — decisions, all blocking.** Decisions 1–9 in §4. Decision 3 gates C-5/C-6/C-7 and blocks UL-21 (trust tier must be a derived concept, not a field) and the declined `cognitive_patterns` field. Decision 1 gates C-2 and UL-63. Decision 4 gates C-21. Decision 5 gates UL-15 scope. Decision 6 gates UL-62's name. Decision 7 gates the davidondrej rows (UL-19, UL-28, UL-29) *and* their ACKNOWLEDGMENTS section. Decision 8 gates C-26/C-30.

**Wave 2 — attribution.** C-26 (seven sections) then C-30 (rewrite the disclaimer). Ship credit **with or before** the borrows it covers, never after. Open the early-history archaeology row here.

**Wave 3 — three independent parallel tracks.**
- *Tooling track (serialized internally):* UL-15 (catalog authority) first, because UL-21 (trust tier check), UL-42 (resource-graph lint), and UL-41 (semantic anchors) all extend the same scripts and would conflict. UL-7 and UL-20 can run alongside — different files. UL-45 and UL-46 after UL-15.
- *Loops/gates track:* UL-1 → UL-3 → UL-12 in that order (UL-3's three-state exit code changes the `gate()` composition UL-12 builds on). UL-4, UL-5, UL-24 are independent edits to `eval-split-hygiene.md` — serialize those three against each other only. UL-17, UL-25, UL-26, UL-27, UL-52 are independent.
- *Authoring/doctrine track:* UL-16 first (it defines the vocabulary UL-31, UL-32, UL-23, UL-57 all extend), then the rest in any order. UL-38 (adaptation policy ADR) should land early in this track — it is the written form of the rule Decision 6 applies.

**Wave 4 — new builds.** UL-19 (dangerous-command guard) after F9 reconciliation. UL-62 (human-steps script) after its name is fixed. Both trigger the catalog ripple, so they land *after* UL-15 makes the name lists guardable — that is the whole point of doing UL-15 first.

**Wave 5 — the repeatable skill.** Build `upstream-lineage-sweep` last and seed `lineage.yml` from this document's §2, with `last_reviewed_ref` set to each clone's current HEAD, `tree_clean_at_review: false` for the seven dirty repos, and `verdict: UNREVIEWED` for `space-agent`, `RuView`, `trinity`, and `context-engineering-intro`. Reconcile the 27-vs-26 count at this step. The first re-run then becomes a `git log --since-ref` delta instead of a second full sweep.