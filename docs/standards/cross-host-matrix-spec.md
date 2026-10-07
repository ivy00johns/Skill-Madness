# F3 / F5 Cross-Host Load & Outcome Matrix Specification (UA-19)

Depth for extending the parked `F3` (per-host smoke tests) and `F5` (`skill-eval` / `skill-optimize`)
proposals into a low-cost, measured cross-host load and outcome matrix without running paid models
or inventing a separate evaluation platform.

## Background & Scope

Universal skill support cannot be established merely through static YAML frontmatter linting or
green structural tests (`lint-skills.sh`). UA-19 defines the concrete specification, schema, and
adversarial test fixtures for cross-host load/outcome checks across four evaluation layers:

1. **Resource/load smoke (`F3` extension):** Does the host discover the skill, preserve required
   frontmatter, resolve `SKILL_ROOT`, and provide complete resource closure (assets, scripts,
   references, templates) without symlink escapes or missing files?
2. **Trigger selection (`F5` triggerability):** Does unforced retrieval correctly select the candidate
   skill on positive intent queries and reject near-miss negatives without forcing preloads (`-s`)?
3. **Task efficacy (`F5` / `SO-4` efficacy):** Does running the task with the skill loaded measurably
   improve the accepted artifact over baseline (without skill) on held-out tasks?
4. **Safety & degradation:** Are missing capabilities, checker errors, hard budget breaches, and
   unsafe global actions halted or refused with explicit status rather than reporting a false PASS?

## Implemented receipt interface

Run `python -m scripts.check_matrix records.json` from the installed creator resource
root. Input is a nonempty JSON list of cells. `layer` is `load`, `trigger` or `efficacy`;
`evidence_kind` is `offline-fixture` or `live-host`. Host requires nonempty name/version,
and live evidence requires a pinned model ID. All usage and ceilings must be finite,
nonnegative numbers; calls are integers. Malformed input returns JSON rejection and exit 2. Each cell requires `run_id`, `task_id`, `layer`,
SHA-256 `skill_hash`, `baseline_hash`, `verifier_hash`, `host`, `model`, `split`,
`falsifier`, `limits`, `trajectory`, acceptance dimensions, `status` and `evidence_kind`.
Limits use `max_calls`, `max_seconds`, `max_cost_usd`; trajectory uses `calls`,
`seconds`, `cost_usd`. Exit 2 means rejected evidence, not a negative trigger.
Efficacy additionally requires identical `baseline_model`/`baseline_host`, unforced
`retrieval_proof`, at least two trials, `held_out_test` and `test_touches: 1`.

The validator does not dispatch calls or enforce running-process budgets; those must
be provided by the approved external controller. An `offline-fixture` must report zero
model calls/spend and cannot support a model capability claim. A successful negative
trigger can legitimately have no candidate retrieval; absence disqualifies treatment
only for positive trigger or efficacy claims. All live model cells remain NOT RUN.
The illustrative schema below describes conceptual records, not the CLI's strict interface.

## Bounded Matrix Structure

Runs are structured into a deterministic, reproducible matrix evaluated against frozen baselines
with strict budget ceilings:

```json
{
  "matrix_id": "cross-host-matrix-v1",
  "baseline_commit": "9e0289a2b83e82ff5920fe87358f218845b7d7c0",
  "hosts": [
    {"id": "claude-code", "mode": "attended", "native": true},
    {"id": "cursor", "mode": "attended", "target": "rules"},
    {"id": "gemini-cli", "mode": "attended", "target": "extensions"},
    {"id": "codex", "mode": "attended", "target": "agents"},
    {"id": "hermes", "mode": "attended", "target": "skills"}
  ],
  "budget_ceilings": {
    "max_calls_per_cell": 3,
    "max_seconds_per_cell": 120,
    "max_cost_usd_per_cell": 0.0,
    "allow_unmetered_local_only": true
  }
}
```

## Record and Grade Schema

Every execution cell is recorded with separated Outcome, Proof, Architecture, and Trajectory
dimensions. Acceptance is strictly `Outcome + Proof + Architecture`. Trajectory cost never
compensates for an outcome failure:

```json
{
  "$schema": "http://json-schema.org/draft-07/schema#",
  "title": "CrossHostEvalRecord",
  "type": "object",
  "required": [
    "run_id",
    "skill_name",
    "skill_hash",
    "host",
    "split",
    "outcome",
    "proof",
    "architecture",
    "status"
  ],
  "properties": {
    "run_id": {"type": "string"},
    "skill_name": {"type": "string"},
    "skill_hash": {"type": "string"},
    "host": {
      "type": "object",
      "required": ["name", "mode"],
      "properties": {
        "name": {"type": "string"},
        "version": {"type": "string"},
        "mode": {"type": "string", "enum": ["attended", "unattended-gated"]}
      }
    },
    "model": {
      "type": "object",
      "properties": {
        "provider": {"type": "string"},
        "id": {"type": "string"},
        "effort": {"type": "string"}
      }
    },
    "split": {"type": "string", "enum": ["train", "dev", "held_out_test"]},
    "task_id": {"type": "string"},
    "retrieval_proof": {"type": "string"},
    "outcome": {"type": "string", "enum": ["pass", "fail", "inconclusive"]},
    "proof": {"type": "string", "enum": ["pass", "fail", "unverified"]},
    "architecture": {"type": "string", "enum": ["pass", "fail", "violated"]},
    "status": {"type": "string", "enum": ["success", "error", "timeout", "blocked", "budget_exceeded"]},
    "trajectory": {
      "type": "object",
      "properties": {
        "calls": {"type": "integer"},
        "seconds": {"type": "number"},
        "cost_usd": {"type": ["number", "null"]}
      }
    }
  }
}
```

## Disqualifier Rules (`[HE]` / `[SO]`)

A cell result is automatically disqualified and marked `inconclusive` or `fail` if:

1. **Unforced treatment retrieval absent:** A positive trigger/efficacy treatment was never retrieved or was forced via an out-of-band preload flag (`-s`); a valid negative query may correctly retrieve nothing.
2. **Execution error masked:** A tool timeout or crash was recorded as a passing negative non-trigger.
3. **Split leakage:** The held-out test split was accessed during tuning or candidate selection.
4. **Evaluator-only assertion:** The model self-certified completion without external execution proof.
5. **Budget overrun:** Calls or runtime exceeded the approved cell ceiling.
