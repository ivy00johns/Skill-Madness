#!/usr/bin/env bash
#
# skill-health.sh — Deterministic skill-health telemetry engine for Skill Madness.
#
# Contract: contracts/installer/skill-health.md v1.0.0 (P2-C).
#
# The scoring math lives HERE, in code — never in a prompt. This is the explicit
# ECC continuous-learning anti-pattern this build refuses to repeat. The engine
# turns whatever coarse events exist (see the telemetry schema) into per-skill
# health metrics and detects version drift. No network, no LLM, no eval.
#
# Honest scope note: Claude Code does not emit a clean "skill X invoked →
# outcome Y" event, so the *emitter* (hooks/scripts/skill-usage.sh) is
# necessarily coarse/best-effort. The value here is (1) a documented JSONL event
# schema, (2) this deterministic computation engine, and (3) version-drift
# detection (which needs no runtime signal — it compares the recorded version of
# a skill's most-recent event against the skill's current SKILL.md frontmatter).
#
# Telemetry event schema (JSONL, one object per line):
#   {"ts":"ISO8601","skill":"orchestrator","version":"1.9.0",
#    "outcome":"success|failure|unknown","session_id":"string",
#    "source":"hook|manual"}
#
# Usage:
#   scripts/skill-health.sh report [--log FILE] [--json] [--days N]
#   scripts/skill-health.sh record --skill NAME --outcome OUT [--log FILE] [--session ID]
#   scripts/skill-health.sh drift  [--log FILE]
#   scripts/skill-health.sh --help
#
# Default log: $ATS_TELEMETRY_LOG or ~/.claude/ats-telemetry/skill-events.jsonl
#
# Exit codes: 0 ok (including no-data), 2 argument failure.
#
# Bash 3.2 portable: no associative arrays, no mapfile. python3 stdlib only.

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
LIB_DIR="$SCRIPT_DIR/lib"
REPO_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
SKILLS_ROOT="$REPO_ROOT/skills"

# shellcheck source=scripts/lib/term.sh
. "$LIB_DIR/term.sh"
# shellcheck source=scripts/lib/frontmatter.sh
. "$LIB_DIR/frontmatter.sh"

# ---------------------------------------------------------------------------
# Tunable constants (named, not magic numbers buried in code)
# ---------------------------------------------------------------------------
# A skill is flagged `declining` when its recent (7d) success rate has dropped
# more than DECLINING_THRESHOLD below its 30d success rate.
DECLINING_THRESHOLD="0.15"
RECENT_WINDOW_DAYS=7
TREND_WINDOW_DAYS=30

# ---------------------------------------------------------------------------
# Default log location
# ---------------------------------------------------------------------------
default_log() {
  printf '%s' "${ATS_TELEMETRY_LOG:-$HOME/.claude/ats-telemetry/skill-events.jsonl}"
}

# ---------------------------------------------------------------------------
# CLI state
# ---------------------------------------------------------------------------
LOG_FILE=""
AS_JSON=false
DAYS_OVERRIDE=""
REC_SKILL=""
REC_OUTCOME=""
REC_SESSION=""
REC_SOURCE="manual"

# ---------------------------------------------------------------------------
# current_version <skill-name>
# Resolve a skill's current frontmatter `version` by locating its SKILL.md under
# skills/ (excluding archive/ and in-progress/, per catalog.sh's definition).
# Prints the version string, or empty if the skill / version is not found.
# ---------------------------------------------------------------------------
current_version() {
  local skill="$1" f
  [[ -d "$SKILLS_ROOT" ]] || return 0
  while IFS= read -r f; do
    [[ -z "$f" ]] && continue
    if [[ "$(basename "$(dirname "$f")")" == "$skill" ]]; then
      get_field version "$f"
      return 0
    fi
  done < <(find "$SKILLS_ROOT" -name SKILL.md -type f 2>/dev/null \
             | grep -v "$SKILLS_ROOT/archive/" \
             | grep -v "$SKILLS_ROOT/in-progress/")
  return 0
}

# ---------------------------------------------------------------------------
# record — append one schema-valid JSONL event.
# Creates the log dir if missing. Outcome normalized to success|failure|unknown.
# ts is generated here in UTC ISO8601; source defaults to "manual".
# ---------------------------------------------------------------------------
cmd_record() {
  local log="$1" skill="$2" outcome="$3" session="$4" source="${5:-manual}"
  if [[ -z "$skill" ]]; then
    ats_err "record: --skill is required"
    exit 2
  fi
  case "$outcome" in
    success|failure|unknown) : ;;
    "") ats_err "record: --outcome is required (success|failure|unknown)"; exit 2 ;;
    *)  ats_err "record: invalid --outcome '$outcome' (success|failure|unknown)"; exit 2 ;;
  esac

  local ver
  ver="$(current_version "$skill")"

  local dir
  dir="$(dirname "$log")"
  mkdir -p "$dir" 2>/dev/null || true

  # Build the JSON line with python3 so values are properly escaped.
  python3 - "$skill" "$ver" "$outcome" "$session" "$source" <<'PYEOF' >> "$log"
import json, sys
from datetime import datetime, timezone
skill, ver, outcome, session, source = sys.argv[1:6]
obj = {
    "ts": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
    "skill": skill,
    "version": ver,
    "outcome": outcome,
    "session_id": session,
    "source": source,
}
sys.stdout.write(json.dumps(obj) + "\n")
PYEOF

  ats_ok "recorded $outcome for skill '$skill'${ver:+ (v$ver)}"
}

# ---------------------------------------------------------------------------
# compute_metrics <log> <recent_days> <trend_days> <threshold> <json|text>
#
# The deterministic engine. Reads the JSONL log, groups events by skill, and
# computes per skill: total, 7d/30d success rates, declining flag, last-seen,
# and the latest recorded version. All math is done in this one python3 block —
# windows are derived from each event's `ts` vs now (epoch seconds).
#
# It prints, one per line: skill<TAB>total<TAB>rate7<TAB>rate30<TAB>declining<TAB>lastseen<TAB>recorded_version
# (rates as "n/a" when the window has zero invocations). The shell layer then
# joins in the current frontmatter version for drift and renders text or JSON.
# ---------------------------------------------------------------------------
compute_metrics() {
  local log="$1" recent="$2" trend="$3" threshold="$4"
  python3 - "$log" "$recent" "$trend" "$threshold" <<'PYEOF'
import json, sys, os
from datetime import datetime, timezone

log, recent_days, trend_days, threshold = sys.argv[1], int(sys.argv[2]), int(sys.argv[3]), float(sys.argv[4])
now = datetime.now(timezone.utc).timestamp()
recent_cut = now - recent_days * 86400
trend_cut = now - trend_days * 86400

def parse_ts(ts):
    if not ts:
        return None
    s = ts.strip()
    # Normalize trailing Z to +00:00 for fromisoformat.
    if s.endswith("Z"):
        s = s[:-1] + "+00:00"
    try:
        dt = datetime.fromisoformat(s)
    except Exception:
        return None
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt.timestamp()

# order preserves first-seen for stable output
order = []
skills = {}

if os.path.exists(log):
    with open(log) as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                ev = json.loads(line)
            except Exception:
                continue  # skip malformed lines, never crash
            name = ev.get("skill")
            if not name:
                continue
            epoch = parse_ts(ev.get("ts"))
            if epoch is None:
                continue
            outcome = ev.get("outcome", "unknown")
            version = ev.get("version") or ""
            if name not in skills:
                order.append(name)
                skills[name] = {
                    "total": 0,
                    "r7_ok": 0, "r7_n": 0,
                    "r30_ok": 0, "r30_n": 0,
                    "last": None, "last_version": "",
                }
            s = skills[name]
            s["total"] += 1
            # Only success/failure events count toward a success RATE; unknown is
            # counted in total but excluded from the denominator (no signal).
            graded = outcome in ("success", "failure")
            ok = 1 if outcome == "success" else 0
            if epoch >= trend_cut and graded:
                s["r30_n"] += 1
                s["r30_ok"] += ok
            if epoch >= recent_cut and graded:
                s["r7_n"] += 1
                s["r7_ok"] += ok
            if s["last"] is None or epoch >= s["last"]:
                s["last"] = epoch
                s["last_version"] = version

def fmt_rate(ok, n):
    if n == 0:
        return "n/a"
    return "%.2f" % (ok / n)

for name in order:
    s = skills[name]
    r7 = fmt_rate(s["r7_ok"], s["r7_n"])
    r30 = fmt_rate(s["r30_ok"], s["r30_n"])
    declining = "false"
    if s["r7_n"] > 0 and s["r30_n"] > 0:
        rate7 = s["r7_ok"] / s["r7_n"]
        rate30 = s["r30_ok"] / s["r30_n"]
        if rate7 + threshold < rate30:
            declining = "true"
    last_iso = ""
    if s["last"] is not None:
        last_iso = datetime.fromtimestamp(s["last"], timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    print("\t".join([name, str(s["total"]), r7, r30, declining, last_iso, s["last_version"]]))
PYEOF
}

# ---------------------------------------------------------------------------
# report — render per-skill metrics. Joins compute_metrics output with current
# frontmatter version for drift. Skills with no events → no-data (never error).
# ---------------------------------------------------------------------------
cmd_report() {
  local log="$1"
  local recent="$RECENT_WINDOW_DAYS" trend="$TREND_WINDOW_DAYS"
  if [[ -n "$DAYS_OVERRIDE" ]]; then
    recent="$DAYS_OVERRIDE"
  fi

  # Gather metric rows (may be empty if log absent/empty → all no-data).
  local rows
  rows="$(compute_metrics "$log" "$recent" "$trend" "$DECLINING_THRESHOLD")"

  if $AS_JSON; then
    report_json "$rows" "$recent" "$trend"
  else
    report_text "$rows" "$log" "$recent" "$trend"
  fi
}

# drift_for <recorded_version> <skill> — echo stale|ok|no-data
drift_for() {
  local recorded="$1" skill="$2" cur
  if [[ -z "$recorded" ]]; then
    echo "no-data"; return 0
  fi
  cur="$(current_version "$skill")"
  if [[ -z "$cur" ]]; then
    echo "no-data"; return 0
  fi
  if [[ "$recorded" == "$cur" ]]; then
    echo "ok"
  else
    echo "stale"
  fi
}

report_text() {
  local rows="$1" log="$2" recent="$3" trend="$4"
  ats_header "Skill health (deterministic; log: $log)"
  if [[ -z "$rows" ]]; then
    ats_info "no events recorded — every skill is no-data"
    ats_warn "telemetry inactive — emitter hook not wired into ~/.claude/settings.json"
    ats_dim  "  Wire it (opt-in): scripts/install.sh --tool claude-code --wire-hooks"
    printf '  %-22s %s\n' "STATUS" "no-data (empty/absent log)"
    return 0
  fi
  printf '  %-22s %5s %6s %6s %9s %-7s %s\n' \
    "SKILL" "TOT" "${recent}d" "${trend}d" "DECLINING" "DRIFT" "LAST-SEEN"
  printf '  %-22s %5s %6s %6s %9s %-7s %s\n' \
    "----------------------" "-----" "------" "------" "---------" "-------" "---------"
  local name total r7 r30 declining lastseen recver drift
  while IFS=$'\t' read -r name total r7 r30 declining lastseen recver; do
    [[ -z "$name" ]] && continue
    drift="$(drift_for "$recver" "$name")"
    printf '  %-22s %5s %6s %6s %9s %-7s %s\n' \
      "$name" "$total" "$r7" "$r30" "$declining" "$drift" "${lastseen:-n/a}"
  done <<EOF
$rows
EOF
}

report_json() {
  local rows="$1" recent="$2" trend="$3"
  # Re-derive drift in shell, then hand python3 a TSV with drift appended so the
  # JSON is assembled with correct escaping in one place.
  local enriched="" name total r7 r30 declining lastseen recver drift cur
  if [[ -n "$rows" ]]; then
    while IFS=$'\t' read -r name total r7 r30 declining lastseen recver; do
      [[ -z "$name" ]] && continue
      drift="$(drift_for "$recver" "$name")"
      cur="$(current_version "$name")"
      enriched+="${name}	${total}	${r7}	${r30}	${declining}	${lastseen}	${recver}	${cur}	${drift}"$'\n'
    done <<EOF
$rows
EOF
  fi
  ATS_SH_ROWS="$enriched" python3 - "$recent" "$trend" "$DECLINING_THRESHOLD" <<'PYEOF'
import json, os, sys
recent, trend, threshold = int(sys.argv[1]), int(sys.argv[2]), float(sys.argv[3])
skills = []
for line in os.environ.get("ATS_SH_ROWS", "").split("\n"):
    line = line.rstrip("\n")
    if not line:
        continue
    parts = line.split("\t")
    if len(parts) < 9:
        continue
    name, total, r7, r30, declining, lastseen, recver, cur, drift = parts[:9]
    skills.append({
        "skill": name,
        "total": int(total),
        "rate_7d": None if r7 == "n/a" else float(r7),
        "rate_30d": None if r30 == "n/a" else float(r30),
        "declining": declining == "true",
        "last_seen": lastseen or None,
        "recorded_version": recver or None,
        "current_version": cur or None,
        "version_drift": drift,
    })
out = {
    "schema": "ats-skill-health/1.0.0",
    "recent_window_days": recent,
    "trend_window_days": trend,
    "declining_threshold": threshold,
    "skill_count": len(skills),
    "skills": skills,
}
print(json.dumps(out, indent=2))
PYEOF
}

# ---------------------------------------------------------------------------
# drift — version drift only. Works with an empty/absent log: every skill with
# no recorded event version → no-data (reported, never errored).
# ---------------------------------------------------------------------------
cmd_drift() {
  local log="$1"
  # Use a wide trend window so we consider every event for the latest-version
  # determination; rates are irrelevant for drift.
  local rows
  rows="$(compute_metrics "$log" "$RECENT_WINDOW_DAYS" 36500 "$DECLINING_THRESHOLD")"

  if $AS_JSON; then
    drift_json "$rows"
    return 0
  fi

  ats_header "Skill version drift (recorded vs current SKILL.md; log: $log)"
  if [[ -z "$rows" ]]; then
    ats_info "no recorded versions — every skill is no-data"
    printf '  %-22s %s\n' "STATUS" "no-data (empty/absent log)"
    return 0
  fi
  printf '  %-22s %-10s %-10s %s\n' "SKILL" "RECORDED" "CURRENT" "DRIFT"
  printf '  %-22s %-10s %-10s %s\n' "----------------------" "----------" "----------" "-----"
  local name total r7 r30 declining lastseen recver cur drift
  while IFS=$'\t' read -r name total r7 r30 declining lastseen recver; do
    [[ -z "$name" ]] && continue
    cur="$(current_version "$name")"
    drift="$(drift_for "$recver" "$name")"
    printf '  %-22s %-10s %-10s %s\n' \
      "$name" "${recver:-n/a}" "${cur:-n/a}" "$drift"
  done <<EOF
$rows
EOF
}

drift_json() {
  local rows="$1" enriched="" name total r7 r30 declining lastseen recver cur drift
  if [[ -n "$rows" ]]; then
    while IFS=$'\t' read -r name total r7 r30 declining lastseen recver; do
      [[ -z "$name" ]] && continue
      cur="$(current_version "$name")"
      drift="$(drift_for "$recver" "$name")"
      enriched+="${name}	${recver}	${cur}	${drift}"$'\n'
    done <<EOF
$rows
EOF
  fi
  ATS_SH_ROWS="$enriched" python3 - <<'PYEOF'
import json, os, sys
skills = []
for line in os.environ.get("ATS_SH_ROWS", "").split("\n"):
    line = line.rstrip("\n")
    if not line:
        continue
    parts = line.split("\t")
    if len(parts) < 4:
        continue
    name, recver, cur, drift = parts[:4]
    skills.append({
        "skill": name,
        "recorded_version": recver or None,
        "current_version": cur or None,
        "version_drift": drift,
    })
print(json.dumps({
    "schema": "ats-skill-health-drift/1.0.0",
    "skill_count": len(skills),
    "skills": skills,
}, indent=2))
PYEOF
}

# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------
usage() {
  sed -n '3,33p' "${BASH_SOURCE[0]}" | sed 's/^# \{0,1\}//'
  exit 0
}

main() {
  [[ $# -eq 0 ]] && usage
  local cmd="$1"; shift || true

  case "$cmd" in
    --help|-h) usage ;;
  esac

  while [[ $# -gt 0 ]]; do
    case "$1" in
      --log)     LOG_FILE="${2:-}"; shift 2 ;;
      --json)    AS_JSON=true; shift ;;
      --days)    DAYS_OVERRIDE="${2:-}"; shift 2 ;;
      --skill)   REC_SKILL="${2:-}"; shift 2 ;;
      --outcome) REC_OUTCOME="${2:-}"; shift 2 ;;
      --session) REC_SESSION="${2:-}"; shift 2 ;;
      --source)  REC_SOURCE="${2:-}"; shift 2 ;;
      --help|-h) usage ;;
      -*) ats_err "Unknown option: $1"; exit 2 ;;
      *)  ats_err "Unexpected argument: $1"; exit 2 ;;
    esac
  done

  [[ -z "$LOG_FILE" ]] && LOG_FILE="$(default_log)"

  case "$cmd" in
    report) cmd_report "$LOG_FILE" ;;
    record) cmd_record "$LOG_FILE" "$REC_SKILL" "$REC_OUTCOME" "$REC_SESSION" "${REC_SOURCE:-manual}" ;;
    drift)  cmd_drift  "$LOG_FILE" ;;
    *) ats_err "Unknown command: $cmd (expected report|record|drift|--help)"; exit 2 ;;
  esac
}

main "$@"
