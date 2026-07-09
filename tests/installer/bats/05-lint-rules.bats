#!/usr/bin/env bats
# 05-lint-rules.bats — Validate scripts/lint-skills.sh rules against fixtures.
#
# Contract: lint-rules.md v1.1.0
# Key: description length is WARN-only (never ERROR) per v1.1.0 changelog.

setup() {
  REPO_ROOT="$(cd "$(dirname "$BATS_TEST_FILENAME")/../../.." && pwd)"
  LINT="$REPO_ROOT/scripts/lint-skills.sh"
  FIXTURES="$REPO_ROOT/tests/installer/fixtures"
  VALID_SKILLS="$FIXTURES/skills"
  MALFORMED="$FIXTURES/malformed"

  # Temp dir for lint output
  TMPDIR_LINT="$(mktemp -d /tmp/ats-lint.XXXXXX)"
}

teardown() {
  rm -rf "$TMPDIR_LINT"
}

# ---------------------------------------------------------------------------
# Clean fixture: valid skills pass with exit 0
# ---------------------------------------------------------------------------

@test "lint: minimal-agent passes with exit 0" {
  run bash "$LINT" "$VALID_SKILLS/roles/minimal-agent/SKILL.md"
  [ "$status" -eq 0 ]
}

@test "lint: full-agent passes with exit 0" {
  run bash "$LINT" "$VALID_SKILLS/roles/full-agent/SKILL.md"
  [ "$status" -eq 0 ]
}

@test "lint: cc-only passes with exit 0" {
  run bash "$LINT" "$VALID_SKILLS/meta/cc-only/SKILL.md"
  [ "$status" -eq 0 ]
}

@test "lint: no-headers passes with exit 0" {
  run bash "$LINT" "$VALID_SKILLS/meta/no-headers/SKILL.md"
  [ "$status" -eq 0 ]
}

# ---------------------------------------------------------------------------
# Malformed frontmatter: missing closing ---
# ---------------------------------------------------------------------------

@test "lint: missing closing --- causes ERROR and exit 1" {
  run bash "$LINT" "$MALFORMED/no-closing-fence.md"
  [ "$status" -eq 1 ]
  echo "$output" | grep -qi "ERROR"
}

@test "lint: missing opening --- causes ERROR and exit 1" {
  run bash "$LINT" "$MALFORMED/no-opening-fence.md"
  [ "$status" -eq 1 ]
  echo "$output" | grep -qi "ERROR"
}

# ---------------------------------------------------------------------------
# Missing required 'name' field
# ---------------------------------------------------------------------------

@test "lint: missing 'name' field causes ERROR and exit 1" {
  run bash "$LINT" "$MALFORMED/missing-name.md"
  [ "$status" -eq 1 ]
  echo "$output" | grep -qi "ERROR"
  echo "$output" | grep -qi "name"
}

# ---------------------------------------------------------------------------
# Name does not match directory
# ---------------------------------------------------------------------------

@test "lint: name mismatch with directory causes ERROR and exit 1" {
  # name-mismatch-dir/ contains SKILL.md with name: wrong-name
  run bash "$LINT" "$MALFORMED/name-mismatch-dir/SKILL.md"
  [ "$status" -eq 1 ]
  echo "$output" | grep -qi "ERROR"
  echo "$output" | grep -qi "does not match\|mismatch"
}

# ---------------------------------------------------------------------------
# Invalid semver version
# ---------------------------------------------------------------------------

@test "lint: invalid semver version causes ERROR and exit 1" {
  run bash "$LINT" "$MALFORMED/bad-semver.md"
  [ "$status" -eq 1 ]
  echo "$output" | grep -qi "ERROR"
  echo "$output" | grep -qi "semver\|version"
}

# ---------------------------------------------------------------------------
# Description length — WARN only, never ERROR (contract v1.1.0)
# ---------------------------------------------------------------------------

@test "lint: 800-char description produces WARN not ERROR (exit 0)" {
  run bash "$LINT" "$VALID_SKILLS/meta/long-desc/SKILL.md"
  # Must exit 0 (no errors — only warnings)
  [ "$status" -eq 0 ]
  # Should have a WARN about description length
  echo "$output" | grep -qi "WARN\|warn"
}

@test "lint: 800-char description output does NOT contain ERROR" {
  run bash "$LINT" "$VALID_SKILLS/meta/long-desc/SKILL.md"
  ! echo "$output" | grep -q "^ERROR"
}

# ---------------------------------------------------------------------------
# Body word count < 50 — WARN only
# ---------------------------------------------------------------------------

@test "lint: body word count < 50 produces WARN not ERROR" {
  # Create a temp fixture with short body
  TMPSKILL_DIR="$TMPDIR_LINT/short-body"
  mkdir -p "$TMPSKILL_DIR"
  cat > "$TMPSKILL_DIR/SKILL.md" <<'EOF'
---
name: short-body
version: 1.0.0
description: Apply short-body when testing body word count warning for lint.
---

This body has fewer than fifty words total. Testing lint WARN.
EOF
  run bash "$LINT" "$TMPSKILL_DIR/SKILL.md"
  # Exit 0 (warn only, no error for short body)
  [ "$status" -eq 0 ]
  echo "$output" | grep -qi "WARN\|stub\|words"
}

# ---------------------------------------------------------------------------
# Cross-skill duplicate name — ERROR
# ---------------------------------------------------------------------------

@test "lint: duplicate name across two skills causes ERROR and exit 1" {
  # Run lint on both duplicate fixtures together
  run bash "$LINT" \
    "$VALID_SKILLS/roles/duplicate-name-a/SKILL.md" \
    "$VALID_SKILLS/roles/duplicate-name-b/SKILL.md"
  [ "$status" -eq 1 ]
  echo "$output" | grep -qi "ERROR"
  echo "$output" | grep -qi "unique\|collision\|not unique"
}

@test "lint: duplicate name error message references 'collision-test'" {
  run bash "$LINT" \
    "$VALID_SKILLS/roles/duplicate-name-a/SKILL.md" \
    "$VALID_SKILLS/roles/duplicate-name-b/SKILL.md"
  echo "$output" | grep -qi "collision-test"
}

# ---------------------------------------------------------------------------
# composes_with referencing unknown skill — WARN only
# ---------------------------------------------------------------------------

@test "lint: composes_with referencing unknown skill produces WARN not ERROR" {
  TMPSKILL_DIR="$TMPDIR_LINT/ref-unknown"
  mkdir -p "$TMPSKILL_DIR"
  cat > "$TMPSKILL_DIR/SKILL.md" <<'EOF'
---
name: ref-unknown
version: 1.0.0
description: Apply ref-unknown when testing broken composes_with reference for lint warning.
composes_with:
  - nonexistent-skill-xyz
---

## Overview

This fixture skill references a nonexistent skill in composes_with. The lint script should emit a WARN about the broken reference but must NOT emit an ERROR. The exit code must be 0.

This body is long enough to pass the fifty-word word count check for the body. More words here to ensure we are safely above the threshold and the only warning is about composes_with.
EOF
  run bash "$LINT" "$TMPSKILL_DIR/SKILL.md"
  # composes_with broken ref → WARN only, exit 0
  [ "$status" -eq 0 ]
  echo "$output" | grep -qi "WARN\|warn"
  echo "$output" | grep -qi "nonexistent-skill-xyz\|unknown"
}

# ---------------------------------------------------------------------------
# --format junit produces parseable XML
# ---------------------------------------------------------------------------

@test "lint: --format junit produces XML with testsuites root element" {
  run bash "$LINT" --format junit "$VALID_SKILLS/roles/minimal-agent/SKILL.md"
  echo "$output" | grep -q '<?xml'
  echo "$output" | grep -q '<testsuites'
  echo "$output" | grep -q '</testsuites>'
}

@test "lint: --format junit XML is parseable by python3 xml.etree" {
  run bash "$LINT" --format junit "$VALID_SKILLS/roles/minimal-agent/SKILL.md"
  echo "$output" | python3 -c "import sys, xml.etree.ElementTree as ET; ET.parse(sys.stdin)"
}

@test "lint: --format junit with errors produces failure elements" {
  run bash "$LINT" --format junit "$MALFORMED/no-closing-fence.md"
  echo "$output" | grep -q '<failure'
}

# ---------------------------------------------------------------------------
# Exit code 2 on bad argument
# ---------------------------------------------------------------------------

@test "lint: unknown option exits with code 2" {
  run bash "$LINT" --unknown-flag-xyz
  [ "$status" -eq 2 ]
}

@test "lint: --format with invalid value exits with code 2" {
  run bash "$LINT" --format markdown
  [ "$status" -eq 2 ]
}

# ---------------------------------------------------------------------------
# SR12 — description ceiling-approach WARN band (>950 chars). WARN only,
# never ERROR, never changes the exit code.
# ---------------------------------------------------------------------------

@test "lint: description >950 chars produces the ceiling WARN, exit 0" {
  TMPSKILL_DIR="$TMPDIR_LINT/ceiling-band"
  mkdir -p "$TMPSKILL_DIR"
  # Deterministic ~980-char description (>950 band, <1024 schema hard max).
  python3 - "$TMPSKILL_DIR/SKILL.md" <<'PY'
import sys
desc = ("Use ceiling-band to exercise the description ceiling-approach warning band. "
        + "trigger context filler words " * 100)[:980]
body = "This body has well over fifty words so the only interesting output is the ceiling warning. " * 3
open(sys.argv[1], "w").write(
    "---\nname: ceiling-band\nversion: 1.0.0\ndescription: %s\n---\n\n%s\n" % (desc, body))
PY
  run bash "$LINT" "$TMPSKILL_DIR/SKILL.md"
  [ "$status" -eq 0 ]
  echo "$output" | grep -qi "hard ceiling"
  ! echo "$output" | grep -q "^ERROR"
}

@test "lint: normal-length description does NOT produce the ceiling WARN" {
  run bash "$LINT" "$VALID_SKILLS/roles/minimal-agent/SKILL.md"
  [ "$status" -eq 0 ]
  ! echo "$output" | grep -qi "hard ceiling"
}

# ---------------------------------------------------------------------------
# SR18 — owns.patterns glob-intersection check across skills. WARN only.
# ---------------------------------------------------------------------------

# _mk_pattern_skill <name> <pattern> -> echoes the SKILL.md path
_mk_pattern_skill() {
  local name="$1" pat="$2"
  local dir="$TMPDIR_LINT/$name"
  mkdir -p "$dir"
  cat > "$dir/SKILL.md" <<EOF
---
name: $name
version: 1.0.0
description: Apply $name when testing owns.patterns glob-intersection detection for lint.
owns:
  directories: []
  patterns: ["$pat"]
  shared_read: ["*"]
---

This fixture declares a single owns.patterns entry so the cross-skill glob check has something to compare. The body is padded well past the fifty-word stub threshold with additional filler words here for safety and clarity in the test.
EOF
  printf '%s\n' "$dir/SKILL.md"
}

@test "lint: intersecting owns.patterns across skills produce a WARN, exit 0" {
  local a b
  a="$(_mk_pattern_skill alpha-ui '*.tsx')"
  b="$(_mk_pattern_skill beta-tests '*.test.*')"
  run bash "$LINT" "$a" "$b"
  [ "$status" -eq 0 ]
  echo "$output" | grep -qi "owns.patterns overlap"
  echo "$output" | grep -q "alpha-ui"
  echo "$output" | grep -q "beta-tests"
}

@test "lint: non-intersecting owns.patterns produce no overlap WARN" {
  local a b
  a="$(_mk_pattern_skill gamma-py '*.py')"
  b="$(_mk_pattern_skill delta-js '*.js')"
  run bash "$LINT" "$a" "$b"
  [ "$status" -eq 0 ]
  ! echo "$output" | grep -qi "owns.patterns overlap"
}

@test "lint: documented-tiebreak pair (frontend/qe) is NOT flagged as overlapping" {
  local a b
  a="$(_mk_pattern_skill frontend-agent '*.tsx')"
  b="$(_mk_pattern_skill qe-agent '*.test.*')"
  run bash "$LINT" "$a" "$b"
  [ "$status" -eq 0 ]
  ! echo "$output" | grep -qi "owns.patterns overlap"
}

# ---------------------------------------------------------------------------
# SR24 — known_external allowlist covers artifact-design / dataviz so
# non-namespaced host-global composes_with refs stop warning forever.
# ---------------------------------------------------------------------------

@test "lint: composes_with artifact-design/dataviz are NOT flagged unknown (allowlisted)" {
  TMPSKILL_DIR="$TMPDIR_LINT/allowlisted-externals"
  mkdir -p "$TMPSKILL_DIR"
  cat > "$TMPSKILL_DIR/SKILL.md" <<'EOF'
---
name: allowlisted-externals
version: 1.0.0
description: Apply allowlisted-externals when testing that host-global composes refs do not warn.
composes_with:
  - artifact-design
  - dataviz
---

This fixture composes with two host-global skills that live outside the collection. The lint script must not flag either as an unknown skill because both are on the known-external allowlist. Body padded past the fifty-word stub threshold with filler words here for safety.
EOF
  run bash "$LINT" "$TMPSKILL_DIR/SKILL.md"
  [ "$status" -eq 0 ]
  ! echo "$output" | grep -q "unknown skill 'artifact-design'"
  ! echo "$output" | grep -q "unknown skill 'dataviz'"
}

@test "lint: composes_with a genuinely unknown skill still WARNs" {
  TMPSKILL_DIR="$TMPDIR_LINT/unknown-external"
  mkdir -p "$TMPSKILL_DIR"
  cat > "$TMPSKILL_DIR/SKILL.md" <<'EOF'
---
name: unknown-external
version: 1.0.0
description: Apply unknown-external when testing that a bogus composes ref still warns for lint.
composes_with:
  - definitely-not-a-real-skill-xyz
---

This fixture composes with a skill that does not exist and is not on the allowlist, so the lint script must emit a WARN about the unknown reference. Body padded past the fifty-word stub threshold with additional filler words here for safety.
EOF
  run bash "$LINT" "$TMPSKILL_DIR/SKILL.md"
  [ "$status" -eq 0 ]
  echo "$output" | grep -q "unknown skill 'definitely-not-a-real-skill-xyz'"
}

# ---------------------------------------------------------------------------
# SR13 — --changed version-bump-drift guard (git-based, opt-in). Builds a
# self-contained fixture repo with a copied linter (so its REPO_ROOT is the
# fixture), one committed skill at 1.0.0, then mutates the working tree.
# ---------------------------------------------------------------------------

# _mk_changed_fixture — sets FIX (repo), BASE (base commit SHA), SK (skill path).
_mk_changed_fixture() {
  FIX="$BATS_TEST_TMPDIR/changed"
  mkdir -p "$FIX/scripts" "$FIX/spec" "$FIX/skills/meta/drift-skill"
  cp -R "$REPO_ROOT/scripts/lib" "$FIX/scripts/lib"
  cp "$REPO_ROOT/scripts/lint-skills.sh" "$FIX/scripts/lint-skills.sh"
  cp "$REPO_ROOT/spec/frontmatter.schema.json" "$FIX/spec/frontmatter.schema.json" 2>/dev/null || true
  SK="$FIX/skills/meta/drift-skill/SKILL.md"
  cat > "$SK" <<'EOF'
---
name: drift-skill
version: 1.0.0
description: Apply drift-skill when testing the version-bump-drift guard for lint --changed mode.
---

Original body content. This baseline body is committed to the fixture repo before any drift is introduced by the individual test cases.
EOF
  git -C "$FIX" init -q
  git -C "$FIX" config user.email "t@example.com"
  git -C "$FIX" config user.name "t"
  # Neutralize inherited signing config (1Password/gpg) — a global
  # commit.gpgsign=true otherwise fails these commits non-interactively.
  git -C "$FIX" config commit.gpgsign false
  git -C "$FIX" config tag.gpgsign false
  git -C "$FIX" add -A
  git -C "$FIX" commit -qm base
  BASE="$(git -C "$FIX" rev-parse HEAD)"
}

@test "lint --changed: body changed without a version bump is a drift ERROR (exit 1)" {
  command -v git >/dev/null 2>&1 || skip "git not available"
  _mk_changed_fixture
  cat > "$SK" <<'EOF'
---
name: drift-skill
version: 1.0.0
description: Apply drift-skill when testing the version-bump-drift guard for lint --changed mode.
---

Rewritten body with substantial new material but deliberately NO version bump. This must trip the drift guard.
EOF
  run bash "$FIX/scripts/lint-skills.sh" --changed "$BASE"
  [ "$status" -eq 1 ]
  echo "$output" | grep -q "ERROR"
  echo "$output" | grep -qi "body changed"
  echo "$output" | grep -q "drift-skill"
}

@test "lint --changed: body changed WITH a version bump passes (exit 0)" {
  command -v git >/dev/null 2>&1 || skip "git not available"
  _mk_changed_fixture
  cat > "$SK" <<'EOF'
---
name: drift-skill
version: 1.1.0
description: Apply drift-skill when testing the version-bump-drift guard for lint --changed mode.
---

Rewritten body with substantial new material AND a version bump to 1.1.0. This must pass the drift guard.
EOF
  run bash "$FIX/scripts/lint-skills.sh" --changed "$BASE"
  [ "$status" -eq 0 ]
  echo "$output" | grep -qi "PASSED"
}

@test "lint --changed: frontmatter-only change (body identical) needs no bump (exit 0)" {
  command -v git >/dev/null 2>&1 || skip "git not available"
  _mk_changed_fixture
  # Edit ONLY the description; keep the body byte-identical; no version bump.
  cat > "$SK" <<'EOF'
---
name: drift-skill
version: 1.0.0
description: Apply drift-skill with an EDITED description only and an unchanged body for lint --changed mode.
---

Original body content. This baseline body is committed to the fixture repo before any drift is introduced by the individual test cases.
EOF
  run bash "$FIX/scripts/lint-skills.sh" --changed "$BASE"
  [ "$status" -eq 0 ]
  echo "$output" | grep -qi "PASSED"
}

@test "lint --changed: brand-new skill (absent in base) is skipped (exit 0)" {
  command -v git >/dev/null 2>&1 || skip "git not available"
  _mk_changed_fixture
  mkdir -p "$FIX/skills/meta/brand-new"
  cat > "$FIX/skills/meta/brand-new/SKILL.md" <<'EOF'
---
name: brand-new
version: 1.0.0
description: Apply brand-new when testing that a new skill is not treated as drift by lint --changed.
---

A brand-new skill file that did not exist in the base ref, so the drift guard has no prior version to compare and must skip it.
EOF
  run bash "$FIX/scripts/lint-skills.sh" --changed "$BASE"
  [ "$status" -eq 0 ]
  echo "$output" | grep -qi "PASSED"
}

@test "lint --changed: unresolvable base ref exits 2" {
  command -v git >/dev/null 2>&1 || skip "git not available"
  _mk_changed_fixture
  run bash "$FIX/scripts/lint-skills.sh" --changed no-such-ref-xyz
  [ "$status" -eq 2 ]
}
