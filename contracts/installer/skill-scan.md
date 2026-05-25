# Contract: Skill Supply-Chain / Injection Scanner (P2-D)

**Version:** 1.0.0
**Status:** ACTIVE — orchestrator, AllTheSkills P2
**Source plan:** `DeepResearch/The-Hive/ecc_deepdive/source-material/14-alltheskills-frontier.md` (P2)
**Models:** ECC's deterministic security layer (supply-chain IOC + the "scan the thing you distribute" insight). AllTheSkills *distributes* skills to 11 harnesses but nothing scans skill bodies before install.

A deterministic, LLM-free scanner over `skills/` that the `security-agent` **consumes** (rather than freelance-auditing). Findings are reproducible and CI-gateable.

## Critical: must pass clean on the current tree

The scanner is wired as a **blocking CI gate**, so it MUST exit 0 on the repo's current `skills/` tree. Tune the rules to avoid false positives on legitimate content — e.g. skills that *document* prompt-injection defenses, the repo's own "Prompt Defense Baseline" text, or example payloads in security/meta skills. Provide an ignore mechanism (a `# scan-skills:ignore[ rule]` inline annotation and/or a `.scan-skills-ignore` file of `path:rule` entries) and use it to exempt known-legitimate hits — but only after confirming each is genuinely benign. If a genuine secret/issue exists in a real skill, **report it as a finding for the user; do NOT auto-edit skills and do NOT silence it with an ignore.**

## Component — `scripts/scan-skills.sh`
```
scripts/scan-skills.sh [--check | --text | --json] [PATH ...] [--help]
  --check  (default) scan; exit 1 if any HIGH-severity finding; else 0
  --text   human-readable findings grouped by severity
  --json   machine-readable findings array
```
Scans every `SKILL.md` (and its `references/`) under the given paths (default `skills/`, excluding `archive/` + `in-progress/`). Rule set:

| Rule | Severity | Detects |
|------|----------|---------|
| `secret-aws` | HIGH | `AKIA[0-9A-Z]{16}`, AWS secret-key shapes |
| `secret-generic` | HIGH | `api[_-]?key`, `token`, `password`, `secret` assigned a long literal; `Authorization: Bearer <token>` |
| `private-key` | HIGH | `-----BEGIN (RSA |EC |OPENSSH )?PRIVATE KEY-----` |
| `zero-width-unicode` | HIGH | zero-width / invisible / bidi-control codepoints (U+200B–200F, U+202A–202E, U+2060, U+FEFF) |
| `prompt-injection` | MEDIUM | case-insensitive "ignore (all )?previous instructions", "disregard (the )?above", "you are now", "system prompt:" override phrasing |
| `untrusted-composes` | MEDIUM | a `composes_with` entry naming a skill not present under `skills/` |
| `mcp-ref` | LOW | references to MCP servers (informational inventory) |
| `long-base64` | LOW | base64-looking blobs ≥ 200 chars |

Pure bash + python3 stdlib (unicode scan is easiest in python3); no network, no `eval`. Findings carry `path`, `line`, `rule`, `severity`, `excerpt` (truncated, never the full secret).

## CI
Orchestrator wires `scripts/scan-skills.sh --check` as a blocking step into `.github/workflows/lint-skills.yml` (**do not edit the workflow yourself**). It must be green on the current tree.

## security-agent wiring (additive)
Append a short "## Automated pre-scan" note to `skills/roles/security-agent/SKILL.md`: the agent should run `scripts/scan-skills.sh --json` and consume/triage its findings rather than hunting from scratch, and must not invent findings the scanner didn't produce. Additive prose only; keep within lint length limits.

## Tests (`tests/scan-skills/`, bats, bash-3.2)
- temp fixture skill with a planted AWS key / private key / `api_key="<long>"` → HIGH finding, `--check` exit 1.
- temp fixture with a zero-width char → HIGH.
- temp fixture with "ignore previous instructions" in body → MEDIUM (does NOT alone fail `--check`).
- `composes_with: [does-not-exist]` → MEDIUM untrusted-composes; a real skill name → no finding.
- `# scan-skills:ignore secret-generic` annotation suppresses that one finding on that line.
- **regression: `scripts/scan-skills.sh --check skills/` on the real tree exits 0** (after any needed ignores for legit content, each justified).
- excerpts never print a full secret value.

## Ownership (P2-D agent)
OWNS: `scripts/scan-skills.sh`, `tests/scan-skills/`, an optional `.scan-skills-ignore`, and an additive "## Automated pre-scan" note in `skills/roles/security-agent/SKILL.md`.
MUST NOT touch: `.github/workflows/` (orchestrator wires CI), `scripts/install*.sh`, `scripts/convert.sh`, `scripts/catalog.sh`, `scripts/skill-health.sh` + `tests/skill-health/` (P2-C), `hooks/`, README root, `skills/meta/skill-audit/SKILL.md` + `skills/meta/skill-improvement-plan/SKILL.md` (P2-C), `skills/workflows/repo-deep-dive/`.

## DoD
`scan-skills.sh` flags planted secrets/injection/zero-width/untrusted-composes deterministically, **exits 0 on the current real `skills/` tree**, supports ignores, never leaks full secrets; security-agent pointer added; `bash -n` clean; bats pass. **No git ops.**

## Changelog
- 1.0.0 — initial (orchestrator, P2-D).
