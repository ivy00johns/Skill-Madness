# Contract: Portable Skill Frontmatter Spec (PSFS) — Publish as a Named Standard (P3)

**Version:** 1.0.0
**Status:** ACTIVE — orchestrator, AllTheSkills P3
**Source plan:** `DeepResearch/The-Hive/ecc_deepdive/source-material/14-alltheskills-frontier.md` (P3 — "Publish the frontmatter standard")
**Models:** This repo's own `skills/meta/skill-writer/references/frontmatter-spec.md` (the crown-jewel spec) + `scripts/lint-skills.sh` (the existing bash validator) + `contracts/installer/lint-rules.md` (the machine-checkable rule translation).

## Intent

`frontmatter-spec.md` is already more complete than ECC's frontmatter and is effectively a spec for "what a portable, ownership-aware, composable skill declares." P3 turns that local convention into **ecosystem leverage**: publish it as a *named, versioned standard* — the **Portable Skill Frontmatter Spec (PSFS), v1.0.0** — with a **portable, tool-agnostic JSON Schema** as the canonical machine-readable validator and `lint-skills.sh` as the bash reference implementation. Other collections (including ECC, which is Node, not bash) can then validate conformance in any language by running the schema, and converge on the standard without adopting this repo's tooling.

## Hard guardrails

- **Do not weaken the existing lint gate.** `scripts/lint-skills.sh skills/` MUST still exit 0 on the current tree after all P3 changes. The schema and the bash linter must AGREE on the current tree (every real `SKILL.md` validates clean against the schema).
- **No new source of truth that drifts.** The PSFS standard doc, the JSON Schema, and `frontmatter-spec.md` describe the *same* fields. The published standard (`spec/PSFS.md`) becomes canonical; `frontmatter-spec.md` stays the in-repo authoring reference and gains a one-line pointer declaring PSFS as the published standard it conforms to. Do NOT fork the field definitions into three diverging copies.
- **No git operations. No network. No LLM calls in the validator.** Bash 3.2 portable; reuse `scripts/lib/term.sh` helpers. Schema validation uses `python3` stdlib + (optionally) the `jsonschema` package *if present*; if absent, degrade to a clear advisory (mirror the existing `pyyaml` advisory pattern — WARN, never hard-fail the environment).
- **Conformance, not coercion.** The standard defines two tiers (Core / Extended). It does not require every collection to adopt the multi-agent extensions.

## The two conformance tiers (define these precisely in PSFS.md)

- **Core conformance** — valid `name` (kebab-case, ≤64, matches folder), `version` (semver), `description` (present, ≤1024 chars, no `<`/`>`), plus any Anthropic-spec optionals (`compatibility`, `license`, `allowed-tools`, `metadata`, `argument-hint`, `disable-model-invocation`) used correctly. **No Extended field is required.** This is the tier ECC and other vendor-neutral collections can claim.
- **Extended conformance** — Core + correct use of this repo's multi-agent extensions where present (`requires_agent_teams`, `requires_claude_code`, `min_plan`, `owns`, `composes_with`, `spawned_by`). Required for orchestrated builds.

## Components & ownership

### Agent A — Standards Author (`spec/PSFS.md` + pointer)
OWNS exclusively:
- `spec/PSFS.md` — the published standard. Must contain, in this order: a titled header `# Portable Skill Frontmatter Spec (PSFS)` with `**Version:** 1.0.0` and a `**Status:** Published` line; a one-paragraph abstract; the two conformance tiers above stated normatively (RFC-2119 MUST/SHOULD/MAY language); the full field catalog (Core then Extended) — you MAY reproduce the field tables from `frontmatter-spec.md` but framed as a standard (normative, versioned), not a how-to; a **Reference Validators** section naming BOTH `spec/frontmatter.schema.json` (canonical, portable, JSON Schema 2020-12) AND `scripts/lint-skills.sh --standard` (bash reference impl) and stating exactly which checks are schema-expressible (per-file structure) vs validator-only (cross-file: name-uniqueness, name==dirname, `owns` non-overlap); a **Conformance** statement (how a collection claims Core vs Extended); a **Relationship to Anthropic's Agent Skills spec** section (Core is a strict superset-compatible profile; Extended fields are ignored safely by Anthropic parsers); and a **Changelog** (`1.0.0 — initial publication`).
- A one-line alignment pointer appended near the top of `skills/meta/skill-writer/references/frontmatter-spec.md`: a sentence stating this reference conforms to **PSFS v1.0.0** (`spec/PSFS.md`), the published standard, and that the schema + lint rules are its reference validators. **Additive only — do not restructure the existing spec.**

MUST NOT touch: `spec/frontmatter.schema.json`, `scripts/`, `tests/`, `.github/workflows/`, `contracts/`, any other `skills/` file.

### Agent B — Schema + Validator (`spec/frontmatter.schema.json` + `lint-skills.sh --standard` + tests)
OWNS exclusively:
- `spec/frontmatter.schema.json` — **JSON Schema draft 2020-12** (`$schema`, `$id` referencing PSFS v1.0.0, `title`, `description`). Encodes per-file structural conformance:
  - required: `name`, `version`, `description`.
  - `name`: `type: string`, `pattern: "^[a-z][a-z0-9-]*$"`, `maxLength: 64`.
  - `version`: `type: string`, `pattern: "^\\d+\\.\\d+\\.\\d+$"`.
  - `description`: `type: string`, `maxLength: 1024`, `pattern: "^[^<>]*$"` (no angle brackets — anywhere a string field is constrained, forbid `<`/`>`).
  - Anthropic optionals typed: `compatibility` (string, 1–500), `license` (string), `allowed-tools` (array of string) **plus the deprecated alias `allowed_tools`** (array of string — accept both, document `allowed-tools` as canonical), `argument-hint` (string), `disable-model-invocation` (boolean), `metadata` (object, free-form — `additionalProperties: true` inside).
  - Extended optionals typed: `requires_agent_teams` (boolean), `requires_claude_code` (boolean), `min_plan` (enum `starter|pro|team|enterprise`), `owns` (object with optional `directories`/`patterns`/`shared_read`, each array-of-string), `composes_with` (array of string), `spawned_by` (array of string).
  - Top-level `additionalProperties`: enumerate every documented field above and set `additionalProperties: false` **only if** that keeps the real tree green; if any current skill uses a legitimate field not listed, ADD it to the schema (and note it for the standards author) rather than loosening to `true`. Decide empirically by running against the full real tree.
  - The schema expresses **per-file structure only**. Cross-file checks (uniqueness, name==dirname, `owns` non-overlap) are explicitly out of scope for JSON Schema and remain in `lint-skills.sh` — add a top-level `description` note in the schema saying so.
- Additive changes to `scripts/lint-skills.sh`:
  - `--standard` flag: prints the PSFS standard name + version this linter implements (e.g. `Portable Skill Frontmatter Spec (PSFS) v1.0.0`) and the path to the canonical schema, then exits 0. Wire into the existing `case` arg parser (around line 553) and `usage()` (line 546) and the header comment block (lines 12–16).
  - Optional schema cross-check: when `python3` + the `jsonschema` package are available, validate each parsed frontmatter object against `spec/frontmatter.schema.json` and emit any schema violation as an **ERROR** (it's a structural defect). When `jsonschema` is absent, emit a single WARN advisory (`install python3 jsonschema for schema validation`) and continue with the existing checks — mirror the existing pyyaml-absent advisory at lines 225–226. Reuse the existing python3 helper (lines 80–132) rather than spawning a new interpreter per file where avoidable.
  - Keep the script bash 3.2 clean (`bash -n` passes) and under the existing structure; do not regress any current behavior or exit code.
- `tests/standard/` — bats (bash 3.2), with a `run-tests.sh` mirroring `tests/skill-health/run-tests.sh`:
  - `--standard` prints a line containing `PSFS` and `1.0.0`; exit 0.
  - schema is itself valid JSON and parses as a JSON Schema (`python3 -c "import json; json.load(...)"`; if `jsonschema` present, `Draft202012Validator.check_schema`).
  - **regression (the gate): every real `skills/**/SKILL.md` frontmatter validates against `spec/frontmatter.schema.json`** (skip `archive/` + `in-progress/` consistent with catalog/scan). If `jsonschema` is unavailable in the test env, this test SKIPs with a clear message rather than failing.
  - positive/negative fixtures under a temp dir: a minimal Core-valid frontmatter passes; a frontmatter with a bad-semver `version`, a non-kebab `name`, a `<` in `description`, and a bad `min_plan` enum each fail schema validation.
  - `scripts/lint-skills.sh skills/` still exits 0 on the real tree (regression that the gate wasn't weakened).

MUST NOT touch: `spec/PSFS.md`, `skills/`, `.github/workflows/`, `contracts/`, `README.md`, any other `scripts/*.sh` besides `lint-skills.sh`.

### Orchestrator (NOT the agents) — integration, owned by lead
- Wire schema validation into CI (`.github/workflows/lint-skills.yml`) — agents must not touch the workflow.
- Bind the standard into `contracts/installer/lint-rules.md` (version bump + a "Conforms to PSFS v1.0.0" note) — contract edits are the lead's job.
- README pointer to `spec/PSFS.md`; `coordination/MISSION_SKILLS.md` + `BUILD_RESULTS.md` updates.

## QE (Wave 2) — gate, owned by qe-agent
OWNS: `coordination/p3-qa-report.json` (conforms to the qe-agent qa-report schema; reuse `hooks/scripts/qa-gate-validate.py` to self-validate the report). Independently verifies (by execution + read, not by editing source):
- `scripts/lint-skills.sh skills/` exits 0 (gate not weakened).
- `scripts/lint-skills.sh --standard` reports PSFS v1.0.0.
- Every real `SKILL.md` validates against the schema (run a standalone `jsonschema` pass over the whole tree; if the package is unavailable, record this as an environment limitation in the report, not a pass).
- `bats tests/standard` passes; `bash -n scripts/lint-skills.sh` clean.
- `spec/PSFS.md` exists, is versioned 1.0.0, names BOTH reference validators, and defines Core vs Extended tiers; `frontmatter-spec.md` carries the PSFS pointer.
- Schema and bash linter do not disagree on any current skill.

## DoD
PSFS v1.0.0 published (`spec/PSFS.md`), portable `spec/frontmatter.schema.json` validates the entire real tree clean, `lint-skills.sh --standard` binds the bash impl to the named standard + optional schema cross-check, tests pass, existing lint gate still exits 0, CI wired by lead, `lint-rules.md` bound to PSFS, QA gate passed. **No git ops in agents. No real `~/.claude` writes.**

## Changelog
- 1.0.0 — initial (orchestrator, P3).
