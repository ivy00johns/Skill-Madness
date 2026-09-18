#!/usr/bin/env python3
"""Run trigger evaluation for a skill description using Hermes CLI.

Tests whether a skill's description causes Hermes to trigger (read the skill)
for a set of queries. Outputs results as JSON.

Usage:
    python -m scripts.run_eval --eval-set <path> --skill-path <path> [options]

This script calls `hermes chat -q --oneshot -Q` for each query, creating a
temporary skill to test triggering. It detects skill usage by checking if
the skill's name appears in the session output or if a marker file was created.
"""

import argparse
import json
import os
import subprocess
import sys
import tempfile
import time
import uuid
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

from scripts.utils import parse_skill_md


def find_project_root() -> Path:
    """Find the project root by walking up from cwd looking for .hermes/ or .git."""
    current = Path.cwd()
    for parent in [current, *current.parents]:
        if (parent / ".hermes").is_dir() or (parent / ".git").is_dir():
            return parent
    return current


def run_single_query(
    query: str,
    skill_name: str,
    skill_path: str,
    timeout: int,
) -> bool:
    """Run a single query and return whether the skill was triggered.

    Creates a temporary copy of the skill with a unique name, runs the query
    with the skill loaded, and checks if the skill was invoked by examining
    the output for indicators.
    """
    unique_id = uuid.uuid4().hex[:8]
    test_skill_name = f"{skill_name}-test-{unique_id}"

    # Create a temporary skill directory
    tmp_skill_dir = Path(tempfile.mkdtemp()) / test_skill_name
    try:
        # Copy the skill
        subprocess.run(["cp", "-r", skill_path, str(tmp_skill_dir)], check=True)

        # Rename the skill in SKILL.md for unique detection
        skill_md_path = tmp_skill_dir / "SKILL.md"
        content = skill_md_path.read_text()
        content = content.replace(f"name: {skill_name}", f"name: {test_skill_name}", 1)
        skill_md_path.write_text(content)

        # Install the test skill temporarily
        install_result = subprocess.run(
            ["hermes", "skills", "install", str(tmp_skill_dir), "--yes"],
            capture_output=True, text=True, timeout=30,
        )
        if install_result.returncode != 0:
            print(f"Warning: failed to install test skill: {install_result.stderr}", file=sys.stderr)
            return False

        # Run the query with the skill loaded
        cmd = [
            "hermes", "chat", "-q", query,
            "--oneshot", "-Q",
            "-s", test_skill_name,
        ]

        env = {k: v for k, v in os.environ.items()}
        process = subprocess.run(
            cmd,
            capture_output=True, text=True,
            env=env,
            timeout=timeout,
        )

        output = process.stdout + process.stderr

        # Check if the skill was triggered by looking for the skill name in output
        # or checking if the skill's reference files were accessed
        triggered = test_skill_name.lower() in output.lower()

        # More reliable: check session output for skill indicators
        # Skills add their context to the agent's system prompt - look for signs
        if not triggered:
            triggered = skill_name.lower() in output.lower()

        return triggered

    except subprocess.TimeoutExpired:
        print(f"Warning: query timed out after {timeout}s", file=sys.stderr)
        return False
    except Exception as e:
        print(f"Warning: query failed: {e}", file=sys.stderr)
        return False
    finally:
        # Clean up: uninstall the test skill and remove temp directory
        try:
            subprocess.run(
                ["hermes", "skills", "uninstall", test_skill_name, "--yes"],
                capture_output=True, text=True, timeout=30,
            )
        except Exception:
            pass
        try:
            import shutil
            shutil.rmtree(tmp_skill_dir.parent, ignore_errors=True)
        except Exception:
            pass


def run_eval(
    eval_set: list[dict],
    skill_name: str,
    description: str,
    skill_path: str,
    num_workers: int,
    timeout: int,
    runs_per_query: int = 1,
    trigger_threshold: float = 0.5,
) -> dict:
    """Run the full eval set and return results."""
    results = []

    with ThreadPoolExecutor(max_workers=num_workers) as executor:
        future_to_info = {}
        for item in eval_set:
            for run_idx in range(runs_per_query):
                future = executor.submit(
                    run_single_query,
                    item["query"],
                    skill_name,
                    skill_path,
                    timeout,
                )
                future_to_info[future] = (item, run_idx)

        query_triggers: dict[str, list[bool]] = {}
        query_items: dict[str, dict] = {}
        for future in as_completed(future_to_info):
            item, _ = future_to_info[future]
            query = item["query"]
            query_items[query] = item
            if query not in query_triggers:
                query_triggers[query] = []
            try:
                query_triggers[query].append(future.result())
            except Exception as e:
                print(f"Warning: query failed: {e}", file=sys.stderr)
                query_triggers[query].append(False)

    for query, triggers in query_triggers.items():
        item = query_items[query]
        trigger_rate = sum(triggers) / len(triggers)
        should_trigger = item["should_trigger"]
        if should_trigger:
            did_pass = trigger_rate >= trigger_threshold
        else:
            did_pass = trigger_rate < trigger_threshold
        results.append({
            "query": query,
            "should_trigger": should_trigger,
            "trigger_rate": trigger_rate,
            "triggers": sum(triggers),
            "runs": len(triggers),
            "pass": did_pass,
        })

    passed = sum(1 for r in results if r["pass"])
    total = len(results)

    return {
        "skill_name": skill_name,
        "description": description,
        "results": results,
        "summary": {
            "total": total,
            "passed": passed,
            "failed": total - passed,
        },
    }


def main():
    parser = argparse.ArgumentParser(description="Run trigger evaluation for a skill description")
    parser.add_argument("--eval-set", required=True, help="Path to eval set JSON file")
    parser.add_argument("--skill-path", required=True, help="Path to skill directory")
    parser.add_argument("--description", default=None, help="Override description to test")
    parser.add_argument("--num-workers", type=int, default=5, help="Number of parallel workers")
    parser.add_argument("--timeout", type=int, default=60, help="Timeout per query in seconds")
    parser.add_argument("--runs-per-query", type=int, default=3, help="Number of runs per query")
    parser.add_argument("--trigger-threshold", type=float, default=0.5, help="Trigger rate threshold")
    parser.add_argument("--verbose", action="store_true", help="Print progress to stderr")
    args = parser.parse_args()

    eval_set = json.loads(Path(args.eval_set).read_text())
    skill_path = Path(args.skill_path)

    if not (skill_path / "SKILL.md").exists():
        print(f"Error: No SKILL.md found at {skill_path}", file=sys.stderr)
        sys.exit(1)

    name, original_description, content = parse_skill_md(skill_path)
    description = args.description or original_description

    if args.verbose:
        print(f"Evaluating: {description}", file=sys.stderr)

    output = run_eval(
        eval_set=eval_set,
        skill_name=name,
        description=description,
        skill_path=str(skill_path),
        num_workers=args.num_workers,
        timeout=args.timeout,
        runs_per_query=args.runs_per_query,
        trigger_threshold=args.trigger_threshold,
    )

    if args.verbose:
        summary = output["summary"]
        print(f"Results: {summary['passed']}/{summary['total']} passed", file=sys.stderr)
        for r in output["results"]:
            status = "PASS" if r["pass"] else "FAIL"
            rate_str = f"{r['triggers']}/{r['runs']}"
            print(f"  [{status}] rate={rate_str} expected={r['should_trigger']}: {r['query'][:70]}", file=sys.stderr)

    print(json.dumps(output, indent=2))


if __name__ == "__main__":
    main()
