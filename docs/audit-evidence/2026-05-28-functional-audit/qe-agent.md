# Audit Evidence: Functional Audit — qe-agent (reports-v2)

```yaml
# docs/audit-evidence typed header — see docs/audit-evidence/README.md
report: 2026-05-28-functional-audit / qe-agent
skill: qe-agent (skills/roles/qe-agent/SKILL.md, v1.4.0 at audit time)
audit-date: 2026-05-28
revision-reviewed: unrecorded (pre-convention — the audit predates this header requirement; do not treat the findings as claims about any specific commit)
worker-config: >
  One functional-auditor subagent dispatched by the "skill-functional-audit"
  dynamic workflow (audit/_tools/functional_audit_workflow.js, local working
  tree); high-severity findings re-checked by a skeptical-verifier subagent
  (default stance "refuted") before surviving into the master report.
  Model per worker: unrecorded.
verdict: works-with-gaps (triggerability n/a — spawn-only; spawn path real)
evidence-links:
  - skills/roles/qe-agent/SKILL.md
  - skills/roles/qe-agent/references/qa-report-schema.json
  - skills/roles/qe-agent/references/qa-report-schema.md
  - skills/roles/qe-agent/references/severity-thresholds.md
  - skills/roles/qe-agent/references/llm-judge-rubrics.md
  - skills/roles/qe-agent/references/validation-checklist.md
  - skills/orchestrator/SKILL.md
  - skills/orchestrator/references/phase-guide.md
source: audit/reports-v2/qe-agent.md (gitignored local working tree — .gitignore line 34)
republished: 2026-07-24 (verbatim below the divider; only this header was added)
```

> **Staleness note (republish time):** this report describes qe-agent as of
> 2026-05-28 (v1.4.0). Its BUG finding was remediated in the `FA`-prefixed sweep
> (see `docs/COMPLETED-WORK.md`); re-check the cited files against the current tree
> before treating any finding as still open.

---
# Functional Audit: qe-agent

- **Path:** skills/roles/qe-agent/SKILL.md
- **Category:** roles
- **Version:** 1.4.0
- **User-invocable:** No (`disable-model-invocation: true`, spawn-only)

**Functional verdict:** works-with-gaps
**Triggerability:** n/a-spawn-only (spawn path is real and reaches it)

## One-line summary

A well-structured, genuinely useful QA-gate role agent whose ONE serious defect is a self-contradictory report schema: the bundled `qa-report-schema.json` (which the orchestrator actually parses) and the bundled `qa-report-schema.md` / `severity-thresholds.md` (which tell the agent how to author the report) describe two incompatible JSON shapes, so an agent that follows the prose references emits a report the orchestrator rejects.

## Does it work?

Tracing the skill on a realistic dispatch (orchestrator spawns qe-agent after backend+frontend report done, contracts in `/contracts/`):

- **Phases 1-3 (conformance, integration, adversarial)** are concrete and executable. The body names exact tools (`curl`, `pytest`/`vitest`, `/playwright`), gives a sensible run order, and the `validation-checklist.md` provides copy-pasteable `curl` recipes with `${RESOURCE_PATH}`/`${PORT}` placeholders the agent fills from the contract. The "Static Analysis Mode" fallback for sandboxed envs is a real, valuable addition. An agent would not get stuck here.
- **allowed-tools vs body:** consistent. Body uses Read/Write/Edit/Bash/Glob/Grep + `python3`/`curl` (all under Bash); frontmatter declares exactly those tools and `compatibility: requires Bash + curl + python3`. No tool gap.
- **Ownership vs body:** consistent. Body writes only into `tests/`, `e2e/`, `__tests__/`, `qa-report.{md,json}` — all owned. The `tests/performance/` carve-out for performance-agent is explicitly handled (SKILL.md:57 "excluding `tests/performance/`") and matches `_inventory.json` and the frontmatter spec's resolved-conflicts table. No ownership conflict.
- **Phase 4 (the report) is where it breaks.** The body says "Field names in JSON must match the schema exactly" and points the agent at FIVE references. Two of them describe a DIFFERENT report shape than the canonical `qa-report-schema.json`:
  - `qa-report-schema.json` requires top-level `scores` (object of `{score,notes}` per dimension), `test_results`, `blockers` (severity enum `CRITICAL|HIGH`), `issues` (severity enum `MEDIUM|LOW|INFO`), `recommendations`, `gate_decision`, plus `schema_version`/`timestamp`/`agent_role`/`build_session_id`/`status`. It has NO `findings` array and NO `passed` array.
  - `qa-report-schema.md` (lines 20-30, 44-59) tells the agent to emit top-level dimension keys (`correctness`, … as siblings, not under `scores`), a `findings` array (with `dimension`/`agent`/`evidence`/`expected`/`actual`), and a `passed` array. None of these fields exist in the canonical JSON schema. It even says "The `passed` array is not optional."
  - An agent that authors per the `.md` reference produces JSON that fails validation against the `.json` schema — and the orchestrator (SKILL.md:161, phase-guide.md:166-168) validates against the `.json` and bounces non-conformant reports. The skill's own anti-pattern ("Skipping the JSON … The orchestrator only parses JSON") makes this worse: the agent is told the JSON is what matters, but two of its references teach the wrong JSON.

So: Phases 1-3 hold up cleanly; Phase 4 will produce a non-conformant report roughly half the time depending on which reference the agent anchors on. Hence works-with-gaps, not works.

## Will it trigger?

Spawn-only (`disable-model-invocation: true`), so user utterances are not the mechanism. Honest assessment of the spawn path:

- **Reachability: real.** orchestrator/SKILL.md:51 lists `qe-agent` in its dispatch set; SKILL.md:144 makes spawning a QE agent mandatory ("Testing is not optional"); the frontmatter `composes_with` includes qe-agent. qe-agent's `spawned_by: ["orchestrator"]` matches. The spawn edge exists in both directions. Not dead.
- **Downstream spawn (playwright): real and bidirectional.** Body Phase 2 invokes `/playwright`; playwright declares `spawned_by: ["orchestrator", "qe-agent"]` and its body has a "When spawned by qe-agent during Phase 2" handoff section returning `.playwright/<run-id>/`. Fully wired.
- Should-fire-equivalents (i.e., conditions under which the orchestrator MUST dispatch it): (1) "build X with an agent team" → orchestrator reaches Phase 13 QA gate → spawns qe-agent; (2) implementation agents report done and contracts exist → mandatory QE spawn; (3) orchestrator needs a `qa-report.json` to satisfy Definition of Done. All three are real paths.
- Over/under-fire: N/A for user triggers; `disable-model-invocation: true` correctly prevents auto-fire on stray "test this" utterances.

**Overlap candidates:** `contract-auditor` (also does static contract-vs-implementation conformance — qe-agent Phase 1 + Static Analysis Mode overlap heavily; the body lists contract-auditor in `composes_with` but never says "if contract-auditor already ran, skip Phase 1 static conformance," so the two can duplicate work); `playwright` (qe-agent delegates browser testing to it — complementary, not redundant); `performance-agent` (carved out cleanly); `deployment-checklist` and `render-sanity` (both run verification near build-end and `compose_with` qe-agent — adjacent but distinct concerns).

## Is it complete?

- **Promises vs delivers:** The description promises "owns the `qa-report.json` build gate" and the body delivers a full four-phase methodology. The gate-ownership claim is accurate (orchestrator defers to it). The one broken promise is "Field names in JSON must match the schema exactly" while shipping references whose field names do NOT match the schema.
- **Stubs/TODOs:** none. No placeholder sections.
- **Orphan reference files:** none. All five references (`qa-report-schema.md`, `severity-thresholds.md`, `llm-judge-rubrics.md`, `qa-report-schema.json`, `validation-checklist.md`) are explicitly named in the Phase 4 bullet list (SKILL.md:101-105) and re-referenced in Validation/Coordination. No dead weight.
- **Referenced-but-absent:** none. Every referenced file exists on disk.
- **Internal cross-skill schema match:** the `references/qa-report-schema.json` path the orchestrator cites (`roles/qe-agent/references/qa-report-schema.json` in orchestrator/SKILL.md:161 and phase-guide.md:166) matches the actual file location. Path is correct; only the prose-vs-JSON *content* diverges.

## Scripts / templates / schemas

- **`qa-report-schema.json`** — parses as valid JSON (verified with `python3 -c json.load`). Self-consistent draft-2020-12 schema. Its `x-gate-rules` (status FAIL/BLOCKED, any CRITICAL blocker, `contract_conformance.score < 3`, `security.score < 3`) match the orchestrator's gate logic exactly. **This is the authority and it's correct.**
- **`qa-report-schema.md`** — describes a shape (`findings`/`passed`/top-level dimensions) that contradicts the `.json`. Documentation defect, not a parse defect.
- **`severity-thresholds.md`** — gate rule #1 (line 31) reads "The `findings` array contains a finding with `severity == \"CRITICAL\"`." The canonical JSON schema has no `findings` array; CRITICALs live in `blockers`. The documented gate rule references a field the machine schema lacks.
- **`llm-judge-rubrics.md`** — Gate Rules section (lines 60-61) cites `scores.contract_conformance < 3` / `scores.security < 3`; the JSON path is `scores.contract_conformance.score`. Minor path imprecision, but reinforces the same fork.
- **`validation-checklist.md`** — runnable `curl`/`python3` recipes; checklist item "JSON report conforms to qa-report-schema.json" is correct. No `bash`/`python` syntax executed (recipes are illustrative templates with placeholders, not standalone scripts), but they are syntactically plausible and parameterized.

## Findings (by severity)

### BUG — Bundled report references contradict the canonical JSON schema the orchestrator parses
- **Location:** `references/qa-report-schema.md:20-59` and `references/severity-thresholds.md:31` vs `references/qa-report-schema.json`
- **Evidence:** schema.md shows top-level `"correctness": {...}, … "findings": [...], "passed": [...]` and "Each finding in the `findings` array must include: … `dimension` … `agent` … `evidence` … `expected` … `actual`". The JSON schema's `required` is `[schema_version, timestamp, agent_role, build_session_id, status, scores, test_results, blockers, issues, recommendations, gate_decision]` — no `findings`, no `passed`, dimensions nested under `scores`. severity-thresholds.md:31: gate rule keys on "the `findings` array" which does not exist in the JSON.
- **Why:** The body tells the agent "Field names in JSON must match the schema exactly" and routes it through these `.md` files. An agent anchoring on the prose emits `findings`/`passed`/flat-dimension JSON; the orchestrator validates against the `.json` (orchestrator/SKILL.md:161) and rejects it as non-conformant, bouncing the report and stalling the gate. This is the exact "looks done but breaks on execution" failure the audit targets.
- **Fix:** Make `qa-report-schema.json` the single source of truth. Rewrite `qa-report-schema.md` to describe the JSON's actual shape (`scores` object, `blockers`, `issues`, `test_results`, `gate_decision`); if `findings`/`passed` are genuinely wanted, add them to the JSON schema as optional and reconcile both. Rewrite severity-thresholds.md gate rule #1 to key on `blockers[].severity == CRITICAL` (matching the JSON's `x-gate-rules`). Fix llm-judge-rubrics.md paths to `scores.X.score`.

### ALIGNMENT — severity enums fork between blockers/issues (JSON) and a single findings ladder (prose)
- **Location:** `references/severity-thresholds.md:7-12` vs `qa-report-schema.json` `$defs.Blocker.severity` (`CRITICAL|HIGH`) and `$defs.Issue.severity` (`MEDIUM|LOW|INFO`)
- **Evidence:** severity-thresholds.md presents one 4-rung ladder (CRITICAL/HIGH/MEDIUM/LOW) for a flat `findings` array. The JSON splits severity across two arrays: `blockers` accept only `CRITICAL|HIGH`, `issues` accept only `MEDIUM|LOW|INFO`. The prose ladder has no `INFO`; the JSON `issues` enum has no `HIGH`.
- **Why:** Even after fixing the top-level shape, an agent must know a HIGH finding goes in `blockers` and a LOW goes in `issues`. The prose never explains the blockers/issues split, so severity-to-array routing is left to guesswork.
- **Fix:** In the corrected schema.md, document the blockers-vs-issues split explicitly and map each severity rung to its target array (CRITICAL/HIGH → `blockers`; MEDIUM/LOW/INFO → `issues`).

### NIT — Phase 1 static conformance overlaps contract-auditor with no dedupe guidance
- **Location:** SKILL.md:62-71 + "Static Analysis Mode" (111) vs `composes_with: [... contract-auditor ...]`
- **Evidence:** Static Analysis Mode = "compare each route handler against the OpenAPI spec … check for CORS middleware … confirm every contracted endpoint has a route" — which is contract-auditor's entire job ("Audits implementations against integration contracts … Static analysis pass").
- **Why:** When the orchestrator runs both, Phase 1 duplicates contract-auditor's pass. Not breaking — wasted effort.
- **Fix:** Add one line: "If contract-auditor already ran in this build, consume its report instead of repeating static conformance; focus Phase 1 on runtime conformance."

## Top 3 fixes (ranked)

1. **Reconcile the report schema (BUG).** Pick `qa-report-schema.json` as canonical and rewrite `qa-report-schema.md` to match it field-for-field (`scores`/`blockers`/`issues`/`test_results`/`gate_decision`); kill or formally adopt `findings`/`passed`. This is the only defect that makes the skill's primary output fail at the gate.
2. **Fix the gate rules in `severity-thresholds.md` and `llm-judge-rubrics.md`** to key on real JSON paths (`blockers[].severity`, `scores.X.score`) and document the blockers-vs-issues severity split (ALIGNMENT).
3. **Add a one-line contract-auditor dedupe note** so Phase 1 / Static Analysis Mode doesn't redo work contract-auditor already did (NIT).
