#!/usr/bin/env python3
"""qa-gate-validate.py — Structural validator + gate-rule evaluator for QA reports.

Stdlib only — no third-party jsonschema dependency. Legacy structural checks
are pure; strict checks additionally read Git and current file contents.
Validates the required keys/types of skills/roles/qe-agent/references/qa-report-schema.json
structurally, then applies the orchestrator's gate rules.

Usage:
    qa-gate-validate.py <report.json> [--strict]
    qa-gate-validate.py <report.json> --snapshot --run-id <active-run-id>

Exit codes (per contracts/hooks/hooks-layer.md §3):
    0  allow   — report is conformant AND no gate rule fires
    1  block   — report is conformant but a gate rule fires (reason -> stdout)
    2  malformed / not-found — file missing or structurally non-conformant
                  (reason -> stdout)
"""
import argparse
import hashlib
import json
import os
from pathlib import Path
import subprocess
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


def content_digest(root, paths):
    """Bind relative names, modes and bytes; refuse ambiguous linked boundaries."""
    digest = hashlib.sha256()
    for relative in sorted(set(paths)):
        path = root / relative
        if not path.parent.resolve().is_relative_to(root):
            raise ValueError("snapshot path escapes project through a symlink: %s" % relative)
        name = os.fsencode(relative)
        digest.update(len(name).to_bytes(8, "big") + name)
        if not path.exists() and not path.is_symlink():
            digest.update(b"missing\0")
            continue
        mode = path.lstat().st_mode
        digest.update(str(mode).encode() + b"\0")
        if path.is_symlink():
            raise ValueError("symlink requires a separate evidence boundary: %s" % relative)
        elif path.is_file():
            content = path.read_bytes()
        else:
            # A submodule or special file requires its own evidence boundary.
            raise ValueError("unsupported snapshot entry: %s" % relative)
        digest.update(len(content).to_bytes(8, "big") + content)
    return digest.hexdigest()


def snapshot_binding(root, contracts, run_id, report=None):
    """Read-only working-tree binding; ignored files and QA outputs are excluded."""
    if not run_id or not run_id.strip():
        raise ValueError("strict QA requires an active run ID")
    root = Path(root).resolve()

    def git(*args):
        return subprocess.check_output(["git", "-C", str(root), *args], stderr=subprocess.DEVNULL, timeout=10)

    if Path(os.fsdecode(git("rev-parse", "--show-toplevel")).strip()).resolve() != root:
        raise ValueError("QA project root must be the Git worktree root")
    revision = git("rev-parse", "HEAD").decode().strip()
    paths = [os.fsdecode(p) for p in git("ls-files", "--cached", "--others", "--exclude-standard", "-z").split(b"\0") if p]
    excluded = {
        "qa-report.json", "qa-report.md", "coordination/qa-report.json",
        "coordination/qa-report.md", ".claude/qa-report.json", ".claude/qa-report.md",
    }
    if report:
        report_path = Path(report).resolve()
        if report_path.is_relative_to(root):
            relative = report_path.relative_to(root)
            excluded.add(str(relative))
            excluded.add(str(relative.with_suffix(".md")))
    paths = [p for p in paths if p not in excluded]
    contracts = Path(contracts).resolve() if contracts else root / "contracts"
    if not contracts.is_relative_to(root):
        raise ValueError("QA contracts must be within the project root")
    contract_prefix = str(contracts.relative_to(root))
    contract_paths = [p for p in paths if p == contract_prefix or p.startswith(contract_prefix + "/")]
    return {
        "run_id": run_id,
        "revision": revision,
        "source_sha256": content_digest(root, paths),
        "contract_sha256": content_digest(root, contract_paths),
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("report", nargs="?")
    parser.add_argument("--strict", action="store_true")
    parser.add_argument("--snapshot", action="store_true", help="print current proof_binding JSON without validating")
    parser.add_argument("--root", default=os.environ.get("CLAUDE_PROJECT_DIR", os.getcwd()))
    parser.add_argument("--contracts", default=os.environ.get("ATS_QA_CONTRACTS"))
    parser.add_argument("--run-id", default=os.environ.get("ATS_QA_RUN_ID", ""))
    args = parser.parse_args()
    if args.snapshot:
        try:
            print(json.dumps(snapshot_binding(args.root, args.contracts, args.run_id, args.report), sort_keys=True))
        except (OSError, ValueError, subprocess.SubprocessError) as exc:
            fail_malformed("QA snapshot unavailable: %s" % exc)
        return
    if not args.report:
        fail_malformed("report malformed: usage qa-gate-validate.py <report.json>")
    path = args.report
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

    # Strict certification is tied to current bytes, not only a commit ID.
    if args.strict:
        try:
            expected = snapshot_binding(args.root, args.contracts, args.run_id, path)
        except (OSError, ValueError, subprocess.SubprocessError) as exc:
            fail_malformed("QA proof unavailable: %s" % exc)
        binding = data.get("proof_binding")
        require_keys(binding, list(expected), "proof_binding")
        if data.get("build_session_id") != expected["run_id"]:
            fail_malformed("QA proof stale: build_session_id does not match the active run")
        for key, value in expected.items():
            if binding[key] != value:
                fail_malformed("QA proof stale: proof_binding.%s does not match current context" % key)

    # --- Gate rules (contract §3 step 4) ---
    reasons = []
    if data["status"] in ("FAIL", "BLOCKED"):
        reasons.append("report status is %s" % data["status"])
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
