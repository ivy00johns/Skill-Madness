# Report Template

Save the report to `docs/render-sanity-YYYY-MM-DD.md`. Every report has the same shape so a reviewer can scan it. Placeholders in angle brackets are illustrative; each row is a real `(route, evidence, verdict)` tuple from the run.

```markdown
# Render Sanity — <project> — YYYY-MM-DD

## Stack state
- Dev server: <url> reachable / not reachable (with evidence)
- Sign-in available: yes (mechanism: seed creds / demo button / OAuth / magic-link) / no — REASON
- Project mock-ID pattern (from Step 1): <pattern> (e.g. `mock_*`, prefixed UUIDs, sequential ints)
- Project placeholder vocabulary (from Step 1): <generic-noun + @handle pairs>

## Route inventory
N total — M public, K auth-gated, J role-gated. (Listed below in walk order.)

## Check 1 — Visible-text smells
| Route | Pattern | Matched text | Verdict |
|---|---|---|---|
| <route> | <which pattern from the table> | "<the matched substring>" | CRITICAL / Pass |

## Check 2 — Click-through
| Source list page | First item href | Destination outcome | Verdict |
|---|---|---|---|
| <route> | <href> | <renders real content / "not found" / etc.> | CRITICAL / Pass |

## Check 3 — Signed-out matrix
| Route | Outcome | Verdict |
|---|---|---|
| <auth-gated route> | <redirect / dead-end shell / 500> | CRITICAL / Pass |
| <public route> | <real content renders> | Pass |

## Check 4 — Signed-in matrix
Signed in as: <user / role>
| Route | Outcome | Verdict |
|---|---|---|
| <user-scoped route> | <reflects seeded user data / generic empty / wrong user's data> | CRITICAL / Pass |

## Summary
- Critical: <count>
- Pass: <count>
- Total routes walked: <count> of <inventory size>

[The next agent / orchestrator must fix every Critical before declaring the build done. Polish items belong to ux-review, not here.]
```

## Pass/fail decision

- **PASS**: zero critical findings across all four checks.
- **FAIL**: one or more critical findings. The report names them; the build cannot be declared done until they're fixed and render-sanity is re-run.

A FAIL is a gate, not a recommendation. The orchestrator's Definition of Done depends on render-sanity returning PASS on a UI build.
