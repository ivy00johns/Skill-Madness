# Severity Thresholds and Gate Rules

The QA report is the build gate. This document defines severity assignment, score-threshold rules, and the gate decision logic the orchestrator applies to `qa-report.json`.

Defects are recorded in two arrays: `blockers` (severity `CRITICAL` or `HIGH`) and `issues` (severity `MEDIUM`, `LOW`, or `INFO`). There is no `findings` array.

## Severity ladder

Assign exactly one severity to each defect, then place it in the right array. Use the strictest applicable level:

- **CRITICAL** — blocks release; goes in `blockers`. The build must not ship until this is fixed. Examples: missing required endpoint, broken auth, contract field-name mismatch on the wire, data corruption risk, exposed secrets.
- **HIGH** — should block; goes in `blockers`. Will cause user-visible failure in expected use. Examples: wrong status code, missing CORS for the contracted origin, error envelope omitted, validation gap on a documented input.
- **MEDIUM** — fix before the next release; goes in `issues`. Edge-case failure or contract drift risk that does not yet break the happy path. Examples: shared types not imported (manual dicts that could drift), inconsistent error wording, missing rate limit on a non-critical endpoint.
- **LOW** — nice to fix; goes in `issues`. Style, naming, or low-impact code smell.
- **INFO** — observational; goes in `issues`. Not a defect, but worth surfacing.

## Score-to-severity mapping

Scores are not arbitrary — they reflect the worst defect (blocker or issue) in a dimension:

| Worst defect in the dimension          | Maximum `scores.<dim>.score`    |
| -------------------------------------- | ------------------------------- |
| Any CRITICAL                           | 2 (forces gate fail)            |
| Any HIGH but no CRITICAL               | 3                               |
| Only MEDIUM                            | 4                               |
| Only LOW/INFO or none                  | 5                               |

If a dimension has multiple CRITICAL defects, score it 1.

## Gate decision logic

The orchestrator blocks the build if **any** of the following hold:

1. The `blockers` array contains an entry with `severity == "CRITICAL"`.
2. `scores.contract_conformance.score < 3`.
3. `scores.security.score < 3`.
4. `status` is `FAIL` or `BLOCKED`.
5. The report is missing any of the required keys or is not valid against `qa-report-schema.json`.

Otherwise the build is allowed to complete. The orchestrator does not negotiate — these thresholds are hardcoded. Note: the other three score dimensions (`correctness`, `completeness`, `code_quality`) are scored but do **not** gate, even below 3.

## Why these specific thresholds

- **Contract conformance and security are non-negotiable.** A build that ships with a contract mismatch causes downstream agents to fail at integration; a build that ships with a security score below 3 is releasing known exploitable code.
- **Correctness, completeness, and code_quality below 3 are warnings, not blockers** — they show up in the report, the orchestrator surfaces them, but they do not auto-block. This matches the team's actual risk tolerance: a feature with a code-quality score of 2 ships; one with a contract-conformance score of 2 does not.

## When to escalate to the lead instead of finalizing

Stop the report and message the orchestrator immediately when:

- Services won't start at all
- You discover ≥ 3 CRITICAL contract conformance failures
- You find a contract gap (the contract is wrong, not the implementation)
- Agent ownership of a finding is ambiguous

A premature `qa-report.json` with the lead unaware is worse than no report.

## Anti-patterns to avoid

- Marking a dimension 5 without evidence in its `notes` of what was actually tested. Score must reflect what was actually tested.
- Bundling multiple problems under one blocker or issue to avoid raising the severity. One defect per entry.
- Lowering a CRITICAL to HIGH because "the team will fix it next sprint." Severity describes the defect, not the schedule.
- Skipping the JSON and only writing the markdown. The orchestrator only parses JSON; markdown is for humans.
