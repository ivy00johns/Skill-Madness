---
name: render-sanity
version: 1.1.0
description: |
  Lightweight visual sanity check that catches failure modes passing
  "tests green + dev server boots + 0 console errors" but visibly breaking
  the app when a human clicks — stale mock IDs on "live" pages, lone `?` /
  `—` / `undefined` / `Loading…` where data should be, dead links from
  list pages, and "Couldn't load X / Unauthorized" dead-end shells. Runs
  four objective checks BEFORE the build is declared done: smell scan,
  click-through every list, signed-out matrix, signed-in matrix. Use when
  a build is wrapping up, after ux-review or qe-agent finishes, when the
  user says "is it actually working", "broken pages", "dead links", or
  pastes a screenshot showing `?`, `undefined`, or a "Not found" page.
  Also invoke proactively when a frontend agent rewires mocks → real
  backend, when auth was added, or when seed data is regenerated.
compatibility: Claude Code; requires Playwright MCP tools
requires_claude_code: true
requires_agent_teams: false
min_plan: starter
allowed-tools: ["Read", "Bash", "Glob", "Grep",
  "mcp__plugin_playwright_playwright__browser_navigate",
  "mcp__plugin_playwright_playwright__browser_snapshot",
  "mcp__plugin_playwright_playwright__browser_click",
  "mcp__plugin_playwright_playwright__browser_evaluate",
  "mcp__plugin_playwright_playwright__browser_console_messages",
  "mcp__plugin_playwright_playwright__browser_network_requests"]
owns:
  directories: []
  patterns: []
  shared_read: ["*"]
composes_with: ["superpowers:ux-review", "orchestrator", "frontend-agent", "feature-dev:feature-dev", "playwright"]
spawned_by: ["orchestrator", "superpowers:ux-review"]
---

# Render Sanity

> **Why this exists:** "Tests pass, dev server boots, console is clean" is a process bar. It's not the same as "the app works." This skill is the missing semantic check between those two — it catches failure modes that render plausibly but are quietly broken.

This skill is **not** subjective. It does not evaluate visual hierarchy, typography, or polish — those are `superpowers:ux-review`'s job. It hunts four specific, objectively-verifiable failure modes that ship past every other gate.

**Announce at start:** "Using render-sanity to click through [N routes] and check for stale data, placeholder text, dead links, and auth dead-ends."

## The Four Checks

Each produces concrete file/route/text evidence — not "feels off."

### Check 1 — Visible-text smell scan

The app may render. The text it renders may be garbage. For every page in the sitemap, grab `document.body.innerText` and grep for known smell patterns (lone `?`, persistent `Loading…`, `undefined`, `Couldn't load`, repeated generic fallbacks, leaked mock IDs).

The full pattern table — universal smells plus how to derive project-specific patterns from the project's mocks/fixtures/seed files — lives in `references/smell-patterns.md`. Read it before running this check.

### Check 2 — Click-through every list

Pages that render a list of links (feed, catalog, search results, dashboard rows, recent items, leaderboards, threads, files — anything iterating a collection into `<a>` tags) are the most common silent-failure surface. The list renders fine; the items link to dead targets.

For every list page:

1. Snapshot the page.
2. Identify the first list-item link (`<a>` inside the card / row / item container).
3. Read its `href`.
4. Navigate to that href.
5. Confirm the destination renders real content — not a generic 404, not the project's missing-resource page, not an empty shell.

Clicking the first item is sufficient to catch the systemic "all our list IDs are stale mocks" bug. If the first works and you have time, sample one from the middle and one from the end. This catches "every link in the list is dead because the data source is wrong," not "this one particular item happens to be missing."

### Check 3 — Signed-out matrix

For every route, navigate with no session and record the outcome:

| Outcome | Verdict |
|---|---|
| Public page renders real content | Pass |
| Redirect to `/login` (or equivalent) | Pass |
| Empty shell with persistent "Couldn't load X · Unauthorized" / "Failed to fetch" / blank ledger / `—` everywhere | **Critical** — pick one: gate with a real auth wall (redirect) OR fall back to a public read-only view. A dead-end-but-still-rendered page is the worst of both. |
| Console errors but no visible error state | Critical — the fetch is throwing, the page is silently broken |
| 500 / unhandled exception in network log | Critical — server bug, not UX |

### Check 4 — Signed-in matrix

If the project has any way to log in (seed creds, demo button, OAuth with a test account, magic-link in dev), sign in **once** with a known seeded user and re-walk every auth-gated route.

What to verify:

- **User-scoped data views** (profile, account, balance, inbox, dashboard, "your X" pages) must reflect WHO is signed in. If the seed gives this user known activity, the page must show it. "Logged in but the page is empty / zeroed / generic" when the seed says otherwise = Critical.
- **User-scoped lists** (your items, followers, conversations, orders) must show entries belonging to this user. Wrong user's data or "0 items" when the seed says otherwise = Critical.
- **Counterparty / participant labels** (the other end of any two-party relationship — thread participant, task assignee, post author, resource owner) must resolve to real names/handles — not the generic-fallback label from the placeholder vocabulary captured in Check 1.
- **Empty states are FINE** when the seed legitimately has no data for this user. The bar is coherence: "Follow some people to see activity here" is good; a 401-shaped error on an authed page is bad.

**Finding seed credentials.** Read seed/fixture files (`db/seed.*`, `fixtures/`, `scripts/seed.*`, `prisma/seed.*`, `factories/`, `.env.example`, README "Demo accounts" sections). If the project ships a LoginPage with hardcoded demo defaults or a "demo" button, use them — but verify they work against the running auth endpoint first (a quick curl POST is cheaper than discovering it at click-time).

**If there is no way to sign in** — that itself is a Critical. File as "Cannot enter the app as any user — sign-in path is broken or undocumented." Check 4 cannot be performed without one.

**If the project has roles** (admin/member, buyer/seller, teacher/student), sign in as at least one user per role with distinct UI affordances. The "admin sees nothing where a regular user sees a dashboard" case is real.

## Workflow

### Step 1 — Build the route inventory

Read the router file (`App.tsx`, `app/`, `pages/`, `src/routes/`, etc.) and write down every route. Mark each as **public**, **auth-gated**, or **role-gated** based on `<RequireAuth>` / `requireAuth` / middleware patterns. Do this from code, not by clicking — a route in the router but not linked from any nav still counts.

If the inventory is large (>20 routes), prioritize:

1. Routes linked from the navbar (highest signal — a real user lands here)
2. Routes that render lists or accept `:id` params (highest bug density)
3. Auth-gated routes (highest "looks fine but silently broken" risk)

### Step 2 — Confirm the dev stack is actually up

```bash
# Probe common dev ports (extend if the project uses something exotic)
for p in 3000 3001 4000 4321 5173 8000 8080; do
  if lsof -i :$p -t > /dev/null 2>&1; then
    echo "Port $p is listening"
  fi
done
# Hit the URL and confirm 200
curl -fsS http://localhost:<port>/ > /dev/null && echo "Frontend responsive"
```

If nothing is listening, **stop**. Don't run render-sanity against a dead port and call it a pass. Either bring up the stack (`pnpm dev` / `npm run dev` from the project root, or whatever the workspace's `dev` script is) or report "Cannot run — dev server not responding."

### Step 3 — Run the four checks

For each route in the inventory:

1. Navigate (Playwright)
2. Snapshot + console + network
3. Run Check 1 (smell scan) — uses patterns from `references/smell-patterns.md`
4. If the page renders a list, run Check 2 (click first item, verify destination)
5. Record outcome in the signed-out matrix (Check 3)

Then sign in as a seed user (or hit the demo button) and re-walk auth-gated routes for Check 4.

### Step 4 — Write the report

Save to `docs/render-sanity-YYYY-MM-DD.md` using the template in `references/report-template.md`. The template's structure is fixed so a reviewer can scan any render-sanity report and find the same sections in the same order.

### Step 5 — Decide pass/fail

- **PASS**: zero critical findings across all four checks.
- **FAIL**: one or more critical findings. The report names them; the build cannot be declared done until they're fixed and render-sanity is re-run.

A FAIL is a gate, not a recommendation. The orchestrator's Definition of Done depends on render-sanity returning PASS on a UI build.

## What this skill is NOT

- **Not visual review.** "The spacing feels off" / "the gradient is harsh" — those belong to `superpowers:ux-review`. This skill has no opinion about aesthetics.
- **Not accessibility audit.** Heading hierarchy, ARIA labels, keyboard nav — `superpowers:ux-review` or a11y tooling.
- **Not performance.** Bundle size, LCP, hydration — `performance-agent`.
- **Not contract conformance.** Whether the API matches the OpenAPI spec — `qe-agent` / `contract-auditor`.
- **Not test coverage.** Whether the unit tests cover this code — `qe-agent`.

This skill catches one specific failure mode: **the app renders, but renders broken content that humans can see and machines couldn't tell from the test suite alone.** Keep it focused.

## When invoked by other skills

- **`orchestrator`** is the primary invoker. It calls render-sanity at Phase 12 (post-build verification) BEFORE `superpowers:ux-review` — render-sanity catches broken-content failures; ux-review then assesses polish on a known-good shell. A render-sanity FAIL blocks the build's Definition of Done.
- **`superpowers:ux-review`** MAY invoke render-sanity as a precondition. When it does, the render-sanity report becomes the "Critical Issues" section of the ux-review report.
- **`feature-dev:feature-dev`** SHOULD invoke render-sanity after a feature is wired end-to-end, before declaring "the feature works."
- **The user** can invoke this skill directly any time they want a fast objective answer to "is the UI actually working" — typically after a build claims done, after a refactor, after auth was added, or after seeing a screenshot with `?` / `Couldn't load` / dead links.

## Key principles

- **Concrete evidence beats subjective judgment.** Every finding is a tuple of `(route, pattern, matched text)` or `(source list, first link, destination, outcome)`. No "feels broken."
- **Click, don't just look.** Lists that render but link to nowhere are this skill's primary catch. Snapshots and screenshots don't catch them. Clicking does.
- **Both auth states.** "It works when I'm logged in" is half a test. "It works when I'm signed out" is the other half. A skill that only walks one state misses the half its build session happened to be in.
- **Treat mock-ID leakage as a P0.** The "frontend imports mocks.ts directly into a 'live' page" bug class is silent, common, and embarrassing. A mock ID on a live page = "page is wired to fake data" Critical, not a polish item.
- **Refuse to pass a dead stack.** If the dev server isn't listening, this skill must not say "passed." Either bring it up or report that you couldn't run.

## Reference files

- `references/smell-patterns.md` — Check 1's universal smell pattern table plus project-specific derivation guidance
- `references/report-template.md` — the markdown skeleton for Step 4's report + pass/fail decision rule
