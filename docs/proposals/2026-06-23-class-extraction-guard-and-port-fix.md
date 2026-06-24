# Fix Plan — utility-class soup gap + orchestrator port bug

> Status: **IMPLEMENTED** (2026-06-24). Skill + orchestrator wiring shipped; open decisions resolved as `class-extraction-guard` / WARN-default.
> Triggered by: raw utility-class soup shipped in `petri-dish-of-madness` despite the
> Madness gates, plus the orchestrator emitting `3000` as a dev port.

## TL;DR

Two independent problems, one shared root cause (a gate-coverage seam):

1. **Port bug** — the orchestrator pastes a worked example containing a hardcoded
   `localhost:3000` into every agent prompt, so agents adopt `3000` as the dev/API
   port. Wrong for the house convention (8000 backend / 5173 frontend; 3001 is the
   FreeLLMAPI proxy). It already leaked into project code. **Small doc fix.**
2. **Utility-soup gap** — correctly-tokenized Tailwind utilities are copy-pasted
   inline 5–9× across files instead of extracted into named classes. **No gate in the
   toolkit checks for this**, so it sailed through a "passing" build. Fix = a **new
   standalone source-level gate skill** + a documented styling convention, scaffolded
   at bootstrap so recurrence is impossible.

---

## Diagnosis (what the investigation found)

### The styling complaint is real, but the framing needs one correction
- In `petri-dish-of-madness` the colors **are** correctly tokenized — palette is
  `lab-*` (`web/tailwind.config.js:14-36`); **0 hardcoded-hex classes**;
  `design-token-guard` is **clean**. (The example tokens `bone-faint`/`rune` aren't in
  this repo — that string is from another codebase — but the *pattern* is very present.)
- The actual problem is **utility-soup duplication**: **568 inline `className` strings
  with 4+ utilities**, the same combos repeated across files:
  - `block font-mono text-[10px] text-lab-muted uppercase tracking-wider` — **9×**
    (`AnimalSpawnForm.tsx:93,118,138`, `ControlPanel.tsx:360,377,393,421,441`, `PersonaPicker.tsx:67`)
  - `lab-panel flex flex-col h-full min-h-0 overflow-hidden` — **7×** (inspector panels)
  - `lab-header flex items-center justify-between gap-2` — **5×**
- A partial `@apply` layer exists (`web/src/index.css:56-141`: `.lab-panel`, `.lab-btn`…)
  but stops at base chrome; composite/label/panel-shell patterns were never extracted,
  and there's no `cn()`/`cva`/`components/ui` infrastructure.
- **No project doc states a "use named classes" convention** — so strictly, the agents
  violated no written standard. This is an undocumented preference that must become an
  *enforced, documented* one.

### Why it got past the Madness gates — it falls in a seam
`design-token-guard` only catches token-system **bypass** — hex/rgb/hsl literals
(`check_design_tokens.py:83-87`), inline `style={{}}`, and (off by default) *bracketed*
arbitrary Tailwind (`text-[#fff]`). Bracketless semantic utilities using real tokens
pass **every rule by construction**. The gate ran (orchestrator wave-gate `SKILL.md:196`
+ Definition-of-Done #11 at `:272`) — it just doesn't check for this.

| gate | reads | catches | misses |
|---|---|---|---|
| render-sanity / ux-review | pixels | broken pages, dead links, stale data | utility soup (renders fine) |
| design-token-guard | source | token bypasses, hardcoded colors, inline styles | **how styling is organized** |
| **(new) class-extraction-guard** | source | **repeated/over-long class strings → extraction** | runtime-only issues |

The toolkit gates **which values** styling uses but never **how styling is organized**.
That's the hole. The toolkit's own anti-patterns #247 ("trusting render-level gates to
catch hardcoded styling") and #249 ("retrofitting a source-convention gate after the
code exists") describe exactly this class of failure — the new gate is the missing
sibling to `design-token-guard`.

---

## Part A — Orchestrator port fix (small; do first)

**Root cause:** one hardcoded value in a worked example, pasted to every agent.

**Canonical offender** (the live, symlinked v1.13.0 copy):
`skills/orchestrator/references/agent-spawning.md:109`
```
- `curl -i localhost:3000/api/habits/` returns 401 without auth, 200 with
```

**Fix:**
1. Replace the literal with a placeholder + an explicit derive-the-port instruction, and
   align the realistic example value to the house default (8000):
   > `curl -i localhost:<API_PORT>/api/...` — **derive `<API_PORT>` from the project's
   > `dev` script / `.env.example` / docker-compose / framework default (FastAPI 8000,
   > Vite 5173, …). Never assume 3000.**
2. Bump orchestrator version (patch).
3. **Verify:** re-render a backend-agent spawn prompt; confirm no `3000` appears and the
   port is sourced from the project.

**Consistency (already correct — no change, cited as the house standard):**
- `skills/contracts/contract-author/references/openapi-template.yaml:10` → `localhost:8000` ✅
- `skills/workflows/deployment-checklist/references/pre-deploy.md` → 8000 / 5173 ✅

**Leave as-is:** `render-sanity/SKILL.md:113` probes a *range* (`3000 3001 4000 4321 5173
8000 8080`) — not an assertion that 3000 is the port; fine.

**Low-priority normalize (optional, for repo-wide hygiene — separate from the bug):**
`playwright/references/{setup.md,screenshot-workflow.md}`, `diagnose-loop/references/feedback-loop-recipes.md`,
`railway-deploy/references/dockerfile-recipes.md` use `3000` in generic Node examples.

**Stale duplicate copies (not consumed by the live toolkit — only touch if regenerating):**
- `integrations/claude-code/orchestrator/orchestrator/SKILL.md:168` (gitignored, v1.5.1)
- `~/Downloads/AllTheSkillsAllTheAgents/skills/orchestrator/` (v1.0.0, no `3000`)

**Already-leaked instance (project cleanup — see Part D):**
`petri-dish-of-madness/backend/petridish/api/app.py:544` has a stale
`"http://localhost:3000"` CORS origin alongside the real `5173`.

---

## Part B — New standalone gate skill (closes the gap)

### Identity
- **Name:** `class-extraction-guard` (alt: `class-soup-guard`) — *open choice.*
- **Category:** `skills/workflows/` (sibling to `design-token-guard`, `render-sanity`).
- **composes_with:** `orchestrator`, `frontend-agent`, `design-token-guard`,
  `render-sanity`, `code-review-agent`, `sync-skills`.
- **Why standalone, not folded into design-token-guard:** dtg's axis is *value-level*
  (tokens vs literals); this is *structure-level* (extracted vs repeated). Different
  config, different severity profile, different mental model. The user chose a separate
  skill; keeping the two gates distinct keeps each one's "what do I check" crisp.

### What it detects (framework-agnostic, mirrors dtg's source-scanning)
Scans `className=`/`class=` string literals (JSX, Vue, Svelte, Astro, HTML) and string
args to `clsx`/`cva`/`cn`, then flags:
1. **Repeated multi-utility strings** — the same (order-normalized) class string with
   ≥ `min_utilities` tokens appearing ≥ `min_repeats` times across the repo →
   "extract into a named class/component." *(primary rule)*
2. **Over-long strings** — a single string with ≥ `max_utilities` tokens → extraction
   candidate. *(warn)*
3. **Abstraction-defeat** — extra utilities glued onto an existing named/`@apply` class
   (e.g. `lab-header flex items-center justify-between gap-2 !py-1`). *(opt-in, off by default)*

### Detector CLI contract — mirror `check_design_tokens.py` exactly
`scripts/check_class_extraction.py [--root DIR] [--config PATH] [--staged] [--json]
[--quiet] [PATHS...]`, exit codes **0 clean / 1 error-findings / 2 usage**, JSON shape:
```json
{ "summary": {"errors": 0, "warnings": 12},
  "findings": [{"file":"web/.../X.tsx","line":93,"string":"block font-mono text-[10px] …",
                "count":9,"severity":"warning","suggestion":"extract → .lab-form-label"}] }
```
Mirroring the contract means it drops into the **existing** orchestrator wave-gate snippet
unchanged (`--json`; non-zero `summary.errors` blocks the wave, routed back by file).

### Config (`.class-guard.json`, all overridable like dtg's DEFAULT_CONFIG)
- `min_utilities` (default **4**), `min_repeats` (default **3**), `max_utilities` (default **12**)
- `severity` (default **warn / non-blocking**) — see note below
- `allowlist` (strings to never flag), `include`/`exclude` globs
- **`baseline` / ratchet mode** — report only *new* duplication above a recorded baseline,
  so the gate adopts onto an existing repo (petri-dish) without a wall of findings.
  This is the direct answer to anti-pattern #249.

### Default severity = WARN (non-blocking), and why
This is a preference-y standard with no universal "right" threshold, and the toolkit's own
anti-pattern #249 says a gate retrofitted onto existing code must land report-only. It
flips to **ERROR / blocking only when scaffolded in the bootstrap wave** (greenfield), so
violation #1 is caught at commit #1 and the backlog never accumulates.

### Ships with a documented convention (the missing piece)
The skill bundles a short **styling-convention reference** it cites in every finding
("repeated ≥3× → extract per `references/extraction-convention.md`"). The project had *no*
stated convention; the gate must enforce a *written* standard, not a vibe. This is what
makes "well-named classes" an actual rule instead of an after-the-fact complaint.

### Wiring (mirror dtg's `references/wiring-into-orchestrator.md`)
- **frontend-agent self-check** — add a § to `roles/frontend-agent/references/validation-checklist.md`:
  run `class-extraction-guard` on changed files before reporting done.
- **orchestrator wave-gate** — extend `skills/orchestrator/SKILL.md:196` ("for any wave
  that touched UI…") to run this gate alongside `design-token-guard`.
- **orchestrator Definition of Done** — add **#16** ("Source-organization gate passed"),
  parallel to #11; same file-routing as a failed typecheck.
- **orchestrator anti-patterns** — broaden #247/#249 framing from "token values" to also
  cover "styling *organization*", and reinforce "scaffold at bootstrap, don't retrofit."
- **Registration** — category-based (`workflows`); `/sync-skills` creates the symlink.
  **No `manifests/profiles.json` change needed** (it's keyed by category, not per-skill).
- **Bundled assets** (mirror dtg) — `assets/class-guard.config.json`, `assets/pre-commit`,
  `assets/ci-step.yml`; `references/{config.md, wiring-into-orchestrator.md, scaffolding.md,
  extraction-convention.md}`.

### The recurrence fix (why it won't happen again)
The gate alone is not enough — `scaffolding.md` installs the config + pre-commit + CI step
in the **bootstrap wave**, before the first frontend-agent writes a line. Per anti-pattern
#249, a gate added *after* the fleet has written the UI can only ratchet; scaffolding it
first means it's enforced from commit #1. That is the actual answer to "why did this get
past."

### Eval plan (skill-creator loop — runs when we implement)
- **Fixtures:** (1) a React/Tailwind dir with heavy duplicated `className` combos →
  expect flags w/ file:line + extraction suggestion; (2) a clean dir using `@apply`/`cva`
  → expect **zero** findings (false-positive guard); (3) **petri-dish `web/` itself** as a
  real fixture → must surface the 9× `block font-mono text-[10px]…` and 7×
  `lab-panel flex flex-col…` combos.
- **Baseline:** no skill.
- **Assertions:** correct `summary` counts; flags the known duplicates; ignores
  sub-threshold single-use long strings; valid JSON schema; suggestion names an extraction
  target; ratchet mode → 0 errors against a baseline.
- Launch `generate_review.py`, review, iterate per the skill-creator loop.

---

## Part C — Sequencing & effort

| # | Work | Effort | Blocking? |
|---|---|---|---|
| 1 | Port fix (`agent-spawning.md:109`) + version bump + verify | ~15 min | no |
| 2 | New `class-extraction-guard` skill: detector + config + refs + convention doc | ~half day | no |
| 3 | Wire gate into orchestrator (wave-gate, DoD #16, anti-patterns) + frontend-agent | ~1 hr | needs #2 |
| 4 | skill-creator eval loop on the new skill (3 fixtures incl. petri-dish) + iterate | ~1–2 hrs | needs #2 |
| 5 | `/sync-skills` to symlink the new skill globally | ~2 min | needs #2 |

---

## Part D — Project cleanup (out of this session's scope; flagged)
These touch `petri-dish-of-madness`, not the toolkit — listed so they aren't lost:
- Remove stale `"http://localhost:3000"` CORS origin — `backend/petridish/api/app.py:544`.
- Extract the worst duplicated combos (9× / 7× / 5×) into `@apply`/`cva` named classes.
- Add a one-paragraph styling-convention note to the project so the new gate has a local
  standard to cite (run the gate in **ratchet mode** here — existing debt is a manual
  burndown, not a blocking wall).

---

## Open decisions (need your call before implementing)
1. **Skill name** — `class-extraction-guard` (clear intent) vs `class-soup-guard`
   (matches how you described it). Default: `class-extraction-guard`.
2. **Default severity** — WARN/non-blocking (recommended; preference-y standard) vs
   ERROR/blocking from day one.
3. **Low-priority `3000` normalize** in playwright/diagnose-loop/railway-deploy examples —
   fold into the port fix, or skip as out-of-scope.
