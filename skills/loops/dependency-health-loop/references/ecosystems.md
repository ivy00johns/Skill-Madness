# Ecosystem commands, HITL policy, and lockfile safety

Per-ecosystem audit / freshness / update commands for `dependency-health-loop`,
the major-vs-minor HITL policy, the lockfile-safety rules, and the AFK-safe vs
pause table. The loop machinery and the full guardrail stack live in
`loop-controller`; this is only the dependency-specific configuration.

## Contents
- [Per-ecosystem commands](#commands)
- [The freshness policy](#freshness)
- [Major-vs-minor HITL policy](#hitl)
- [Lockfile-safety rules](#lockfile)
- [AFK-safe vs pause table](#afk)

---

<a id="commands"></a>
## Per-ecosystem commands

Detect the ecosystem from the manifest/lockfile present, then use its native
audit, freshness, and single-bump commands. Prefer `.claude/profile.yaml`
overrides if declared; otherwise use the project's package manager (the one whose
lockfile is committed). Run audits with a machine-readable flag so the proof is
parseable.

| Ecosystem | Audit (vulns) | Freshness (outdated) | Apply ONE bump |
|---|---|---|---|
| **npm** | `npm audit --json` | `npm outdated --json` | `npm install <pkg>@<ver> --save-exact` then `npm audit fix` (targeted) |
| **pnpm** | `pnpm audit --json` | `pnpm outdated` | `pnpm update <pkg>@<ver>` |
| **yarn (berry)** | `yarn npm audit --json` | `yarn outdated` (classic) / `yarn upgrade-interactive` non-interactive equivalents | `yarn up <pkg>@<ver>` |
| **pip / requirements** | `pip-audit -f json` | `pip list --outdated --format=json` | edit the pin, `pip install -U <pkg>==<ver>` |
| **poetry** | `pip-audit` (export) or `poetry audit` plugin | `poetry show --outdated` | `poetry update <pkg>` (constrained) |
| **uv** | `pip-audit` against the resolved env | `uv pip list --outdated` | `uv add <pkg>==<ver>` / `uv lock --upgrade-package <pkg>` |
| **cargo** | `cargo audit --json` (RustSec) | `cargo outdated` | `cargo update -p <pkg> --precise <ver>` |
| **go** | `govulncheck ./...` | `go list -m -u all` | `go get <module>@<ver>` then `go mod tidy` |
| **bundler** | `bundle audit check --update` | `bundle outdated` | `bundle update <gem> --conservative` |
| **composer** | `composer audit --format=json` | `composer outdated --direct` | `composer require <pkg>:<ver>` |

After any apply, regenerate the lockfile with the manager's own command (do not
hand-edit a lockfile) and run the full gate via `fix-until-green`.

Severity gate: treat **critical/high** advisories as proof-blocking by default;
read the project's accepted threshold from the [`security-agent`] policy or
`.claude/profile.yaml`. The loop *consumes* that threshold — it does not invent
one.

<a id="freshness"></a>
## The freshness policy

"Over-stale" needs a policy, or the loop chases every patch forever. Default
policy (override in `.claude/profile.yaml`):

- **Security:** any package with a known advisory is over-stale regardless of age
  — fix first.
- **Direct deps:** flag a pin more than **2 minor versions** or **180 days**
  behind latest-compatible.
- **Dev/build deps:** looser — flag at **1 major behind** (and majors are HITL,
  see below).
- **In-policy = not flagged.** The freshness half of the proof passes when no
  pinned dep exceeds these bounds. Record the snapshot in `dep-health.md`.

<a id="hitl"></a>
## Major-vs-minor HITL policy

The version-delta of the chosen bump decides autonomy. This is the load-bearing
boundary of the loop.

| Bump | Autonomy | Rule |
|---|---|---|
| **Patch** (`x.y.Z`) | AFK-safe | Apply + gate + PR unattended within the reversible boundary. |
| **Minor** (`x.Y.z`) | AFK-safe | Same, *if* the gate is green and no lockfile-semantics change (below). SemVer says additive; verify, don't trust. |
| **Major** (`X.y.z`) | **HITL — pause** | Never applied/merged unattended. Breaking by contract. Record as a deferred major with the changelog/migration link; surface for a human. |
| **0.x bumps** | Treat **minor as major** | Pre-1.0, a minor can break. Any `0.x` → `0.(x+1)` is HITL unless the changelog says otherwise. |
| **Security fix only via major** | **HITL — pause** | An advisory whose only fix is a major does not license an unattended major. Escalate it (and, under an orchestrated build, to `security-agent`). |

A bump that is nominally patch/minor but trips a lockfile-semantics change (next
section) is escalated to HITL regardless of the version delta.

<a id="lockfile"></a>
## Lockfile-safety rules

The lockfile diff is the loop's primary evidence and its undo. Classify every
lockfile change before trusting it green.

**Clean bump (AFK-safe within the boundary):**
- A single direct dependency's version changed, plus the transitive closure it
  pulls — and nothing else's resolved version moved unexpectedly.
- The integrity hashes change only for the bumped subtree.
- No new top-level resolution override / `resolutions` / `overrides` / `[patch]`
  entry was introduced.

**Semantics change (HITL — pause):**
- A resolution override, peer-dependency force, or `--force`/`--legacy-peer-deps`
  was needed to install.
- The registry or source for a package changed (a git/url/source swap).
- A transitive pin was removed or widened such that *other* unrelated packages
  re-resolved.
- The lockfile format/version itself changed (a manager upgrade in disguise).

Rule of thumb: if the diff changes **what resolves** rather than **which version
of one thing resolves**, pause. When in doubt, roll the bump back (restore the
prior lockfile) and surface it — a reverted bump is cheaper than a silently
broken transitive tree.

<a id="afk"></a>
## AFK-safe vs pause table

| Action | AFK-safe | Pause (HITL) |
|---|---|---|
| Patch/minor security fix, green gate, clean lockfile | ✅ | |
| In-policy freshness patch/minor, green gate, clean lockfile | ✅ | |
| Opening / updating the dependency-health PR | ✅ | |
| Rolling back a bump that won't go green | ✅ | |
| Major version bump | | ⛔ pause |
| 0.x minor bump (pre-1.0) | | ⛔ pause |
| Lockfile-semantics change (override/force/source swap) | | ⛔ pause |
| Advisory fixable only via a major | | ⛔ pause |
| Merging the PR | | ⛔ never — human merges |
| Adding an audit-ignore/allowlist to clear an advisory | | ⛔ never — that's cheating the proof |

Everything in the right column stops the loop and surfaces to the human with the
evidence (audit report, lockfile diff, changelog link) so the decision is a
one-glance approve/reject.

[`security-agent`]: ../../../roles/security-agent/SKILL.md
