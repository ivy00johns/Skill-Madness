# Maxed-out-window review — 2026-07-08

**Scope:** everything shipped while Fable 5 usage was capped mid-build and after — PRs #45 (`93d1c20`, SR1–SR24 + MT-1), #46 (`8619b00`, PF1–PF5), #47 (`101a8d5`, CB-1–CB-3 + UF-1), #48 (`0f5a00c`, plan-intake v1.2.0) — plus the loops-library integration audit, the mattpocock borrow-fidelity audit (upstream at v1.1.0 = `d574778`), and the fable-handoff artifact review.

**Method:** `/orchestrator` review mode — three parallel read-only review agents (diff-soundness, loops-integration, mattpocock-fidelity, all on Fable 5) + an inline review of the fable-handoff script/manual against `model-adaptation`'s own refusal-and-fallback doctrine.

**Headline verdict:** the maxed-out-window changes are **sound** — zero critical findings. Gates fresh on review day: catalog PASS @ 71, lint 0 errors, bats 338/343 (the 5 fails are one fixture bug, MR-4, environmental-only; CI's gating run passes). The actionable findings were intaken as **MR-1–MR-8** and **CB-9–CB-10** in `docs/REMAINING-WORK.md` (this file is the `[MWR]` source).

---

## 1. Diff soundness (PRs #45–#48)

### Findings

**CRITICAL** — none.

**MAJOR M1 — The canonical `allowed-tools` frontmatter form is invisible to the shell tooling, which still reads only the deprecated `allowed_tools` alias.** All 71 catalog skills use the hyphenated form (zero use the underscore form; migrated back in PR #6), the frontmatter spec declares hyphen canonical, yet:

- `scripts/convert.sh:526` — `get_field "allowed_tools"` means the qwen converter's `tools:` mapping is dead code. Verified empirically: 0 of 34 converted qwen files carry a `tools:` line, so every qwen conversion silently loses the tool whitelist.
- `scripts/convert.sh:244` — the `[copilot] stripped allowed_tools/owns` stderr warning never fires (verified: 0 lines on a full copilot run). Both halves of the condition are dead: the field-name mismatch, plus `fm_has_field "owns"` is always false because dict values never emit a scalar cache entry (`scripts/lib/frontmatter.sh:185` — same behavior in the pre-SR4 parser).
- `scripts/lint-skills.sh:461` — every one of the 10 role skills gets a false "role skill missing recommended 'allowed_tools'" WARN on every lint run, even though all 10 declare `allowed-tools`.
- `README.md` FAQ (~line 680) and `scripts/README.md:61` document stderr output that cannot occur.

Pre-existing since PR #6 — not introduced by this range — but SR4 rewrote `frontmatter.sh` and SR9/SR12/SR18/SR24 touched lint and the README all around it without catching it. → **MR-3**.

**MINOR M2 — The new SR13 test fixture breaks on machines with git commit-signing** (the only defect actually shipped by this range). `tests/installer/bats/05-lint-rules.bats:356` (`_mk_changed_fixture`) sets `user.email`/`user.name` in its throwaway repo but never `commit.gpgsign false`, so an inherited global 1Password signing config makes `git commit` fail non-interactively (status 128). All 5 `lint --changed` tests (261–265) fail locally; all 5 pass with `GIT_CONFIG_GLOBAL=/dev/null`. CI's Ubuntu gate passes (no signing config on runners). → **MR-4**.

**MINOR M3 — Stale "Used by" list for `disable-model-invocation`.** `skills/meta/skill-writer/references/frontmatter-spec.md:136` names 13 users; 27 catalog skills actually set it (adds contract-auditor and all 13 loop skills). (The `requires_claude_code` wrong-criterion issue at ~:152/:231 is real but already tracked as PF2.) → **MR-7a**.

**MINOR M4 — REMAINING-WORK banner heading not updated by #47** (omitted CB-1–CB-3, stale as-of date). → fixed by the MR/CB-9/10 intake itself.

**NIT** — SR4's "~25s" convert claim measured 34.1s wall here (machine-dependent; direction and magnitude hold). The Haiku no-`effort` fact is restated in three places (small drift surface). `.markdownlint.json` is wired into neither CI nor any script; 169 style-class violations on the 44 changed files, essentially all pre-existing debt (not filed).

### Spot-check verifications (all pass)

- **SR1 / PF3:** 34/71 is exactly right on disk — 37 `requires_claude_code: true`, 32 `false`, 2 flag-absent = 71; portable = 34. Both hand-maintained README numbers agree today. A full convert run corroborates: 411 processed = 71 (claude-code) + 10 hosts × 34; 370 skipped = 10 × 37.
- **SR2:** `.github/workflows/lint-skills.yml:99-128` — the `installer-ubuntu` job runs `catalog.sh --check` then the full bats suite, and "Installer + Catalog (Ubuntu)" is confirmed via the GitHub API as a required status check on main. Genuinely gating.
- **SR3:** `install.sh --wire-hooks` matches its claims — opt-in default-off, TTY prompt defaulting to No, timestamped backup before first write, idempotent, refuses malformed settings.json, propagates via `ATS_WIRE_HOOKS`.
- **SR4:** the parse-once cache design is sound — per-process cache dir keyed `$$.$RANDOM`, path-collision fallback re-parses, failed parses never cached, EXIT trap clears the cache, PyYAML-absent fallback degrades exactly like the old code. Preserves (does not regress) prior parser behavior, including the M1 blind spot. SR12/SR18/SR24 guards present and covered by passing tests 256–260.
- **MT-1:** no contradictions, no duplicated tables. Canonical doctrine in model-adaptation; the priced ladder lives only in `references/model-effort-tiering.md` (internally consistent — every tier's output price is 5× input). Orchestrator, workflow-orchestration.md, loop-controller Step 6, and use-freellmapi all point rather than restate. Repo-wide grep found no stray copy of the ladder.
- **PR #46:** all PF rows verified against reality (PF1 empirically: converted `diagnose-loop` references `scripts/hitl-loop.template.sh`, which convert.sh never ships).
- **PR #47:** CB-1–CB-3 rows well-formed; CB-4–CB-8 in FUTURE.md as claimed; prefixes registered.
- **PR #48:** plan-intake 1.1.1 → 1.2.0; contains everything claimed (two-column review table, gate tied to the plain-language sentence, house-format rule, YAGNI over-build pass with `[speculative]` routing).
- **Ledger internals:** 25 open rows matching the header prose; IDs unique; statuses valid; every source link resolves.

### Gates

| Gate | Command | Result |
|---|---|---|
| Catalog | `scripts/catalog.sh --check` | **PASS** — plugin.json matches disk (71); counts + README table all match |
| Bats suite | `bash tests/run-all.sh --tap` | **343 tests: 338 ok, 5 not ok** — all 5 are the M2 fixture/signing issue; re-run with `GIT_CONFIG_GLOBAL=/dev/null` → 5/5 ok. Effectively green; CI's gating run passes |
| Skill lint | `scripts/lint-skills.sh skills/` | **PASS (exit 0)** — 0 errors, 123 warnings across 77 skills (10 are M1's false `allowed_tools` WARNs) |
| Markdownlint | `npx markdownlint-cli@0.45.0` (44 changed files) | Not a repo gate — 169 style-class violations, advisory |

---

## 2. Loops integration & trigger audit

| loop | disable-model-invocation | spawned_by ok? | reachable via | guardrails declared? | registered everywhere? |
|---|---|---|---|---|---|
| loop-controller | yes | yes `["orchestrator"]` (also user front door — NIT) | slash; madness map; orchestrator | defines the stack (Step 3) | yes |
| fix-until-green | yes | yes — orchestrator actually dispatches it | slash; orchestrator wave/QA gates; loop-controller body | yes | yes |
| orchestrator-task-loop | yes | yes — dispatched at runtime detection | orchestrator (env-gated); slash | yes | yes |
| contract-conformance-loop | yes | WEAK: claims `["orchestrator"]`, never mentioned there | slash only | yes + fresh-context evaluator fully specified | yes |
| coverage-loop | yes | WEAK: same | slash; one loop-controller prose mention | yes | yes |
| perf-loop | yes | WEAK: same | slash; loop-controller prose | yes | yes |
| migration-loop | yes | WEAK: same | slash; taxonomy archetype only | yes | yes |
| babysit | yes | yes `[]` | `/babysit`, `/loop 5m /babysit` | yes + HITL section | yes |
| self-healing-loop | yes | yes `[]` | slash via `/loop` cadence | yes + HITL | yes |
| nightly-docs-and-changelog | yes | yes `[]` | `/schedule` routine; slash | yes + never-merges HITL | yes |
| dependency-health-loop | yes | yes `[]` | `/loop 30m`; slash | yes + HITL on majors | yes |
| codebase-exploration-loop | yes | yes `[]` | slash | yes (read-only loop) | yes |
| repo-cleanup-loop | yes | yes `[]` | `/loop`/`/schedule` weekly; slash | yes + HITL/no-force-delete | yes |

Registration verified three ways: plugin.json (13/13, 71 total), `catalog.sh --check` green, marketplace.json prose count correct. Lint 0 errors; no description contains `<`/`>`; all versions valid semver.

**CRITICAL — none.** No loop can auto-fire; the orchestrator's claims about the three loops it wires match those skills' text exactly, including verbatim-matching 3-failure/ping-pong no-progress semantics.

**MAJOR 1 — Four build loops claim orchestrator parentage the orchestrator doesn't honor.** contract-conformance-loop, coverage-loop, perf-loop, migration-loop all declare `spawned_by: ["orchestrator"]` and say "or have the orchestrator dispatch it", but a recursive grep of `skills/orchestrator/` (SKILL.md + all 11 references) returns ZERO mentions of any of the four. Because `disable-model-invocation` hides them from model invocation, an orchestrated build following the playbook never reaches them. → **MR-1**.

**MAJOR 2 — The "pick the specific loop" promise has no machine-followable table behind it.** madness routes all loop intents to loop-controller claiming "(it picks the specific loop + primitive)", but loop-controller's contract picks the *primitive*; `skill-explorer/references/routing-table.md` — which madness leans on for the long tail — contains ZERO rows for any of the 13 loop skills. A user arriving with "keep my PR green" or "keep deps fresh" has no documented path to babysit / dependency-health-loop / nightly-docs-and-changelog / repo-cleanup-loop. → **MR-2**.

**MINOR 3 — Long-run hygiene is inherited only transitively.** loop-controller Step 6 carries all four spot-checked model-adaptation patterns and points at `long-run-hygiene.md`, but babysit, self-healing-loop, and migration-loop contain zero hygiene wiring of their own despite `long-run-hygiene.md` instructing per-loop confirmation. Drift: Step 6 landed with the MT-1 sweep after the loops shipped at 1.0.0. → **MR-5**.

**MINOR 4 — Five descriptions sit near the 1024-char hard ceiling** (orchestrator-task-loop 1017; repo-cleanup-loop 995; migration-loop 983; babysit 962; nightly-docs-and-changelog 954). Any trigger-text addition flips these to schema FAIL. → **MR-7e**.

**NITs** — loop-controller's `spawned_by` understates its madness/user parentage (informational field, harmless); `fix-until-green-workspace/` is gitignored eval debris (cosmetic).

Everything else clean: all 12 concrete loops carry the full 5-part contract with stop conditions enumerating the mandatory stack; contract-conformance-loop's fresh-context evaluator is exactly per design; all prod-touching loops have "HITL is load-bearing" sections; every cited reference exists on disk; `composes_with` targets all resolve.

---

## 3. Mattpocock borrow fidelity (upstream v1.1.0 = `d574778`)

**CRITICAL C1 — The entire v1.1.0 refresh existed only in one untracked file, and the intake it promised never happened.** The delta doc (`DeepResearch/skills-comparative_deepdive/source-material/11-delta-2026-07.md`) was untracked in its repo; the promised expand–contract + HITL/AFK rows existed nowhere in Skill-Madness. → resolved by this intake (**CB-9/CB-10** filed; delta doc committed in the vault with IDs stamped back).

**MAJOR M1 — the delta doc's "Negative Space lives in GLOSSARY.md" claim was false at v1.1.0.** Upstream added both failure modes in `0847bb3`, then DROPPED Negative Space before tagging in `af6d692` ("Drop Negative Space; keep Negation only"). Negation itself is real: `writing-great-skills/SKILL.md:83` + `GLOSSARY.md:161`. → corrected in the delta doc 2026-07-08.

**MAJOR M2 — the keep-despite-upstream-deletion decision (caveman `7d3ada9`, zoom-out `e112a6b`) was recorded nowhere durable in Skill-Madness**; `ACKNOWLEDGMENTS.md:90-91` still cites both upstream paths as if live. → **MR-6**.

**MINOR** — CB ledger pinned v1.0.1 while CB-1 cites a v1.1.0-only path (→ fixed by this intake's preamble re-pin); CB-7 in FUTURE.md uses dead upstream names `to-prd`/`to-issues` (→ **MR-7b**); caveman's "Same behavior, same examples" overstates — our examples never existed in any upstream revision, and ours deliberately stays model-invocable (→ **MR-7d**); `ACKNOWLEDGMENTS.md:194-196` credits caveman to karpathy-skills while the line-90 table says mattpocock fork (→ **MR-7c**).

**NIT** — zoom-out has no inline attribution (repo-level MIT notice satisfies the license); stale historical attribution paths (`engineering/diagnose`→`diagnosing-bugs`, `productivity/write-a-skill` removed) (→ **MR-7d**); grill-me/find-unknowns are clean — no misattribution, no dead references.

### Delta-doc fact-check (against v1.1.0)

| Claim | Verdict |
|---|---|
| Pulled upstream to d574778 = v1.1.0 | CONFIRMED |
| `to-prd` renamed `to-spec` | CONFIRMED (`386d4ff`) |
| `to-plan`+`to-issues` merged into `to-tickets`; to-issues deleted | CONFIRMED |
| wayfinder graduated in-progress→engineering (was decision-mapping) | CONFIRMED (`4027ea6`, `639df6e`, `0557d57`) |
| code-review graduated; 12 Fowler smells; 2 binding rules; parallel sub-agents; never rerank | CONFIRMED (`14c13c5`; SKILL.md:38-56, :40-41, :11/:58, :78-80) |
| Negation failure mode in SKILL.md body | CONFIRMED (also GLOSSARY.md:161) |
| Negative Space entry in GLOSSARY.md | **REFUTED** (dropped pre-tag, `af6d692`) — delta doc corrected |
| expand–contract technique upstream | CONFIRMED (`to-tickets/SKILL.md:40`) |
| HITL/AFK ticket typing; self-grilling breaks the contract | CONFIRMED (`wayfinder/SKILL.md:75-79`; fix `e5932a7`) |
| Upstream deleted caveman + zoom-out | CONFIRMED (`7d3ada9`, `e112a6b`) |
| Deletion reasons (quotes) | UNVERIFIABLE from git (commit messages say only "streamline" / "remove") |

**Verdict:** substantively correct but not current — everything shipped is sound; the follow-ups are commits and doc refreshes, not skill rework.

---

## 4. Fable-handoff artifact review

Context: a circulating article ("You have a few days to clone Fable 5 into Opus 4.8") prompts Fable 5 to write an "operating manual" and load it as Opus 4.8's system prompt before the July 12 plan change. The repo root held two untracked artifacts: `fable_to_opus.py` (a hardened rewrite of the article's script) and `fable_handover.md` (a 169-line extracted manual).

**Article verdict: the core mechanic is real but oversold.** A written manual transfers *discipline* — verification procedure, epistemic labeling (VERIFIED/SOURCED/ASSUMED), answer-first delivery — not capability; the weights-based edge isn't describable. "Clone Fable 5" is marketing; "port the checklists" is the honest claim, and that part works. The article's script defects (all fixed in the local rewrite): a `\!=` syntax error; no refusal handling (would silently save an empty manual on a `reasoning_extraction` refusal); text-only continuation (can 400 against thinking blocks — must echo content blocks verbatim); the false "extraction costs nothing today" claim (API bills per token regardless of the plan change); a weak trap test (plain Opus 4.8 catches 5%-vs-20% unaided). The article's pricing checks out against our own ladder ($10/$50 Fable ≈ 2× $5/$25 Opus 4.8; Sonnet intro $2/$10 through 2026-08-31).

**Local artifacts verdict: sound.** The rewrite's refusal handling and prompt framing match `model-adaptation/references/refusal-and-fallback.md` exactly — it asks for forward-looking working procedures for a successor (the documented-fine category), not a reasoning transcript (the refusal-risk category). The manual is high-quality generic craft: every procedure executable, nothing introspective, fully model-portable. Three script claims unverified against local docs (check before treating as durable): `thinking: {"type": "adaptive"}` on Opus 4.8; the `stop_details.category/.explanation` response shape; the "4,096-token prompt-cache minimum" print (cosmetic).

**Integration:** → **MR-8** (fold into `model-adaptation` as `references/capability-handoff.md` + `scripts/` + the manual as a reusable system-prompt asset; add trigger keywords; keep the manual on-demand — do not inject into Claude Code sessions, where the harness already covers most of it; note the PF1 `scripts/`-shipping interaction).

---

## 5. Disposition

All findings intaken 2026-07-08 via `plan-intake` (full table user-approved): **MR-1–MR-8** (new `MR` prefix, Source `[MWR]` = this file) + **CB-9** (expand–contract) + **CB-10** (HITL/AFK, `[speculative]`) in `docs/REMAINING-WORK.md`. Fixed by the intake itself rather than filed: the ledger banner staleness (diff M4) and the CB preamble v1.0.1 pin. Fixed same-day in the vault: the delta doc's Negative Space error + the doc committed with final IDs stamped back. Not filed (advisory): the markdownlint style debt, the convert-timing nit, the Haiku-fact triplication.
