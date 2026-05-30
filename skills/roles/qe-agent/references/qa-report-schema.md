# QA Report Schema Reference

The `qa-report.json` is the orchestrator's build gate. The orchestrator parses it programmatically and blocks the build on CRITICAL blockers or `contract_conformance` / `security` scores below 3. A non-conformant report is as bad as no report.

`qa-report-schema.json` in this directory is the authoritative schema — the single source of truth. This document explains the structure, the score model, and how to produce a conformant report; if anything here disagrees with the JSON, the JSON wins.

## File pair

The QE agent writes both files at the end of Phase 4:

- `qa-report.md` — human-readable narrative with a defect table and summary
- `qa-report.json` — machine-readable per `qa-report-schema.json` (the gate)

Both files describe the same defects; the JSON exists so the orchestrator can parse without LLM calls.

## Top-level keys

The `qa-report.json` is an object with these required top-level keys (all must be present):

- `schema_version` — string, const `"1.0.0"`
- `timestamp` — RFC 3339 / ISO 8601 date-time string
- `agent_role` — string, const `"qe"`
- `build_session_id` — string identifying the build session
- `status` — one of `PASS` | `FAIL` | `PARTIAL` | `BLOCKED`
- `scores` — object of the five scored dimensions (see below)
- `test_results` — object of test counts per suite (see below)
- `blockers` — array of blocker objects (gate-affecting defects)
- `issues` — array of issue objects (non-gating defects)
- `recommendations` — array of strings
- `gate_decision` — object with `proceed` (boolean) and `reason` (string)

The orchestrator parses by name, not position — field names must match the schema exactly.

## Scores

The `scores` object MUST include all five dimensions. Each is an object with `score` (1–5 integer) and `notes` (string explaining the score). Bare integers are non-conformant.

```json
{
  "correctness":          { "score": 4, "notes": "..." },
  "completeness":         { "score": 4, "notes": "..." },
  "code_quality":         { "score": 4, "notes": "..." },
  "security":             { "score": 4, "notes": "..." },
  "contract_conformance": { "score": 5, "notes": "..." }
}
```

## Dimension definitions

Score each 1–5 per `references/llm-judge-rubrics.md`. Use these definitions when assigning scores so the orchestrator's interpretation matches yours:

- **correctness** — does it work? Do endpoints return correct responses for the happy path and contracted edge cases?
- **completeness** — is everything there? Are all contracted endpoints implemented? Is the data model complete?
- **code_quality** — is it well-built? Clean separation, consistent patterns, error handling, no dead code?
- **security** — is it safe? Input validated, no injection, CORS correct, no secrets leaked? Coordinate with security-agent if present — avoid duplicating their deeper audit.
- **contract_conformance** — does the implementation match the spec? URLs, methods, request/response shapes, status codes, error envelope, field names.

## test_results

The `test_results` object MUST include `unit`, `integration`, `e2e`, `contract`, and `security_scan`. Each is an object of `pass`, `fail`, and `skip` integer counts (each ≥ 0).

## blockers and issues

Defects are split into two arrays — there is no `findings` or `passed` array.

- **`blockers`** — gate-affecting defects. Each entry has `severity` of `CRITICAL` or `HIGH`. A single `CRITICAL` blocker fails the gate.
- **`issues`** — non-gating defects. Each entry has `severity` of `MEDIUM`, `LOW`, or `INFO`.

Each blocker and issue object requires:

- `id` — stable identifier (e.g., `CR-001`)
- `severity` — `CRITICAL` | `HIGH` for blockers; `MEDIUM` | `LOW` | `INFO` for issues
- `category` — for blockers, one of `contract_violation` | `security` | `build_failure` | `test_failure` | `other`; for issues, a free-form string
- `description` — what is wrong, with exact reproduction command or `file:line` reference and expected vs actual
- `suggested_fix` — how to resolve it

`file` (string or null) and `line` (integer or null) are optional on both.

## recommendations and gate_decision

- **`recommendations`** — array of strings. Forward-looking advice that is not itself a defect.
- **`gate_decision`** — object with `proceed` (boolean) and `reason` (string). The QE agent fills this per the gate rules in `references/severity-thresholds.md`; the orchestrator re-derives it from `status`, `blockers`, and `scores`.

## Crediting what works

There is no `passed` array. Credit what works inside the `notes` of each score and in `recommendations` — call out contract-conformance checks that succeeded, happy-path flows that ran clean, and adversarial probes that did not break the system. A score must reflect what was actually tested.

## Examples

See the canonical schema file `qa-report-schema.json` and an example report under the orchestrator's reference materials. Field names must match the schema exactly — the orchestrator parses by name, not position.
