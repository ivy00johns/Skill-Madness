---
name: render-sanity
version: 1.2.2
description: |
  Load and apply this skill on its trigger even when the host has no browser or shell — it is a checklist you apply with whatever tools are available, never a reason to decline because browser tools are absent. Every check you cannot run is reported as BLOCKED, not a refusal. Runs the before-done visual sanity check for the failure modes that pass "tests green + dev server boots + 0 console errors" but visibly break the UI when a human clicks: stale mock IDs on live pages, lone `?` / `—` / `undefined` / `Loading…` where data should be, dead links, and "Couldn't load X / Unauthorized" shells. Four checks: smell scan, click-through every list, signed-out matrix, signed-in matrix. Use when tests pass but the checkout UI is broken, when a build is wrapping up, after ux-review or qe-agent, or when the user says "is it actually working", "broken pages", or "dead links".
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
composes_with: ["ux-review", "orchestrator", "frontend-agent", "feature-dev:feature-dev", "playwright"]
spawned_by: ["orchestrator", "ux-review"]
---

# Render Sanity

> **Why this exists:** "Tests pass, dev server boots, console is clean" is a process bar. It's not the same as "the app works." This skill is the missing semantic check between those two — it catches failure modes that render plausibly but are quietly broken.

This skill is **not** subjective. It does not evaluate visual hierarchy, typography, or polish — those are `ux-review`'s job. It hunts four specific, objectively-verifiable failure modes that ship past every other gate.

> **Load and apply this skill even on a host with no browser and no shell.**
> The checks below are what a *full* host runs. On a constrained host you still load
> the skill, build the route inventory from whatever source you *can* read, run every
> check the available tools allow, and mark each check you could not run as
> **BLOCKED** with the reason — never as a pass, and never as a refusal to start.
> "I can't run this without a browser, so I won't" is the one wrong answer: it is
> indistinguishable from a missing skill, and it discards the static smell scan
> (Check 1), which needs no browser at all. A partial, honestly-labeled report beats
> a clean decline every time.

**Announce at start:** "Using render-sanity to click through [N routes] and check for stale data, placeholder text, dead links, and auth dead-ends." On a host without browser tools, announce the degraded scope instead: "Using render-sanity in static-only mode — no browser here, so the route passes will be reported BLOCKED."

## Non-Negotiable Rules

- **Non-headless when a browser exists; honest when it doesn't.** These checks exist because "the app renders" is not "the app works" — so on a host that *has* a browser they must run in a **visible** Playwright browser: never headless, never via curl or source-reading, and never skipped because the smoke tests passed. On a host with *no* browser tools, do not fake the check and do not decline the skill: load it anyway, run the checks that need no browser (the Check 1 static scan, plus any source-level signal), and mark every browser-dependent check **BLOCKED**.
- **Never infer — observe.** Every finding must be a route you actually navigated and content you actually saw in the browser. If you haven't clicked it, you haven't verified it. Do not guess what a page renders from its component source, from the router, or from a passing test suite. **BLOCKED is not inference** — it is the honest report that this host could not observe the check; report it as BLOCKED, never as a guessed Pass or Critical.
- **No blind edits.** render-sanity is read-only — it reports failures, it does not fix them. When a finding points at a component, read the actual source before describing the cause; don't hypothesize from the symptom.

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

Never call a pass against a dead port. But "the stack is down" is **not** a reason to abandon the skill: bring up the stack if you have a shell (`pnpm dev` / `npm run dev` from the project root, or the workspace's `dev` script); if this host has no shell, mark the live-navigation checks (2, 3, 4) **BLOCKED — dev stack unreachable, no shell** and continue with the source-derivable work in Step 1 and Check 1. Only if neither route is available *and* no source is readable do you report the skill as fully blocked — and you still deliver the route inventory and the BLOCKED rows rather than a bare refusal.

**Full host:** dev stack down and no way to start it → report the run as BLOCKED (not PASS).
**Constrained host (no shell/browser):** skip straight to the static-only path — the route inventory from the router file plus the Check 1 scan — with the browser-dependent checks BLOCKED.

### Step 3 — Run the four checks

For each route in the inventory:

1. Navigate (Playwright)
2. Snapshot + console + network
3. Run Check 1 (smell scan) — uses patterns from `references/smell-patterns.md`
4. If the page renders a list, run Check 2 (click first item, verify destination)
5. Record outcome in the signed-out matrix (Check 3)

Then sign in as a seed user (or hit the demo button) and re-walk auth-gated routes for Check 4.

**Static-only mode (no browser tools).** If the host exposes no browser tool, do not
invent observations and do not stop. Instead: build the route inventory from the router
file, run Check 1 as far as source allows (grep the rendered text constants, mock imports,
placeholder vocabulary, and the routes' data sources with whatever read tools you have),
and mark Checks 2–4 BLOCKED with the reason. The static pass alone catches the highest-value
class — a live page wired to `mocks.ts` — because that is a *source* fact, not a pixel fact.

### Step 4 — Write the report

Save to `docs/render-sanity-YYYY-MM-DD.md` using the template in `references/report-template.md`. The template's structure is fixed so a reviewer can scan any render-sanity report and find the same sections in the same order. Every check you could not run is a **BLOCKED** row with its reason — never omitted, never written up as a pass.

### Step 5 — Decide pass/fail

- **PASS**: zero critical findings across all four checks, and every check actually ran.
- **FAIL**: one or more critical findings. The report names them; the build cannot be declared done until they're fixed and render-sanity is re-run.
- **INCOMPLETE / BLOCKED**: the host could not run one or more checks (no browser, no shell, dev stack unreachable). Report exactly which checks were blocked and why. Do **not** collapse an incomplete run into a PASS — an unimplemented check is not a clean check.

A FAIL is a gate, not a recommendation. The orchestrator's Definition of Done depends on render-sanity returning PASS on a UI build; an INCOMPLETE run means the gate did not clear, and the orchestrator must supply a host that can run the blocked checks (or accept a static-only result at the user's explicit direction).

## Hosts without a browser or shell

Many hosts expose only skill loading, file reading, or plain text. The skill still loads,
and it still produces a report — the shape changes like this:

| Step / Check | Full host (browser + shell) | Constrained host (no browser / no shell) |
|---|---|---|
| Route inventory (Step 1) | From the router file | From the router file — unchanged |
| Check 1 — smell scan | `document.body.innerText` per route | Grep rendered-text constants, `mocks`/fixture imports, placeholder vocabulary, and each route's data source in **source** — a partial pass, marking routes you could not observe |
| Check 2 — click-through | Navigate the first item's `href` | **BLOCKED** — needs a browser |
| Check 3 — signed-out matrix | Navigate every route signed out | **BLOCKED** — needs a browser |
| Check 4 — signed-in matrix | Sign in, re-walk auth-gated routes | **BLOCKED** — needs a browser + seeded creds |

The static pass is not worthless: the highest-value bug class this skill catches — a "live"
page importing `mocks.ts` — is a **source** fact, plainly visible without a browser. Report
it Critical even in static-only mode. What you must not do is guess the browser-dependent
checks: mark them **BLOCKED** with the reason and move on.

## What this skill is NOT

- **Not visual review.** "The spacing feels off" / "the gradient is harsh" — those belong to `ux-review`. This skill has no opinion about aesthetics.
- **Not accessibility audit.** Heading hierarchy, ARIA labels, keyboard nav — `ux-review` or a11y tooling.
- **Not performance.** Bundle size, LCP, hydration — `performance-agent`.
- **Not contract conformance.** Whether the API matches the OpenAPI spec — `qe-agent` / `contract-auditor`.
- **Not test coverage.** Whether the unit tests cover this code — `qe-agent`.

This skill catches one specific failure mode: **the app renders, but renders broken content that humans can see and machines couldn't tell from the test suite alone.** Keep it focused.

## When invoked by other skills

- **`orchestrator`** is the primary invoker. It calls render-sanity during post-build verification, BEFORE `ux-review` — render-sanity catches broken-content failures; ux-review then assesses polish on a known-good shell. A render-sanity FAIL blocks the build's Definition of Done.
- **`ux-review`** MAY invoke render-sanity as a precondition. When it does, the render-sanity report becomes the "Critical Issues" section of the ux-review report.
- **`feature-dev:feature-dev`** SHOULD invoke render-sanity after a feature is wired end-to-end, before declaring "the feature works."
- **The user** can invoke this skill directly any time they want a fast objective answer to "is the UI actually working" — typically after a build claims done, after a refactor, after auth was added, or after seeing a screenshot with `?` / `Couldn't load` / dead links.

## Key principles

- **Concrete evidence beats subjective judgment.** Every finding is a tuple of `(route, pattern, matched text)` or `(source list, first link, destination, outcome)`. No "feels broken."
- **Click, don't just look.** Lists that render but link to nowhere are this skill's primary catch. Snapshots and screenshots don't catch them. Clicking does.
- **Both auth states.** "It works when I'm logged in" is half a test. "It works when I'm signed out" is the other half. A skill that only walks one state misses the half its build session happened to be in.
- **Treat mock-ID leakage as a P0.** The "frontend imports mocks.ts directly into a 'live' page" bug class is silent, common, and embarrassing. A mock ID on a live page = "page is wired to fake data" Critical, not a polish item.
- **Never decline — degrade instead.** A constrained host is a *scope* problem, not a reason to refuse. Load the skill, run what you can, and mark the rest BLOCKED. A refusal produces no inventory, no static scan, and no signal; a degraded report produces all three and tells the next host exactly which checks to finish.
- **Never pass a dead stack or an unrun check.** If the dev server isn't listening, or a check had no tools to run with, the report must not say "passed." Bring the stack up, run the check, or mark it BLOCKED — a blocked check is a blocked gate.

## Reference files

- `references/smell-patterns.md` — Check 1's universal smell pattern table plus project-specific derivation guidance
- `references/report-template.md` — the markdown skeleton for Step 4's report + pass/fail decision rule
