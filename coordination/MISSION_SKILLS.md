# Mission skill manifest — ledger drain (build/ledger-drain)

Source: /orchestrator mission "build starting with the harness, then use those improvements; review; /model-adaptation" + `docs/REMAINING-WORK.md` open rows · Scanned: 2026-07-24
Branch: `build/ledger-drain` · Runtime: Agent Teams / parallel subagents · Session model: Fable 5 (set via /model mid-session → every spawn passes `model` explicitly)

Scope: **HE-1–HE-2 (wave 1, "the harness"), then WC-1–WC-2 + PX-3 (wave 2), PX-1→PX-2 + CB-3 (wave 3), review gates (wave 4)**. RV2 resolved by user decision (MIT LICENSE, wave 0). CB-10 stays filed speculative — not built, per its own ledger row. Prior build's manifest archived at `coordination/archive/2026-07-03-sr-mt-manifest.md`.

Work items = the ledger rows themselves (`docs/REMAINING-WORK.md`); no duplicate briefs/ files — the rows carry acceptance criteria and sources (defaults approved by user 2026-07-23: single-context, format-by-detection, ledger-as-tracker).

Every box must end the build either ✅ (invoked, with the artifact path)
or annotated with a one-line reason for deferral. Empty boxes are bugs.

## Wave 0 — scaffold (inline)
- [x] `git-commit` — ✅ invoked; intake commit 98117ec (`docs/harness-engineering-intake`) + capture-settle a12b5da (`fix/walkthrough-capture-settle`) split onto their own branches.
- [x] `model-adaptation` — ✅ mission-named; read in full. Tiering applied to every dispatch: authoring/adversarial-verify = fable, mechanical = sonnet, explicit `model` on every spawn (subagent-model footgun).
- [x] RV2 — ✅ MIT LICENSE added at root per user decision.

## Wave 1 — harness (HE-1, HE-2)
- [ ] HE-1 agent — sanitized audit-evidence projection (`docs/audit-evidence/`) + typed report headers + plan-intake citation rule. **USER REVIEWS published content before any PR.**
- [ ] HE-2 agent — decision-keyed `routing-table.md` + `madness` load budget (route to one / none is legal).

## Wave 2 — patches (WC-1, WC-2, PX-3)
- [ ] WC-1 agent — `$ARGUMENTS` translation or fail-loud lint in the convert pipeline.
- [ ] WC-2 agent — agent-brief numeric split gate + pre-dispatch checklist (`agent-spawning.md`) + cost-tagged anti-patterns (`skill-writer` pattern).
- [ ] PX-3 agent — image-proxy model-safety allowlist section in `model-adaptation`.

## Wave 3 — new skills (PX-1 → PX-2, CB-3)
- [ ] `skill-writer` — MUST be invoked by the PX-1 and CB-3 agents (new SKILL.md scaffolds).
- [ ] PX-1 agent — `use-pxpipe` opt-in token-saver proxy skill.
- [ ] CB-3 agent — YAGNI build-gate skill (ponytail borrow).
- [ ] PX-2 agent — `madness` proxy-suggestion hook (after PX-1; serialized behind HE-2's madness edit).
- [ ] Catalog integration — single mechanical pass ripples 71→73 through README table/diagram + plugin.json + marketplace.json once for both new skills.

## Wave 4 — review + gates
- [ ] `fix-until-green` — explicitly dispatched as the wave-gate driver each wave: `scripts/lint-skills.sh` + `scripts/catalog.sh --check` + bats suite red→green, no gate-cheating.
- [ ] `skill-review` — adversarial review pass on every new/edited skill (fable).
- [ ] qe-agent — mandatory; runs the full gate suite, emits `coordination/ledger-drain-qa-report.json` per schema.
- [ ] `code-review` — diff review pass on the branch.
- [ ] Ledger sweep — closed rows → `docs/COMPLETED-WORK.md` verbatim + PLAN.md closure log (inline, final step).

## N/A for this build (with reasons)
- `wiki-research` — no wiki in this repo (verified: no index.md / wiki/).
- `nano-banana`, `ui-ux-pro-max`, `frontend-design`, `ux-review`, `render-sanity`, `design-token-guard`, `class-extraction-guard` — docs/skills/tooling build, no UI surface; nothing renders in a browser.
- `contract-author` — work items are independent skill/doc edits with exclusive file ownership; the ledger rows are the contracts. Deliberate deferral.
- `deployment-checklist` — nothing ships to a runtime; distribution stays the existing convert/install pipeline gated by its own bats suite.
