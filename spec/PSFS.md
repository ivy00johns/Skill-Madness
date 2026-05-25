# Portable Skill Frontmatter Spec (PSFS)

**Version:** 1.1.0
**Status:** Published

The Portable Skill Frontmatter Spec (PSFS) is a named, versioned standard for the YAML
frontmatter that a skill declares in its `SKILL.md`. It defines a small, tool-agnostic
set of fields and two conformance tiers — **Core** and **Extended** — so that skill
collections written by different teams, in different languages and toolchains, can
validate against the *same* contract without adopting any one repository's tooling. PSFS
Core is a compatibility-preserving profile of Anthropic's open Agent Skills frontmatter:
a Core-conformant skill uploads to Claude.ai and runs on Claude Code and the Agent SDK
unchanged. The optional Extended fields add multi-agent coordination metadata that
non-understanding parsers ignore safely.

> **Motivation (non-normative).** Portability and convergence matter because skills are
> increasingly shared across ecosystems. A single normative spec plus a portable
> machine-readable validator lets any collection claim conformance and interoperate,
> rather than each vendor inventing a divergent frontmatter dialect.

## Conformance Tiers

The key words MUST, MUST NOT, REQUIRED, SHALL, SHALL NOT, SHOULD, SHOULD NOT,
RECOMMENDED, MAY, and OPTIONAL in this document are to be interpreted as described in
RFC 2119.

### Core

A skill claiming **Core** conformance:

- MUST declare a `name` that is kebab-case, at most 64 characters, and matches its
  containing folder name.
- MUST declare a `version` that is valid semantic versioning (`MAJOR.MINOR.PATCH`).
- MUST declare a `description` that is present, at most 1024 characters, and contains no
  `<` or `>` characters.
- MUST NOT include `<` or `>` characters anywhere in any frontmatter string value (see
  the angle-bracket rule under Field Catalog for the rationale).
- MAY include any of the Anthropic Agent Skills optional fields (`compatibility`,
  `license`, `allowed-tools`, `metadata`, `argument-hint`, `disable-model-invocation`),
  and where present those fields MUST be used with the correct type and semantics defined
  in the field catalog below.
- SHOULD keep `description` at or under a 200-character target so triggers stay tight and
  scannable; the 1024-character ceiling is the hard limit.
- SHOULD NOT use a `name` beginning with `claude-` or `anthropic-`; these prefixes are
  reserved by Anthropic for first-party skills.
- **No Extended field is REQUIRED.** Core is the tier that vendor-neutral collections —
  including ECC (Everything Claude Code) — can claim.

> **Reserved-prefix exception (non-normative).** A skill that precisely targets a
> corresponding Anthropic product or feature (for example, a skill named
> `claude-design-brief` for Claude's design canvas) may reasonably use a reserved prefix.
> This is author judgement, not a validator-checkable constraint; reference
> implementations treat a reserved-prefix `name` as a warning, not a failure.

### Extended

A skill claiming **Extended** conformance:

- MUST satisfy every Core requirement.
- MUST use this standard's multi-agent extension fields (`requires_agent_teams`,
  `requires_claude_code`, `min_plan`, `owns`, `composes_with`, `spawned_by`) correctly
  where present, with the types and semantics defined in the field catalog below.
- MUST claim Extended conformance if it participates in orchestrated, multi-agent builds,
  because ownership and composition metadata is required for zero-conflict parallel work.
- MAY omit any individual Extended field that does not apply; Extended conformance
  constrains the *correctness* of these fields, not their presence.

### Parser requirements

- A PSFS parser operating at Core tier MUST accept and ignore frontmatter keys it does
  not recognize. This is what lets an Extended skill load unchanged under a Core-only
  parser, and what lets future PSFS versions add fields without breaking older parsers.
- When both `allowed-tools` (canonical) and `allowed_tools` (deprecated alias) are
  present, a parser MUST treat `allowed-tools` as authoritative and SHOULD emit a warning
  about the redundant alias.

## Field Catalog

This catalog is normative. Field names, types, and constraints are part of PSFS v1.1.0.

**Angle-bracket rule.** Any string-typed field MUST NOT contain `<` or `>`. Frontmatter
is injected verbatim into the model's system prompt, where `<...>` sequences can be
interpreted as control or tool tags, or abused as a prompt-injection vector. The ban is
on the literal characters and is intentionally strict: it also rejects otherwise-benign
uses such as `n <= 5` or `a > b`. Authors should phrase these as `at most` / `greater
than`, or use the Unicode forms `≤` / `≥`. Reliably distinguishing a benign angle bracket
from an injection vector inside a system-prompt context is not worth the risk, so PSFS
forbids the literal characters outright rather than attempting to allow "safe" ones.

This constraint applies to every string value **and key**, at any depth — including
those nested inside the free-form `metadata` object. Enforcement is split: the JSON
Schema constrains the named typed fields, and the bash reference validator walks the
entire parsed frontmatter to cover arbitrary leaves (such as `metadata` values), a
constraint JSON Schema cannot express over a free-form object. The check runs against
parsed YAML *values*, so block-scalar indicators like `description: >` or
`description: |` are structural and never trip the rule.

### Core Fields

| Field | Required | Type | Constraints | Semantics |
|-------|----------|------|-------------|-----------|
| `name` | MUST | string | kebab-case `^[a-z][a-z0-9-]*$`, ≤64 chars, matches folder name, unique within the collection | Stable identifier for the skill. |
| `version` | MUST | string | semver `^\d+\.\d+\.\d+$` | Top-level semantic version. See Skill Versioning below. |
| `description` | MUST | string | present, ≤1024 chars, no `<`/`>`; ≤200 chars RECOMMENDED | Primary trigger text. Claude reads this to decide whether to invoke the skill: `[what it does] + [when to use] + [key capabilities/keyword variants]`. |
| `compatibility` | MAY | string | 1–500 chars, no `<`/`>` | Human-readable declaration of host, required packages, network, and MCP servers. For programmatic gating use the `requires_*` booleans. |
| `license` | MAY | string | no `<`/`>` | Per-skill SPDX license override (e.g. `MIT`, `Apache-2.0`). Usually unnecessary; the repo-level license applies. |
| `allowed-tools` | MAY | string[] | each item no `<`/`>` | **Canonical.** Whitelist of tools the skill may invoke. |
| `allowed_tools` | MAY | string[] | each item no `<`/`>` | **Deprecated alias** of `allowed-tools` (underscore form). Accepted for back-compat; new skills SHOULD use `allowed-tools`. If both appear, `allowed-tools` wins (see Parser requirements). |
| `argument-hint` | MAY | string | short, no `<`/`>` | Hint shown in Claude Code's slash-command UI for skills taking a positional argument. |
| `disable-model-invocation` | MAY | boolean | default `false` | When `true`, the skill is invocable only by an orchestrator or explicit slash-command, not by Claude's model-driven auto-trigger. Recognized by the Claude Code runtime. |
| `metadata` | MAY | object | free-form key/value | Attribution and cataloging. See the metadata note below. |

**metadata note.** `metadata` is an OPTIONAL free-form object. The keys `author`,
`category`, `tags`, `mcp-server`, `documentation`, and `support` are RECOMMENDED
conventional keys with the obvious meanings; additional keys MAY appear. PSFS does not
constrain `metadata` values beyond the angle-bracket rule on any string within them. This
mirrors Anthropic's nested-metadata form.

### Extended Fields

These fields are this standard's multi-agent extensions. They are not part of Anthropic's
Agent Skills spec; parsers that do not understand them MUST be able to ignore them safely
(see Parser requirements). They are evaluated for correctness only under Extended
conformance.

| Field | Type | Constraints | Semantics |
|-------|------|-------------|-----------|
| `requires_agent_teams` | boolean | default `false` | `true` if the skill requires `CLAUDE_CODE_EXPERIMENTAL_AGENT_TEAMS=1`. Such skills SHOULD degrade gracefully when teams are unavailable. |
| `requires_claude_code` | boolean | default `false` | `true` if the skill requires the Claude Code CLI (bash, filesystem access). |
| `min_plan` | enum | one of `starter`, `pro`, `team`, `enterprise`; default `starter` | Minimum plan tier required to run the skill. |
| `owns` | object | OPTIONAL object; see owns note below | Ownership declaration for agent role skills. |
| `composes_with` | string[] | each item no `<`/`>` | Other skill names this one naturally works with (informational). Plugin-external refs use a `plugin:name` prefix. |
| `spawned_by` | string[] | each item no `<`/`>` | Which skills spawn this one. Plugin-external refs use a `plugin:name` prefix. |

**owns note.** `owns` is an OPTIONAL object with three OPTIONAL properties, each an array
of strings (no other properties are permitted):

- `owns.directories` — directories this agent skill owns exclusively.
- `owns.patterns` — file glob patterns this agent owns.
- `owns.shared_read` — directories this agent reads but does not own.

An `owns` object MAY be empty (`owns: {}`) and any single property MAY be omitted; for
example, a skill MAY declare `owns.patterns` without `owns.directories`. The non-overlap
of `owns.directories` between agent skills is a cross-file rule (see Validator-only
checks), not a per-file one.

**Ownership resolution.** When ownership of a path is contested, resolve in this order:
(1) directory ownership takes precedence over pattern ownership — a file matching agent
A's glob but living under agent B's owned directory belongs to B; (2) a more specific
subdirectory carve-out overrides a parent directory — an agent owning `tests/performance/`
keeps it even if another owns `tests/`; (3) any conflict unresolved by (1)–(2) is
**undefined behavior at the PSFS layer** — a runtime that consumes PSFS metadata SHOULD
provide a deterministic resolution mechanism and MUST surface any conflict it cannot
resolve. (An orchestrated multi-agent build, for example, resolves at spawn time and
escalates an unresolvable conflict to a human; a static analyzer might simply report it.)

**Reference resolution.** A `composes_with` or `spawned_by` entry that names an in-collection
skill SHOULD resolve to a skill that exists in the collection; an unresolved in-collection
reference is a warning, not an error (these fields are informational and a dangling
reference does not make the skill malformed). A plugin-namespaced reference — any value
containing a `:` (e.g. `superpowers:brainstorming`), matching the prevailing Anthropic
plugin `plugin:name` convention — is external by definition: it is out of scope for
in-collection resolution and MUST NOT be flagged as unresolved.

## Skill Versioning

`version` is the skill's own semantic version (distinct from the PSFS spec version; see
Spec Versioning and Stability). Start at `1.0.0`. For a skill, treat as **breaking**
(MAJOR) any change to behavior a caller or a composing skill could depend on: renaming the
skill (its `name`/folder), removing a tool from `allowed-tools`, narrowing `owns`,
changing `spawned_by`/`composes_with` relationships, or altering `description` such that
the skill's trigger semantics shift materially. *Broadening* `owns` is also breaking at
the collection level — it can claim territory another skill relied on or create an
ownership overlap — even though it is additive from the broadening skill's own
perspective. Bump MINOR for additive capability and
PATCH for fixes that change nothing a caller relies on. When in doubt, defer to
[semver.org](https://semver.org); "breaking" means "a dependent could observe the
difference."

## Reference Validators

PSFS v1.1.0 has two reference validators:

1. **`spec/frontmatter.schema.json`** — the canonical, portable machine-readable
   validator. It is a JSON Schema 2020-12 document, runnable in any language with a
   conforming JSON Schema implementation, and is the authoritative encoding of per-file
   structural conformance.
2. **`scripts/lint-skills.sh --standard`** — the bash reference implementation. It binds
   the linter to the named standard (reporting `Portable Skill Frontmatter Spec (PSFS)
   v1.1.0` and the canonical schema path) and, where `python3` and the `jsonschema`
   package are available, cross-checks each parsed frontmatter object against the
   canonical schema. It additionally performs the cross-file checks below, which a per-file
   schema cannot express.

The two validators are kept in agreement by a regression test (`tests/standard/`) that
asserts every skill in the collection validates identically under both, run in CI by the
`Frontmatter Standard / PSFS` job.

### Schema-expressible checks (per-file structure)

The JSON Schema expresses everything verifiable by inspecting a single frontmatter object
in isolation:

- Required fields present: `name`, `version`, `description`.
- `name` is kebab-case (`^[a-z][a-z0-9-]*$`) and at most 64 characters.
- `version` matches the semver pattern `^\d+\.\d+\.\d+$`.
- `description` is at most 1024 characters and contains no `<`/`>`.
- No `<`/`>` in any constrained string field.
- Correct enum values (e.g. `min_plan` is one of `starter`, `pro`, `team`, `enterprise`).
- Correct types for every documented optional field, including the `owns` sub-object shape.

### Validator-only / cross-file checks

These require knowledge beyond a single file and are out of scope for JSON Schema. They
live in `scripts/lint-skills.sh`:

- **Name uniqueness within the collection** — each `name` appears in exactly one skill in
  the validated collection. (Global uniqueness across all PSFS collections is not claimed:
  it would require a registry PSFS does not define.)
- **`name` equals directory name** — the `name` field MUST match the skill's folder name
  on disk.
- **`owns.directories` non-overlap between agents** — no two agent skills declare ownership
  of the same directory, resolved by the Ownership resolution rules above.
- **In-collection reference resolution** — each in-collection `composes_with` / `spawned_by`
  name resolves to an existing skill (WARN if not); plugin-namespaced refs (containing `:`)
  are external and not checked. See Reference resolution above.

## Conformance

A collection declares its conformance level explicitly:

- A collection claims **Core conformance** when every skill it ships satisfies all Core
  requirements above. Vendor-neutral collections that do not use the multi-agent
  extensions — such as ECC — claim Core. Core conformance is verified end-to-end by
  running `spec/frontmatter.schema.json` against each skill's frontmatter (per-file
  structure) plus the cross-file checks listed under Reference Validators.
- A collection claims **Extended conformance** when, in addition to Core, every skill that
  uses an Extended field uses it correctly per the field catalog, and the cross-file
  `owns.directories` non-overlap rule holds across all agent skills.

A skill or collection states the tier and the standard version it targets — for example,
`Conforms to PSFS v1.1.0 (Core)` — and validates that claim with the reference validators
named above. A collection SHOULD declare this claim in its root README. A machine-readable
conformance manifest (for example a `psfs.json` file a registry could consume) is
intentionally deferred: its shape is reserved for the version that introduces a consuming
registry, rather than being specified speculatively here.

## Relationship to Anthropic's Agent Skills Spec

PSFS Core is a compatibility-preserving profile of Anthropic's open Agent Skills
frontmatter standard:

- A Core-conformant skill uses only `name`, `version`, `description`, and the Anthropic
  Agent Skills optional fields (`compatibility`, `license`, `allowed-tools`, `metadata`,
  `argument-hint`, `disable-model-invocation`). Such a skill uploads to Claude.ai and runs
  on Claude Code and the Agent SDK without modification.
- The Extended fields (`requires_agent_teams`, `requires_claude_code`, `min_plan`, `owns`,
  `composes_with`, `spawned_by`) are additive metadata. Spec-compliant parsers ignore
  unrecognized frontmatter keys, so a skill carrying Extended fields remains loadable
  everywhere Core is loadable.

In short: Core does not diverge from Anthropic's spec, and Extended never breaks
compatibility with it.

## Examples

A minimal **Core** skill (no Extended fields):

```yaml
---
name: simplify
version: 1.2.0
description: |
  Refactor code for readability without changing behavior. Use when the user asks to
  simplify, clean up, or reduce complexity in a function or module.
allowed-tools: ["Read", "Edit"]
metadata:
  author: jane-doe
  category: workflows
  tags: [refactoring, readability]
  documentation: https://example.com/skills/simplify
---
```

An **Extended** skill (an orchestrated agent that declares ownership):

```yaml
---
name: backend-agent
version: 2.0.1
description: |
  Build and own backend services in an orchestrated multi-agent build. Use when the
  orchestrator dispatches API, service, or data-layer work.
allowed-tools: ["Read", "Write", "Edit", "Bash"]
requires_claude_code: true
min_plan: starter
owns:
  directories: ["src/api/", "src/services/"]
  patterns: ["Dockerfile*"]
  shared_read: ["contracts/"]
composes_with: ["contract-author"]
spawned_by: ["orchestrator"]
---
```

## Spec Versioning and Stability

This versions the **standard itself**, not the skills that conform to it.

- **Canonical identifier.** The standard is `spec/PSFS.md` in the Skill-Madness
  repository; its machine-readable form is `spec/frontmatter.schema.json`, whose `$id`
  carries the same version. The document `Version` header and the schema `title`/`$id` are
  bumped in lockstep.
- **Versioning policy.** PSFS uses semantic versioning. A MAJOR bump removes or
  incompatibly redefines a field or constraint; a MINOR bump adds an optional field or
  relaxes a constraint in a backward-compatible way (existing conformant skills stay
  conformant); a PATCH bump is editorial. Because Core parsers MUST ignore unrecognized
  keys, additive MINOR releases do not break older parsers.
- **Deprecation.** A field is marked deprecated at least one MINOR release before any
  MAJOR release removes it (as `allowed_tools` is deprecated in favor of `allowed-tools`).
  Deprecated fields continue to validate until the removing MAJOR release.

## Changelog

This section tracks every released version of the standard.

- 1.1.0 — Editorial and normative clarifications from spec review; backward-compatible
  (no field added or removed, no constraint changed, every previously-conformant skill
  stays conformant). Folded across two review passes:
  - *Initial 1.1.0 changes.* Added a **Parser Requirements** section (Core parsers MUST
    accept and ignore unrecognized keys; `allowed-tools` is authoritative when the
    deprecated `allowed_tools` alias is also present); documented the angle-bracket threat
    model and its intentional strictness; added **Skill Versioning** and **Spec Versioning
    and Stability** sections; defined the `owns` object shape and the ownership-resolution
    order; added Core and Extended worked examples; scoped `name` uniqueness to the
    collection (not a global "ecosystem"); moved the rationale into a non-normative
    Motivation note.
  - *Second review pass.* Clarified that the angle-bracket rule applies to every string
    value and key at any depth (including `metadata`) and documented the split enforcement
    (schema for typed fields, bash validator walks the whole frontmatter) — the reference
    validator was updated to enforce this. Made ownership-resolution rule (3) tool-agnostic
    (undefined at the PSFS layer; runtimes SHOULD resolve deterministically and MUST surface
    unresolvable conflicts). Added a **Reference resolution** rule for
    `composes_with`/`spawned_by` (in-collection refs WARN if unresolved, plugin-namespaced
    refs are external and not flagged) — the validator was updated to stop flagging
    `plugin:` refs. Noted that *broadening* `owns` is breaking at the collection level.
    Recommended declaring the conformance claim in the collection README (machine-readable
    manifest deferred).
- 1.0.0 — initial publication.
