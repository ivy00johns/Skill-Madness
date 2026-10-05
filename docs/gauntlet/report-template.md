# Gauntlet II — Run Report

> **Run id:** `<run_id>`
> **Date:** `<YYYY-MM-DD>`
> **Baseline revision:** `<commit>`
> **Primary cell:** Claude Code · **Secondary cell:** Freebuff/DeepSeek
> **Budget status:** `<within-approved-caps | stopped-at-cap | unknown-no-paid-authorization>`

Fill every section. If a section has no data, say so — an unexplained blank is a defect in the report, not a clean result.

---

## 1. Headline

One paragraph: did the run exercise the collection, what fired, what missed, and which traps were caught. State plainly that per-skill triggering and efficacy remain measured for the two cells only, not universal.

## 2. Gate outputs

| Gate | Command | Result |
|---|---|---|
| Skill lint | `scripts/lint-skills.sh` | `<output>` |
| Catalog | `scripts/catalog.sh --check` | `<output>` |
| Tests | `tests/run-all.sh` | `<output>` |
| Trap verify | `scripts/gauntlet/trap-verify.sh` | `<output>` |

## 3. Coverage results

Copy the roll-up from `coverage-matrix.md` and mark each must-fire: fired (with the trace record), missed, or blocked. List every near-miss control that fired as a false positive.

| Category | Must-fire | Fired | Missed | Blocked | False positives |
|---|---|---|---|---|---|
| orchestrator | 1 | | | | |
| roles | 10 | | | | |
| contracts | 2 | | | | |
| meta | 7 | | | | |
| git | 4 | | | | |
| loops | 13 | | | | |
| workflows | 39 | | | | |
| **Total** | **76** | | | | |

## 4. Trap results

| Trap | Expected terminal state | Observed | Caught by | Verdict |
|---|---|---|---|---|
| T1 | frontend solo mode applies | | | |
| T2 | inline layout finding under strict | | | |
| T3 | duplicate declaration group detected | | | |
| T4 | copied chrome flagged | | | |
| T5 | explicit attended state plan or refusal | | | |
| T6 | wrapper cancels at cap | | | |
| T7 | frozen verifier digests | | | |
| T8 | fail-closed on validator failure | | | |
| T9 | dry-run writes nothing; resources survive | | | |
| T10 | train/dev selection, held-out once | | | |
| T11 | unknown stays unknown | | | |

`trap-verify.sh` reports BLOCKED, not PASS, wherever a checker could not read its input. Any trap that stayed green means no rule exists — file it.

## 5. Disqualified runs

List any run excluded under the nine disqualifiers in `scoring-rubric.md`, with the disqualifier number and the evidence.

## 6. Second-cell differences

Report the Freebuff/DeepSeek cell separately: what the sequential path did differently, which capabilities were missing, and the equivalence rating of each fallback. Do not blend into a universal number.

## 7. Host-friction log

Every point the host lacked a tool that an instruction demanded: the exact instruction, what was missing, and what was done instead. This is primary evidence.

## 8. Proposed intake (`[G2]` rows)

Every missed firing, false positive, uncaught trap, and friction point as a candidate ledger row. Formatted for `plan-intake`.

| Proposed ID | Priority | Area | What you would notice | One-line problem | Proposed fix | Evidence / source | Size |
|---|---|---|---|---|---|---|---|
| G2-01 | | | | | | | |

## 9. Definition of done

Check each item from `GAUNTLET-II.md` §10 and state pass or fail with evidence.
