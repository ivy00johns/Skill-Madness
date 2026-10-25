---
name: skill-triage
version: 0.1.0
description: >-
  Measure and fix skill routing with TypeSafe's Jev decision model: ask which
  skill a request should load, score the catalog against labeled routing cases,
  and find description collisions where one skill steals another's trigger
  phrases. Returns probabilities, not opinions, in under a second per call. Use
  when skills misfire or under-trigger, before or after editing a description,
  when skill-review needs trigger evidence, when madness wants a second opinion
  on a route, or to regression-test the catalog after adding a skill. Trigger
  on: "jev", "typesafe", "which skill should fire for this", "why did the wrong
  skill trigger", "description collisions", "are my skills stealing each
  other's triggers", "check routing accuracy", "trigger check", "test the
  routing table", "score skill descriptions".
requires_agent_teams: false
requires_claude_code: false
min_plan: starter
owns:
  directories: []
  patterns: []
  shared_read: ["skills/"]
allowed-tools: ["Read", "Bash", "Grep", "Glob"]
composes_with: ["madness", "skill-review", "skill-update", "skill-explorer", "skill-writer"]
spawned_by: []
---

# skill-triage

Skill routing fails quietly. With dozens of pushy descriptions loaded at once, a
request lands on a plausible-but-wrong skill, or on none, and nobody notices
until the output is off. This skill makes routing **measurable**: it asks a
small decision model which skill fits, gets back a probability for every skill,
and turns that into accuracy numbers and a list of who is stealing from whom.

## What Jev is (and isn't)

Jev is TypeSafe AI's "System One" model. You send it a _state_ (here, the user
request) plus typed questions. It returns typed answers: a `choice` over up to
255 options with a full probability distribution and a confidence, or a `noul`
(the probability a statement is true). It does not write text or code, and it
cannot replace the model running your session. It is a fast, cheap classifier
that you call from code.

That shape fits skill routing well. Each skill's name and description become
one option of a Choice question, which is roughly the same text a host sees
when it decides whether to load a skill.

TypeSafe ships its own agent skill (`typesafe-ai/skills`) that teaches agents
the API in general. This skill doesn't duplicate it. It applies Jev to one job:
routing this catalog.

## The script

Everything runs through `scripts/triage.py` (python3 stdlib, no install).
It discovers skills the same way `scripts/catalog.sh` does
(`skills/<category>/<skill>/SKILL.md` plus the top-level orchestrator, skipping
`archive/`, `in-progress/`, `node_modules/`). Pass `--root` for any other
skills directory, and `--only` to narrow the catalog to the skills actually
available on this host.

| Mode                                         | What it answers                                            | Calls                       |
| -------------------------------------------- | ---------------------------------------------------------- | --------------------------- |
| `route "<request>"`                          | Which one skill should handle this, or none                | 2                           |
| `check --cases F` / `--from-routing-table F` | How often the catalog routes labeled requests correctly    | 1 per case                  |
| `collisions [--skill X]`                     | Which skills lose their _own_ trigger phrases, and to whom | 1 per quoted trigger phrase |

Always `--dry-run` a `check` or `collisions` run first. It prints the call count
and approximate input tokens without touching the network, and the
full-catalog collision scan is several hundred calls.

### How `route` decides

It follows TypeSafe's published skill-suggestion pattern (which cut wrong skill
loads from 16.8% to 7.3% over 488 requests in their test):

1. **Wide rank.** One Choice over every skill, plus three gate nouls: does the
   request act on the user's system, would an expert follow a documented
   procedure, could a short answer suffice (inverted). If the gate mean is below
   `GATE_THRESHOLD`, the answer is **no skill**. That is a legitimate result,
   the same as madness's "none is a legal outcome."
2. **Rerank.** The top `SHORTLIST` skills get their description plus a body
   excerpt, a second Choice, and a per-skill "fits" noul. If no candidate fits
   above `FITS_THRESHOLD`, there's no winner.

The thresholds are constants at the top of the script, kept in one place so a
human can review and tune them. Change them there, not with ad-hoc flags.

### Why `check` and `collisions` rank on descriptions only

The host decides whether to load a skill from its name and description, not
its body. Scoring that same text means a miss points at the _description_,
which is the thing you can fix. `route` is different: it's making a real
decision, so it uses every signal it has.

## Credentials, cost, privacy

- **Key:** Venice is the default provider. The script uses the first of
  `VENICE_API_KEY` (`api.venice.ai/api`), `TYPESAFE_API_KEY` (direct,
  `api.typesafe.ai`) or `OPENROUTER_API_KEY` that is set, and `JEV_PROVIDER`
  forces one. All three serve the same `/v1/systemone` contract. Venice omits `usage.cost`, so the script estimates it
  from Venice's published input price, and Venice only offers `jev-latest`, so
  pinned before/after comparisons need TypeSafe or OpenRouter. Look for
  the key _name_ in the environment and the project's `.env` files before
  asking the user for anything, and pass `--env-file` rather than exporting it.
  The script never prints the value.
- **Model:** `JEV_MODEL`/`--model`, default `jev-latest`. Every run reports the
  model that actually served it. Pin a version (e.g. `jev-1.13`) when comparing
  two `check` runs, or a model change will look like a description change.
- **Cost:** measured 2026-10-22 via OpenRouter: a full 76-skill `route` was
  about $0.0006 and 0.6–1.0 s; a 65-case `check` was $0.034 and 7 s. A 402
  "insufficient credits" means the account needs credits; topping up is the
  user's call, never yours.
- **Fallback (exit 4):** no key, a rejected key, an empty account (401/402/403),
  an unreachable endpoint, or rate limits that outlast the retries all exit
  **4** with a one-line `jev unavailable: ...` reason. Exit 4 means "carry on
  without Jev": route by judgment exactly as you would have, and say so in one
  line. Never retry in a loop and never fabricate probabilities. Exit 3 is
  different: the API rejected the request itself, which is a bug to report.
- **Privacy:** every call sends the request text and the catalog's
  descriptions to TypeSafe (and to OpenRouter on that path). The catalog here
  is public OSS, but a user's request may not be. Don't route private requests
  through it unless the user has opted in.

## Reading the results

Treat Jev as a fast second opinion, not the judge. A disagreement is a reason
to look, and either side can be wrong:

- **Stealers** (`winner <- owner: count`). The winner's description claims
  territory the owner meant to own. Usually you'd sharpen the _owner's_
  phrasing or add a scoped "not for X" to the stealer. Hand the edit to
  `skill-update`, then re-run the same `check` to confirm it moved.
- **The label may be wrong.** Example from the first run: "run until green" went
  to `loop-controller` over `fix-until-green`, but madness deliberately routes
  loops through `loop-controller`. That's a routing-table question, not a
  description bug. Say which one you think it is, and why.
- **Probe noise in `collisions`.** Probes are the quoted strings after the
  description's first trigger marker ("Trigger on", "Use when", ...), or every
  quote if there's no marker. A quote that's prose, not a trigger (e.g. "don't
  skip it because it 'looks fine'"), shows up as a miss. Read the quote in
  context before calling it a collision.
- **Thin margins** (correct, but by less than `LOW_MARGIN`). These are the next
  misses waiting to happen, so they're worth fixing before they flip.
- **Skipped phrases** in `--from-routing-table` point at skills outside this
  catalog (plugin skills like `superpowers:*`). That's expected; to include
  them, add their roots with `--root`.

For a report, give the accuracy, the stealer list, each miss with a one-line
verdict (description fix / label fix / genuine ambiguity), and the served model
and cost.

## Composing with the rest of the toolkit

- **madness:** the pre-check is off by default, because every call costs money
  and sends the request off the machine. It runs only when `SKILL_TRIAGE_ROUTE=1`
  is set or the user asks for Jev in the session. madness then runs `route` and
  uses the result as a hint; its own judgment and its confirm gate still decide.
  A Jev pick never skips the "...go?" on an expensive route. Any non-zero exit
  means madness routes as if the pre-check never ran.
- **skill-review / skill-update:** `collisions --skill <name>` gives trigger
  evidence for one skill under review. Re-run it after the update.
- **skill-writer:** after adding a skill, run `collisions --skill <new>` and a
  `check` over the routing table. A new skill's commonest failure is stealing
  an existing skill's triggers.

## When not to use it

- The user already named the skill. Run that skill.
- The script exits 4 (no key, empty account, no network). Say so in one line
  and route by judgment. Never fabricate probabilities.
- Grading skill _output quality_. This measures which skill is picked, not how
  well it works once loaded. That's the skill-creator eval loop.

## Anti-patterns

| Anti-pattern                                         | Why it fails                                                                                            |
| ---------------------------------------------------- | ------------------------------------------------------------------------------------------------------- |
| Rewriting a description until Jev agrees             | Overfits one classifier; the real router is the host model. Fix only what you can explain in a sentence |
| Comparing runs on `jev-latest`                       | The alias moves (1.13 → 1.14 in October 2026); pin the model for before/after                           |
| Full collision scan without `--dry-run`              | Hundreds of paid calls you didn't size first                                                            |
| Letting a route hint override madness's confirm gate | Cost and blast radius are madness's call, not the classifier's                                          |
| Sending private requests by default                  | Every call leaves the machine; opt-in only                                                              |
