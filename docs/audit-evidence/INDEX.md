# Audit Evidence — Index

Every audit pass known to have run against this repo, what it produced, and
which of its reports are projected here. Reports marked *local-only* exist only
in the gitignored `audit/` working tree on the machine that ran the pass; they
get republished on demand per [`README.md`](README.md).

## Passes

| Pass | Audit date | Layer | Skills in tree | Source dir (local) | Ledger short-link |
|---|---|---|---|---|---|
| Functional audit (v2) | 2026-05-28 | Function / triggerability / completeness / real bugs | 49 | `audit/reports-v2/` | `[FAUDIT]` in `docs/REMAINING-WORK.md` |
| Compliance & style audit (v1) | 2026-05-20 | skill-review rubric (7 dimensions × 1–5) + bulk cross-cutting checks | 47 | `audit/reports-v1-sufrace/` (sic) + `audit/MASTER_AUDIT_PLAN.md` | — |

## Projected reports

| File | Scope | Verdict | Republished from |
|---|---|---|---|
| [`2026-05-28-functional-audit/master-audit.md`](2026-05-28-functional-audit/master-audit.md) | All 49 active skills (pass-wide synthesis; per-skill verdicts in its §2 scorecard) | Healthy in substance, leaky at the seams — 11 works / 37 works-with-gaps / 0 broken / 0 dead; 6 dead wiring edges; 2 CRITICAL | `audit/reports-v2/00-MASTER-AUDIT.md` |
| [`2026-05-28-functional-audit/qe-agent.md`](2026-05-28-functional-audit/qe-agent.md) | qe-agent (v1.4.0 at audit time) — carries the pass's CRITICAL schema-fork finding; also the exemplar per-skill projection | works-with-gaps | `audit/reports-v2/qe-agent.md` |

## Local-only (not yet projected)

**Functional audit (v2), `audit/reports-v2/`:** 49 per-skill reports (one per
active skill; their verdicts and one-liners are all in the projected master's §2
scorecard), 6 synthesis lens reports (`00-lens-{dead-skills,overlap,crossref,conventions,doc-drift,incomplete}.md`),
`_roster.md` (49-skill trigger/edge roster), `_inventory.json` (frontmatter
graph), `00-MASTER-AUDIT.html` (render of the projected master). Supporting
material one level up: `audit/_tools/functional_audit_workflow.js` (the workflow
that ran the pass — its structure is summarized in each projected report's
`worker-config` field).

**Compliance & style audit (v1), `audit/reports-v1-sufrace/`:** 47 per-skill
report pairs (`{skill}.md` + `{skill}.json`) + `00-bulk-audit.{md,json}`,
synthesized in `audit/MASTER_AUDIT_PLAN.md` (headline: 35 SHIP / 12 NEEDS WORK /
0 MAJOR REWORK, avg 4.49/5). The v2 pass judged this layer surface-level and
many of its findings were already fixed by the time v2 ran; project v1 material
only if something needs to cite it directly.
