# Validation Script Pattern

Documents the convention for bundling a deterministic validation script with a skill. A validation script is a standalone program that checks invariants you can compute — not prose validation, not "review and decide", but an actual pass/fail check.

Source: Anthropic Agent Skills guide (p.26, "Advanced technique: programmatic validation") + this repo's existing scripts.

---

## When to Add a Validation Script

Add a validation script when the skill has invariants that are:

- **Deterministic** — given the same inputs, the answer is always the same. Not judgment calls.
- **Expressible in code** — a regex, a schema check, a file-existence assertion, a count threshold.
- **Worth automating** — the check would otherwise require manual inspection on every iteration.

Good candidates:

- Frontmatter field validity (names, semver, field types)
- Reference file existence (links in body resolve to real files)
- Output schema conformance (generated JSON matches a schema)
- Cross-skill invariants (no two agents own the same directory)
- Security rules (no angle brackets in frontmatter, no known-bad patterns)

Poor candidates:

- "Does this description trigger reliably?" — not deterministic without a live model
- "Is this well-written?" — judgment call
- "Will this work in production?" — depends on runtime state

---

## Existing Scripts (Reference Implementations)

The repo ships two production scripts that implement this pattern:

### `scripts/lint-skills.sh`

Validates every `SKILL.md` against PSFS v1.1.0 (frontmatter schema, body length, description quality). The reference implementation for skill-level validation. Key design choices:

- **Bash + Python3 stdlib only** — no external dependencies
- **Python3 does the YAML/regex work**; bash handles CLI, file collection, and output formatting
- **Exit codes:** 0 = no errors, 1 = at least one error, 2 = argument failure
- **Output modes:** `text` (default, human-readable) and `junit` (for CI)
- **Severity levels:** ERROR (blocking), WARN (advisory), INFO (verbose-only)
- **Cross-skill checks** run after per-skill checks — catches invariants that span files (name uniqueness, ownership overlap, composes_with resolution)
- **`--standard` flag** prints the spec version it implements — pins the linter to a named spec

### `scripts/scan-skills.sh`

Supply-chain and injection scanner for all `SKILL.md` and `references/` files. Catches secrets, prompt-injection payloads, invisible unicode, and untrusted compose references. Key design choices:

- **LLM-free and reproducible** — can be a blocking CI gate without API calls
- **JSONL findings output** — machine-parseable for integration
- **Ignore mechanisms** — inline annotation (`# scan-skills:ignore`) and `.scan-skills-ignore` file
- **Severity levels:** HIGH (blocking in `--check` mode), MEDIUM, LOW (informational)

---

## Conventions for New Validation Scripts

When a skill ships its own validation script, follow these conventions so the pattern stays consistent:

### File location

```
scripts/validate-<skill-name>.{sh,py}
```

Or, if the script is only meaningful within the skill's own context and not part of repo-wide CI:

```
skills/<category>/<skill-name>/references/validate.sh
```

The repo-level `scripts/` location is preferred when the script is a CI gate. The `references/` location is acceptable when the script is a development aid for skill authors.

### Interface contract

```bash
# Exit codes:
#   0  all checks passed
#   1  at least one check failed
#   2  argument or environment error
#
# Output: human-readable findings to stdout.
#         Machine-parseable variant: --json flag → JSONL
#
# Usage:
#   scripts/validate-<name>.sh [PATH ...]
```

### What to check

Three tiers, in order of cost:

1. **Existence checks** (cheapest) — files exist, directories are non-empty, required fields are present
2. **Shape checks** — field types, regex conformance, schema validation
3. **Cross-reference checks** (most expensive) — links resolve, referenced skills exist, ownership doesn't overlap

Stop at the first failure tier if feasible — saves runtime in CI.

### Determinism

Validation scripts must produce the same output given the same inputs. No network calls, no model calls, no random state. If you need to validate something that requires a live model, that's a `skill-review` deep-dive task, not a script.

### Dependency declaration

State dependencies in the file header comment:

```bash
# Dependencies: python3 (stdlib only), bash >=3.2
# No pyyaml, jsonschema, or external packages required for basic checks.
# pyyaml enables YAML parsing; jsonschema enables schema cross-check (both optional).
```

---

## Wiring a Script into the Skill Body

Reference the script from the skill body's validation step:

```markdown
### Step 5: Validate

Run the validation script before declaring the skill done:

    scripts/validate-<name>.sh skills/path/to/skill/

Fix any errors before proceeding. Warnings are advisory; review them and decide.
```

Or, for a skill that uses the repo's existing lint:

```markdown
Before reporting done, run:

    scripts/lint-skills.sh skills/<category>/<skill-name>/

No errors allowed. Warnings above "description is N chars" are worth reviewing.
```

---

## Anti-patterns

- **Prose validation as a "script"** — a skill body that says "validate by reading the output carefully" is not a validation script. Scripts run; prose is inspected.
- **Scripts that call the model** — validation must be deterministic. Model-in-the-loop checks belong in `skill-review`.
- **Scripts without exit codes** — CI gates depend on exit codes. A script that always exits 0 regardless of findings is not a gate.
- **One giant script that checks everything** — prefer composable checks with clear categories. `lint-skills.sh` and `scan-skills.sh` are separate for a reason: one checks spec conformance, the other checks security. Mixing them would make the output harder to act on.
