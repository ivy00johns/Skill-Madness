# Cost-aware cross-vendor tiering — policy draft

## Preserve the current doctrine, extend its policy surface

[Model-effort-tiering:49–106](../../../../skills/meta/model-adaptation/references/model-effort-tiering.md#L49) already implements cheap worker / strong reasoning gate and strong optimizer / cheap deployed target. **MT1 and MA2 are closed work, not missing skills.** [Completed ledger:124–143](../../../../docs/COMPLETED-WORK.md#L124) records these closures. FreeLLMAPI is explicitly the aggregating exception; ordinary builds stay within one provider. This draft retains that default and proposes an explicit approved exception, not silent model-router vendor hopping.

## Policy before price

A run policy declares allowed providers/endpoints, data classification, allowed egress, maximum dollars or quota reservation, deadline, maximum calls/iterations, desired independent-review quality, and whether cross-provider review is authorized. User controls this policy. “Cheapest” means cheapest **eligible measured candidate**, not cheapest advertised tokens or any free endpoint.

```yaml
provider_policy:
  default: current-confirmed-provider
  cross_provider: disabled
  allowed_providers: []
  data_classification: private-repo
run_limits:
  max_calls: 8
  max_runtime_seconds: 900
  max_cost_usd: null  # user sets before a metered unattended run
  quota_reservation: null
quality:
  mechanical_verifier: required
  subjective_review: independent-context
```

Illustrative limits only, not defaults installed or sufficient for all tasks. A null monetary cap must not mean unlimited; if price telemetry cannot enforce it, unattended metered mode is unavailable. Subscriptions need quota/turn/time budgets, not fake dollar conversion.

## Cross-vendor ladder

| Stage | Anthropic | OpenAI/GPT | Gemini | DeepSeek / Qwen / Kimi / local / proxy | Gate before promotion |
|---|---|---|---|---|---|
| Zero-cost local | Same scripts/tests/scanners for all providers | Same | Same | Same | Deterministic tool status and artifact closure |
| Mechanical/free | Eligible cheap family in actual catalog | Available low-cost candidate; official Codex docs name Luna for lighter work | Eligible Flash-like candidate after API check | FreeLLMAPI live routed model or approved local/free candidate | Tool/format handling, deterministic outcome, privacy/quotas |
| Standard implementation | Eligible mid tier; native CC retained | Lowest-cost candidate meeting task benchmark | Lowest-cost eligible candidate meeting benchmark | Provider-relative cheap/medium candidate meeting benchmark | Outcome + proof + architecture at fixed task/context |
| Consequential reasoning | Strong approved candidate when needed | Official Sol demanding-work example; actual account/effort probe | Strong eligible candidate, documented thinking controls | Strong in-provider candidate; unknown families no fixed map | Calibrated reviewer/contract quality, cost reservation |
| Final independent review | Separate read-only context; not automatically maximum effort | Same; Codex child or independent session | Same; CLI child or independent session | Same; optional approved second provider | Frozen rubric/artifacts, real verifier, human if ambiguous |
| Strong optimizer once | Author/optimize skill under approved stronger tier | Same | Same | Same | Dev selection; untouched final holdout; cheap-target efficacy |

Model family labels are examples, not pinned fresh price tables. [Official GPT host docs](https://learn.chatgpt.com/docs/agent-configuration/subagents) and [Gemini thinking docs](https://ai.google.dev/gemini-api/docs/thinking) verify the names/controls discussed in sibling drafts, but **exact current per-model prices and cross-vendor ranking are UNVERIFIED**. Existing Anthropic/DeepSeek numbers have their own older verification dates; this audit did not refresh those prices. Do not quote July/August numbers as October verified prices.

## Low-budget operating default (proposal)

Run local checks first. Use one cheap scoped worker, then one clean reviewer only when acceptance has subjective or high-consequence clauses. Avoid ten-agent fan-out by default. A stronger reviewer is not a reason to send the entire private repository to an unapproved provider. Escalate after one recorded capability failure, then at most the agreed bounded retries. A larger model may be cheaper per accepted result if it avoids repeated broken builds; measure rather than infer.

A solo frontend task should not require a premium architecture model merely to get mobile-first/shared-shell discipline. The portable role body and deterministic gates are the cheapest leverage. Keep strong optimizer work amortized across future runs, but eval must exercise the cheap execution target.

## Accounting and enforcement

Estimated reserved cost per call:

```text
reservation = worst_case_input_charge + maximum_output_and_thinking_charge
              + tool_and_host_charge + retry_margin
remaining = approved_run_budget - actual_spend - outstanding_reservations
```

Use provider-specific cached input/cache creation/reasoning/output units, subscription quotas, and external tool fees. Unknown unit price requires fresh authoritative lookup or a conservative agreed maximum. Cache-hit input can dominate economics; one provider's output/input ratio must not become a universal law.

Controller reserves before launch, rejects insufficient remaining budget, accounts returned usage, and cancels at calls/time/spend cap. A model self-report or `/cost` watcher is not enforcement. Persist reservations across retries/restarts and prevent concurrent jobs double-spending. Provider usage delivery may be delayed; conservative reservations prevent overshoot. Free requests still consume quota, time, privacy and human attention.

Record **cost per accepted result** and separate Outcome, Proof, Architecture from trajectory diagnostics (tokens, latency, retries, reviewer interventions). A cheaper failed run is not better. Never average security/contract failure into a pleasant cost score.

## FreeLLMAPI and fallback

[use-freellmapi:33–44](../../../../skills/workflows/use-freellmapi/SKILL.md#L33) already says not to trust static provider roster/counts. Query the approved live catalog, prove a real tool-capable request, record routed model/headers, respect data policy and rate/quota limits. `auto` and failover complicate reproducible eval; pin or record actual route, and reject treatment/baseline runs served by different unknown models.

Do not treat the app-only contrast in [use-pxpipe:43](../../../../skills/workflows/use-pxpipe/SKILL.md#L43) as truth about FreeLLMAPI: its actual skill explicitly supports coding agents too. Correct the sibling description rather than creating another model-routing skill.

## Approval path and image compression

Cross-provider mode is optional: owner names approved providers and budget; resolver validates tools/privacy; separate reviewer packet contains only required artifacts; results state actual providers. Without approval, stay single-provider. This is a policy extension UA-16, not a rewrite of closed MT1.

Image proxy remains measured allowlist only. Token savings do not prove semantic fidelity, and API price/caching can make compression uneconomical. Exact IDs/hashes/secrets/numbers stay text; lossless scoped retrieval is preferred on a budget.
