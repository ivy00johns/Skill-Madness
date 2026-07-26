# Verifying pxpipe is actually saving

Wiring the env var proves nothing. Two things must both be true before reporting success:
**compression fired** and **the prompt cache stayed warm**. This file gives the concrete checks,
what healthy looks like, and the failure signatures — all against the proxy's own telemetry, which
lands one flat JSON line per request in `~/.pxpipe/events.jsonl` (never raw text — only sizes,
counts, durations, and sha prefixes).

## Check 1 — compression fired

After at least two or three real harness turns:

```bash
tail -n 5 ~/.pxpipe/events.jsonl | grep -c "unsupported_model"
```

- `unsupported_model` on every recent row → the session's model is outside `PXPIPE_MODELS` scope.
  Either the model isn't on the `model-adaptation` allowlist (then stop — do not widen scope to
  force compression) or the scope env is mis-set.
- No rows at all → the harness isn't routing through the proxy; re-check `ANTHROPIC_BASE_URL` in
  the shell that launched Claude Code (a different terminal's export does not apply).
- Rows present, no compression, no `unsupported_model` → most often the profitability gate
  declining a session that is still too small (below the minimum collapsible history) or too
  sparse. That is correct behavior, not a bug: pxpipe only images where the token math wins.
  Long sessions compress more as history accumulates.

The dashboard (`http://127.0.0.1:47821/`) shows the same thing visually — compressed vs
passthrough requests, with skip reasons, plus previews of the actual rendered pages.

## Check 2 — the cache stayed warm (the −250% landmine)

The historical failure this check exists for: in an early upstream version (2026-05-19), the
history-collapse boundary moved by one message every turn, so the rendered PNGs — and therefore
the prompt-cache key — changed every turn. Every turn paid the `cache_create` rate (1.25×) on the
entire history instead of the `cache_read` rate (0.1×). Measured "savings": **−250%**. Upstream
fixed it with a quantized boundary (the collapse point advances in ~50-message jumps, so the
imaged prefix is byte-stable for long stretches — a staircase, not a ramp), but a wiring skill
must still verify warmth, because a cold cache silently converts the whole exercise into a cost
*increase*.

Warm looks like, across consecutive event rows for the same session:

- **`history_image_sha8` stable** — the imaged-history fingerprint should repeat turn after turn,
  stepping only occasionally (when the conversation crosses a collapse-grid line).

  ```bash
  tail -n 6 ~/.pxpipe/events.jsonl | grep -o '"history_image_sha8":"[a-f0-9]*"' | sort | uniq -c
  ```

  One dominant value = warm. A different value on every line = the boundary is churning.
- **`cache_read_tokens` dominating `cache_create_tokens`** after the first turn of a stretch. A
  `cache_create` spike on *every* turn is the regression signature.
- Occasional single `cache_create` steps are normal and paid for — that's the staircase.

Attribution when something looks cold: a changed prefix fingerprint means pxpipe serialized
different bytes (its problem); a stable fingerprint with a `cache_create` spike means upstream
cache eviction (not pxpipe's doing — e.g. a >5-minute gap between turns).

## Reading the savings numbers honestly

The dashboard's accounting is deliberately adversarial to its own product; read it the same way:

- **Savings are unfloored.** A turn where the image busted its own cache shows a *negative*
  saving. Negative session totals mean turn it off and investigate — the number is not noise.
- **Two percentages.** The input-only figure flatters; the total figure prices output on both
  sides (at its real ~5× rate) and answers "did this move the real bill". Quote the total figure
  to the user.
- **Rows the math refuses to credit** — passthrough rows, and rows whose free `count_tokens`
  baseline probe failed or half-resolved (`baseline_probe_status` of `failed`/`partial`) — count
  as zero saved by design, so caching alone can never masquerade as a pxpipe win.
- **`safety_flagged` rows** (refusal / content-filter stops) emit almost no output and would read
  as cheap; never count them as savings evidence. A *cluster* of them right after enabling the
  proxy is a signal the imaged prompt itself is tripping the classifier — turn it off and report.

## Kill-switch matrix

| Switch | Scope | Latency | Survives proxy restart? |
| --- | --- | --- | --- |
| `unset ANTHROPIC_BASE_URL` | This shell's sessions — hard off, proxy out of the path | Immediate (next session) | n/a |
| Dashboard passthrough toggle (`POST /api/compression`) | All traffic — proxy stays up, compression off | Immediate, no restart | No (in-memory) |
| `PXPIPE_DISABLE=1` | All traffic — same as the toggle, env-driven | Immediate (read live) | Yes, while set |
| `PXPIPE_MODELS=off` | Scope layer — every model unsupported | On restart / env re-read | Yes, while set |

Dashboard model-scope chips are in-memory only: a restart reverts to the `PXPIPE_MODELS` env or
the built-in default. Anything meant to persist must be in the environment.

## Security posture recap

- Loopback-only by default (`127.0.0.1`). The dashboard is **unauthenticated** and serves captured
  request context and a kill switch — never `HOST=0.0.0.0` on a shared machine.
- Telemetry rows contain sizes/counts/hashes, not raw text; 4xx error bodies are the one captured
  payload class (stored gzipped under `~/.pxpipe/`).
- Treat `~/.pxpipe/` as local operational data: it fingerprints sessions and working directories.
  Don't commit it, don't ship it in bug reports without a skim.
