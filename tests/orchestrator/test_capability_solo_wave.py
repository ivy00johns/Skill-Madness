import os
import sys
from pathlib import Path
import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(REPO_ROOT / "scripts" / "lib"))

from capability_resolver import (
    parse_frontmatter,
    resolve_skill_execution,
    DEFAULT_TOOL_CAPABILITIES,
)


def test_capability_resolver_legacy_claude_code():
    fm_cc = {"name": "test-cc", "version": "1.0.0", "requires_claude_code": True}
    res_cc = resolve_skill_execution(fm_cc, "claude-code")
    assert res_cc["status"] == "ALLOWED"

    res_cursor = resolve_skill_execution(fm_cc, "cursor")
    assert res_cursor["status"] == "SKIPPED"
    assert "claude_code_runtime" in res_cursor["missing_capabilities"]


def test_capability_resolver_explicit_capabilities():
    fm = {
        "name": "test-skill",
        "version": "1.0.0",
        "requires_capabilities": ["read_files", "write_files", "run_shell"],
    }
    # claude-code has read/write/shell
    res = resolve_skill_execution(fm, "claude-code")
    assert res["status"] == "ALLOWED"

    # simulate limited host
    res_limited = resolve_skill_execution(
        fm, "custom-host", observed_capabilities={"read_files"}
    )
    assert res_limited["status"] == "SKIPPED"
    assert "write_files" in res_limited["missing_capabilities"]
    assert "run_shell" in res_limited["missing_capabilities"]


def test_capability_resolver_refuse_if():
    fm = {
        "name": "dangerous-skill",
        "version": "1.0.0",
        "refuse_if": ["unattended_without_budget_enforcement"],
    }
    res_ok = resolve_skill_execution(fm, "claude-code", active_conditions=set())
    assert res_ok["status"] == "ALLOWED"

    res_refused = resolve_skill_execution(
        fm,
        "claude-code",
        active_conditions={"unattended_without_budget_enforcement"},
    )
    assert res_refused["status"] == "REFUSED"
    assert "refuse_if" in res_refused["reason"]


def test_capability_resolver_execution_modes_ladder():
    fm = {
        "name": "mode-skill",
        "version": "1.0.0",
        "execution_modes": {
            "parallel": {
                "requires": ["parallel_subagents", "independent_evaluator"],
                "quality": "equivalent",
            },
            "attended-sequential": {
                "requires": ["ask_user_structured"],
                "quality": "degraded-safe",
            },
        },
    }

    # Host with parallel_subagents and independent_evaluator
    res_parallel = resolve_skill_execution(
        fm,
        "custom",
        observed_capabilities={"parallel_subagents", "independent_evaluator"},
    )
    assert res_parallel["status"] == "ALLOWED"
    assert res_parallel["mode"] == "parallel"
    assert res_parallel["quality"] == "equivalent"

    # Host with only ask_user_structured
    res_seq = resolve_skill_execution(
        fm, "custom", observed_capabilities={"ask_user_structured"}
    )
    assert res_seq["status"] == "ALLOWED"
    assert res_seq["mode"] == "attended-sequential"
    assert res_seq["quality"] == "degraded-safe"

    # Host with neither
    res_none = resolve_skill_execution(
        fm, "custom", observed_capabilities={"read_files"}
    )
    assert res_none["status"] == "SKIPPED"
    assert res_none["mode"] is None


@pytest.mark.parametrize('metadata', [
    {'requires_capabilities': 'read_files'}, {'refuse_if': 'unattended'},
    {'requires_claude_code': 'false'}, {'execution_modes': []},
    {'execution_modes': {'solo': {'requires': 'write_files'}}},
    {'execution_modes': {'solo': {'quality': 'certified'}}},
])
def test_malformed_capability_metadata_never_allows(metadata):
    with pytest.raises(ValueError):
        resolve_skill_execution(metadata, 'cursor')


def test_sequential_execution_reference_and_schema():
    # Verify sequential-execution.md doc exists and is readable
    seq_doc = REPO_ROOT / "skills" / "orchestrator" / "references" / "sequential-execution.md"
    assert seq_doc.is_file()
    content = seq_doc.read_text(encoding="utf-8")
    assert "DISCOVER" in content
    assert "CONTRACTS_FROZEN" in content
    assert "INDEPENDENT_QE" in content
    assert "Role Packets" in content

    # Verify loop-controller wrapper reinforcement
    loop_skill = REPO_ROOT / "skills" / "loops" / "loop-controller" / "SKILL.md"
    loop_text = loop_skill.read_text(encoding="utf-8")
    assert "process wrapper" in loop_text
    assert "SIGTERM" in loop_text

    # Verify migration-checklist verifier freezing & grep distinction
    mig_doc = REPO_ROOT / "skills" / "loops" / "migration-loop" / "references" / "migration-checklist.md"
    mig_text = mig_doc.read_text(encoding="utf-8")
    assert "Distinguish grep errors from zero matches" in mig_text
    assert "Freeze verifier, config, and test assertions" in mig_text

    # Verify contract-author v1.6.0
    ca_doc = REPO_ROOT / "skills" / "contracts" / "contract-author" / "SKILL.md"
    ca_text = ca_doc.read_text(encoding="utf-8")
    assert "version: 1.6.0" in ca_text
    assert "skip contracts" not in ca_text
