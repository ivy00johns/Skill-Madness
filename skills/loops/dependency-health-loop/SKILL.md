---
name: dependency-health-loop
version: 1.0.0
description: >-
  Keep a project's dependencies healthy on a schedule: audit for known
  vulnerabilities and over-stale pins, apply ONE safe update (or a vuln fix) per
  pass, run the full gate to prove the update is non-breaking, and open or update
  a PR — looping on a sprint cadence with HITL on every major version bump and
  never auto-merging. Use when you want deps watched while you build, want
  security advisories acted on a cadence, want lockfiles kept fresh without
  breaking the build, or want a dependency audit run every 30 minutes during a
  sprint. Trigger on "audit my dependencies", "keep deps up to date", "dependency
  health", "check for vulnerable packages", "npm audit on a schedule", "pip-audit
  loop", "cargo audit loop", "update dependencies safely", "watch for CVEs",
  "keep the lockfile fresh", "dependabot-style loop", "bump deps and test". Routes
  major/breaking bumps to a human and never merges. A configuration of
  loop-controller.
requires_claude_code: true
min_plan: starter
disable-model-invocation: true
allowed-tools: ["Read", "Edit", "Bash", "Grep", "Glob"]
composes_with: ["loop-controller", "security-agent", "infrastructure-agent", "fix-until-green", "git-pr", "loop"]
spawned_by: []
---

# dependency-health-loop

> **A configuration of [`loop-controller`].** That skill supplies the loop
> machinery — primitive selection, the full guardrail stack, state
> externalization. This skill supplies the three things specific to "keep deps
> healthy": the **per-pass recipe** (audit → one safe bump → gate → PR), a
> **mechanical proof** that combines a security/freshness audit with a green gate
> after every update, and the **HITL boundary** that holds majors for a human.
> Read `loop-controller` for the guardrails; they're inherited, not repeated
> here.
>
> **Why `disable-model-invocation`:** this loop edits the lockfile, commits, and
> pushes branches on its own, on a clock. It is user-driven — you want to *type*
> `/loop 30m /dependency-health-loop` (or `/dependency-health-loop`), not have
> Claude silently start bumping packages because an advisory landed.

## The 5-part contract

| Part | This loop |
|---|---|
| **trigger** | a sprint in flight (deps drifting / new advisories), scheduled via `/loop 30m /dependency-health-loop`, or an explicit `/dependency-health-loop` |
| **action** | ONE pass: run the ecosystem audit → pick **one** safe update (a security fix first, else one over-stale patch/minor) → apply it → run the **whole** [`fix-until-green`] gate → open or update a PR. One bump per pass; re-audit the whole tree after |
| **proof** | **no known vulnerabilities AND no pinned dep stale beyond policy AND the gate exits green** — all three observed in the same pass, from the audit report + gate exit codes. Default-FAIL: assume **unhealthy** until the audit proves otherwise |
| **memory** | `dep-health.md` (audit snapshot, the bump→result log, deferred majors + why), the PR branch, the lockfile diff, and git history — durable across the session-scoped `/loop` fires |
| **stop** | proof holds (clean audit + in-policy freshness + green gate) **OR** poll/iteration cap **OR** no-progress for 3 passes (same advisory unfixable within the reversible boundary) **OR** budget cap **OR** an HITL checkpoint is hit (a major bump, or a lockfile-semantics change) |

## The proof: clean audit + in-policy freshness + green gate, default-FAIL

"Healthy" is not "the last bump installed." It is **three conditions read
together in one pass**: the ecosystem audit reports **zero known
vulnerabilities** at or above the policy severity, **no pinned dependency is
stale beyond the freshness policy**, and the full gate (`fix-until-green`'s three
exit codes) is **green after the update**. Assume the tree is **unhealthy** until
a fresh audit proves all three — that is the default-FAIL stance, and it is why
every pass *re-audits* rather than trusting the last verdict. A loop that stops
after one bump ships a tree that picked up a new CVE and a red typecheck.

This is the only loop whose proof fuses a **security/freshness audit** with a
**green gate after each bump** — neither half alone is the proof. Name the
artifacts: the audit report (`npm audit --json` / `pip-audit` / `cargo audit` /
`govulncheck`) plus the gate's exit codes. Both must read clean *in the same
pass*. Per-ecosystem audit + freshness commands are in
`references/ecosystems.md`.

## Step 1 — Audit, pick exactly one update

Run the ecosystem audit and the freshness check (the precise commands per stack
are in `references/ecosystems.md`). Then pick **one** target, in priority order:

1. **A security fix** for the highest-severity known vulnerability (a patch/minor
   that resolves an advisory).
2. Else **one over-stale dependency** past the freshness policy — smallest safe
   bump first (patch before minor).

One bump per pass. Batching destroys the signal about which change broke (or
fixed) the gate, and it makes the PR un-reviewable. If the only available fix for
an advisory is a **major** bump, that is an HITL checkpoint — do not apply it;
record it as a deferred major and surface it.

## Step 2 — Apply, then verify with the whole gate

Apply the single bump, regenerate the lockfile, and re-run the **entire**
[`fix-until-green`] gate (test + lint + typecheck) from scratch — not just the
package's own tests. A bump that installs cleanly but reds typecheck has made the
tree worse, and only a full re-run catches it. **Do not re-implement the gate** —
invoke `fix-until-green`; this loop adds only the dependency discipline around it.
If the gate goes red and the fix is a mechanical adaptation to the new API,
`fix-until-green` resolves it; if it can't be made green within the bump, **roll
the bump back** (the lockfile diff is the undo) and record it as needing a human.

## Step 3 — Open or update the PR, re-audit

On a green bump, commit a checkpoint naming the package and version, then open or
update a single dependency-health PR via [`git-pr`]. Then **re-audit the whole
tree** — the proof is about the whole, re-checked after every change. When the
audit is clean, freshness is in policy, and the gate is green together, the
loop's proof holds; report the audit report + gate output as evidence. The loop
prepares the PR for a human to merge — it never merges.

## HITL is load-bearing for this loop

This loop runs **only inside the reversible boundary** unattended. The
irreversible or breaking actions are **HITL checkpoints — never autonomous**:

- **A major version bump** — pause, always. A breaking major is never merged
  unattended; record it as a deferred major and surface it for a human, with the
  changelog/migration link.
- **Anything that changes lockfile semantics** beyond a clean add/bump — a
  resolution override, a peer-dependency force, a registry/source swap, removing
  a transitive pin — pause. These change *what resolves*, not just a version.
- **Merging** — never. Reaching the proof means *ready for the human to merge*,
  not "merge it." This loop does not auto-merge, full stop.

Within the boundary — a patch/minor security update or in-policy freshness bump
with a green gate, on its own branch/PR — it is AFK-safe. The full AFK-safe vs
pause table is in `references/ecosystems.md`.

## Guardrails specific to this loop

Inherits the full stack from `loop-controller` → `references/safety.md`. The caps
this loop sets:

- **Poll / iteration cap** — `/loop`'s ~3-day session expiry is the outer bound;
  set an inner per-run pass cap (default ~20) so a tree full of advisories
  doesn't burn the window. Hitting it is a *stop-and-escalate*, not a license to
  loosen the proof.
- **No-progress detection** — if the **same advisory** survives **3 consecutive
  passes** (only fixable by a major, or the bump can't be made green), stop and
  surface it. Three passes on one advisory means it needs a human decision, not a
  fourth attempt.
- **Budget cap** — a watch loop firing every 30 minutes adds up; enforce a
  token/cost ceiling that *terminates* the loop (read from `.claude/profile.yaml`
  when present), not just warns.
- **Never cheat the proof.** Forbidden, each a *finding*: pinning around an
  advisory with an audit-ignore/allowlist entry instead of fixing it, downgrading
  the policy severity to clear the count, suppressing a deprecation rather than
  resolving it, or merging to make the audit moot. A clean audit that came from
  silencing the auditor is not health.

## How this differs from its neighbors

This loop is **not** a one-shot dependency update, and it is not a re-skin of an
existing skill — it draws three explicit boundaries:

- **vs a one-shot `npm update` / dependabot bump:** those apply versions; they do
  not *prove* health. This loop's substance is the **loop discipline** — a
  default-FAIL proof that fuses audit + freshness + a green gate, one bump per
  pass with full re-verification, no-progress detection, scheduling, and an HITL
  gate on majors. The bump is the easy part; the proof and the boundary are the
  product.
- **vs [`security-agent`]:** the security role authors the **policy** — which
  severities block, which advisories are accepted, the SBOM/audit expectations.
  This loop **consumes** that policy as its proof threshold and *acts on a
  cadence*; it does not define security posture. On a vuln it can't resolve
  within the reversible boundary, it escalates to the human (and, under an
  orchestrated build, to the security role).
- **vs [`infrastructure-agent`]:** infra owns the dependency manifests and
  lockfiles as files. This loop proposes single, gated bumps **as PRs** for the
  owner to merge — it never force-merges into infra-owned files, and majors route
  to a human exactly because they may change runtime/build semantics infra owns.
- **vs [`fix-until-green`]:** that loop's proof is three exit codes. This loop's
  proof *contains* a green gate but is strictly larger (audit + freshness), and
  it **invokes** `fix-until-green` to verify each bump rather than re-implementing
  the gate.

## Choosing the driver primitive

Per `loop-controller` Step 1, this is a **watch/poll** job — you wait for the
dependency tree and advisory feed to *change* on a cadence — so the primitive is
**`/loop`** (sprint cadence) or **`/schedule`** (a longer, e.g. nightly,
cadence), **not** `/goal` (which pushes to a finish line). The daily-driver
recipe:

```
/loop 30m /dependency-health-loop
```

The *per-pass* exit (this pass made one clean, reversible, gated bump and
re-audited) is provable from the audit report + gate exit codes, so a pass can
run unattended within the HITL boundary above. `/loop`'s session-scope, ~3-day
expiry, and no-catch-up mechanics live in `loop-controller`'s
`references/primitives.md`; don't re-document them.

## Reference files

- `references/ecosystems.md` — per-ecosystem audit + freshness + update commands
  (npm/pnpm/yarn, pip/poetry/uv, cargo, go, bundler, composer), the
  major-vs-minor HITL policy, the lockfile-safety rules (what's a clean bump vs a
  semantics change), and the AFK-safe vs pause table.

[`loop-controller`]: ../loop-controller/SKILL.md
[`fix-until-green`]: ../fix-until-green/SKILL.md
[`security-agent`]: ../../roles/security-agent/SKILL.md
[`infrastructure-agent`]: ../../roles/infrastructure-agent/SKILL.md
[`git-pr`]: ../../git/git-pr/SKILL.md
