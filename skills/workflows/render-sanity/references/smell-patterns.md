# Visible-Text Smell Patterns

Check 1's universal pattern table. Grep `document.body.innerText` for each.

## Universal smells (apply to any project, any stack)

| Pattern | What it usually means |
|---|---|
| Lone `?` where a name/value should be | A `find()` / `get()` / lookup against a collection that didn't match — usually mock data vs real backend IDs |
| Lone `—`, `--`, or persistent `Loading…` that doesn't resolve after a few seconds | Async fetch never resolved, threw silently, or the loading state is the steady state |
| `undefined`, `null`, `NaN`, `[object Object]`, `Symbol(...)` in user-facing text | Field unwrapping went wrong; a typed contract is being violated |
| `Couldn't load`, `Unauthorized`, `Failed to fetch`, `Not found`, `Forbidden`, `500`, `Internal server error`, `Network error` | Backend rejected the call, the UI is rendering its error state AS the page content. (May be correct on a deep route. Almost never correct on a landing page or top-nav target.) |
| Hardcoded `Lorem ipsum`, `Placeholder`, `TODO`, `FIXME`, `Coming soon` shipped to a "live" page | Stub content that never got replaced |
| Repeated identical fallback strings (e.g. the same generic noun + `@same-handle` across rows where data should differ) | A lookup returning the same default on every miss — almost always a stale mock or wrong ID space |

## Project-specific smells (derived in Step 1)

Before scanning, read the project's mocks / fixtures / seed files (`mocks.ts`, `__fixtures__/`, `seed.sql`, `factories/`, `dev/seed.json`, anywhere with hardcoded "demo data"). Capture two things:

1. **The mock-ID format.** Mock data uses a recognizable, non-cryptographic pattern — sequential UUIDs (`00000000-0000-...`), prefixed slugs (`mock_*`, `demo_*`, `fixture_*`), or project-specific pseudo-IDs. Any ID matching this pattern on a page supposed to come from the real backend = Critical (page wired to mocks).
2. **The placeholder-label vocabulary.** Mock data often uses generic role nouns as defaults ("User", "Item", "Account", "Seller", "Buyer") plus a corresponding lowercased `@handle`. Multiple of these on a page that should show distinct real data = Critical (lookup missing real records).

Record both in Step 1's notes so Step 3's scan knows what to grep for. Do not hardcode patterns from one project into the skill — they vary per project.

## Output tuple

When the scan flags something, capture: the route, the matched string, and the surrounding 30 chars. That tuple goes in the Critical Issues section of the report.

> A user-facing `?` or `Couldn't load` is a critical issue, not a polish item.
