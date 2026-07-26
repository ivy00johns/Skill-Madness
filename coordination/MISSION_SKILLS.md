# Mission skill manifest — ledger drain (build/ledger-drain)

Source: /orchestrator mission "build starting with the harness, then use those improvements; review; /model-adaptation" + `docs/REMAINING-WORK.md` open rows · Scanned: 2026-07-24 · Closed out: 2026-07-24
Branch: `build/ledger-drain` · Runtime: Agent Teams / parallel subagents · Session model: Fable 5 (set via /model mid-session → every spawn passed `model` explicitly)

Scope: HE-1–HE-2 (wave 1, "the harness"), then WC-1–WC-2 + PX-3 (wave 2), PX-1→PX-2 + CB-3 (wave 3), review gates (wave 4). RV2 resolved by user decision (MIT LICENSE, wave 0). CB-10 stays filed speculative — not built, per its own ledger row. Prior build's manifest archived at `coordination/archive/2026-07-03-sr-mt-manifest.md`.

Work items = the ledger rows themselves; defaults approved by user 2026-07-23 (single-context, format-by-detection, ledger-as-tracker).

## Wave 0 — scaffold (inline)
- [x] `git-commit` — ✅ invoked; intake 98117ec + capture-settle a12b5da split onto their own branches; all build commits follow the convention.
- [x] `model-adaptation` — ✅ mission-named; read in full. Applied: explicit `model` on every spawn (fable for authoring/adversarial, sonnet for mechanical), brief-instruction-plus-reason style enforced in briefs, refusal-landmine constraint in every agent prompt, and the adversarial pass ran the canonical landmine sweep.
- [x] RV2 — ✅ MIT LICENSE at root per user decision (81532d2).

## Wave 1 — harness
- [x] HE-1 agent — ✅ `docs/audit-evidence/` projection + plan-intake 1.3.0 citation rule (dc6b718). **User review of published fragments still pending before PR** (see BUILD_RESULTS handoff).
- [x] HE-2 agent — ✅ decision-keyed routing index + madness load budget (dc6b718).

## Wave 2 — patches
- [x] WC-1 agent — ✅ fail-loud `$ARGUMENTS` lint + 2 bats cases + lint-rules.md v1.4.0 (83b68b2).
- [x] WC-2 agent — ✅ ~60-line split gate + 10-box pre-dispatch checklist + cost-tagged anti-patterns pattern #6 (7f621dc).
- [x] PX-3 agent — ✅ image-proxy model allowlist, fail-closed, durable/aging split (d7424c5).

## Wave 3 — new skills
- [x] `skill-writer` — ✅ invoked via the Skill tool by BOTH new-skill agents (PX-1 and CB-3 reports confirm the 7-step flow).
- [x] PX-1 agent — ✅ `skills/workflows/use-pxpipe/` v1.0.1 (8172614 + fix 11e9d19).
- [x] CB-3 agent — ✅ `skills/workflows/yagni-gate/` v1.0.1 (8e73164; renamed from `ponytail` by lead ruling — upstream identity not taken, kept as trigger word).
- [x] PX-2 agent — ✅ madness token-saver question riding the expensive confirm (9f37d00).
- [x] Catalog integration — ✅ single ripple 71→73 (06ae2f7); `--check` clean; CLAUDE.md name-enumeration gap caught and fixed.

## Wave 4 — review + gates
- [x] `fix-until-green` — ✅ dispatched as the wave-gate discipline: lint + catalog re-run and driven green between every wave (one mid-flight description-cap ERROR routed back by ownership and fixed at source; no gate cheating — adversarial pass verified the WC-1 green with a hostile fixture).
- [x] `skill-review` — ✅ fresh-context adversarial reviewer invoked it for the house rubric; 7 checks, 0 refuted, 2 MEDIUM + 4 LOW findings, all fixed (11e9d19).
- [x] qe-agent — ✅ fresh-context QE: `coordination/ledger-drain-qa-report.json` (schema-valid; proceed=true; 346/346; scores 5/5/5/5/5; 0 blockers) (847a601).
- [x] `code-review` — deferred with reason: the diff is docs/skills prose + 14 lines of bash + 33 lines of bats, and BOTH the adversarial skill-review pass (live fixture verification, fact spot-checks, byte-diffs) and the independent QE gate already reviewed it at outcome level; a third pass adds cost, not coverage. The user can run `/code-review` (or `ultra`) on the PR if wanted.
- [x] Ledger sweep — ✅ 9 rows → `docs/COMPLETED-WORK.md` verbatim with closure annotations; REMAINING-WORK banner rewritten (open = CB-10 only); PLAN.md closure-log entry added.

## N/A for this build (with reasons)
- `wiki-research` — no wiki in this repo (verified: no index.md / wiki/).
- `nano-banana`, `ui-ux-pro-max`, `frontend-design`, `ux-review`, `render-sanity`, `design-token-guard`, `class-extraction-guard` — docs/skills/tooling build, no UI surface; nothing renders in a browser.
- `contract-author` — work items were independent skill/doc edits with exclusive per-agent file ownership; the ledger rows served as the contracts (each row's "observable change" = acceptance criterion, and QE scored contract_conformance against them).
- `deployment-checklist` — nothing ships to a runtime; distribution stays the existing convert/install pipeline gated by its own 346-test bats suite.
