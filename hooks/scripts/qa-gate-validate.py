#!/usr/bin/env python3
"""qa-gate-validate.py — Structural validator + gate-rule evaluator for QA reports.

Pure, unit-testable. Stdlib only (json) — no third-party jsonschema dependency.
Validates the required keys/types of skills/roles/qe-agent/references/qa-report-schema.json
structurally, then applies the orchestrator's gate rules.

Usage:
    qa-gate-validate.py <report.json>

Exit codes (per contracts/hooks/hooks-layer.md §3):
    0  allow   — report is conformant AND no gate rule fires
    1  block   — report is conformant but a gate rule fires (reason -> stdout)
    2  malformed / not-found — file missing or structurally non-conformant
                  (reason -> stdout)
"""
import json
import sys

ALLOW = 0
BLOCK = 1
MALFORMED = 2


def fail_malformed(reason):
    print(reason)
    sys.exit(MALFORMED)


def is_int(v):
    # bool is a subclass of int in Python; exclude it for integer fields.
    return isinstance(v, int) and not isinstance(v, bool)


def require_keys(obj, keys, where):
    if not isinstance(obj, dict):
        fail_malformed("report malformed: %s is not an object" % where)
    for k in keys:
        if k not in obj:
            fail_malformed("report malformed: missing key '%s' in %s" % (k, where))


def check_score_entry(obj, where):
    require_keys(obj, ["score", "notes"], where)
    if not is_int(obj["score"]):
        fail_malformed("report malformed: %s.score must be an integer" % where)
    if not (1 <= obj["score"] <= 5):
        fail_malformed("report malformed: %s.score out of range 1..5" % where)
    if not isinstance(obj["notes"], str):
        fail_malformed("report malformed: %s.notes must be a string" % where)


def check_test_counts(obj, where):
    require_keys(obj, ["pass", "fail", "skip"], where)
    for k in ("pass", "fail", "skip"):
        if not is_int(obj[k]) or obj[k] < 0:
            fail_malformed("report malformed: %s.%s must be a non-negative integer" % (where, k))


def main():
    if len(sys.argv) != 2:
        fail_malformed("report malformed: usage qa-gate-validate.py <report.json>")

    path = sys.argv[1]
    try:
        with open(path) as f:
            text = f.read()
    except OSError:
        fail_malformed("report not found: %s" % path)

    try:
        data = json.loads(text)
    except ValueError as e:
        fail_malformed("report malformed: invalid JSON (%s)" % e)

    if not isinstance(data, dict):
        fail_malformed("report malformed: top-level value is not an object")

    # --- Top-level required keys (subset enforced per contract §3) ---
    require_keys(
        data,
        [
            "schema_version", "status", "scores", "test_results",
            "blockers", "issues", "recommendations", "gate_decision",
        ],
        "report",
    )

    if data["schema_version"] != "1.0.0":
        fail_malformed(
            "report malformed: schema_version must be '1.0.0' (got %r)"
            % data["schema_version"]
        )

    if data["status"] not in ("PASS", "FAIL", "PARTIAL", "BLOCKED"):
        fail_malformed("report malformed: status %r not in enum" % data["status"])

    # --- scores ---
    scores = data["scores"]
    require_keys(
        scores,
        ["correctness", "completeness", "code_quality", "security", "contract_conformance"],
        "scores",
    )
    for k in ("correctness", "completeness", "code_quality", "security", "contract_conformance"):
        check_score_entry(scores[k], "scores.%s" % k)

    # --- test_results ---
    tr = data["test_results"]
    require_keys(tr, ["unit", "integration", "e2e", "contract", "security_scan"], "test_results")
    for k in ("unit", "integration", "e2e", "contract", "security_scan"):
        check_test_counts(tr[k], "test_results.%s" % k)

    # --- blockers / issues / recommendations must be arrays ---
    for k in ("blockers", "issues", "recommendations"):
        if not isinstance(data[k], list):
            fail_malformed("report malformed: %s must be an array" % k)

    # --- gate_decision ---
    gd = data["gate_decision"]
    require_keys(gd, ["proceed", "reason"], "gate_decision")
    if not isinstance(gd["proceed"], bool):
        fail_malformed("report malformed: gate_decision.proceed must be a boolean")
    if not isinstance(gd["reason"], str):
        fail_malformed("report malformed: gate_decision.reason must be a string")

    # Blockers: each must at least carry a 'severity' string to evaluate the rule.
    for i, b in enumerate(data["blockers"]):
        if not isinstance(b, dict):
            fail_malformed("report malformed: blockers[%d] is not an object" % i)
        if "severity" not in b or not isinstance(b["severity"], str):
            fail_malformed("report malformed: blockers[%d] missing string 'severity'" % i)

    # --- Gate rules (contract §3 step 4) ---
    reasons = []
    if gd["proceed"] is False:
        reasons.append("gate_decision.proceed is false")

    crit = [b for b in data["blockers"] if b.get("severity") == "CRITICAL"]
    if crit:
        ids = ", ".join(str(b.get("id", "?")) for b in crit)
        reasons.append("CRITICAL blocker(s) present: %s" % ids)

    cc = scores["contract_conformance"]["score"]
    if cc < 3:
        reasons.append("contract_conformance score %d < 3" % cc)

    sec = scores["security"]["score"]
    if sec < 3:
        reasons.append("security score %d < 3" % sec)

    if reasons:
        print("; ".join(reasons))
        sys.exit(BLOCK)

    sys.exit(ALLOW)


if __name__ == "__main__":
    main()
