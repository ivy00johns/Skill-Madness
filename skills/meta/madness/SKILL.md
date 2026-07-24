---
name: madness
version: 1.3.0
description: >-
  The front door to the whole toolkit — one reliable entry point that reads what
  you want, picks the RIGHT starting skill (orchestrator, plan-builder, a loop, a
  role or workflow skill, or skill-explorer), and launches it for you — so you
  stop reaching for `orchestrator` on everything just to be sure a skill fires.
  Use when you don't know which skill to start with, want to kick off work but
  aren't sure of the entry point, or just want to summon the toolkit. Confirms
  before anything expensive (agent swarms, autonomous loops, full builds) and
  fires cheap routes immediately. Trigger on: "/madness", "madness", "where do I
  start", "which skill do I use", "route me", "kick this off", "get me into the
  right workflow", "I don't know what skill", "use the toolkit", "what's the
  front door", "what should I run for this". It routes and hands off — it does
  not do the work itself and it is not a meta-orchestrator.
requires_agent_teams: false
requires_claude_code: false
min_plan: starter
owns:
  directories: []
  patterns: []
  shared_read: ["skills/"]
composes_with: ["skill-explorer", "orchestrator", "plan-builder", "loop-controller", "use-pxpipe"]
spawned_by: []
---

# Madness — the front door

This is the one entry point you can reach for when you don't want to think about
which of the dozens of skills is the right one. You say what you're trying to do;
`madness` figures out the correct *starting* skill, confirms if it's about to
launch something heavy, and hands you off into it.

## Why this exists

The toolkit under-triggers. With dozens of skills loaded every session,
descriptions blur and the model often answers a request directly instead of
reaching for the skill that would do it better. The usual workaround is to type
`orchestrator` as a panic button — but `orchestrator` is a *multi-agent build*
entry point (contracts, role agents, QA gates). On anything that isn't a
parallel build it either spins up machinery you don't need or bounces you with
"this isn't a multi-agent build." So the crutch works, but it's the wrong shape.

`madness` is the right-shaped crutch: a hair-trigger router whose only job is to
land you in the correct front door and get out of the way. Type `/madness`, or
ask "where do I even start with this," and it routes.

## The prime directive: route, then hand off

**Pick the right starting skill, launch it, and stop.** `madness` is not a
meta-orchestrator and must never *become* the work. It does not write the code,
draft the plan, or run the loop itself — it identifies which skill does that and
invokes it. The moment the target skill is running, `madness` is done. If you
find yourself doing the task instead of dispatching it, you've drifted; route and
hand off.

This is the deliberate counterpart to `skill-explorer`, which *names* a skill but
will not invoke it. `madness` is the active version: it names **and** launches.
See "madness vs skill-explorer" below for when to use which.

## How a dispatch goes

1. **Get the intent.** If invoked as `/madness <task>`, the argument is the
   intent. If invoked bare (`/madness` with nothing after it), or the intent is
   too vague to route confidently, show the menu (below) and ask — one question,
   then route. Don't guess at a heavy route from a one-word prompt.

2. **Classify to a front door.** Match the intent against the entry-point map
   below. Route to the *front door*, not the leaf skill — `orchestrator`,
   `plan-builder`, and `loop-controller` each do their own internal routing, so
   handing off to them is enough. For the long tail the map doesn't cover, lean
   on `skill-explorer`'s `references/routing-table.md` (the full intent->skill
   table) rather than reinventing it here.

3. **Decide cheap or expensive.** See the confirm gate below. This decides
   whether you launch immediately or check first.

4. **Announce, then launch.** State the pick in one line — "This is a multi-agent
   build -> launching `orchestrator`." For an expensive route, end that line with
   a question and *wait* ("...that spins up a team and runs autonomously — go?").
   For a cheap route, just invoke. Use the Skill tool (or the skill's trigger
   phrase) to actually fire it — naming it without invoking is `skill-explorer`'s
   job, not this one.

5. **Hand off and get out of the way.** Once the target skill is active, let it
   drive. Don't narrate over it or duplicate its work.

## The entry-point map

Route intent -> front door. Each front door owns the deeper routing from there.

| When the intent is... | Front door | Cost |
|---|---|---|
| Multi-agent / parallel / "swarm" / "team" build, a `MISSION.md`, coordinate a build across components | `orchestrator` | expensive |
| Turn research / a PRD / a goal into a build plan first | `plan-builder` (then `orchestrator`) | cheap |
| Keep working until something is provably true — tests green, coverage target, contract met, queue drained, overnight/autonomous, "loop until" | `loop-controller` (it picks the specific loop + primitive) | expensive |
| One concrete feature in an existing codebase (single-developer flow) | `feature-dev:feature-dev` | cheap->medium |
| Build one component when you already know the role | the role skill (`backend-agent`, `frontend-agent`, `infrastructure-agent`, `db-migration-agent`, ...) | cheap->medium |
| Design / rebuild / redesign a UI | `ui-brief` (then `frontend-design:frontend-design` or `frontend-agent`) | cheap |
| Author or audit an integration contract | `contract-author` / `contract-auditor` | cheap |
| Review code, security, or deploy-readiness | `code-review` / `security-review` / `deployment-checklist` | cheap |
| Anything about the skills themselves — create, audit, update, sync | `skill-writer` / `skill-review` / `skill-update` / `sync-skills` | cheap |
| Just browsing — "what do I have", "I forgot the name", "which skill for X" (no intent to launch yet) | `skill-explorer` | cheap |
| Git: commit, PR, address feedback, cleanup | `git-commit` / `git-pr` / `git-pr-feedback` / `git-post-merge-cleanup` | cheap |
| Docs / research / deep-dive / wiki / diagram / image | `repo-deep-dive` / `llm-wiki` / `interactive-doc` / `mermaid-charts` / `nano-banana` | cheap |
| Onboard / profile / set up a repo or harness | `project-profiler` / `setup-project-skills` / `settings-consolidator` | cheap |

## The load budget: one skill, or none

Route to **one** skill. Pushy descriptions mean any request touching a shared
term ("deploy", "review") makes several skills look plausible — but
plausible-on-topic is not the test. Ask which decision is actually *unresolved*
and route to the skill that resolves it (the "By unresolved decision" index in
`skill-explorer/references/routing-table.md` keys on exactly this). Add a second
skill only when the request genuinely contains two distinct open concerns — a
sequenced handoff like `plan-builder` -> `orchestrator` is one route with a next
step, not a second pick.

And **"no skill" is a legal outcome.** When no decision a skill resolves is
open, say so plainly and stop — a wrong-but-plausible launch costs more than
"nothing here needs a skill; closest miss is X, and here's the gap." If it looks
like a genuinely new pattern, point at `skill-writer`.

## The confirm gate: cheap goes, expensive confirms

The split exists so a reflexive `/madness` can never *silently* spend an hour or
spawn a swarm. Judge by blast radius, not by category label.

**Expensive — confirm with a one-line "...go?" first.** Anything that spawns
multiple agents, runs autonomously on its own loop or schedule, kicks off a full
multi-component build, or is awkward to unwind: `orchestrator`, every `loops/*`
skill (via `loop-controller`), large `plan-builder`->`orchestrator` handoffs that
proceed straight into building, anything that pushes commits or opens PRs without
you in the seat.

**Cheap — just launch.** Single-skill, read-mostly, fast, and easy to walk back:
`skill-explorer`, a single role skill, `ui-brief`, `mermaid-charts`,
`contract-author`, `repo-deep-dive`, a `git-*` helper. Confirming these only adds
a turn of friction for no safety gain.

When unsure which side a route falls on, treat it as expensive and ask. The cost
of one needless confirm is a sentence; the cost of an unwanted swarm is real.

### The token-saver question (rides the expensive confirm)

The runs `madness` gates as expensive — swarms, autonomous loops, full builds —
are exactly the long, token-heavy sessions where the pxpipe proxy pays (it cuts
input tokens roughly in half to a third by imaging re-sent bulk; see
`use-pxpipe`). So when an expensive route confirms, fold one extra question into
the same line: *"enable the token-saver proxy for this run?"* Once per session —
a decline holds; don't re-ask on the next route.

Know when **not** to ask, so the courtesy never becomes a nag:

- **Cheap or short routes** — the proxy's own profitability gate passes small
  sessions through anyway, so the question is pure friction.
- **Byte-exact-critical work** — runs where history would be the sole copy of
  secrets, hashes, or exact numbers have the wrong loss profile for imaging.
- **Already answered** — the proxy is already wired (`ANTHROPIC_BASE_URL` points
  at it) or the user declined earlier this session.
- **Model not on the allowlist** — if the session's model isn't allowed per
  `model-adaptation`'s *Image-proxy model allowlist*, the proxy would pass
  requests through uncompressed; there's nothing to offer.

Suggest-only, never auto-enable. On a yes, launch `use-pxpipe` to do the wiring
(the allowlist check and cache-warm verification are its job), then continue
into the route. `madness` never sets the env var itself — that would be doing
the work instead of routing it.

## No args or vague intent -> the menu

If you can't route confidently, don't pick at random — show the lay of the land
and ask which door. Keep it to the front doors, not the whole library:

```
Where do you want to go?
  • Build something — multi-agent (orchestrator) or one feature (feature-dev)
  • Plan it first — turn research/PRD/goal into a build plan (plan-builder)
  • Run a loop — work until tests pass / coverage / a contract holds (loop-controller)
  • Design a UI — brief first, then build (ui-brief)
  • The skills themselves — find / create / audit / sync (skill-explorer, skill-writer, ...)
  • Just browsing — "what do I have / which one for X" (skill-explorer)
```

Then route the answer through the normal flow (classify -> cost -> launch).

## madness vs skill-explorer

They are deliberately the two halves of one idea:

- **`skill-explorer`** answers "what do I have / what's it called / which one
  fits" and **stops at the name**. Passive. Use it to browse and decide.
- **`madness`** takes the intent and **launches** the right front door. Active.
  Use it to actually get moving.

So if the user is clearly just orienting ("what skills do I have for testing?"),
hand to `skill-explorer` — that's its job, and `madness` shouldn't take it over.
If the user wants to *do* the thing ("set up the tests and run them till green"),
`madness` routes and launches.

## When NOT to use madness

- The user already named the skill they want (`"use ui-brief for the dashboard"`)
  — just run that skill; routing through `madness` is a pointless hop.
- The user is mid-task inside an active skill and asks a domain question — let the
  running skill handle it.
- The request is a clean, unambiguous match for one skill's own triggers
  ("write the OpenAPI contract", "commit this") — those skills should fire
  directly. `madness` is for *routing confusion and cold starts*, not for adding a
  hop in front of triggers that already work.

## On non-Claude-Code hosts

Converted copies of this skill ship to other AI coding tools, but only the
*portable subset* of the library ships with them — the Claude-Code-bound skills
(`orchestrator`, every `loops/*` skill, the role agents, and the workflows bound
to the Artifact tool or `~/.claude` config) don't exist there. On those hosts,
route only to skills actually present (the git conventions and the planning /
docs / review / debugging / contract workflows); when the right front door would
be a missing Claude-Code-only skill, say so and name it rather than routing into
a dead end.

## Anti-patterns

| Anti-pattern | Why it fails |
|---|---|
| Doing the task yourself instead of dispatching | `madness` is a router; if it does the work it has become the meta-orchestrator it's meant to replace |
| Routing everything to `orchestrator` | That's the exact crutch this skill exists to retire — most intents have a lighter, correcter front door |
| Launching an expensive route with no confirm | A reflexive `/madness` must never silently spawn a swarm or start an overnight loop |
| Naming the skill but not invoking it | That's `skill-explorer`'s contract; `madness` is the active half — it launches |
| Duplicating the full routing table here | The long-tail map lives in `skill-explorer/references/routing-table.md`; route to front doors and lean on it |
| Adding a hop in front of a clean trigger | If a request already fires the right skill on its own, get out of the way |
| Routing to several plausible skills at once | The budget is one; a second pick needs a second genuinely distinct open concern, and "none" beats force-fitting the closest miss |
| Auto-enabling the token-saver proxy, or re-asking after a no | The proxy question is suggest-once; wiring is `use-pxpipe`'s job after a yes, and repeat-asking turns a courtesy into friction |
