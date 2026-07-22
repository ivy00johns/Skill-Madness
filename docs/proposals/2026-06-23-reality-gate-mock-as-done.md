# Fix Plan — "mock-as-done": the gate-coverage hole that ships a fiction

> Status: **DONE — skills edited + eval green** (2026-06-23; eval outcome inlined under *Done when* — the eval workspace itself is local and gitignored). One follow-on remains open and is explicitly out of this change's scope: the `integrations/*` per-platform refresh (last checkbox). Surfaced by the `llm-colosseum` build:
> a complete, gorgeous "Twitch-for-AIs" spectator UI was declared **done** with
> **zero real LLM calls** — every match was a mock emitter replaying a fixture.
> Every gate was green. The product's entire moat ("watch real models reason and
> get caught") was never exercised.

## TL;DR

One root cause, four altitudes.

**Root cause:** every gate in the toolkit measures *presentation* or *internal
consistency* — `fix-until-green` proves `test+lint+typecheck exit 0`;
`render-sanity` is explicitly pixels ("not contract conformance"); `ui-brief`'s
DoD is "loads with zero console errors" + a screenshot diff. **None gate on the
product's value mechanism running against real data/services.** A mock-backed
build greens all of them. The orchestrator has a dozen anti-patterns about
"don't trust a green gate" — but every one is about *gaming an existing gate*
(relocating a violation, masking an exit code). **Not one asks whether a gate
exists for the thing that matters most: the product actually working.**

This is *convergence on a fiction*: an objective, default-FAIL, un-gameable
proof that measures a stand-in instead of the goal. It looks **more** rigorous
than subjective judgment, which is exactly why it sails through.

## The fix, at four altitudes

| Skill | Hole (exact text today) | Fix |
|---|---|---|
| `loop-controller` | "The one rule": *a loop is only as good as its stopping condition*; Step 2: make "done" *mechanical and default-FAIL*. Silent assumption: mechanical ⇒ meaningful. | Add the sibling rule: **the proof must measure the real goal, not a stand-in.** A green proof against a mock/stub/fixture is objective and wrong. When the goal depends on a real dependency, the proof must exercise it once — or be explicitly labelled scaffold-level, not goal-level. |
| `fix-until-green` | Proof = three exit codes; anti-cheat covers gaming, not coverage. | One sibling line to "never cheat the gate": a gate that is only green because the **real dependency is mocked/stubbed** is green-on-a-proxy — surface it as a coverage signal, don't call it done. |
| `ui-brief` | "What makes a good brief" §10 + Step 5 require only "loads, zero console errors" + screenshot-diff. Its own example briefs are live-data products (MarketsBeRigged "LLM-reasoning moat", Bazaar). | DoD must **prove the moat is real, not just rendered.** When the moat depends on live data / a real service / an integration, require the build to exercise the real path once (real call, real data). If the brief scopes the backend out, it must declare itself a **SHELL spec**, loudly — not a product spec. |
| `orchestrator` | DoD (15 items) + post-build verification are all presentation gates (render-sanity = pixels, ux-review = subjective). Item 3 ("render real content") is satisfied by realistic mock data. | Add a **Reality Gate** DoD item: a build whose value depends on a live backend / integration / real data must exercise ≥1 real end-to-end path (a real service call, observed). A mock-only result is reported as **"scaffold complete — NOT done,"** the headline, not a deferred footnote. Also: kill the hardcoded `localhost:3000` worked-example port in `references/agent-spawning.md` (separate leak, same review). |

Each fix is *aligned with the skill's own thesis*, not bolted on: `ui-brief`
already says "every decision is evaluated against the moat" — we extend it to
"so the DoD must verify the moat actually works." `loop-controller` already says
"don't let the agent self-grade" — we add "and don't let an objective gate grade
a stand-in."

## Why mocks are still right (what this is NOT)

Mocks/fixtures/stubs are correct **build accelerators** — they let the UI be
built before the backend lands (exactly what `ui-brief` and the colosseum brief
prescribed). The bug is never "you used a mock." The bug is **declaring done
without graduating from it**, and having **no gate that forces the graduation**.
The fix is conditional: it fires only when the product's moat depends on the real
path. A static marketing site or a portfolio has no real-path gate to add.

## Verification

- `ui-brief`: skill-creator eval — generate a brief for (a) a live-data product
  and (b) a static product, with the OLD vs NEW skill. Assert: NEW adds a
  real-path DoD gate for (a) and does **not** over-impose one for (b); OLD lacks
  it for (a). (Workspace: `skills/workflows/ui-brief-workspace/` — **local, gitignored**;
  the outcome is inlined in the *Done when* checklist below rather than linked.)
- loop/orchestrator edits: reasoned (full-build evals impractical), validated
  against the colosseum failure they would have caught.

## Done when

- [x] All four canonical skills edited: `ui-brief` (SKILL §10 + Step 5 + anti-pattern,
      and `references/brief-template.md` §11), `loop-controller` ("the one rule" +
      Step 2 *measure the goal, not a stand-in*), `fix-until-green` (green-on-a-mock
      guardrail), `orchestrator` (DoD item 4 Reality Gate + Phase 13 step (b) +
      the `localhost:3000`→`8000` worked-example port leak in `references/agent-spawning.md`).
- [x] ui-brief eval (4-run A/B, `ui-brief-workspace/iteration-1/RESULTS.md`) shows
      the conditional real-path gate appears for live-data products (live/NEW: 3
      items) and is correctly omitted with reasoning for static ones (static/NEW),
      while the OLD skill green-lit a mock for the live product (live/OLD) — the
      colosseum failure, reproduced and closed.
- [ ] `integrations/*` per-platform copies refreshed via the repo's publish step
      (separate from this change — `sync-catalog-skills.py` only reconciles
      `plugin.json`, it does not propagate SKILL.md content). The canonical
      `skills/**` edits are what `~/.claude` symlinks to and what runs today.
- [x] Proposal moved to DONE with the eval outcome recorded. The eval artifact
      (`ui-brief-workspace/iteration-1/RESULTS.md`) is local/gitignored, so the
      outcome is inlined in the checkbox above instead of linked: 4-run A/B —
      live/NEW adds 3 real-path DoD items, static/NEW correctly omits the gate
      with reasoning, live/OLD green-lights the mock (the reproduced colosseum
      failure).
