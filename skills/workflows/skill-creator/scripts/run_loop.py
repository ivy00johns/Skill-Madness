#!/usr/bin/env python3
"""Description optimization: train feedback, dev selection, one final held-out check."""
import argparse
import hashlib
import json
from pathlib import Path
import sys

from scripts.generate_report import generate_html
from scripts.improve_description import improve_description
from scripts.run_eval import add_host_arguments, host_config_from_args, run_eval, validate_eval_set
from scripts.utils import parse_skill_md


def item_split_hash(query_str: str) -> float:
    key = " ".join(query_str.casefold().split())
    return int.from_bytes(hashlib.sha256(key.encode()).digest()[:8], "big") / 2**64


def split_eval_set_hygiene(eval_set: list[dict], holdout: float, dev_ratio: float = 0.5):
    validate_eval_set(eval_set)
    if not 0 <= holdout < 1 or not 0 < dev_ratio < 1:
        raise ValueError("holdout must be in [0,1); dev_ratio in (0,1)")
    splits = {"train": [], "dev": [], "test": []}
    for item in eval_set:
        provenance = item.get("provenance", "synthetic")
        if provenance not in ("real", "synthetic", "generated"):
            raise ValueError("provenance must be real, synthetic or generated")
        h = item_split_hash(item["query"])
        bucket = "train" if provenance != "real" or holdout == 0 else (
            "test" if h < holdout else "dev" if h < holdout + (1 - holdout) * dev_ratio else "train")
        splits[bucket].append(item)
    # Never move items to fill an empty bucket: that violates per-item stability.
    return splits["train"], splits["dev"], splits["test"]


def claim_holdout(test_set: list[dict], state_dir: Path, description: str) -> Path:
    """Atomically burn each query before dispatch; failed/crashed runs still consume it.

    Query-keyed claims also reject reuse across changed corpus order, labels, model,
    seed, ratio or subset. Use the same state directory across runs.
    """
    state_dir.mkdir(parents=True, exist_ok=True)
    keys = sorted(hashlib.sha256(" ".join(i["query"].casefold().split()).encode()).hexdigest() for i in test_set)
    for key in keys:
        if (state_dir / (key + ".json")).exists():
            raise ValueError("Held-out query already consumed; carve fresh real tasks")
    receipt = {"description_sha256": hashlib.sha256(description.encode()).hexdigest(), "status": "consumed-before-dispatch"}
    for key in keys:
        with (state_dir / (key + ".json")).open("x", encoding="utf-8") as out:
            json.dump(receipt, out)
    return state_dir


def freeze_splits(train: list[dict], dev: list[dict], test: list[dict], state_dir: Path) -> None:
    """Persist query assignments so changed ratios/provenance cannot leak test to train."""
    directory = state_dir / 'splits'
    directory.mkdir(parents=True, exist_ok=True)
    for label, items in (('train', train), ('dev', dev), ('test', test)):
        for item in items:
            key = hashlib.sha256(' '.join(item['query'].casefold().split()).encode()).hexdigest()
            path = directory / (key + '.json')
            record = {'split': label, 'should_trigger': item['should_trigger'], 'provenance': item.get('provenance', 'synthetic')}
            try:
                with path.open('x') as out:
                    json.dump(record, out)
            except FileExistsError:
                if json.loads(path.read_text()) != record:
                    raise ValueError('Frozen split/provenance changed; use fresh real tasks, not a new seed or ratio')


def run_loop(eval_set: list[dict], skill_path: Path, description_override: str | None,
             num_workers: int, timeout: int, max_iterations: int, runs_per_query: int,
             trigger_threshold: float, holdout: float, model: str, verbose: bool,
             live_report_path: Path | None = None, log_dir: Path | None = None,
             worker_model: str | None = None, holdout_state_dir: Path | None = None,
             host: str = "hermes", host_config: dict | None = None) -> dict:
    if max_iterations < 1 or runs_per_query < 1 or not model:
        raise ValueError("Positive iteration/trial limits and model are required")
    name, original, content = parse_skill_md(skill_path)
    current = description_override if description_override is not None else original
    train, dev, test = split_eval_set_hygiene(eval_set, holdout)
    if not train or (holdout > 0 and (not dev or not test)):
        raise ValueError("Insufficient real tasks for nonempty train/dev/test; do not reassign held-out items")
    state = holdout_state_dir
    if state is None:
        # Stable repo/project workspace, never timestamped results directory.
        project = Path.cwd()
        for parent in (project, *project.parents):
            if (parent / ".git").exists():
                project = parent
                break
        state = project / ".workspaces" / name / "heldout-consumed"
    if state is not None:
        freeze_splits(train, dev, test, state)
    def evaluate(items, description):
        return run_eval(items, name, description, str(skill_path), num_workers, timeout,
                        runs_per_query, trigger_threshold, worker_model or model, host, host_config)
    history = []
    exit_reason = "max_iterations"
    for iteration in range(1, max_iterations + 1):
        training = evaluate(train, current)
        validation = evaluate(dev, current) if dev and not training['summary'].get('errored', 0) else None
        if training["summary"].get("errored", 0) or (validation and validation["summary"].get("errored", 0)):
            exit_reason = "execution_error"
            break  # An operational error is not a prompt failure to optimize.
        entry = {"iteration": iteration, "description": current, "test_touched": False}
        for label, data in (("train", training), ("dev", validation)):
            entry[label + "_results"] = data["results"] if data else []
            for key in ("passed", "failed", "total"):
                entry[label + "_" + key] = data["summary"][key] if data else 0
        entry.update(results=entry["train_results"], passed=entry["train_passed"],
                     failed=entry["train_failed"], total=entry["train_total"])
        history.append(entry)
        if live_report_path:
            live_report_path.write_text(generate_html({"history": history, "best_description": current}, True, name))
        if entry["train_failed"] == 0 and entry["dev_failed"] == 0:
            exit_reason = "all_passed"
            break
        if iteration < max_iterations:
            blinded = [{k: v for k, v in h.items() if not k.startswith(("dev_", "test_"))} for h in history]
            endpoint = None
            if host == "freebuff":
                endpoint = {k: (host_config or {}).get(k) for k in ("base_url", "api_key_env")}
            current = improve_description(name, content, current, training, blinded, model,
                                          log_dir=log_dir, iteration=iteration,
                                          optimizer_endpoint=endpoint)
    best = max(history, key=lambda h: (h["dev_passed"], h["train_passed"])) if history else None
    final = None
    if best and test and exit_reason != "execution_error":
        claim_holdout(test, state, best["description"])
        final = evaluate(test, best["description"])
    final_score = None if not final or final["summary"].get("errored", 0) else f"{final['summary']['passed']}/{final['summary']['total']}"
    selection = None if not best else f"{best['dev_passed']}/{best['dev_total']} (dev)" if dev else f"{best['train_passed']}/{best['train_total']} (train-only calibration)"
    return {"exit_reason": exit_reason, "original_description": original,
            "best_description": best["description"] if best else original,
            "best_iteration": best["iteration"] if best else None,
            "best_score": selection, "selection_score": selection,
            "held_out_test_score": final_score, "best_test_score": final_score,
            "final_description": current, "history": history, "iterations_run": len(history),
            "train_size": len(train), "dev_size": len(dev), "test_size": len(test),
            "holdout": holdout, "test_touched_once": final is not None,
            "final_test_results": final, "holdout_state_dir": str(state) if state else None,
            "worker_model": worker_model or model, "optimizer_model": model,
            "calibration_only": holdout == 0}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--eval-set", required=True)
    parser.add_argument("--skill-path", required=True)
    parser.add_argument("--description")
    parser.add_argument("--model", required=True, help="Approved optimizer model")
    parser.add_argument("--worker-model", help="Pinned target; defaults to optimizer model")
    parser.add_argument("--holdout-state-dir", type=Path)
    parser.add_argument("--holdout", type=float, default=0.4)
    parser.add_argument("--num-workers", type=int, default=1)
    parser.add_argument("--timeout", type=int, default=60)
    parser.add_argument("--max-iterations", type=int, default=5)
    parser.add_argument("--runs-per-query", type=int, default=3)
    parser.add_argument("--trigger-threshold", type=float, default=0.5)
    parser.add_argument("--verbose", action="store_true")
    parser.add_argument("--report", default="none")
    parser.add_argument("--results-dir", type=Path)
    add_host_arguments(parser)
    args = parser.parse_args()
    report = Path(args.report) if args.report not in ("none", "auto") else None
    output = run_loop(json.loads(Path(args.eval_set).read_text()), Path(args.skill_path), args.description,
                      args.num_workers, args.timeout, args.max_iterations, args.runs_per_query,
                      args.trigger_threshold, args.holdout, args.model, args.verbose,
                      live_report_path=report, worker_model=args.worker_model,
                      holdout_state_dir=args.holdout_state_dir,
                      host=args.host, host_config=host_config_from_args(args))
    serialized = json.dumps(output, indent=2)
    print(serialized)
    if args.results_dir:
        args.results_dir.mkdir(parents=True, exist_ok=True)
        (args.results_dir / "results.json").write_text(serialized)
        (args.results_dir / "report.html").write_text(generate_html(output, skill_name=Path(args.skill_path).name))
    if report:
        report.write_text(generate_html(output, skill_name=Path(args.skill_path).name))
    return 2 if output["exit_reason"] == "execution_error" or (output["final_test_results"] and output["final_test_results"]["summary"].get("errored")) else 0


if __name__ == "__main__":
    sys.exit(main())
