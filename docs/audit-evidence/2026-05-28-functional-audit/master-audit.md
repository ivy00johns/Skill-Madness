# Audit Evidence: Functional Audit — Master Report (reports-v2)

```yaml
# docs/audit-evidence typed header — see docs/audit-evidence/README.md
report: 2026-05-28-functional-audit / master-audit
skill: all 49 active skills as of the audit date (repo-wide synthesis)
audit-date: 2026-05-28
revision-reviewed: unrecorded (pre-convention — the audit predates this header requirement; do not treat the findings as claims about any specific commit)
worker-config: >
  Dynamic workflow "skill-functional-audit" (audit/_tools/functional_audit_workflow.js,
  local working tree). Four phases: one functional-auditor subagent per skill;
  one skeptical-verifier subagent per skill (default stance "refuted" — re-checks
  every high-severity finding against the real files before it survives);
  six cross-cutting synthesis lens agents (dead-skills, overlap, crossref,
  conventions, doc-drift, incomplete); one master-synthesis agent.
  Model per worker: unrecorded.
verdict: >
  Healthy in substance, leaky at the seams — 11 works / 37 works-with-gaps /
  0 broken / 0 dead skills; 6 dead wiring edges; 2 CRITICAL verified findings
  (plugin.json installs 46 of 49; qe-agent schema prose contradicts the
  canonical JSON gate).
evidence-links:
  - skills/roles/qe-agent/references/qa-report-schema.json
  - skills/roles/qe-agent/references/qa-report-schema.md
  - skills/orchestrator/SKILL.md
  - skills/orchestrator/references/phase-guide.md
  - skills/meta/skill-writer/references/frontmatter-spec.md
  - skills/orchestrator/references/file-ownership.md
  - .claude-plugin/plugin.json
  - .claude-plugin/marketplace.json
source: audit/reports-v2/00-MASTER-AUDIT.md (gitignored local working tree — .gitignore line 34)
republished: 2026-07-24 (verbatim below the divider; only this header was added)
```

> **Staleness note (republish time):** these findings describe the 49-skill tree of
> 2026-05-28. Most were subsequently fixed — the `FA`-prefixed remediation rows were
> shipped and swept to `docs/COMPLETED-WORK.md` (FA-fidelity sweep, PR #32), and the
> catalog has since grown to 71 skills (per `CLAUDE.md`). Re-check any finding against
> the current tree before acting on it; this document is evidence of what the audit
> found, not a description of current state.

---
# Master Audit — Skill Madness (reports-v2)

**Date:** 2026-05-28 · **Scope:** all 49 active skills + repo docs/manifests · **Layer:** function / triggerability / completeness / real bugs (NOT the surface-level style/compliance pass already in `audit/reports/`).

**Ground truth (re-verified this pass):** `find skills -name SKILL.md -not -path '*/archive/*'` → **49** skills (orchestrator 1, contracts 2, git 4, meta 4, roles 10, workflows 28). Archive holds 6, not counted. The plugin install manifest lists **46**.

---

## 1. Executive Summary

The ecosystem is **healthy in substance, leaky at the seams.** Every one of the 49 skills is individually executable on its happy path — there are **zero stubbed, abandoned, or truly dead leaf skills**, and the orphan-reference-file roster is genuinely empty. The role-agent cohort (10 skills) is the strongest-built part of the repo and should be the template everything else is normalized toward. What's broken is almost entirely **integration wiring and self-documentation**: skills that advertise a spawner that never calls them, producer/consumer pairs that disagree on a file path, and bundled schema docs that contradict the canonical schema the gate actually parses.

**Health tally (functional verdict):**

| Bucket | Count | Meaning |
|---|---|---|
| Works | 11 | Executes end-to-end, no functional gap |
| Works-with-gaps | 37 | Executes, but has a real seam defect (wiring, path, schema, or doc) |
| Incomplete / half-built | 0 (skill-level) | No skill is a stub; defects are finish/trim items inside otherwise-complete skills |
| Broken | 0 | No skill fails outright on its own happy path |
| Dead | 0 (skills) / **6 dead wiring edges** | No dead leaf skill; the deadness is in the spawn graph |

**The deadness is in the WIRING, not the skills.** This is the finding the prior audit missed: the spawn graph overstates reality. Six `spawned_by` edges are decorative — the declared spawner never invokes the skill in any executable step. Tools and graph-readers (including `skill-explorer` and `skill-review` themselves) will trust those edges and propagate the lie.

**The 5-8 things that matter most before the next phase:**

1. **`plugin.json` silently installs only 46 of 49 skills.** `living-plan`, `plan-intake`, and `render-sanity` are missing from the install manifest. `render-sanity` is the orchestrator's *hard ship gate* — a plugin-manager install yields an orchestrator referencing a skill the user doesn't have. **(CRITICAL, verified.)**
2. **The QE gate can silently reject a conformant-looking report.** `qe-agent`'s bundled `qa-report-schema.md` prose describes a `findings[]`/`passed[]` shape that does **not** match the canonical `qa-report-schema.json` (`scores/test_results/blockers/issues/gate_decision`) the orchestrator actually parses. An agent following the prose emits a report the gate rejects. **(CRITICAL, verified.)**
3. **Two role agents promise a QE score that does not exist.** `observability-agent` and `performance-agent` both tell the executing agent its work feeds a qe-agent "observability"/"performance" score that gates the build — but the schema has exactly 5 score dimensions and neither is among them. Their output is an orphan at the gate boundary. **(verified: `grep -c -i observability\|performance qa-report-schema.json` → 0.)**
4. **Six dead spawn edges** mislead the dependency graph: `code-review-agent`, `context-manager`, `project-profiler` (declared orchestrator-spawned, never invoked in any phase), `wiki-research` (claims 8 spawners, 2 real), `render-sanity` (qe-agent edge not reciprocated). Trim or wire each.
5. **Producer/consumer path disagreements break real handoffs:** `contract-author` writes `contracts/types.<ext>` (file) but `contract-auditor` reads `contracts/types/` (dir); `llm-wiki` writes `wiki/index.md` but `wiki-research` auto-detects root `index.md`; `setup-project-skills` bakes a *broken* contract-template path (`.../references/templates/<x>`, no such dir) into every consumer repo's durable docs.
6. **Three scripts diverge from their own docs:** `nano-banana` (env-key lookup, `--resolution`, model tiers all mis-documented), `sync-skills` (body promises an "ask before replacing" prompt; script does silent `rm -rf`), `mermaid-charts` (documents an `mmdc` render pipeline its `allowed-tools` can't run).
7. **Repo docs miscount the library (47 vs 49)** in CLAUDE.md, START-HERE.md, README (self-contradicting), and marketplace.json (fabricated sub-counts) — and there's no CI guard, so it will rot again.
8. **Ownership map is not actually canonical:** `file-ownership.md` bills itself as the override-everything map but omits 7 of its owning skills and creates 3 unresolved nesting conflicts (`docs/adr/`, `docs/agents/`, `skills/`).

None of this requires deleting a skill. Every defect is a **finish, trim, wire, or doc-fix.** The single human decision worth surfacing is whether `context-manager`'s build-loop role should be wired into the orchestrator or reframed as user-only (its logic is already duplicated by `handoff-protocol.md`, which is what actually runs).

---

## 2. Skill Scorecard (worst-first)

Functional verdict: **W** = works · **WWG** = works-with-gaps. Triggerability: **fires** = model+user · **spawn** = spawn-only · **collides** = live trigger collision · **explicit** = user slash only · **dead-edge** = advertised spawn path doesn't fire.

| Skill | Cat | Verdict | Trigger | One-line |
|---|---|---|---|---|
| qe-agent | roles | WWG | spawn | Bundled schema prose (`findings[]/passed[]`) contradicts canonical JSON gate → agent can emit a report the gate rejects. **CRITICAL.** |
| code-review-agent | roles | WWG | spawn / **dead-edge** | Read-only/Write frontmatter contradiction; orchestrator routes diff review to external `/code-review`, so this skill's spawn edge is bypassed; output path undefined. |
| context-manager | wf | WWG | fires / **dead-edge** | User side works; orchestrator-spawned validation role is never invoked (logic duplicated by `handoff-protocol.md`). |
| observability-agent | roles | WWG | spawn | Promises a qe-agent "observability score" that does not exist in the schema; owned dirs absent from ownership map. |
| performance-agent | roles | WWG | spawn | Promises a qe-agent "performance score" / SLA gate that does not exist; report is an orphan at the gate. |
| setup-project-skills | wf | WWG | explicit | Bakes a broken contract-template path into consumer repos' durable docs; "fail loud" claim contradicts soft-fallback consumers. |
| nano-banana | wf | WWG | fires | Script diverges from body on API-key lookup, `--resolution`, and flash/pro model tiers → agent misreports behavior. |
| sync-skills | wf | WWG | fires | Body promises "ask before replacing"; script does silent `rm -rf`. `owns: skills/` nests over every skill. README cites nonexistent `--force`. |
| mermaid-charts | wf | WWG | fires | `mmdc` render pipeline unrunnable (no Bash in allowed-tools); `other.md` lists 7 chart types with zero syntax. |
| wiki-research | wf | WWG | fires / **dead-edge** | `spawned_by` claims 8 spawners, 2 real; Step 1 uses Bash not in allowed-tools; index-layout mismatch with llm-wiki. |
| llm-wiki | wf | WWG | fires | Writes `wiki/index.md`; sibling wiki-research auto-detects root `index.md` → produced wiki not found. URL ingest needs WebFetch (not declared). |
| project-profiler | wf | WWG | fires / **dead-edge** | User path works + feeds real consumers; orchestrator spawn edge is frontmatter-only; references a nonexistent "spec" + absent validator. |
| contract-auditor | contracts | WWG | spawn | Reads `contracts/types/` (dir) vs author's file; "consumed by qe-agent" handoff has no artifact path. |
| contract-author | contracts | WWG | fires | Shared-types path disagrees with auditor; two divergent format-decision trees; checklist runs `tsc` without Bash. |
| skill-review | meta | WWG | fires | Coverage-gap check points at nonexistent `docs/architecture.md`; bare-name cross-plugin ref. |
| skill-update | meta | WWG | fires | `owns: skills/` misuses agent-role field and nests over sync-skills' subdir. |
| skill-writer | meta | WWG | fires | Documents a validation gate (lint scripts) it can't run (no Bash). |
| orchestrator | orch | WWG | fires | Two stale `skills/`-prefix path typos; bare (unprefixed) external plugin names in composes_with against its own spec. |
| backend-agent | roles | WWG | spawn | Data-layer scaffold writes to dirs no role owns; CORS step-pointer off by one; asymmetric wiki-research edge. |
| security-agent | roles | WWG | spawn | Wires secret-scan baseline to the toolkit's own CI scanner via a non-resolvable path (wrong tool, wrong context). |
| docs-agent | roles | WWG | spawn | Tells agent completeness/code_quality scores gate the build (they don't); owns `docs/` but doesn't carve out 2 nested owners. |
| infrastructure-agent | roles | WWG | spawn | `.env.example` ownership collides with backend-agent; docker-compose owner ambiguous across orchestrator docs. |
| db-migration-agent | roles | WWG | spawn | Validation checklist cites a contract section name (`required_indexes`) that doesn't exist; absent from ownership map. |
| maintain-context | wf | W | fires | `docs/adr/**` ownership silently overridden by docs-agent's `docs/` per spec precedence. |
| playwright | wf | WWG | fires | Step 5 never tells agent to author report.json/report.md; `--reporter=json` doesn't persist to file. |
| render-sanity | wf | WWG | fires / **dead-edge** | Says "Phase 12", orchestrator runs it at Phase 13; qe-agent spawn/compose edge not reciprocated. |
| deployment-checklist | wf | WWG | fires | Non-portable `grep -oP` in env diff; project-specific happy-path payload. |
| repo-deep-dive | wf | WWG | fires | Body bans ASCII diagrams; the template it points to prescribes them; Phase-5 vault schema drifts from llm-wiki. |
| skill-explorer | meta | W | **collides** | Live trigger collision with in-session `find-skills`; routing table points at plugin skills not loaded. |
| settings-consolidator | wf | WWG | fires | Baseline ships `Bash(./*)` its own rules say to flag; Step-1 `find` doesn't exclude the global merge target. |
| ui-brief | wf | WWG | fires | Two stale example-file pointers in closing section. |
| git-commit | git | WWG | fires | Omits the repo-mandated `Co-Authored-By` trailer; lowercase/no-scope rules contradicted by repo history. |
| git-pr-feedback | git | WWG | fires | PR-author lookup for replied-detection never fetched; placeholder-substitution subtlety. |
| git-post-merge-cleanup | git | WWG | fires | Merge-base reference drift (`origin/$DEFAULT` body vs local `$DEFAULT` ref) — errs safe. |
| living-plan | wf | WWG | fires | `cp template/...` assumes skill dir is cwd; uncounted/unlisted in CLAUDE.md + README + plugin.json. |
| interactive-doc | wf | WWG | fires | `conversation_search` is not a Claude Code tool; half-populated metadata stub. |
| claude-design-brief | wf | WWG | fires | Stale "13 categories" count vs 12-row table. |
| dependency-coordinator | wf | W | spawn | Finished, reachable, all refs real. Only nit: stale CLAUDE.md count. |
| plan-builder | wf | W | fires | Solid synthesis skill; minor cross-link asymmetry (wiki-research claims it as a spawner). |
| plan-intake | wf | W | fires | Finished fail-closed intake; absent from CLAUDE.md/README/plugin.json. |
| work-item-brief | wf | W | fires | Finished; writes `out-of-scope/` not declared in owns.patterns. |
| diagnose-loop | wf | W | fires | Finished; trigger overlap with `superpowers:systematic-debugging`. |
| grill-me | wf | W | fires | Finished; one-directional compose edge to plan-builder. |
| architecture-rescue | wf | W | fires | Finished and well-traced; cosmetic gloss nit only. |
| zoom-out | wf | W | explicit | Finished; mislabeled "spawn-only" (nothing spawns it); description reads as auto-trigger bait but auto-invoke is disabled. |
| railway-deploy | wf | W | fires | Finished; two unused imports in script template. |
| frontend-agent | roles | W | spawn | Finished; bare plugin names where its own spec says to prefix `superpowers:`. |
| caveman | wf | W | fires | Finished tiny mode-toggle; description omits one valid exit phrase the body accepts. |
| git-pr | git | W | fires | Finished gh-CLI reference card; optional anti-pattern guard missing. |

---

## 3. DEAD / Unreachable / Never-Triggered

**No leaf skill is dead.** The deadness is in **wiring edges** — `spawned_by` claims a caller that never calls. Disposition column: **wire** = add the missing invoke step · **trim** = drop the false edge · **relabel** = fix the roster metadata.

| # | Dead edge | Evidence (re-verified) | Disposition (HUMAN DECISION where noted) |
|---|---|---|---|
| 1 | `code-review-agent` ← orchestrator | `code-review-agent` is `disable-model-invocation:true` (spawn-only), but orchestrator's only concrete review action routes to external `/code-review` (`mission-interpretation.md:117`). It appears in orchestrator dispatch *prose* (`SKILL.md:51`) but no phase actually spawns it. | **HUMAN DECISION:** wire (add an orchestrator phase that spawns it as a parallel review role) **OR** trim (document that `/code-review` CLI substitutes, and define when this skill is chosen). It is bypassed in practice today. |
| 2 | `context-manager` ← orchestrator | Repo-wide grep: appears in orchestrator ONLY at `SKILL.md:20` (composes_with array). The Context Management section defers to `handoff-protocol.md`, which self-validates (`:58-61`) and never hands control to context-manager. ~90% of its logic is duplicated there. | **HUMAN DECISION:** wire (have `handoff-protocol.md` defer validation to context-manager, making the protocol a thin caller) **OR** trim (drop `spawned_by:[orchestrator]`, reframe as user-invocable compaction helper). Either way the duplicated logic must live in one place. |
| 3 | `project-profiler` ← orchestrator | `spawned_by:[orchestrator]` reciprocal with composes_with, but orchestrator body names it in no phase/INVOKES/dispatch/research list. User path fires; output is consumed by deployment-checklist/dependency-coordinator/code-review-agent. | wire (orchestrator pre-build invoke: "if no CLAUDE.md/profile.yaml, run project-profiler") **OR** trim (reframe as user-invocable + consumed-by-orchestrator). |
| 4 | `wiki-research` ← 6 phantom spawners | Declares 8 spawners; grep confirms only `orchestrator` (Phase 0) and `code-review-agent` (body:64) invoke it. repo-deep-dive/project-profiler/backend/frontend/security/plan-builder never reference it. | trim `spawned_by` to `[orchestrator, code-review-agent]` (low risk) **OR** wire the role agents that genuinely should open with wiki context (backend/frontend/security are real candidates). |
| 5 | `render-sanity` ← qe-agent | render-sanity declares qe-agent in `spawned_by`/composes_with, but qe-agent uses the `playwright` skill, never render-sanity. (orchestrator edge is real and reciprocated — render-sanity is NOT dead overall.) | trim qe-agent from render-sanity's edges **OR** add a qe-agent body line routing UI-state criteria to render-sanity. |
| 6 | `zoom-out` mislabeled spawn-only | `disable-model-invocation:true`, `spawned_by:[]`, nothing in repo names it. Only entry is `/zoom-out`. Per `frontmatter-spec.md:127` this is *intended*. Roster mislabels it "spawn-only". | **relabel** to "user-invocable-explicit-only"; reframe description's "Use when..." as reasons to explicitly invoke. No body change. |

Adjacent (description-level, not dead): `setup-project-skills` is explicit-slash-only (`disable-model-invocation:true`) so its natural-language trigger phrases are inert — same class as zoom-out; relabel + trim description. `skill-explorer` collides live with the in-session `find-skills` plugin (both model-invocable on "find a skill") — see §4.

---

## 4. Overlap & Redundancy Map

No merges are mandatory; the fix is mostly reciprocal "not-this-skill" boundary clauses. Four clusters + three pairwise collisions.

**Cluster A — Design briefs (5 skills).** `ui-brief` (Markdown brief for a Code build), `claude-design-brief` (paste-ready claude.ai canvas prompt), plus plugins `hallmark` (redesign/audit), `ui-ux-pro-max` (design+build), `frontend-design` (build). claude-design-brief already disambiguates against ui-brief; **ui-brief does not return the favor.** *Fix:* one boundary sentence in ui-brief — it produces a brief not code; for building use frontend-design/ui-ux-pro-max, for the canvas use claude-design-brief, for a redesign audit use hallmark, to review a running app use ux-review.

**Cluster B — Planning/intake (4 skills).** `plan-builder` (goal+source → plan), `living-plan` (set up planning docs), `plan-intake` (report → ledger entries), `work-item-brief` (ledger entry → brief). Chain is well-wired; risk is *first-utterance routing* ("plan this out" after pasting an audit). *Fix:* one "not-this-skill" pointer each in plan-builder ("to file an existing report, use plan-intake") and living-plan ("to produce plan content from a goal, use plan-builder").

**Cluster C — Knowledge-doc (5 skills).** `interactive-doc`'s trigger list literally includes "architecture diagram" (owned by `mermaid-charts`) and "wiki page" (a 3-way magnet with `llm-wiki` build / `wiki-research` read). *Fix (cheapest single change):* narrow interactive-doc's two weak tokens → "architecture deep-dive as a rich doc", "wiki page with an HTML companion". **Plus a functional break inside this cluster:** llm-wiki builds `wiki/index.md` but wiki-research detects root `index.md` — pick one canonical layout, document once, align repo-deep-dive's Phase-5 vault example to it.

**Cluster D — Meta (4 skills).** `skill-explorer` vs in-session `find-skills` is the one **live coin-flip collision** (both model-invocable on "find a skill for X"). skill-explorer also over-claims into skill-review ("any meta-question"). skill-writer body over-claims into skill-review ("reviewing existing skills for spec compliance"). *Fix:* add boundary to skill-explorer (installing new = find-skills; navigating yours = this; auditing quality = skill-review; creating = skill-writer); reword skill-writer body:26.

**Pairwise collisions:**
- `git-commit` vs `commit-commands:commit` — the only collision that can produce a **non-conformant artifact**: whichever wins, neither documents this repo's mandated `Co-Authored-By` trailer (git-commit itself omits it). *Fix:* document the trailer in git-commit (also a §5 item) so the convention exists regardless of routing.
- `diagnose-loop` vs `superpowers:systematic-debugging` — near-duplicate intent, both model-invocable. *Fix:* note the relationship in diagnose-loop's description (this builds the deterministic loop first).
- `qe-agent` Static Analysis Mode vs `contract-auditor` — qe re-derives the auditor's contract-conformance work with no dedupe rule. *Fix:* give contract-auditor a concrete output path, then add one line to qe Phase 1: "if contract-auditor ran this build, consume its report; focus Phase 1 on runtime conformance."

---

## 5. Incomplete / Half-Built / Broken Scripts

No skill needs deletion. Every item is **finish** or **trim**.

| # | Item | Verdict | Action |
|---|---|---|---|
| 1 | qe-agent: `qa-report-schema.md` prose (`findings[]/passed[]`) contradicts canonical `qa-report-schema.json` (`scores/blockers/issues/test_results/gate_decision`). **CRITICAL — verified lines 27-28 of the prose.** | FINISH | Make the JSON the single source of truth; rewrite the prose schema; fix `severity-thresholds.md` gate rule to key on `blockers[].severity==CRITICAL`; repoint `llm-judge-rubrics.md` to `scores.X.score`. |
| 2 | observability-agent & performance-agent promise a QE score that doesn't exist (5 dims only; **verified grep → 0**). | FINISH | Reword to truth: results are machine-readable inputs QE may cite as issues; neither is a scored gate dimension. (Or add real ScoreEntry + x-gate-rule if they should gate.) |
| 3 | setup-project-skills bakes broken contract-template path `.../references/templates/<x>` into consumer repos (**verified: no `templates/` subdir; real files are one level up**). | FINISH | Rewrite all four `contract-format-*.md` to `skills/contracts/contract-author/references/<x>-template.<ext>`; fix `jsonschema-template.json` → `json-schema-template.json`. |
| 4 | nano-banana script ≠ body: API-key lookup (script hardcodes repo-root .env; body promises cwd-upward + `~/.config`), `--resolution` echoed-not-sent, flash/pro tiers are aliases of one model. | FINISH | Make script search cwd-upward + add `~/.config` fallback (or rewrite body to match script); annotate/remove resolution + tier claims. |
| 5 | sync-skills body promises "ask before replacing"; script does silent `rm -rf` (**verified lines 391/458/559**). README cites a `--force` flag that doesn't exist. | FINISH | Reword body to "warns and replaces" (low-effort) or add a real prompt/`--force`; fix README. |
| 6 | mermaid-charts: `mmdc` render pipeline unrunnable (no Bash in allowed-tools); `other.md` lists 7 chart types with zero syntax. | FINISH | Add Bash + compatibility line (or downgrade to "emit .mmd, tell user to run mmdc"); add minimal syntax blocks to `other.md`. |
| 7 | code-review-agent: Write in allowed-tools vs "you never modify code" + body misquotes own tools; output destination undefined. | FINISH | Resolve Write intent, define an output path (or return-in-message), document spawn-vs-`/code-review` selection. |
| 8 | security-agent: secret-scan baseline points at the toolkit's own CI scanner (`scan-skills.sh`, anchored to this repo) via a path that won't resolve from a target project. | TRIM/FINISH | Remove the pre-scan section or replace with a target-appropriate scanner (gitleaks/trufflehog or read-only grep) marked optional. |
| 9 | skill-review: coverage-gap check points at nonexistent `docs/architecture.md` (4 locations). | FINISH | Repoint to files that exist (CLAUDE.md §Skill Categories, README, file-ownership.md) or add an "if absent, skip" guard. |
| 10 | skill-writer: documents lint/scan validation gate it can't run (no Bash). | FINISH | Add Bash; make Step 5 run + pass both scripts before declaring done. |
| 11 | contract-author ↔ contract-auditor: `contracts/types.<ext>` (file) vs `contracts/types/` (dir) (**verified**). | FINISH | Standardize on the flat file; update auditor's 3 refs + frontend-agent:51. |
| 12 | llm-wiki `wiki/index.md` vs wiki-research root `index.md`. | FINISH | Pick one canonical layout; document once both reference. |
| 13 | playwright Step 5 never tells the agent to author report.json/report.md; `--reporter=json` doesn't persist. | FINISH | State the Write step explicitly; set `PLAYWRIGHT_JSON_OUTPUT_NAME` so raw JSON lands as a file. |
| 14 | orchestrator self-refs missing `skills/` prefix (`file-ownership.md:25`, `phase-guide.md:65`, `SKILL.md:161`, `phase-guide.md:166`). | FINISH | Prefix all four with `skills/`. |
| 15 | project-profiler references a nonexistent "spec" + an absent validator. | TRIM | Reword "per the spec" → "as follows" (the 9 bullets already define structure); soften validation to field-presence check. |
| 16 | git-commit omits the repo-mandated `Co-Authored-By` trailer. | FINISH | Add a "Commit Trailer" subsection. |
| 17 | setup-project-skills "fail loud" claim contradicts soft-fallback consumers. | TRIM | Reword to "surfaces a one-time prompt, then proceeds with defaults." |

---

## 6. Cross-Reference & Ownership Integrity

**Dangling refs / archive leaks — CLEAN.** Verified positive: every `composes_with`/`spawned_by` ref across all 49 active skills resolves to a local active skill or a known plugin skill. Zero refs to nonexistent skills; zero live refs into the 6 archived skills. *One latent risk:* confirm `sync-skills` excludes `skills/archive/` from publishing so archived bare-refs can't go live.

**Decorative spawn edges (reciprocity gaps).** The 6 dead edges in §3 are all reciprocity failures — `spawned_by` declares a caller whose body never calls. This is the single most systemic graph defect and the one tools will silently trust.

**Namespace inconsistency.** `frontmatter-spec.md:184-193` mandates plugin-external refs be prefixed (`superpowers:`, `claude-mem:`) and bare names be in-repo only — and at line 193 names `orchestrator` and `frontend-agent` as *exemplars* of the convention. Both violate it: 13 bare external refs (orchestrator: brainstorming, writing-plans, frontend-design, ui-ux-pro-max, ux-review, feature-dev, loop, schedule, claude-api; frontend-agent: frontend-design, ui-ux-pro-max; skill-review: skill-creator). The spec names its own violators as good examples. *Fix:* one namespace-normalization pass + a lint rule that FAILs on a bare ref matching a known-plugin name.

**Ownership nesting conflicts (3).** The "canonical" `file-ownership.md` (`:5-12`) bills itself as overriding any role skill but lists only 6 owners and omits 7 (db-migration, docs, observability, security, context-manager, setup-project-skills, maintain-context owners of durable paths). It cannot adjudicate the conflicts it creates:
- `skill-update owns: skills/` swallows the entire tree including `sync-skills`' subdir → set to `[]` (write comes from allowed-tools, not owns; sibling meta skills correctly leave it empty).
- `docs/agents/` (setup-project-skills) nests inside `docs/` (docs-agent), unregistered → register the carve-out; have docs-agent declare it does NOT own `docs/agents/`.
- `docs/adr/**` (maintain-context) is silently overridden by `docs/` (docs-agent) per the spec's own directory-over-pattern precedence → carve out `docs/adr/` to maintain-context.

Plus a real collision: `.env.example` is claimed by both infrastructure-agent and (via team-sizing.md) backend-agent — pick one owner.

*Fix:* rebuild `file-ownership.md` to enumerate all 13 owning skills with the 3 carve-outs explicit; until then it should not call itself "canonical."

---

## 7. Convention Drift

The 10 role agents are the disciplined cohort (near-identical frontmatter + body skeleton, precise `compatibility` strings, correct `metadata`) — **hold them up as the house template.** The discipline never propagated:

- **`disable-model-invocation` placed at 4 different positions** across the 14 skills that set it. Root cause: the spec's Quick Reference YAML doesn't list it, so there's no anchor. *Fix:* add it to the spec at a fixed slot (after `description`, with the `requires_*` gating booleans); move all 14 to that slot.
- **`compatibility` is roles-only** (11 skills). Skills that demonstrably need a non-trivial env omit it: nano-banana (python3+google-genai+key), railway-deploy (railway CLI+Docker), sync-skills, settings-consolidator (jq), playwright, git-post-merge-cleanup, claude-design-brief, ui-brief, living-plan, plan-intake. *Fix:* make it mandatory for any skill with `requires_claude_code:true` OR a non-Read/Write/Edit/Grep/Glob tool OR a `scripts/` dir; backfill ~15 workflows.
- **`allowed-tools` doesn't match body behavior.** Used-but-undeclared (real functional gaps under an enforcing host): wiki-research uses Bash in Step 1, llm-wiki needs WebFetch+Bash, mermaid-charts needs Bash for mmdc, skill-writer needs Bash for lint, contract-author needs Bash for tsc. Declared-but-unused: git-post-merge-cleanup (Write), context-manager (Bash). *Fix:* treat allowed-tools as a contract the lint verifies against body content.
- **Field ordering + `metadata` block** are non-canonical (5 files, 5 orders; metadata populated on 10 roles, a broken stub on interactive-doc, absent on 38). *Fix:* make the spec Quick Reference order normative + add an order-check; decide metadata all-or-nothing.
- **`requires_agent_teams` (false on all 49) and `min_plan` (`starter` on all)** are inert boilerplate — ~98 lines of dead frontmatter diluting the block where the real gating field lives. *Fix:* omit-when-default.

---

## 8. Documentation Drift — exact corrections

Root cause of 3 of the worst findings: `living-plan` + `plan-intake` (PR #10) were added without updating the 4 places that enumerate skills.

| File:line | Says | Change to |
|---|---|---|
| `.claude-plugin/plugin.json` skills[] | 46 paths | add `./skills/workflows/living-plan`, `./skills/workflows/plan-intake`, `./skills/workflows/render-sanity` |
| `CLAUDE.md:10` | 47 | **49** |
| `CLAUDE.md:45` | workflows (26), enum omits 2 | **(28)**, append `living-plan, plan-intake` |
| `README.md` catalog (`:259-308`) | rows 1-47 | add rows 48 `living-plan`, 49 `plan-intake` |
| `README.md:47` | 26 workflow skills | 28 |
| `README.md:307,321` | stray 47 / "(47)" | 49 |
| `README.md:327` | workflows # 26 | 28 |
| `README.md:82` | "installs all 49" | true once plugin.json fixed |
| `.claude-plugin/marketplace.json:18` | 9 roles/3 contract/5 git/9 meta/13 wf + dangling "and the interactive-doc workflow" | 1 orch / 10 roles / 2 contracts / 4 meta / 4 git / 28 workflows (or drop sub-counts) |
| `START-HERE.md:8` | 47 (present tense) | 49 (leave `:41` frozen history) |
| `PLAN.md:15` | "mature 47-skill library" | 49 (leave `:18/:25/:41` frozen history) |

**Prevent recurrence:** add `scripts/check-catalog-sync.sh` to CI — fail when `len(plugin.json.skills) != count(active SKILL.md)` OR any active skill is absent from the README catalog / CLAUDE.md enumeration. Matches the repo's stated "fail loud, fail early" principle.

---

## 9. Real Bugs Roll-Up (deduped, grouped by theme)

**A. Schema / gate contract (highest blast radius).**
- qe-agent prose schema contradicts canonical JSON gate — silent build-gate failure. **(CRITICAL.)**
- observability-agent + performance-agent reference nonexistent QE score dimensions.
- docs-agent tells the agent completeness/code_quality scores gate the build (only contract_conformance/security/CRITICAL blockers do).

**B. Producer/consumer path disagreement.**
- contract-author file vs contract-auditor directory (`contracts/types`).
- llm-wiki `wiki/index.md` vs wiki-research root `index.md`.
- setup-project-skills broken `templates/` subpath baked into consumer repos.
- repo-deep-dive Phase-5 vault schema drifts from llm-wiki layout.

**C. Script ≠ documentation.**
- nano-banana (key lookup / resolution / model tiers).
- sync-skills (silent `rm -rf` vs documented prompt; phantom `--force`).
- mermaid-charts (mmdc unrunnable under own allowed-tools).
- skill-writer / contract-author / wiki-research / llm-wiki (use a capability not in allowed-tools).

**D. Path / portability defects.**
- orchestrator 4× missing `skills/` prefix (won't resolve from repo root). **(verified.)**
- security-agent secret-scan path won't resolve from a target project's cwd.
- deployment-checklist `grep -oP` non-portable (no GNU grep on macOS/BSD).
- living-plan `cp template/...` assumes skill dir is cwd.
- git-post-merge-cleanup merge-base `origin/$DEFAULT` vs local `$DEFAULT` drift (errs safe).

**E. Frontmatter/body contradictions.**
- code-review-agent Write vs read-only.
- caveman description omits a valid exit phrase the body accepts.
- claude-design-brief "13 categories" vs 12-row table.
- render-sanity "Phase 12" vs orchestrator Phase 13. **(verified.)**

**F. Ownership.**
- skill-update `owns: skills/`, skill-update/sync-skills nesting, docs/adr + docs/agents carve-outs, .env.example collision (all §6).

**G. Host-mismatched tool names.**
- interactive-doc `conversation_search` is not a Claude Code tool.

---

## 10. Prioritized Roadmap to Better Working Order

Each wave is a disjoint, parallelizable set. **Do not start a later wave's doc-count edits until P0's plugin.json + count source-of-truth lands, or they'll conflict.**

### P0 — Blockers (ship-stoppers; do first)
1. **`plugin.json`: add the 3 missing skills** (`living-plan`, `plan-intake`, `render-sanity`). *DoD:* `len(plugin.json.skills) == 49`; a fresh `/plugin install` yields a working render-sanity ship gate.
2. **qe-agent: reconcile schema prose to the canonical JSON.** Rewrite `qa-report-schema.md`, `severity-thresholds.md`, `llm-judge-rubrics.md` to `scores/blockers/issues/test_results/gate_decision`. *DoD:* a report authored straight from the prose validates against `qa-report-schema.json` and passes the gate.
3. **observability-agent + performance-agent: remove the fictional QE score** (reword to "machine-readable input QE may cite"). *DoD:* neither body references a score dimension absent from the schema.
4. **setup-project-skills: fix the broken contract-template path** in all four `contract-format-*.md`. *DoD:* every path resolves; a freshly written consumer `docs/agents/contract-format.md` points at a real file.

**P0 definition of done:** the toolkit installs completely, the QA gate accepts a correctly-authored report, no role agent gates on a phantom score, and config bootstrap stops propagating a broken path into downstream repos.

### P1 — Wiring & handoff integrity
5. **Resolve the 6 dead spawn edges** (§3). For the two HUMAN DECISIONS (code-review-agent, context-manager): pick wire-vs-trim. Trim wiki-research → 2 spawners; reconcile render-sanity↔qe-agent; relabel zoom-out. *DoD:* every `spawned_by` edge is honored by an executable step in the named spawner, OR is removed.
6. **Fix producer/consumer path pairs:** contract types (file), llm-wiki↔wiki-research index layout, repo-deep-dive vault example. *DoD:* each consumer reads exactly where the producer writes.
7. **Rebuild `file-ownership.md` as truly canonical:** all 13 owners + 3 carve-outs; set `skill-update owns:[]`; resolve `.env.example`. *DoD:* no two skills claim the same path; every owning skill appears in the map.
8. **Namespace pass + lint rule:** prefix the 13 bare external refs; add a lint that FAILs on bare known-plugin names. *DoD:* spec exemplars (orchestrator, frontend-agent) actually follow the spec.

**P1 DoD:** the dependency graph is truthful — a graph-reader (or skill-explorer/skill-review) sees only edges that fire and ownership that doesn't collide.

### P2 — Script/doc fidelity & polish
9. **Script truth-up:** nano-banana, sync-skills (+README `--force`), mermaid-charts mmdc, playwright report authoring, security-agent secret-scan, deployment-checklist `grep -oP`, living-plan `cp`, orchestrator `skills/` prefixes.
10. **allowed-tools as contract:** add Bash/WebFetch where bodies use them; trim unused; standardize order. Backfill `compatibility` on ~15 env-dependent workflows.
11. **Doc-count source of truth + CI guard:** apply the §8 table; add `check-catalog-sync.sh`. Drop dead `requires_agent_teams`/`min_plan` defaults.
12. **Disambiguation clauses:** ui-brief, plan-builder/living-plan, interactive-doc tokens, skill-explorer↔find-skills, git-commit `Co-Authored-By` trailer, diagnose-loop↔systematic-debugging, qe↔contract-auditor dedupe.
13. **Cosmetic:** caveman exit phrase, claude-design-brief count, render-sanity Phase label, interactive-doc `conversation_search` + metadata stub, frontmatter field ordering.

**P2 DoD:** every documented script behavior matches the script, every documented tool is in allowed-tools, docs can't silently rot, and the trigger collisions have explicit boundaries.

### Items needing a HUMAN DECISION
- **code-review-agent:** spawn as an in-build role, or formally cede to the external `/code-review` CLI? (Borderline near-dead skill — keep only if wired.)
- **context-manager:** wire its validation into `handoff-protocol.md`, or reframe user-only and delete the duplicated logic from one of the two homes?
- **metadata block:** backfill across all 49 (discovery argument) or drop entirely (rely on directory category + description)?
- **observability/performance scores:** truly out of the gate (reword), or should they gate (then add real schema dimensions + rubrics)?
