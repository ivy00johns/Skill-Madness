#!/usr/bin/env bats
# 01-standard.bats — PSFS standard: schema + lint-skills.sh --standard.
#
# Contract: contracts/standards/psfs.md v1.0.0 (P3, Agent B).
#
# Cases:
#   - `lint-skills.sh --standard` prints a line containing PSFS and 1.1.0; exit 0
#   - spec/frontmatter.schema.json is valid JSON
#   - schema passes Draft202012Validator.check_schema (skips if jsonschema absent)
#   - GATE: every real skills/**/SKILL.md frontmatter validates against the
#     schema, excluding archive/ + in-progress/ (skips if jsonschema absent)
#   - negative fixtures (bad semver, non-kebab name, '<' in description,
#     bad min_plan enum) each FAIL schema validation; a minimal Core-valid
#     frontmatter PASSES (skips if jsonschema absent)
#   - regression: `lint-skills.sh skills/` exits 0 on the real tree

setup_file() {
  export REPO_ROOT
  REPO_ROOT="$(cd "$(dirname "$BATS_TEST_FILENAME")/../.." && pwd)"
  export LINTER="$REPO_ROOT/scripts/lint-skills.sh"
  export SCHEMA="$REPO_ROOT/spec/frontmatter.schema.json"
  # Detect jsonschema once for skip gating.
  export HAS_JSONSCHEMA=false
  if python3 -c "import jsonschema" >/dev/null 2>&1; then
    HAS_JSONSCHEMA=true
  fi
}

@test "--standard prints PSFS and 1.1.0 and exits 0" {
  run "$LINTER" --standard
  [ "$status" -eq 0 ]
  [[ "$output" == *"PSFS"* ]]
  [[ "$output" == *"1.1.0"* ]]
}

@test "--standard names the canonical schema path" {
  run "$LINTER" --standard
  [ "$status" -eq 0 ]
  [[ "$output" == *"frontmatter.schema.json"* ]]
}

@test "schema is valid JSON" {
  run python3 -c "import json,sys; json.load(open(sys.argv[1]))" "$SCHEMA"
  [ "$status" -eq 0 ]
}

@test "schema declares JSON Schema draft 2020-12" {
  run python3 -c "import json,sys; d=json.load(open(sys.argv[1])); print(d.get('\$schema',''))" "$SCHEMA"
  [ "$status" -eq 0 ]
  [[ "$output" == *"2020-12"* ]]
}

@test "schema passes Draft202012Validator.check_schema" {
  if [ "$HAS_JSONSCHEMA" != "true" ]; then
    skip "python3 jsonschema not installed"
  fi
  run python3 -c "import json,sys; from jsonschema import Draft202012Validator; Draft202012Validator.check_schema(json.load(open(sys.argv[1])))" "$SCHEMA"
  [ "$status" -eq 0 ]
}

@test "GATE: every real SKILL.md validates against the schema" {
  if [ "$HAS_JSONSCHEMA" != "true" ]; then
    skip "python3 jsonschema not installed — cannot run real-tree schema gate"
  fi
  run python3 - "$REPO_ROOT/skills" "$SCHEMA" <<'PY'
import os, sys, json, yaml
from jsonschema import Draft202012Validator
skills_root, schema_path = sys.argv[1], sys.argv[2]
validator = Draft202012Validator(json.load(open(schema_path)))
failures = []
checked = 0
for dp, dn, fn in os.walk(skills_root):
    parts = dp.split(os.sep)
    if "archive" in parts or "in-progress" in parts:
        continue
    if "SKILL.md" not in fn:
        continue
    f = os.path.join(dp, "SKILL.md")
    lines = open(f).read().split("\n")
    if not lines or lines[0].strip() != "---":
        failures.append(f"{f}: missing opening ---"); continue
    end = None
    for i in range(1, len(lines)):
        if lines[i].strip() == "---":
            end = i; break
    if end is None:
        failures.append(f"{f}: no closing ---"); continue
    try:
        data = yaml.safe_load("\n".join(lines[1:end])) or {}
    except Exception as e:
        failures.append(f"{f}: YAML error {e}"); continue
    checked += 1
    for err in sorted(validator.iter_errors(data), key=str):
        loc = "/".join(str(p) for p in err.absolute_path) or "(root)"
        failures.append(f"{f}: {loc}: {err.message}")
print(f"checked {checked} files")
if failures:
    for x in failures:
        print("FAIL", x)
    sys.exit(1)
PY
  [ "$status" -eq 0 ]
  [[ "$output" == *"checked"* ]]
}

# _validate <yaml-frontmatter-text> — returns schema validator exit code.
# 0 = valid, 1 = invalid. Body of the file is irrelevant for schema check.
_validate() {
  local fm="$1"
  local tmp
  tmp="$(mktemp "${TMPDIR:-/tmp}/ats-std-fix.XXXXXX")"
  printf '%s\n' "$fm" > "$tmp"
  python3 - "$tmp" "$SCHEMA" <<'PY'
import sys, json, yaml
from jsonschema import Draft202012Validator
data = yaml.safe_load(open(sys.argv[1]).read()) or {}
v = Draft202012Validator(json.load(open(sys.argv[2])))
errs = list(v.iter_errors(data))
sys.exit(1 if errs else 0)
PY
  local rc=$?
  rm -f "$tmp"
  return $rc
}

@test "fixture: minimal Core-valid frontmatter PASSES" {
  if [ "$HAS_JSONSCHEMA" != "true" ]; then
    skip "python3 jsonschema not installed"
  fi
  run _validate "name: good-skill
version: 1.0.0
description: A valid Core skill used as a positive fixture."
  [ "$status" -eq 0 ]
}

@test "fixture: bad-semver version FAILS" {
  if [ "$HAS_JSONSCHEMA" != "true" ]; then
    skip "python3 jsonschema not installed"
  fi
  run _validate "name: good-skill
version: 1.0
description: Bad semver fixture."
  [ "$status" -eq 1 ]
}

@test "fixture: non-kebab name FAILS" {
  if [ "$HAS_JSONSCHEMA" != "true" ]; then
    skip "python3 jsonschema not installed"
  fi
  run _validate "name: Bad_Name
version: 1.0.0
description: Non-kebab name fixture."
  [ "$status" -eq 1 ]
}

@test "fixture: '<' in description FAILS" {
  if [ "$HAS_JSONSCHEMA" != "true" ]; then
    skip "python3 jsonschema not installed"
  fi
  run _validate "name: good-skill
version: 1.0.0
description: has a < angle bracket which is forbidden"
  [ "$status" -eq 1 ]
}

@test "fixture: bad min_plan enum FAILS" {
  if [ "$HAS_JSONSCHEMA" != "true" ]; then
    skip "python3 jsonschema not installed"
  fi
  run _validate "name: good-skill
version: 1.0.0
description: Bad min_plan enum fixture.
min_plan: gold"
  [ "$status" -eq 1 ]
}

@test "regression: lint-skills.sh skills/ exits 0 on the real tree" {
  run "$LINTER" "$REPO_ROOT/skills/"
  [ "$status" -eq 0 ]
}

# --- linter behavior (not schema-only): angle-bracket walk + plugin-ref skip ---
# These exercise scripts/lint-skills.sh directly via a temp skill whose folder
# name matches its `name` (the linter requires name == directory name). They
# need pyyaml (the linter's parser), not jsonschema.

_has_pyyaml() { python3 -c "import yaml" >/dev/null 2>&1; }

# _make_skill <name> <body-of-SKILL.md-after-name-line...>  -> echoes the file path
_make_skill() {
  local name="$1"; shift
  local dir="$BATS_TEST_TMPDIR/$name"
  mkdir -p "$dir"
  printf '%s\n' "$1" > "$dir/SKILL.md"
  printf '%s\n' "$dir/SKILL.md"
}

@test "linter: '<' in a metadata value is an ERROR (not just typed fields)" {
  _has_pyyaml || skip "python3 pyyaml not installed"
  local f
  f="$(_make_skill meta-angle '---
name: meta-angle
version: 1.0.0
description: A clean Core skill whose metadata hides a forbidden angle bracket.
metadata:
  note: "value with <angle> brackets"
---
Body content long enough to clear the stub-length check with plenty of real words here.')"
  run "$LINTER" "$f"
  [ "$status" -eq 1 ]
  [[ "$output" == *"metadata.note"* ]]
  [[ "$output" == *"'<' or '>'"* ]]
}

@test "linter: plugin-namespaced composes_with ref is NOT flagged as unknown" {
  _has_pyyaml || skip "python3 pyyaml not installed"
  local f
  f="$(_make_skill plugin-ref '---
name: plugin-ref
version: 1.0.0
description: A clean Core skill that composes with an external plugin skill only.
composes_with: ["superpowers:brainstorming"]
---
Body content long enough to clear the stub-length check with plenty of real words here.')"
  run "$LINTER" "$f"
  [ "$status" -eq 0 ]
  [[ "$output" != *"unknown skill 'superpowers:brainstorming'"* ]]
}
