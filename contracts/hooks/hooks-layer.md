# Contract: Hooks Layer (P0)

**Version:** 1.1.0
**Status:** ACTIVE — authored by orchestrator for the AllTheSkills P0 build
**Source plan:** `DeepResearch/The-Hive/ecc_deepdive/source-material/14-alltheskills-frontier.md` (P0)

AllTheSkills ships zero hooks today. This contract defines a hooks layer that turns the orchestrator's *doctrine* (QA gate, formatting, profile injection) into *enforcement*, modeled on ECC's gated-hook design but built in the repo's own bash + python3 idiom. It is the binding interface every implementing/testing agent works from.

## Scope

In scope (P0): a canonical `hooks/` source tree, a `run-with-flags` wrapper with profile/disable gating, four high-value hooks (the qa-gate being the marquee), Claude Code emission via the installer, a lint check, and bats tests.

Out of scope (later phases): plan/apply install + profiles + content-hash install-state (P1), catalog-as-CI-invariant for skill counts (P1), skill-health telemetry (P2), pre-install skill supply-chain/injection scanner (P2). Do **not** build these here.

## House rules (must match the repo)

- Bash, `set -euo pipefail`, **bash 3.2 portable** (macOS default). No `mapfile`, no associative arrays unless guarded.
- Source shared helpers: `. "$LIB_DIR/term.sh"` for `ats_ok/ats_warn/ats_err/ats_info`; reuse `platform.sh` where useful.
- Hooks must `exit 0` on disabled state and on non-critical errors (never wedge the host harness). Only the qa-gate intentionally blocks: on a gate failure, malformed report, or unavailable strict enforcement.
- Blocking hooks must stay fast (<200 ms) except the qa-gate, which runs a python3 validation pass (still sub-second).
- python3 validation uses **stdlib only** (`json`) — no third-party `jsonschema` dependency. Validate required keys + types structurally against `skills/roles/qe-agent/references/qa-report-schema.json`.

## 1. Directory layout (new, additive)

```text
hooks/
├── hooks.manifest.json        # canonical registry: id → {event, script, profiles, blocking, description}
├── run-with-flags.sh          # dispatcher/wrapper — the ONLY entrypoint harnesses call
├── lib/
│   └── hook-flags.sh          # parses ATS_HOOK_PROFILE + ATS_DISABLED_HOOKS; is_enabled <id>
└── scripts/
    ├── post-edit-format.sh        # PostToolUse(Edit|Write): format the edited file if a formatter exists
    ├── session-start-profile.sh   # SessionStart: inject CLAUDE.md / .claude/profile.yaml summary (≤8 KB)
    ├── pre-commit-lint.sh         # PreToolUse(Bash git commit): run lint-skills.sh if skills changed; non-blocking warn
    └── qa-gate.sh                 # Stop/TaskCompleted: validate qa-report.json → BLOCK on gate failure  [MARQUEE]
        └── qa-gate-validate.py    # python3 stdlib validator + gate-rule evaluator (called by qa-gate.sh)
```

## 2. Gating model

Two environment variables tune the whole graph (mirrors ECC's `ECC_HOOK_PROFILE`/`ECC_DISABLED_HOOKS`):

- `ATS_HOOK_PROFILE` ∈ `{minimal, standard, strict}`, default `standard`.
  - `minimal` → qa-gate only.
  - `standard` → qa-gate + post-edit-format + session-start-profile.
  - `strict` → all hooks, and qa-gate treats a missing report as a BLOCK (see §3).
- `ATS_DISABLED_HOOKS` → comma-separated hook ids to force-off (e.g. `post-edit-format,pre-commit-lint`).

`lib/hook-flags.sh` exposes `is_enabled <hook-id>` returning 0/1 by combining the manifest's `profiles` array with the active profile and the disable list. `run-with-flags.sh <hook-id>` calls `is_enabled`; if disabled it prints nothing and `exit 0`; otherwise it execs `scripts/<hook-id>.sh`, passing stdin through unchanged.

## 3. qa-gate (marquee) behavior

Invoked as a Claude Code **Stop** hook via `run-with-flags.sh qa-gate`.

1. Locate the report: `$ATS_QA_REPORT` if set, else first existing of `./qa-report.json`, `coordination/qa-report.json`, `.claude/qa-report.json`.
2. If no report found: `standard`/`minimal` → `ats_warn` + `exit 0` (allow); `strict` → block.
3. Validate with `qa-gate-validate.py` against the required keys/types of `qa-report-schema.json` (schema_version, status, scores{correctness,completeness,code_quality,security,contract_conformance each {score,notes}}, test_results, blockers, issues, recommendations, gate_decision{proceed,reason}). A non-conformant report → block with a "report malformed" reason.
4. Apply the **gate rules** (identical to the orchestrator's): BLOCK when any of —
   - `gate_decision.proceed == false`
   - any blocker with `severity == "CRITICAL"`
   - `scores.contract_conformance.score < 3`
   - `scores.security.score < 3`
5. **Strict proof binding (UA-12):** require `proof_binding` with the active `run_id`, Git `revision`, `source_sha256`, and `contract_sha256`. `build_session_id` must equal the active run. The hook uses `ATS_QA_RUN_ID`, falling back to the host payload's `session_id`; absent context blocks. The project root is `CLAUDE_PROJECT_DIR` (or cwd), and contracts default to its `contracts/` directory (`ATS_QA_CONTRACTS` may select another directory inside the root). The validator recomputes the binding and blocks mismatches, including uncommitted and untracked nonignored changes at the same HEAD. Legacy unbound reports still work under standard/minimal, but cannot certify strict completion. In strict mode the wrapper dispatches QA directly even if manifest discovery fails; a missing QA script blocks unless the hook was explicitly disabled.
6. **Enforcement failures:** strict mode blocks a missing validator, Python/runtime failure, invalid hook payload, and unexpected validator status. Standard/minimal preserve their permissive policy, emit `UNVERIFIED` for checker failures, and never call those failures a pass. Unknown profiles select strict rather than silently downgrading. Hook diagnostics go to stderr; stdout contains only decision JSON or nothing. If Python is unavailable, the shell emits a fixed valid blocking decision.
7. **Bounded Stop reentry:** read `stop_hook_active` from the payload as a JSON boolean. If true, return control with `UNVERIFIED` on stderr and no block/allow certification, preventing an endless Stop loop. This is a host escape, not proof of success; the owner must repair the gate/report before treating the build as verified. Keep DV-1's no-read-from-TTY protection and all explicit hook-disable opt-ins.
8. Blocking mechanism: emit the Claude Code Stop-hook block decision — print JSON `{"decision":"block","reason":"<why>"}` to stdout and `exit 0` (Claude Code's documented Stop-hook contract), and also write the human reason to stderr. Allowing → `exit 0` with no decision.

The validator is unit-testable: `qa-gate-validate.py <report.json>` exits `0` (allow), `1` (block — prints reason to stdout), `2` (malformed/not-found/proof unavailable). `FAIL`/`BLOCKED` status blocks even if `gate_decision.proceed` is incorrectly true. `--strict` adds read-only Git/content binding checks; `--snapshot` emits only the current binding JSON.

### Producing strict evidence

The lead supplies the run ID; the verifier captures the binding **before** testing, then compares it after testing and writes it into `proof_binding` only if the source and contract boundary remained unchanged. Set `build_session_id` to that run ID. For example:

```bash
export ATS_QA_RUN_ID="owner-assigned-build-id"
export CLAUDE_PROJECT_DIR="$PWD"
python3 hooks/scripts/qa-gate-validate.py coordination/qa-report.json --snapshot
python3 hooks/scripts/qa-gate-validate.py coordination/qa-report.json --strict
```

Do not retrofit fresh hashes onto an old result: rerun verification after any source/contract changes. The digest includes relative names, modes and bytes of Git-tracked and nonignored untracked files, including deleted tracked paths. It excludes the selected QA JSON/narrative pair and the three conventional QA-report pairs to avoid self-reference. Ignored files (including root credentials), external runtime/database state and unsupported symlinks/submodules/special files are not certified by this snapshot; require separate evidence for those boundaries, and strict mode refuses unsupported entries. An empty contract set is bound as empty, not claimed as a passed contract test. Binding establishes freshness, **not authenticity, independent review or proof that tests ran**.

## 4. Installer emission

- **convert.sh**: add `convert_hooks_claude_code()` (called from `convert_claude_code` or `main`) that copies `hooks/` into `integrations/claude-code/hooks/` and generates `integrations/claude-code/hooks.json` in Claude Code settings-hook format, mapping events → `"$CLAUDE_PROJECT_DIR"/.claude/ats-hooks/run-with-flags.sh <id>`. Use the existing `write_file_from_stdin`/emit helpers and `ats_ok` logging.
- **install.sh**: copy the hooks tree to a **namespaced** target `~/.claude/ats-hooks/` (never the user's own hook dir), and write `integrations/claude-code/hooks.json` to `~/.claude/ats-hooks/hooks.json`. Do **not** auto-merge the user's `~/.claude/settings.json` — instead `ats_info` print the exact merge snippet and a one-line instruction. Non-destructive is mandatory (the user is remote; clobbering settings is unacceptable).
- **Harness support matrix:** `claude-code` = full. All others (`copilot antigravity gemini-cli opencode cursor openclaw qwen kimi aider windsurf`) have no native lifecycle-hook system → **skip with an `ats_info "hooks: unsupported for <tool>"`** and record `unsupported` status. Do not fabricate hook support.

## 5. Lint / CI

- Add `scripts/lint-hooks.sh` (or a `lint_hooks` section reusing `emit_issue`) validating: every manifest entry's `script` exists and is executable; each hook script starts with `#!/usr/bin/env bash` + `set -euo pipefail` and sources `term.sh`; `hooks.manifest.json` parses and every id is unique; profiles ⊆ {minimal,standard,strict}.
- Wire an **additive** step into `.github/workflows/lint-skills.yml` that runs `scripts/lint-hooks.sh` and the new bats suite. Do not remove or restructure existing steps.

## 6. Tests (bats, `tests/hooks/`)

Mirror `tests/installer/` conventions (setup_file, mktemp, bash-3.2). Required cases:

- wrapper: a hook in `ATS_DISABLED_HOOKS` is a no-op `exit 0`; profile `minimal` runs only qa-gate; `standard` runs the three; unknown id → `exit 0` with stderr note.
- qa-gate: PASS fixture (`tests/installer/qa-report.json`) → allow (exit 0, no block JSON). New FAIL fixtures → block for each rule: `proceed=false`, a CRITICAL blocker, `contract_conformance<3`, `security<3`. Malformed JSON → exit 2. Missing report → allow under `standard`, block under `strict`.
- convert: running convert for claude-code produces `integrations/claude-code/hooks/run-with-flags.sh` (executable) and a `hooks.json` that parses and references `run-with-flags.sh`.
- lint-hooks: passes on the shipped tree; fails when a manifest script is missing (use a temp tree).

## 7. Definition of Done (this contract)

- `hooks/` tree exists and `scripts/lint-hooks.sh` passes on it.
- `bash -n` clean on every new `.sh`; `python3 hooks/scripts/qa-gate-validate.py` behaves per §3 against PASS + 4 FAIL fixtures.
- `scripts/convert.sh --tool claude-code` emits the hooks artifacts; other tools log `unsupported` and do not error.
- bats suite in `tests/hooks/` passes; CI workflow runs it.
- README gains a "Hooks" section; `.claude-plugin/` metadata updated if it enumerates components.
- **No git operations performed** — all changes left uncommitted in the working tree.

## Changelog

- 1.1.0 — UA-12 strict fail-closed enforcement, run/content/contract binding, JSON-only decisions and bounded Stop reentry; legacy standard/minimal report policy retained.
- 1.0.0 — initial contract (orchestrator, P0 hooks layer).
