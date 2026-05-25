# Contract: Skill-Health Telemetry (P2-C)

**Version:** 1.0.0
**Status:** ACTIVE — orchestrator, AllTheSkills P2
**Source plan:** `DeepResearch/The-Hive/ecc_deepdive/source-material/14-alltheskills-frontier.md` (P2)
**Models:** ECC's `scripts/skills-health.js` (per-skill 7d/30d success-rate decay + version drift from run logs).

The meta-skills `skill-review` / `skill-update` (the repo's actual audit + change-application skills; the ECC source material's `skill-audit` / `skill-improvement-plan` names do not exist here) currently run on static review with no runtime signal. This contract adds a deterministic skill-health engine. **The scoring math lives in code, never in a prompt** — that is the explicit ECC continuous-learning anti-pattern this build refuses to repeat.

## Honest scope note

Claude Code does not emit a clean "skill X invoked → outcome Y" event. So the *emitter* is necessarily coarse/best-effort; the *deliverable of value* is (1) a documented event schema, (2) a deterministic computation engine that turns whatever events exist into health metrics, and (3) version-drift detection (which needs no runtime signal at all — it compares recorded vs current frontmatter `version`). Do not fabricate per-skill attribution the host can't provide; build the engine and a coarse emitter, and document the gap.

## Telemetry event schema (JSONL)

One JSON object per line, appended to `$ATS_TELEMETRY_LOG` (default `~/.claude/ats-telemetry/skill-events.jsonl`):

```json
{"ts":"ISO8601","skill":"orchestrator","version":"1.9.0","outcome":"success|failure|unknown","session_id":"string","source":"hook|manual"}
```

## Components

### 1. `scripts/skill-health.sh`
```
scripts/skill-health.sh report  [--log FILE] [--json] [--days N]   # per-skill metrics table (default text)
scripts/skill-health.sh record  --skill NAME --outcome OUT [--log FILE] [--session ID]   # append one event
scripts/skill-health.sh drift   [--log FILE]                        # version drift only (recorded vs current SKILL.md)
scripts/skill-health.sh --help
```
- `report` computes, **deterministically**, per skill seen in the log: total invocations, 7-day success rate, 30-day success rate, a `declining` flag when `rate_7d + threshold < rate_30d` (threshold a named constant, e.g. 0.15), last-seen timestamp, and version-drift (latest event `version` vs the skill's current frontmatter `version` → `stale` if different). Skills with no events are reported as `no-data` (never an error).
- Time windows computed from `ts` vs now; bash 3.2 portable date math (epoch seconds via `date`).
- `record` appends a schema-valid line (creates the log dir if missing). Used by the hook and by manual/test calls.
- `drift` works with an empty/absent log (every skill = no recorded version → reported, not errored).
- Output JSON (`--json`) is parseable; text is a readable table. **No network, no LLM, no `eval`.**

### 2. Coarse usage hook — `hooks/scripts/skill-usage.sh` (+ manifest entry)
A best-effort, **non-blocking** hook (PostToolUse or Stop) that appends a coarse event via `skill-health.sh record` and always `exit 0`. It must degrade silently if it cannot attribute a skill (record `outcome:unknown` or skip). Add its entry to `hooks/hooks.manifest.json` (profile: `standard`+`strict`, blocking: false) and keep `scripts/lint-hooks.sh` + `tests/hooks` green.

### 3. Meta-skill wiring (additive doc pointers only)
Append a short "## Data source" note to `skills/meta/skill-review/SKILL.md` and `skills/meta/skill-update/SKILL.md` telling those skills to consult `scripts/skill-health.sh report --json` for real usage signal before recommending changes. Additive prose only — do not restructure the skills; keep bodies within the lint length limit.

## Tests (`tests/skill-health/`, bats, bash-3.2, temp log via `--log`)
- `record` then `report` → the event appears; success rate computed correctly (e.g. 3 success + 1 failure = 0.75).
- 7d vs 30d windows: events older than 7d count in 30d only; `declining` flag fires when recent rate drops past threshold.
- version drift: an event with an old `version` vs current SKILL.md → `stale`; matching version → not stale.
- empty/absent log → `report` and `drift` exit 0 with `no-data`, never crash.
- `--json` parses (python3) and totals are internally consistent.

## Ownership (P2-C agent)
OWNS: `scripts/skill-health.sh`, `tests/skill-health/`, `hooks/scripts/skill-usage.sh` + its `hooks/hooks.manifest.json` entry, and additive "Data source" pointers in `skills/meta/skill-review/SKILL.md` + `skills/meta/skill-update/SKILL.md`.
MUST NOT touch: `.github/workflows/` (orchestrator wires CI), `scripts/install*.sh`, `scripts/convert.sh`, `scripts/catalog.sh`, `scripts/scan-skills.sh` + `tests/scan-skills/` (P2-D), `scripts/install-plan|apply|state.sh`, README root, `skills/roles/security-agent/SKILL.md` (P2-D), `skills/workflows/repo-deep-dive/`.

## DoD
`skill-health.sh report/record/drift` deterministic + tested; coarse hook added without breaking hooks lint/bats; meta-skill pointers added; `bash -n` clean; bats pass. **No git ops. No real `~/.claude/` writes in tests (use `--log` temp).**

## Changelog
- 1.0.0 — initial (orchestrator, P2-C).
