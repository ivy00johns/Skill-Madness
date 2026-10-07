#!/usr/bin/env python3
"""
Capability resolver for Skill Madness (UA-02).

Resolves safe execution mode, missing prerequisites, and capability equivalence
for skills based on observed host/model capabilities and declared execution modes.
Preserves legacy requires_claude_code compatibility while allowing capability-driven
toolchain execution.
"""

from __future__ import annotations

import argparse
import json
import os
import re
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Tuple

# Canonical semantic capabilities
KNOWN_CAPABILITIES = {
    "read_files",
    "write_files",
    "run_shell",
    "web_fetch",
    "spawn_subagent",
    "parallel_subagents",
    "team_messaging",
    "shared_task_list",
    "schedule_recurring",
    "completion_gate",
    "ask_user_structured",
    "persistent_memory",
    "browser_automation",
    "artifact_publish",
    "lifecycle_hooks",
    "independent_evaluator",
    "budget_enforcement",
    "permission_scope",
    "workflow_graph",
}

# Default tool capability mapping for known target tools
DEFAULT_TOOL_CAPABILITIES: Dict[str, Set[str]] = {
    host: {"read_files", "write_files", "run_shell"}
    for host in ("claude-code", "cursor", "gemini-cli", "copilot", "antigravity", "opencode", "openclaw", "qwen", "kimi", "aider", "windsurf")
}


def parse_frontmatter(path: Path) -> Dict[str, Any]:
    """Parse required YAML fail-closed; never weaken malformed capability metadata."""
    import yaml
    content = path.read_text(encoding="utf-8")
    match = re.match(r"\A---\r?\n(.*?)\r?\n---(?:\r?\n|\Z)", content, re.DOTALL)
    if not match:
        raise ValueError("Missing delimited YAML frontmatter")
    parsed = yaml.safe_load(match.group(1))
    if not isinstance(parsed, dict):
        raise ValueError("Frontmatter must be a mapping")
    return parsed


def resolve_skill_execution(
    skill_frontmatter: Dict[str, Any],
    tool_or_host: str,
    observed_capabilities: Optional[Set[str]] = None,
    active_conditions: Optional[Set[str]] = None,
) -> Dict[str, Any]:
    """
    Resolve whether and how a skill can execute on a given tool/host.

    Returns:
      {
        "status": "ALLOWED" | "SKIPPED" | "REFUSED",
        "mode": str or None,
        "missing_capabilities": list[str],
        "reason": str,
        "quality": "equivalent" | "degraded-safe" | "unverified"
      }
    """
    # Tolerant YAML loading must not turn malformed safety fields into ALLOWED.
    if not isinstance(skill_frontmatter, dict):
        raise ValueError('Frontmatter must be a mapping')
    for key in ('requires_capabilities', 'optional_capabilities', 'refuse_if'):
        if key in skill_frontmatter and (not isinstance(skill_frontmatter[key], list)
                or any(not isinstance(v, str) or not v for v in skill_frontmatter[key])):
            raise ValueError(key + ' must be a list of nonempty strings')
    for key in ('requires_claude_code', 'requires_agent_teams'):
        if key in skill_frontmatter and type(skill_frontmatter[key]) is not bool:
            raise ValueError(key + ' must be boolean')
    modes = skill_frontmatter.get('execution_modes')
    if modes is not None:
        if not isinstance(modes, dict) or not modes:
            raise ValueError('execution_modes must be a nonempty mapping')
        for name, config in modes.items():
            if not isinstance(name, str) or not isinstance(config, dict):
                raise ValueError('invalid execution mode')
            requirements = config.get('requires', [])
            if not isinstance(requirements, list) or any(not isinstance(v, str) or not v for v in requirements):
                raise ValueError('mode requires must be a list of nonempty strings')
            if config.get('quality', 'unverified') not in ('equivalent', 'degraded-safe', 'unverified'):
                raise ValueError('invalid execution mode quality')
    inferred = observed_capabilities is None
    if observed_capabilities is None:
        observed_capabilities = set(DEFAULT_TOOL_CAPABILITIES.get(tool_or_host, set()))
    if active_conditions is None:
        active_conditions = set()

    # 1. Check refuse_if
    refuse_if = skill_frontmatter.get("refuse_if") or []
    for cond in refuse_if:
        if cond in active_conditions:
            return {
                "status": "REFUSED",
                "mode": None,
                "missing_capabilities": [],
                "reason": f"Active condition matched refuse_if: {cond}",
                "quality": "unverified",
            }

    # 2. Check requires_capabilities (base prerequisites)
    req_caps = set(skill_frontmatter.get("requires_capabilities") or [])
    missing_base = req_caps - observed_capabilities
    if missing_base:
        return {
            "status": "SKIPPED",
            "mode": None,
            "missing_capabilities": sorted(list(missing_base)),
            "reason": f"Missing required capabilities: {', '.join(sorted(missing_base))}",
            "quality": "unverified",
        }

    # 3. Check execution_modes if declared
    exec_modes = skill_frontmatter.get("execution_modes")
    if isinstance(exec_modes, dict) and exec_modes:
        # Check modes in priority order
        for mode_name, mode_cfg in exec_modes.items():
            if not isinstance(mode_cfg, dict):
                continue
            mode_reqs = set(mode_cfg.get("requires") or [])
            if mode_reqs.issubset(observed_capabilities):
                return {
                    "status": "ALLOWED",
                    "mode": mode_name,
                    "missing_capabilities": [],
                    "reason": f"Execution mode selected: {mode_name}",
                    "quality": "unverified" if inferred else mode_cfg.get("quality", "unverified"),
                }
        # If no execution mode matched requirements
        all_reqs = {r for m in exec_modes.values() if isinstance(m, dict) for r in (m.get("requires") or [])}
        missing_mode_caps = all_reqs - observed_capabilities
        return {
            "status": "SKIPPED",
            "mode": None,
            "missing_capabilities": sorted(list(missing_mode_caps)),
            "reason": "No declared execution mode satisfied by observed capabilities",
            "quality": "unverified",
        }

    # 4. Fallback to legacy requires_claude_code
    req_cc = skill_frontmatter.get("requires_claude_code")
    if req_cc is True and tool_or_host != "claude-code":
        return {
            "status": "SKIPPED",
            "mode": None,
            "missing_capabilities": ["claude_code_runtime"],
            "reason": "requires_claude_code: true",
            "quality": "unverified",
        }

    return {
        "status": "ALLOWED",
        "mode": "standard",
        "missing_capabilities": [],
        "reason": "All required capabilities satisfied",
        "quality": "unverified" if inferred else "equivalent",
    }


def main():
    parser = argparse.ArgumentParser(description="Skill Capability Resolver (UA-02)")
    parser.add_argument("--skill", required=True, help="Path to SKILL.md")
    parser.add_argument("--tool", required=True, help="Target tool or host (e.g. claude-code, cursor, gemini-cli)")
    parser.add_argument("--caps", help="Comma-separated observed capabilities (overrides tool default)")
    parser.add_argument("--conditions", help="Comma-separated active condition identifiers")
    parser.add_argument("--json", action="store_true", help="Output JSON result")
    args = parser.parse_args()

    skill_path = Path(args.skill)
    fm = parse_frontmatter(skill_path)

    caps = set(filter(None, args.caps.split(","))) if args.caps is not None else None
    conditions = set(args.conditions.split(",")) if args.conditions else None

    result = resolve_skill_execution(fm, args.tool, observed_capabilities=caps, active_conditions=conditions)

    if args.json:
        print(json.dumps(result, indent=2))
    else:
        print(f"Status: {result['status']}")
        if result["mode"]:
            print(f"Mode: {result['mode']} ({result['quality']})")
        if result["missing_capabilities"]:
            print(f"Missing: {', '.join(result['missing_capabilities'])}")
        print(f"Reason: {result['reason']}")

    if result["status"] == "ALLOWED":
        sys.exit(0)
    elif result["status"] == "SKIPPED":
        sys.exit(1)
    else:  # REFUSED
        sys.exit(2)


if __name__ == "__main__":
    main()
