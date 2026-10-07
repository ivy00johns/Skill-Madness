#!/usr/bin/env python3
"""Unforced Hermes trigger evaluation. No stdout mentions or arbitrary logs count.

Requires the Hermes stream-json protocol (system/init, tool_use/tool_result,
terminal result). Live calls require separately approved credentials and budget.
"""
import argparse
from concurrent.futures import ThreadPoolExecutor
import hashlib
import json
import os
from pathlib import Path
import shutil
import sqlite3
import subprocess
import sys
import tempfile

from scripts.utils import parse_skill_md, update_skill_description


def error_result(message: str, status: str = "error") -> dict:
    return {"triggered": None, "status": status, "error_message": message}


def observe_trace(raw: str, skill_name: str, model: str, state_db: Path | None = None) -> dict:
    """Only correlated successful skill_view(name=exact-name) establishes retrieval."""
    try:
        events = [json.loads(line) for line in raw.splitlines() if line.strip()]
        if not events or any(not isinstance(e, dict) for e in events):
            raise ValueError("Trace is empty or malformed")
        initial = [e for e in events if e.get("type") == "system" and e.get("subtype") == "init"]
        final = [e for e in events if e.get("type") == "result"]
        if len(initial) != 1 or len(final) != 1 or events[-1] != final[0]:
            raise ValueError("Trace must have one init and one terminal result")
        if initial[0].get("model") != model:
            raise ValueError("Worker model changed or was not observed")
        if any(e.get('type') == 'error' for e in events):
            raise ValueError('Worker emitted an execution error')
        if type(final[0].get("exit_code")) is not int or final[0]['exit_code'] != 0 or final[0].get("error"):
            raise ValueError("Worker reported execution failure")
        pending = {}
        evidence = []
        for event in events:
            if event.get("type") == "tool_use":
                key = event.get("tool_call_id") or event.get("name")
                if key in pending:
                    raise ValueError("Ambiguous uncorrelated tool calls")
                pending[key] = event
            elif event.get("type") == "tool_result":
                key = event.get("tool_call_id") or event.get("name")
                call = pending.pop(key, None)
                if not call or call.get("name") != event.get("name"):
                    raise ValueError("Uncorrelated tool result")
                if call.get("name") != "skill_view" or call.get("input", {}).get("name") != skill_name:
                    continue
                if event.get("is_error"):
                    raise ValueError("Candidate retrieval failed")
                output = event.get("output")
                if isinstance(output, str):
                    # Hermes caps output at 5000 characters. Fail closed rather
                    # than guess success from a truncated response.
                    try:
                        output = json.loads(output)
                    except ValueError:
                        call_id = event.get('tool_call_id')
                        session_id = final[0].get('session_id')
                        if not state_db or not state_db.is_file() or not call_id or not session_id:
                            raise ValueError('Truncated retrieval lacks exact-session proof')
                        with sqlite3.connect(state_db.resolve().as_uri() + '?mode=ro', uri=True) as db:
                            records = db.execute('SELECT content FROM messages WHERE session_id=? AND role=? AND tool_call_id=? AND tool_name=?', (session_id, 'tool', call_id, 'skill_view')).fetchall()
                        if len(records) != 1:
                            raise ValueError('Missing/ambiguous exact-session tool result')
                        output = json.loads(records[0][0])
                if not isinstance(output, dict) or output.get("success") is not True or output.get("name") != skill_name:
                    raise ValueError("Candidate retrieval success is unverified")
                evidence.append({"tool": "skill_view", "name": skill_name, "tool_call_id": key})
        if pending:
            raise ValueError("Trace has unfinished tool calls")
        return {"triggered": bool(evidence), "status": "success", "error_message": None,
                "model": model, "retrieval_evidence": evidence,
                "trace_sha256": hashlib.sha256(raw.encode()).hexdigest()}
    except (ValueError, TypeError, KeyError, AttributeError, OSError, sqlite3.Error) as exc:
        return error_result(str(exc))


def run_single_query(query: str, skill_name: str, skill_path: str,
                     candidate_description: str, timeout: int, model: str) -> dict:
    if not model or timeout <= 0:
        return error_result("A pinned worker model and positive timeout are required")
    try:
        with tempfile.TemporaryDirectory(prefix="hermes-eval-") as temporary:
            root = Path(temporary)
            home, work = root / "home", root / "work"
            home.mkdir()
            work.mkdir()
            hermes_home = home / ".hermes"
            candidate = hermes_home / "skills" / skill_name
            shutil.copytree(skill_path, candidate)
            md = candidate / "SKILL.md"
            md.write_text(update_skill_description(md.read_text(), candidate_description), encoding="utf-8")
            actual_name, actual_description, _ = parse_skill_md(candidate)
            if actual_name != skill_name or actual_description != candidate_description.strip():
                raise ValueError("Candidate snapshot mismatch")
            # No real-HOME install/uninstall, config copy or automatic skill seed.
            (hermes_home / ".no-bundled-skills").write_text("isolated trigger evaluation\n")
            env = dict(os.environ, HOME=str(home), USERPROFILE=str(home),
                       HERMES_HOME=str(hermes_home), XDG_CONFIG_HOME=str(home / ".config"),
                       XDG_CACHE_HOME=str(home / ".cache"), PYTHONDONTWRITEBYTECODE="1")
            for key in ("HERMES_PROFILE", "HERMES_CONFIG", "HERMES_ENV", "HERMES_YOLO_MODE"):
                env.pop(key, None)
            cmd = ["hermes", "chat", "--query-file", "-", "--oneshot", "-Q",
                   "--format", "stream-json", "--in", str(work), "-m", model,
                   "--ignore-user-config", "--ignore-rules", "--max-turns", "3",
                   "--run-budget", str(timeout), "-t", "skills"]
            process = subprocess.run(cmd, input=query, cwd=work, env=env,
                                     capture_output=True, text=True, timeout=timeout)
            if process.returncode:
                return error_result(f"Hermes exited {process.returncode}; no trigger score")
            result = observe_trace(process.stdout, skill_name, model, hermes_home / 'state.db')
            result["candidate_sha256"] = hashlib.sha256(md.read_bytes()).hexdigest()
            return result
    except subprocess.TimeoutExpired:
        return error_result("Worker timeout", "timeout")
    except (OSError, ValueError, subprocess.SubprocessError) as exc:
        return error_result(str(exc))


def validate_eval_set(eval_set: list[dict]) -> None:
    if not isinstance(eval_set, list) or not eval_set:
        raise ValueError("Eval set must be a nonempty list")
    seen = set()
    for item in eval_set:
        if not isinstance(item, dict) or not isinstance(item.get("query"), str) or not item["query"].strip() or type(item.get("should_trigger")) is not bool:
            raise ValueError("Each eval item requires query and boolean should_trigger")
        query = " ".join(item["query"].casefold().split())
        if query in seen:
            raise ValueError("Duplicate query would distort scores/splits")
        seen.add(query)


def run_eval(eval_set: list[dict], skill_name: str, description: str, skill_path: str,
             num_workers: int, timeout: int, runs_per_query: int = 1,
             trigger_threshold: float = 0.5, model: str | None = None) -> dict:
    validate_eval_set(eval_set)
    if not model or num_workers < 1 or timeout <= 0 or runs_per_query < 1 or not 0 < trigger_threshold <= 1:
        raise ValueError("Require pinned model, positive worker/run/time limits and threshold in (0,1]")
    def worker(pair):
        item, _ = pair
        return run_single_query(item["query"], skill_name, skill_path, description, timeout, model)
    pairs = [(item, trial) for item in eval_set for trial in range(runs_per_query)]
    with ThreadPoolExecutor(max_workers=num_workers) as pool:
        observations = list(pool.map(worker, pairs))
    results = []
    for index, item in enumerate(eval_set):
        outcomes = observations[index * runs_per_query:(index + 1) * runs_per_query]
        valid = [o for o in outcomes if o["status"] == "success"]
        errors = len(outcomes) - len(valid)
        triggers = sum(o["triggered"] is True for o in valid)
        rate = triggers / len(valid) if valid else None
        passed = None if errors else ((rate >= trigger_threshold) == item["should_trigger"])
        results.append(dict(item, trigger_rate=rate, triggers=triggers, runs=len(outcomes),
                            valid_runs=len(valid), errors=errors, pass_=passed,
                            status="error" if errors else "success", observations=outcomes))
        results[-1]["pass"] = results[-1].pop("pass_")
    summary = {"total": len(results), "passed": sum(r["pass"] is True for r in results),
               "failed": sum(r["pass"] is False for r in results),
               "errored": sum(r["pass"] is None for r in results)}
    return {"skill_name": skill_name, "description": description, "model": model,
            "results": results, "summary": summary}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--eval-set", required=True)
    parser.add_argument("--skill-path", required=True)
    parser.add_argument("--description")
    parser.add_argument("--model", required=True)
    parser.add_argument("--num-workers", type=int, default=1)
    parser.add_argument("--timeout", type=int, default=60)
    parser.add_argument("--runs-per-query", type=int, default=3)
    parser.add_argument("--trigger-threshold", type=float, default=0.5)
    parser.add_argument("--verbose", action="store_true")
    args = parser.parse_args()
    name, original, _ = parse_skill_md(Path(args.skill_path))
    output = run_eval(json.loads(Path(args.eval_set).read_text()), name,
                      args.description if args.description is not None else original,
                      args.skill_path, args.num_workers, args.timeout, args.runs_per_query,
                      args.trigger_threshold, args.model)
    print(json.dumps(output, indent=2))
    return 2 if output["summary"]["errored"] else 0


if __name__ == "__main__":
    sys.exit(main())
