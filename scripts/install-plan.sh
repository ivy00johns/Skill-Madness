#!/usr/bin/env bash
#
# install-plan.sh — Pure resolution of an install into a serializable JSON plan.
#
# Resolves selected tools x profile-selected skills into a list of file
# operations, reading destinations from the install-locations matrix. Computes
# each operation's action (create|overwrite|skip) by comparing the source
# content hash to any existing destination file. NO WRITES are performed.
#
# Usage:
#   scripts/install-plan.sh --tool NAME[,NAME...] [--profile NAME] \
#                           [--root DIR] [--integrations DIR] [--out FILE]
#
# Options:
#   --tool NAME       Tool(s) to plan for. Comma-separated or repeatable. Required.
#   --profile NAME    Named profile from manifests/profiles.json (default: full).
#   --root DIR        Override ~ (HOME) and $PWD bases for destinations
#                     (default: $HOME). Tests pass a temp dir here.
#   --integrations DIR  Source integrations dir (default: <repo>/integrations).
#   --out FILE        Write the plan JSON here (default: stdout).
#   --help            Show this help and exit.
#
# Emits: { schema_version, generated_at, profile, tools,
#          operations:[ {tool, source, dest, action, sha256} ] }
#
# Exit codes: 0 success, 2 argument/resolution error.

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
LIB_DIR="$SCRIPT_DIR/lib"
REPO_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"

# shellcheck source=scripts/lib/term.sh
. "$LIB_DIR/term.sh"
# shellcheck source=scripts/lib/install-state.sh
. "$LIB_DIR/install-state.sh"

PROFILES_JSON="$REPO_ROOT/manifests/profiles.json"
SKILLS_ROOT="$REPO_ROOT/skills"
SCHEMA_VERSION=1

ALL_TOOLS="claude-code copilot antigravity gemini-cli opencode cursor openclaw qwen kimi aider windsurf"

usage() {
  sed -n '3,30p' "${BASH_SOURCE[0]}" | sed 's/^# \{0,1\}//'
  exit 0
}

main() {
  local tools_csv=""
  local profile="full"
  local root="${HOME:-/tmp}"
  local integrations="$REPO_ROOT/integrations"
  local out=""

  while [[ $# -gt 0 ]]; do
    case "$1" in
      --tool)         tools_csv="${tools_csv:+$tools_csv,}${2:?'--tool requires a value'}"; shift 2 ;;
      --profile)      profile="${2:?'--profile requires a value'}"; shift 2 ;;
      --root)         root="${2:?'--root requires a value'}"; shift 2 ;;
      --integrations) integrations="${2:?'--integrations requires a value'}"; shift 2 ;;
      --out)          out="${2:?'--out requires a value'}"; shift 2 ;;
      --help|-h)      usage ;;
      *)              ats_err "Unknown option: $1"; exit 2 ;;
    esac
  done

  if [[ -z "$tools_csv" ]]; then
    ats_err "--tool is required"
    exit 2
  fi
  if [[ ! -d "$integrations" ]]; then
    ats_err "integrations dir not found: $integrations (run scripts/convert.sh first)"
    exit 2
  fi

  # Resolve profile categories (space-separated).
  local cats
  if ! cats="$(profile_categories "$profile" "$PROFILES_JSON")"; then
    ats_err "Unknown profile: $profile"
    exit 2
  fi
  cats="$(printf '%s' "$cats" | tr '\n' ' ')"

  # Normalize tool list, validate, dedupe (preserve order).
  local tools="" t valid
  local IFS_OLD="$IFS"; IFS=','
  # shellcheck disable=SC2086
  set -- $tools_csv
  IFS="$IFS_OLD"
  for t in "$@"; do
    [[ -z "$t" ]] && continue
    valid=0
    for v in $ALL_TOOLS; do [[ "$v" == "$t" ]] && valid=1 && break; done
    if [[ "$valid" -eq 0 ]]; then ats_err "Unknown tool: $t"; exit 2; fi
    case " $tools " in *" $t "*) : ;; *) tools="${tools:+$tools }$t" ;; esac
  done

  # Build category->1 membership lookup file for the python resolver.
  # Pass everything to python which enumerates sources + computes hashes/actions.
  local generated_at
  generated_at="$(date -u +%Y-%m-%dT%H:%M:%SZ)"

  # Pre-compute the canonical slug->category table once (TSV) for python.
  _ats_build_slug_cat "$SKILLS_ROOT"
  local slugcat_tmp; slugcat_tmp="$(mktemp "${TMPDIR:-/tmp}/ats-slugcat.XXXXXX")"
  printf '%s\n' "$_ATS_SLUG_CAT" > "$slugcat_tmp"

  # Detect hash tool once and export the resolved command name for python.
  _ats_detect_hash

  local plan_json rc=0
  plan_json="$(
    ATS_INTEG="$integrations" \
    ATS_ROOT="$root" \
    ATS_CATS="$cats" \
    ATS_TOOLS="$tools" \
    ATS_PROFILE="$profile" \
    ATS_GENERATED_AT="$generated_at" \
    ATS_SCHEMA="$SCHEMA_VERSION" \
    ATS_SLUGCAT="$slugcat_tmp" \
    ATS_HASH_CMD="$_ATS_HASH_CMD" \
    python3 - <<'PYEOF'
import hashlib, json, os, sys

integ   = os.environ["ATS_INTEG"]
root    = os.environ["ATS_ROOT"]
cats    = set(os.environ["ATS_CATS"].split())
tools   = os.environ["ATS_TOOLS"].split()
profile = os.environ["ATS_PROFILE"]
gen_at  = os.environ["ATS_GENERATED_AT"]
schema  = int(os.environ["ATS_SCHEMA"])
slugcat_path = os.environ["ATS_SLUGCAT"]

# Canonical slug -> category map.
slug_cat = {}
with open(slugcat_path) as f:
    for line in f:
        line = line.rstrip("\n")
        if not line:
            continue
        parts = line.split("\t")
        if len(parts) == 2:
            slug_cat[parts[0]] = parts[1]

def sha256(path):
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        for chunk in iter(lambda: fh.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()

# Per-tool source root subdir (matches resolve_dest expectations).
SRC_SUBDIR = {
    "opencode": "agents",
    "qwen": "agents",
    "gemini-cli": "skills",
    "cursor": "rules",
}

def dests_for(tool, relpath):
    """Return the list of destination paths for a source file. Most tools map
    to a single dest; copilot mirrors into BOTH ~/.github/agents/ and
    ~/.copilot/agents/ (install-locations.md:17 + install.sh install_copilot)."""
    if tool == "claude-code":
        return [os.path.join(root, ".claude", "skills", relpath)]
    if tool == "copilot":
        return [os.path.join(root, ".github", "agents", relpath),
                os.path.join(root, ".copilot", "agents", relpath)]
    if tool == "antigravity":
        return [os.path.join(root, ".gemini", "antigravity", "skills", relpath)]
    if tool == "gemini-cli":
        return [os.path.join(root, ".gemini", "extensions", "alltheskills", relpath)]
    if tool == "opencode":
        return [os.path.join(root, ".opencode", "agents", relpath)]
    if tool == "cursor":
        return [os.path.join(root, ".cursor", "rules", relpath)]
    if tool == "openclaw":
        return [os.path.join(root, ".openclaw", "alltheskills", relpath)]
    if tool == "qwen":
        return [os.path.join(root, ".qwen", "agents", relpath)]
    if tool == "kimi":
        return [os.path.join(root, ".config", "kimi", "agents", relpath)]
    if tool == "aider":
        return [os.path.join(root, "CONVENTIONS.md")]
    if tool == "windsurf":
        return [os.path.join(root, ".windsurfrules")]
    return []

def slug_of(tool, src_root, abspath):
    """Derive the canonical skill slug for a source file, for category filtering."""
    rel = os.path.relpath(abspath, src_root)
    parts = rel.split(os.sep)
    if tool in ("claude-code", "gemini-cli"):
        # <category>/<slug>/... (claude-code) or <slug>/... (gemini-cli skills/)
        if tool == "claude-code":
            return parts[1] if len(parts) >= 2 else None
        return parts[0] if parts else None
    if tool == "antigravity" or tool == "openclaw" or tool == "kimi":
        # <slug>/...
        return parts[0] if parts else None
    if tool in ("copilot", "opencode", "qwen", "cursor"):
        # flat: <slug>.<ext> or <slug>-references/...
        base = parts[0]
        if base.endswith("-references"):
            return base[: -len("-references")]
        return os.path.splitext(base)[0]
    return None

operations = []
# Tools whose convert.sh output is absent. Warn loudly per tool (naming the
# path that was missing); if EVERY requested tool is missing, exit non-zero so
# a silent empty plan can never masquerade as success (SR23).
missing_sources = []
for tool in tools:
    tool_root = os.path.join(integ, tool)
    sub = SRC_SUBDIR.get(tool)
    src_root = os.path.join(tool_root, sub) if sub else tool_root
    if not os.path.isdir(src_root):
        # Single-file tools (aider/windsurf) live as files under tool_root.
        if tool == "aider":
            f = os.path.join(tool_root, "CONVENTIONS.md")
            src_root = tool_root
            if os.path.isfile(f):
                files = [f]
            else:
                sys.stderr.write(
                    "[plan] WARN missing source for tool '%s': %s "
                    "(run scripts/convert.sh --tool %s)\n" % (tool, f, tool))
                missing_sources.append(tool)
                continue
        elif tool == "windsurf":
            f = os.path.join(tool_root, ".windsurfrules")
            src_root = tool_root
            if os.path.isfile(f):
                files = [f]
            else:
                sys.stderr.write(
                    "[plan] WARN missing source for tool '%s': %s "
                    "(run scripts/convert.sh --tool %s)\n" % (tool, f, tool))
                missing_sources.append(tool)
                continue
        else:
            sys.stderr.write(
                "[plan] WARN missing source for tool '%s': %s "
                "(run scripts/convert.sh --tool %s)\n" % (tool, src_root, tool))
            missing_sources.append(tool)
            continue
    else:
        files = []
        for dirpath, _dirs, fnames in os.walk(src_root):
            for fn in fnames:
                files.append(os.path.join(dirpath, fn))
    files.sort()

    for src in files:
        # Category filter (per-skill tools). aider/windsurf are whole-repo
        # consolidated files: include iff the profile selects any category that
        # exists on disk (i.e. non-empty profile) — they cannot be subset.
        if tool in ("aider", "windsurf"):
            if not cats:
                continue
        else:
            slug = slug_of(tool, src_root, src)
            cat = slug_cat.get(slug)
            if cat is None or cat not in cats:
                continue
        rel = os.path.relpath(src, src_root)
        dests = dests_for(tool, rel)
        if not dests:
            continue
        digest = sha256(src)
        for dest in dests:
            if os.path.isfile(dest):
                action = "skip" if sha256(dest) == digest else "overwrite"
            else:
                action = "create"
            operations.append({
                "tool": tool,
                "source": src,
                "dest": dest,
                "action": action,
                "sha256": digest,
            })

# Every requested tool lacked a source → refuse to emit an empty plan (SR23).
if missing_sources and len(missing_sources) == len(tools):
    sys.stderr.write(
        "[plan] ERROR all requested tools have missing sources: %s\n"
        % " ".join(missing_sources))
    sys.exit(3)

operations.sort(key=lambda o: (o["tool"], o["dest"]))
plan = {
    "schema_version": schema,
    "generated_at": gen_at,
    "profile": profile,
    "tools": tools,
    "operations": operations,
}
print(json.dumps(plan, indent=2))
PYEOF
  )" || rc=$?
  rm -f "$slugcat_tmp"
  if [[ "$rc" -eq 3 ]]; then
    ats_err "no installable sources for any requested tool (see warnings above); run scripts/convert.sh"
    exit 2
  elif [[ "$rc" -ne 0 ]]; then
    ats_err "plan resolution failed"
    exit 2
  fi

  if [[ -n "$out" ]]; then
    mkdir -p "$(dirname "$out")"
    printf '%s\n' "$plan_json" > "$out"
    ats_ok "Wrote plan: $out"
  else
    printf '%s\n' "$plan_json"
  fi
}

main "$@"
