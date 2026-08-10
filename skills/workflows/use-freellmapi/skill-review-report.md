# Skill Review — use-freellmapi (deep dive, staleness focus)

- **Date:** 2026-08-10
- **Mode:** B (single-skill deep dive)
- **Focus (why-now):** freellmapi repo has moved since the skill's last edit — is the content stale?
- **Skill version reviewed:** 1.3.0 (SKILL.md + references last touched 2026-07-29)
- **Repo drift:** 81 commits since 2026-07-29, spanning releases v0.6.6 → v0.6.9 plus unreleased main
- **Telemetry:** `skill-health.sh report --json` has no rows for this skill (unobserved — not evidence of a problem)
- **Verdict: NEEDS WORK (content staleness).** Structurally the skill is SHIP-quality; the workflow,
  traps, and env-toggle pattern all still hold. But two claims are now wrong, one core framing
  (single-key auth) is outdated, and several new proxy behaviors are missing from
  `references/capabilities.md`.

Every finding below was verified against the freellmapi working tree at `b9b6bf7`, not inferred from
commit messages.

## High-priority findings (claims now wrong or misleading)

### H1. "Not supported: per-user billing / multi-tenant auth" is now half-wrong
`references/capabilities.md` (Not supported list) still says multi-tenant auth has no route.
v0.6.9 added **per-client API keys** (#758/#411): the Keys page can mint `sk-cp-…` client-profile
keys, each independently enable/disable-able, each with an optional **server-enforced system prompt**
prepended to every request authenticated with that key (verified in
`server/src/db/migrations/20260805_000002_client_profiles.ts` and `server/src/lib/system-prompt.ts`).
Billing is still single-user, but "multi-tenant auth — single-user by design" now over-claims.
**Fix:** reword the not-supported bullet to "per-user billing" only, and document client-profile keys
as a supported capability.

### H2. The "single unified key" auth story is outdated
SKILL.md ("the proxy's single *unified key*") and capabilities.md ("Auth: every /v1 call needs the
unified key") predate client-profile keys. There are now three credential kinds: the unified key,
`sk-cp-…` client keys, and revocable URL tokens. For the skill's own core use case — wiring one
project/agent to the proxy — a per-client key is arguably the *better* recommendation (per-client
analytics attribution, revocable without rotating everything, optional enforced system prompt).
**Fix:** update Step 2 and the capabilities Auth paragraph; consider recommending a per-client key
per wired project.

### H3. Tool-calling section misses the schema verdict and the double-encoding repair
capabilities.md "Tool calling" doesn't know about: (a) **opt-in schema verdict on tool arguments**
(#802, `server/src/lib/tool-validate.ts`) — validates returned tool arguments against the tool's JSON
schema and **fails over to the next model when invalid**; (b) **double-encoded argument repair below
the top level** (#794). Both change what you can promise about tool-calling reliability.
**Fix:** add both to the Tool calling section, noting the verdict is opt-in.

### H4. Routing behavior section misses five shipped changes
capabilities.md "Routing behavior" predates: **auto-cooldown of repeatedly failing models**, penalty
beyond 429 (#806); **whole-provider skip on 5xx/timeout/transport errors** instead of key-by-key
(#817); **back-off honored from the error body**, not just headers (#798); **unified output-token cap**
rescuing excessive client `max_tokens` (#783); **community reliability priors folded into the Beta
posterior** + an **exploration toggle for unmeasured models** (#744/#731).
**Fix:** fold into the Routing behavior bullets — especially the provider-skip and cooldown, which
change observable failover behavior users will ask about.

### H5. `X-Fallback-Detail` header missing
capabilities.md documents `X-Routed-Via` / `X-Fallback-Attempts` / `X-Fallback-Trail` but not the
opt-in **`X-Fallback-Detail`** header with per-hop failover timings (#792, verified in
`server/src/lib/fallback-loop.ts` + tests). It's exactly the debugging surface the skill's Step 5
teaches. **Fix:** add alongside the trail header.

### H6. Per-key features absent from the Keys story
Since the last edit, provider API keys gained **per-key model scopes** (#757), **per-key proxy
override** — each key can route through its own exit (#819), **bulk enable/disable/delete within a
group** (#816), and **immediate-probe for custom endpoints** (#730). Neither capabilities.md nor the
Step 6 dashboard tour mentions any of them. **Fix:** one compact bullet in the dashboard tour + a
Keys paragraph in capabilities.md.

### H7. Anthropic surface: document blocks now translate
agent-clients.md (Claude Code section) lists "streaming, system prompts, tool use, and image input"
as translating; #793 fixed silently-dropped **document content blocks**, so PDFs/documents now pass
through too. **Fix:** add documents to that list.

## Medium-priority findings

- **M1. Desktop app is now a real install path.** Step 1 offers only Docker or source; the repo now
  ships a maintained Electron desktop build — macOS, Windows installer + zip (#766/#773), Linux
  AppImage/deb/tar.xz (#739). Worth one sentence as a fallback when Docker isn't available.
- **M2. Keyless roster stamp is dated.** "as of v0.6.5 … Kilo `:free`, OVH, AI Horde" — roster
  **re-verified correct** against `server/src/providers/` at head (still exactly those three plus
  local Ollama), but the stamp should read v0.6.9+ so readers don't assume it's four releases stale.
- **M3. Step 2 can lean on the new provider checklist.** The Keys page now has a provider checklist
  with status icons and flags providers that need a key but have none (#596/#777/#822), plus a
  searchable provider picker (#728). This is exactly the "hold here until a provider is enabled" gate
  Step 2 walks the user through — pointing at it shortens the loop.
- **M4. Dashboard tour drift (Step 6).** Settings now includes an automatic update check with a
  release-notes dialog (#635/#782); a forgotten dashboard password is recoverable via a code from the
  server logs (#560). Both are handoff-worthy.
- **M5. Provider count drift.** AnyAPI landed as a new OpenAI-compatible provider (#772); the
  registry now has 32 `register(…)` calls. The skill's "~29 provider tiers" is hedged (and the skill
  explicitly says not to trust its own numbers), so this is cosmetic — refresh when editing anyway.

## Low-priority notes

- **L1.** `references/recipes.md` (untouched since June) contains generic client-wiring recipes with
  no proxy-behavior claims; spot-check found nothing stale. Not exhaustively re-verified.
- **L2.** Bump frontmatter `version` to 1.4.0 when the content edits land.

## Rubric scores (references/deep-review-rubric.md)

| Dimension | Score | Evidence |
| --- | --- | --- |
| Frontmatter compliance | 4 | All required fields, valid semver, no `<`/`>` in values — but the description is 1267 chars normalized, over the spec's 1024 ceiling (pre-existing; host doesn't enforce it, skill loads fine — trim in a future pass) |
| Description quality | 5 | Action verbs, 10+ trigger phrasings, keyword variants, covers agent + app-code paths |
| Progressive disclosure | 4 | 287-line body, three well-partitioned refs, clear read-only-what-matches pointers |
| Instruction clarity | 5 | Imperative, ordered workflow, explains why (env-toggle rationale, verify-before-done) |
| Coordination | 4 | `composes_with` targets exist (project-profiler, model-adaptation, use-pxpipe); no ownership overlaps |
| Completeness / accuracy | 3 | H1–H7 above: two wrong claims, five missing shipped behaviors |
| Anti-patterns | 4 | Strong self-defense against staleness ("don't hardcode the roster", "confirm against /v1/docs") — which is why only 2 of 81 commits produced outright wrong claims |

## Trigger testing

Skipped (Phase B2): the why-now for this review was content staleness, not triggering, and the
description already embeds an explicit trigger-phrase list. No live eval run; noted per process.

## Recommendation

Run `/skill-update` against the JSON sidecar. Suggested edit order (one focused change at a time):
H1+H2 together (one auth-story edit across SKILL.md + capabilities.md), then H3–H6 (capabilities.md),
then H7 (agent-clients.md), then M1–M5 batch (SKILL.md steps 1/2/6), then L2 version bump.
