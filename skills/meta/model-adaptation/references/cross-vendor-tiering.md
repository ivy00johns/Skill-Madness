# Cost-aware cross-vendor routing

Single-provider execution remains default. MT-1 cheap-worker/strong-reasoning and
MA-2 strong-optimizer/cheap-target doctrine remain intact; this is an approved
exception, not an autonomous provider router.

## Consent before routing

Record the owner's explicit approval (date/run/scope), allowed providers AND endpoints,
data classification, permitted egress, reviewer packet fields, call/iteration/runtime
ceilings, and monetary cap or subscription quota reservation. A skill trigger, free
price label, profile boolean or broad code-edit request is not consent. Refusals,
quota failure and unavailable tools are blocked outcomes, not permission to vendor-hop.
FreeLLMAPI's aggregation also requires approved egress; pin or record the actual route.

```yaml
provider_policy:
  cross_provider: disabled
  allowed_providers: []
  allowed_endpoints: []
  data_classification: private-repo
  egress_approved: false
  approval_record: null
run_limits:
  max_calls: null
  max_runtime_seconds: null
  max_cost_usd: null
  quota_reservation: null
```

This is a declaration shape, not installed defaults or enforcement. Missing approval,
unknown price or null ceilings never mean unlimited. An unattended metered job is
unavailable unless an external controller can reserve and enforce monetary liability.
Subscriptions/free tiers use measured quota, turns and time, not invented dollar conversion.

## Cheapest eligible measured candidate

Run local scripts/tests first. Use one approved scoped worker; escalate only after
recorded failure evidence and within agreed retries. A separate read-only reviewer
gets only necessary artifact/diff, frozen acceptance criteria and executed verifier
receipts. Different providers do not establish independence if builder history leaks.
Model names/family labels never prove current price, tool support or reviewer quality.

## Reservations and accounting

Reserve worst-case input/cache/reasoning/output/tool/host cost plus retry margin before
launch. Remaining budget equals approved ceiling minus actual spend and outstanding
reservations. Persist reservations across restarts/retries and use locks to prevent
concurrent double-spending. Account returned usage, conservatively handle delayed
telemetry, cancel at calls/time/spend caps and refuse dispatch without sufficient
reservation. Model self-reports and `/cost` watchers are not enforcement.

Record total spend across failed attempts and **cost per accepted result** separately
from Outcome, Proof and Architecture. Acceptance requires all three, never a blended
cost score. Zero accepted results means cost-per-accepted-result is undefined, not zero;
unknown spend stays null. Report calls, latency, retries and reviewer interventions as
trajectory diagnostics. Cheap failed runs are not savings.
