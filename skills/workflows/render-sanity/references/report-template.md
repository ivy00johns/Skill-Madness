# Report Template

Save the report to `docs/render-sanity-YYYY-MM-DD.md`. Every report has the same shape so a reviewer can scan it. Placeholders in angle brackets are illustrative; each row is a real `(route, evidence, verdict)` tuple from the run.

```markdown
# Render Sanity — <project> — YYYY-MM-DD

## Stack state
- Host capabilities: browser tool present / absent; shell present / absent
- Dev server: <url> reachable / not reachable / unknown (with evidence)
- Sign-in available: yes (mechanism: seed creds / demo button / OAuth / magic-link) / no — REASON / unknown
- Project mock-ID pattern (from Step 1): <pattern> (e.g. `mock_*`, prefixed UUIDs, sequential ints)
- Project placeholder vocabulary (from Step 1): <generic-noun + @handle pairs>

## Route inventory
N total — M public, K auth-gated, J role-gated. (Listed below in walk order.)

## Check 1 — Visible-text smells
| Route | Pattern | Matched text | Verdict |
|---|---|---|---|
| <route> | <which pattern from the table> | "<the matched substring>" | CRITICAL / Pass / BLOCKED |

## Check 2 — Click-through
| Source list page | First item href | Destination outcome | Verdict |
|---|---|---|---|
| <route> | <href> | <renders real content / "not found" / etc.> | CRITICAL / Pass / BLOCKED |

## Check 3 — Signed-out matrix
| Route | Outcome | Verdict |
|---|---|---|
| <auth-gated route> | <redirect / dead-end shell / 500> | CRITICAL / Pass / BLOCKED |
| <public route> | <real content renders> | Pass |

## Check 4 — Signed-in matrix
Signed in as: <user / role>
| Route | Outcome | Verdict |
|---|---|---|
| <user-scoped route> | <reflects seeded user data / generic empty / wrong user's data> | CRITICAL / Pass / BLOCKED |

## BLOCKED checks
| Check | Reason it could not run |
|---|---|
| 2 — click-through | no browser tool on this host |
| 3 — signed-out matrix | no browser tool on this host |
| 4 — signed-in matrix | no browser tool; no seed credentials readable |

(Delete this section when every check ran. A BLOCKED check is never a Pass.)

## Summary
- Critical: <count>
- Pass: <count>
- BLOCKED: <count>
- Total routes walked: <count> of <inventory size>

[The next agent / orchestrator must fix every Critical before declaring the build done. Polish items belong to ux-review, not here.]
```

## Pass/fail decision

- **PASS**: zero critical findings across all four checks, and every check actually ran.
- **FAIL**: one or more critical findings. The report names them; the build cannot be declared done until they're fixed and render-sanity is re-run.
- **INCOMPLETE / BLOCKED**: one or more checks could not run on this host. Name every blocked check and its reason. Do not report INCOMPLETE as PASS.

A FAIL is a gate, not a recommendation. The orchestrator's Definition of Done depends on render-sanity returning PASS on a UI build. An INCOMPLETE run leaves the gate uncleared: either re-run on a host with the missing tools, or record the static-only result as an explicit, named exception.
