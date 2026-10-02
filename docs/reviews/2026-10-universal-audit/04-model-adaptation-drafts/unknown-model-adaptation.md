# Unknown-model baseline — draft, not installed

## Why unknown is a supported state

A user may use Qwen, Kimi, a routed free model, a renamed frontier model, or a host that withholds exact identity. The safe baseline is not “assume Claude,” nor “all skills unavailable.” [Existing provider policy:83](../../../../skills/meta/model-adaptation/references/model-effort-tiering.md#L83) defaults to Anthropic from a Claude profile. Apply that legacy default only in confirmed native Claude sessions; otherwise record **unknown** and use measured capabilities.

No vendor-specific claims about Qwen/Kimi/current aliases/context/effort/prices are verified here. This draft is generic operating policy, not a claim about any vendor's training or temperament.

## Establish model, host, installation and authority separately

Record provider/endpoint, requested and routed model ID, host/version, exposed tools, context/output limit if known, price/quota source/date, permitted actions and budget. Omit secrets. Unknown fields remain null, not plausible guesses. A proxy may fail over; requested model is not proof of actual serving model. Check `/v1/models` and response routing headers when the approved proxy supports them ([use-freellmapi:33–44](../../../../skills/workflows/use-freellmapi/SKILL.md#L33)).

Probe no-cost tools first. One bounded paid inference/tool round-trip test is optional **after approval**, not automatic bootstrap. If cost telemetry is absent, allow only attended bounded calls with a conservative user-approved ceiling; refuse unattended recurring execution.

## Portable prompt format

Use short, ordered sections:

1. Goal and user-visible acceptance criteria.
2. Read-only context/actual source paths needed now.
3. Allowed files/actions and explicit prohibited side effects.
4. Next small task, exact output shape and verifier command.
5. Missing-capability fallback and stop conditions.

Examples should demonstrate a real confusing boundary: source shared layout versus repeated generated HTML, immutable verifier versus changed implementation. Use one example when needed, not all references at startup. XML or Markdown are delimiters, not capabilities. Avoid all-caps repetition unless eval shows it prevents a concrete miss. Preserve mandatory safety/ownership/consent rules in every compressed packet.

## Small-context and weaker-instruction-following path

- Retrieve metadata → active body → one necessary reference; don't concatenate the whole library.
- Process one role/task per pass; maintain durable JSON state and a compact handoff: mission, immutable criteria, contract version, source revision/diff, evidence, blockers, pending human decision, next action, budget.
- Checkpoint before tool-output bursts or estimated context pressure. A large advertised window is not a reliable working-set budget.
- Re-read relevant source/config on resume; invalidate reports after changed revision/contracts. Never trust a model summary's remembered numbers as exact evidence.
- Keep a stable shared prefix where caching is actually supported; do not assume every provider uses Anthropic cache billing.
- Use local deterministic scans/tests before another model call. Shrink output prose but retain errors, observations and unresolved risk.

## Tool and thinking compatibility

Tool requests are structured data validated against exposed schemas. Never emit a nonexistent tool and call it complete. On a schema failure, return the actual error and supported shape; allow one bounded correction, then stop. Model reasoning mode, output-format mode and effort parameters are endpoint-specific: omit unsupported knobs instead of blindly translating `xhigh`.

Opaque continuation items from vendor SDKs stay opaque and intact. Do not narrate or request hidden chain of thought. A concise decision rationale and executed evidence are enough. Refusal/unavailable tool/quota failure are distinct blocked outcomes; do not route around safety policy just to get a response.

## Conservative quality and cost ladder

1. **No model:** scripts, catalog, linters, tests and syntax validators.
2. **Cheapest approved candidate:** mechanical scoped tasks with deterministic proof.
3. **Measured implementation candidate:** larger context/tool tasks that cheaper candidate failed on a held-out case.
4. **Independent reviewer:** clean session and calibrated rubric; high tier only where it improves accepted results.
5. **Human:** consequential ambiguity, security authority, migration/deploy or unavailable independent proof.

Escalate only after recording failure evidence; cap retries and spend. Single-provider default stays intact. Cross-provider reviewer needs explicit allowed-provider/privacy/budget opt-in; unknown price is not cheap. Read [tiering proposal](cross-vendor-tiering.md).

## Default refusal boundaries

Refuse unattended mode without externally enforced call/runtime/cost limits, scoped permission, a real termination verifier and no-progress detection. Refuse subjective completion from the builder grading itself. UI claims require observed render/interaction or explicitly human-supplied evidence. Missing services/login/browser means BLOCKED/NOT RUN, not inferred PASS. Never publish, install globally, overwrite permissions, commit, push, deploy, or move ledger items merely because a skill's broad trigger fired.

## Audit additions and image proxy

For every unknown-model run capture skill hash, adapter, tools actually used, proof outputs, costs/quotas, interventions and failure categories. Triggering and efficacy remain UNVERIFIED until measured. No unknown model is on the image-proxy allowlist; byte-exact material remains text.

## Consumer wiring

This is the default model reference after provider lookup returns unknown. It composes with the same host-neutral frontend/role/core doctrine, not a new skill fork. Native Claude paths retain their richer mechanisms. Model identity becoming known mid-run updates the adapter without silently changing authority or invalidating privacy policy.
