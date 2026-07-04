#!/usr/bin/env bats
# 07-install-hooks-wire.bats — scripts/install.sh OPT-IN settings.json wiring (SR3).
#
# The skill-usage PostToolUse emitter is inert until its hook is merged into
# ~/.claude/settings.json. install.sh must:
#   - default to NO-CHANGE (print the merge snippet, never touch settings.json)
#   - with --wire-hooks: merge non-destructively, back the file up first, and be
#     idempotent (never duplicate a hook already present)
#   - refuse to touch a settings.json that is not valid JSON
#
# SAFETY: every test points HOME at a throwaway temp dir. The real
# ~/.claude/settings.json is NEVER read or written. Modelled on 06-install-dry-run.
#
# Uses setup_file so the fake repo (scripts + libs + fixture skills + the real
# hooks/ tree + pre-built integrations incl. hooks.json) is built once.

setup_file() {
  export REPO_ROOT
  REPO_ROOT="$(cd "$(dirname "$BATS_TEST_FILENAME")/../../.." && pwd)"
  local SCRIPTS_DIR="$REPO_ROOT/scripts"
  local FIXTURE_SKILLS="$REPO_ROOT/tests/installer/fixtures/skills"

  export FAKEREPO
  FAKEREPO="$(mktemp -d /tmp/ats-hookrepo.XXXXXX)"
  mkdir -p "$FAKEREPO/scripts/lib"
  cp "$SCRIPTS_DIR/convert.sh"         "$FAKEREPO/scripts/convert.sh"
  cp "$SCRIPTS_DIR/install.sh"         "$FAKEREPO/scripts/install.sh"
  cp "$SCRIPTS_DIR/lib/frontmatter.sh" "$FAKEREPO/scripts/lib/frontmatter.sh"
  cp "$SCRIPTS_DIR/lib/slug.sh"        "$FAKEREPO/scripts/lib/slug.sh"
  cp "$SCRIPTS_DIR/lib/term.sh"        "$FAKEREPO/scripts/lib/term.sh"
  cp "$SCRIPTS_DIR/lib/platform.sh"    "$FAKEREPO/scripts/lib/platform.sh"
  cp -r "$FIXTURE_SKILLS"              "$FAKEREPO/skills"
  # The real hooks/ tree so convert emits integrations/claude-code/hooks.json.
  cp -r "$REPO_ROOT/hooks"             "$FAKEREPO/hooks"

  export INTEG_DIR
  INTEG_DIR="$(mktemp -d /tmp/ats-hookinteg.XXXXXX)"
  bash "$FAKEREPO/scripts/convert.sh" --tool claude-code --out "$INTEG_DIR" 2>/dev/null
  ln -sf "$INTEG_DIR" "$FAKEREPO/integrations"

  export INSTALL
  INSTALL="$FAKEREPO/scripts/install.sh"
}

teardown_file() {
  rm -rf "$FAKEREPO" "$INTEG_DIR"
}

setup() {
  export FAKE_HOME
  FAKE_HOME="$(mktemp -d /tmp/ats-hookhome.XXXXXX)"
  export HOME="$FAKE_HOME"
  export WORKDIR
  WORKDIR="$(mktemp -d /tmp/ats-hookwork.XXXXXX)"
}

teardown() {
  rm -rf "$FAKE_HOME" "$WORKDIR"
}

SETTINGS() { printf '%s/.claude/settings.json' "$FAKE_HOME"; }

# ---------------------------------------------------------------------------
# Sanity: the fixture actually produced a hooks.json (else the tests are vacuous)
# ---------------------------------------------------------------------------

@test "fixture: convert emitted integrations/claude-code/hooks.json" {
  [ -f "$INTEG_DIR/claude-code/hooks.json" ]
  run python3 -c "import json,sys; d=json.load(open('$INTEG_DIR/claude-code/hooks.json')); assert 'PostToolUse' in d['hooks']"
  [ "$status" -eq 0 ]
}

# ---------------------------------------------------------------------------
# Default: no --wire-hooks → NO-CHANGE (snippet only, settings untouched)
# ---------------------------------------------------------------------------

@test "install claude-code (no flag): prints merge snippet, does NOT touch settings.json" {
  cd "$WORKDIR" && run bash "$INSTALL" --tool claude-code --no-interactive
  [ "$status" -eq 0 ]
  echo "$output" | grep -qi "NOT auto-merged"
  [ ! -f "$(SETTINGS)" ]
}

@test "install claude-code (no flag): leaves a pre-existing settings.json byte-identical" {
  mkdir -p "$FAKE_HOME/.claude"
  printf '{ "theme": "dark" }\n' > "$(SETTINGS)"
  local before; before="$(shasum -a 256 "$(SETTINGS)" | awk '{print $1}')"
  cd "$WORKDIR" && run bash "$INSTALL" --tool claude-code --no-interactive
  [ "$status" -eq 0 ]
  local after; after="$(shasum -a 256 "$(SETTINGS)" | awk '{print $1}')"
  [ "$before" = "$after" ]
}

# ---------------------------------------------------------------------------
# --wire-hooks: opt-in merge
# ---------------------------------------------------------------------------

@test "install --wire-hooks (no settings yet): creates settings.json wiring the skill-usage emitter" {
  cd "$WORKDIR" && run bash "$INSTALL" --tool claude-code --no-interactive --wire-hooks
  [ "$status" -eq 0 ]
  [ -f "$(SETTINGS)" ]
  run python3 -c "
import json
s=json.load(open('$(SETTINGS)'))
post=[h['command'] for e in s['hooks'].get('PostToolUse',[]) for h in e['hooks']]
assert any('skill-usage' in c for c in post), post
"
  [ "$status" -eq 0 ]
}

@test "install --wire-hooks: preserves existing settings + user hooks, and backs up first" {
  mkdir -p "$FAKE_HOME/.claude"
  printf '{\n  "theme": "dark",\n  "hooks": { "PreToolUse": [ { "hooks": [ {"type":"command","command":"my-own-hook"} ] } ] }\n}\n' > "$(SETTINGS)"
  cd "$WORKDIR" && run bash "$INSTALL" --tool claude-code --no-interactive --wire-hooks
  [ "$status" -eq 0 ]
  # A timestamped backup of the original was written.
  run bash -c "ls '$FAKE_HOME/.claude/'settings.json.bak-* 2>/dev/null | wc -l | tr -d ' '"
  [ "$output" != "0" ]
  run python3 -c "
import json
s=json.load(open('$(SETTINGS)'))
assert s['theme']=='dark', 'lost user key'
pre=[h['command'] for e in s['hooks']['PreToolUse'] for h in e['hooks']]
assert 'my-own-hook' in pre, 'lost user hook'
post=[h['command'] for e in s['hooks'].get('PostToolUse',[]) for h in e['hooks']]
assert any('skill-usage' in c for c in post), post
"
  [ "$status" -eq 0 ]
}

@test "install --wire-hooks twice: idempotent, no duplicate hook entries" {
  cd "$WORKDIR" && bash "$INSTALL" --tool claude-code --no-interactive --wire-hooks >/dev/null 2>&1
  local before; before="$(python3 -c "import json;s=json.load(open('$(SETTINGS)'));print(sum(len(e['hooks']) for v in s['hooks'].values() for e in v))")"
  cd "$WORKDIR" && run bash "$INSTALL" --tool claude-code --no-interactive --wire-hooks
  [ "$status" -eq 0 ]
  echo "$output" | grep -qi "already wired"
  local after; after="$(python3 -c "import json;s=json.load(open('$(SETTINGS)'));print(sum(len(e['hooks']) for v in s['hooks'].values() for e in v))")"
  [ "$before" = "$after" ]
}

@test "install --wire-hooks: refuses to touch a malformed settings.json and leaves it intact" {
  mkdir -p "$FAKE_HOME/.claude"
  printf '{ this is not valid json ,,, \n' > "$(SETTINGS)"
  local before; before="$(shasum -a 256 "$(SETTINGS)" | awk '{print $1}')"
  cd "$WORKDIR" && run bash "$INSTALL" --tool claude-code --no-interactive --wire-hooks
  # install reports the wiring failure (non-zero overall), but never corrupts the file.
  [ "$status" -ne 0 ]
  echo "$output" | grep -qi "not valid json\|could not safely merge"
  local after; after="$(shasum -a 256 "$(SETTINGS)" | awk '{print $1}')"
  [ "$before" = "$after" ]
}

# ---------------------------------------------------------------------------
# Dry-run: previews the wiring, writes nothing
# ---------------------------------------------------------------------------

@test "install --dry-run --wire-hooks: previews the merge and writes no settings.json" {
  cd "$WORKDIR" && run bash "$INSTALL" --tool claude-code --dry-run --no-interactive --wire-hooks
  [ "$status" -eq 0 ]
  echo "$output" | grep -qi "would merge hooks.json"
  [ ! -f "$(SETTINGS)" ]
}
