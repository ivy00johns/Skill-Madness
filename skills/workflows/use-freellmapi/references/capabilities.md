# FreeLLMAPI capabilities & gotchas

What the proxy can serve, what it can't, and the behaviors that surprise people. Check this before
promising a project a capability — if the project's LLM calls need something on the **not-supported**
list, those specific calls won't route through the proxy and still need the real provider.

## Supported endpoints

The proxy speaks **six wire formats** over one router. For wiring a specific client to a non-OpenAI
surface, see `agent-clients.md` — this table is the inventory.

### OpenAI surface (`/v1`)

| Endpoint | Notes |
| --- | --- |
| `POST /v1/chat/completions` | The main surface. Streaming + non-streaming. |
| `POST /v1/responses` | OpenAI **Responses API** shim (the wire format Codex CLI needs). Image *input* not supported here yet — use chat completions for vision. |
| `POST /v1/completions` | **Legacy** prompt/suffix completions, routed through chat models while preserving the `text_completion` shape. Exists for editor ghost-text (Continue autocomplete). |
| `POST /v1/embeddings` | Family-based routing (see below). |
| `POST /v1/images/generations` | Image generation — dashboard **Models → Image** tab. |
| `POST /v1/audio/speech` | Text-to-speech — dashboard **Models → Audio** tab. |
| `POST /v1/audio/transcriptions` | Speech-to-text, catalog-driven. |
| `GET  /v1/models` | Lists available models. Content-negotiated: returns the **Anthropic** shape when `anthropic-version` is sent. |

### Other wire formats

| Endpoint | Notes |
| --- | --- |
| `POST /v1/messages` | **Anthropic Messages API** — native wire format, so Claude Code and the Anthropic SDKs run against the free pool. Clients must target the **origin**, not `/v1`. |
| `POST /v1/messages/count_tokens` | Anthropic token counting. |
| `/v1beta/models/{model}:generateContent` | **Native Gemini API** — plus `:streamGenerateContent` (`?alt=sse`), `:countTokens`, `GET /v1beta/models`, `GET /v1beta/models/{model}`. |
| `/api/{tags,chat,generate,show,version,embed,embeddings}` | **Ollama emulation**, NDJSON streaming. **Off by default** — enable `open-loopback` or `key-required` on the Agents page. |
| `/v1/t/{token}/…` | **Revocable URL tokens** for headerless clients — mirrors models, chat completions, Responses, and Ollama chat/tags. Separately revocable; not the unified key. |
| `POST /mcp` | **Model Context Protocol** (Streamable HTTP). Tools: `list_models`, `provider_health`, `usage_summary`, `routing_info`, `set_routing_strategy`, `cache_stats`, `compression_stats`. |

### Ops & discovery

| Endpoint | Notes |
| --- | --- |
| `GET /api/ping` | Unauthenticated liveness — `{"status":"ok"}`. |
| `GET /livez` · `GET /readyz` | Kubernetes-style liveness/readiness for meta-gateway interop. |
| `GET /v1/providers` | Provider inventory (unified-key auth); `?ready=true` filters to ones that can serve now. |
| `GET /v1/docs` · `GET /v1/openapi.json` | Dependency-free interactive OpenAPI viewer + the spec itself. Useful for confirming a capability on *this* install rather than trusting docs. |

**Auth:** three credential kinds unlock `/v1`, all accepted as `Authorization: Bearer <key>` or
`x-api-key: <key>` (Gemini's `x-goog-api-key` on `/v1beta`): the install-wide **unified key**
(`freellmapi-…`); **per-client keys** (`sk-cp-…`, minted on the Keys page since v0.6.9 — one per
downstream app or tool, independently revocable, each with an optional **server-enforced system
prompt** the proxy prepends to every request on that key); and revocable **URL tokens** for
headerless clients (see the endpoints table). Prefer one per-client key per wired project —
analytics attribute traffic by key, and revoking one doesn't rotate the others. The `/api/*`
dashboard routes use a separate email+password session and are not what apps talk to.

## Routing behavior

- **`model: "auto"`** (or omitting `model`) → the router scores enabled models and picks the best one
  that's under its rate caps, then **fails over** to the next in the fallback chain on a 429/5xx/timeout
  (up to ~20 attempts, bounded by a wall-clock retry budget). You can also pin a specific id like
  `gemini-2.5-flash`.
- **`auto:*` steering** — a suffix overrides the chain for one request, no dashboard change needed:
  `auto:smart` (highest intelligence), `auto:fast` (measured throughput + TTFB), `auto:reliable`
  (recent success rate), `auto:balanced` (the default blend), `auto:cheap` (currently the same blend as
  balanced — everything in the pool is already free). These rank **every enabled model**, ignoring
  chain order. Common synonyms resolve (`auto:fastest`, `auto:smartest`, `auto:budget`, …) and the
  whole string is case-insensitive. **`auto:<profile-name>`** routes through a named profile's chain
  instead, so different tools can use different chains through one key; an unknown profile is a clear
  `400`, not a silent fallback.
- **Six selectable strategies** rank the chain: `priority` (manual order), `balanced`, `smartest`,
  `fastest`, `reliable`, or `custom` weights — scored from live per-model measurements with a
  Thompson-sampling bandit. Community reliability priors seed the posterior so fresh installs don't
  start blind, and an **exploration toggle** controls whether unmeasured models get sampled.
  One-click sort presets reorder the chain from the dashboard.
- **Failing models cool down automatically.** Repeated failures put a model on a growing cooldown —
  not just 429s; hard errors extend the penalty too — and a 5xx/timeout/transport error skips the
  **whole provider** for that request instead of burning one attempt per key. A back-off stated in
  an error *body* is honored like a `Retry-After` header.
- **Output-token cap** — an optional server setting rescues requests whose client sends an excessive
  `max_tokens` (agent harnesses love `max_tokens: 128000`) by capping it to what the routed model
  accepts, instead of letting the provider reject the call.
- **Unified models** — the same logical model on several providers collapses into one entry with
  strict in-group failover, plus merge/split overrides when the grouping guesses wrong.
- **`X-Routed-Via: <platform>/<model>`** response header tells you which provider actually served the
  call; `X-Fallback-Attempts: N` appears if it fell over between providers, and `X-Fallback-Trail`
  carries the ordered list of what was tried. Opt in to **`X-Fallback-Detail`** for per-hop failover
  timings on top of the trail. Great for debugging "why is this answer weird" — check
  which model you actually got. On exhaustion, the error body carries the same full attempt trail.
  **Gotcha:** HTTP headers only carry printable ASCII, so a model id with characters outside that range
  (a Chinese name from a relay catalog) is **percent-encoded** — run the value through
  `decodeURIComponent` / `urllib.parse.unquote` before displaying it. `X-Request-ID` correlates a call
  with its row in dashboard analytics.
- **Sticky sessions:** a multi-turn conversation keeps hitting the same model for 30 minutes (avoids
  the hallucination spike from mid-conversation model switches). Agent harnesses that manage their own
  conversation ids can pin affinity with an `X-Session-Id` header.
- **Per-IP proxy rate limit:** default 120 req/min per client IP (`PROXY_RATE_LIMIT_RPM`, `0` disables).
- **`/v1/models` advertises context windows.** Each model — and `auto` itself (reporting the largest
  window among currently-available models) — carries `context_window` and `context_length`, so clients
  that size their input off the model list (Continue, some agent harnesses) stop truncating against a
  stale default.

## Virtual models

Two model ids aren't real models — they're router behaviors you select by name. Both show up in
`/v1/models` and are available whenever at least one routable model is connected.

- **`auto`** — the default. The router picks the best enabled model for the request and fails over down
  the fallback chain. Use it unless a call needs a specific capability (then pin an id).
- **`fusion`** — multi-model synthesis. The prompt fans out to a panel of *diverse* models in parallel,
  then a judge model blends their answers into one. The point: for a hard reasoning/writing prompt you
  get an answer better than any single free model, still for free. Invoke it like any model and tune it
  with an optional `fusion` object:

  ```json
  {
    "model": "fusion",
    "messages": [{"role": "user", "content": "..."}],
    "fusion": {
      "models": ["gemini-2.5-flash", "llama-3.3-70b"],
      "k": 4,
      "judge": "gemini-2.5-pro",
      "strategy": "synthesize",
      "expose_panel": true
    }
  }
  ```

  Every field is optional. `models` pins the panel (otherwise it auto-picks `k` diverse models, default
  4, hard max 8, one per platform first). `judge` pins the synthesizer (otherwise the top-ranked
  available model). `strategy` is `synthesize` (default, judge blends) or `best_of` (skip the judge,
  return the longest single panel answer — cheaper, no extra call). `expose_panel: true` attaches the
  per-model answers under `x_fusion`; a lightweight `_fusion` summary (which models + judge) is always
  included. Streaming works (it emits additive `_fusion` frames standard OpenAI clients ignore).
  **Tool calling works** — when the request carries `tools`, the panel is filtered to tool-capable
  models (models that can't are dropped with a reason) and the judge call runs without tools. Panel
  selection is also size-aware, so a model whose context is too small can't claim a slot.
  **Image input is still unsupported** — it returns a clear `422` (`fusion_no_vision`); pin a vision
  model directly for that.

## Tool calling

OpenAI-style `tools` / `tool_choice` pass through, and the full multi-step flow round-trips
(assistant `tool_calls` → `tool` role follow-up → final answer) across every provider the router
reaches. OpenAI-compatible providers get the request passed through; Gemini requests are translated to
Google's `functionDeclarations` shape and back. Works with `stream: true`. A Gemini-only extra: pass a
tool named `google_search` (aliases `googlesearch` / `google_search_retrieval`) and the proxy maps it to
Gemini's native Google Search grounding, so a Gemini route can answer with fresh web results.

Two argument-integrity behaviors ride along: the proxy **repairs double-encoded arguments** below the
top level (a model returning a JSON string where an object belongs), and an **opt-in schema verdict**
validates returned tool arguments against the tool's own JSON schema — an invalid set counts as a
failed attempt and **fails over to the next model** instead of handing the app broken arguments.

## Structured outputs & sampling params

`response_format` passes through — both `json_object` and full `json_schema` (schema-constrained
output, translated to Gemini's native `responseSchema` on Gemini routes). Extended sampling params ride
along too: `seed`, `top_k`, `min_p`, presence/frequency/repetition penalties, `logit_bias`, `logprobs`,
and the `max_completion_tokens` alias. Params a given provider is known to reject are **dropped
per-platform** rather than failing the call (Mistral's strict API, Groq's logprobs family, …), and each
model advertises its honest list in `/v1/models` under `supported_parameters`. If a structured-output
or sampling feature silently no-ops, check that field — the model you were routed to may not honor it.
When strict schema output matters, pin a model whose `supported_parameters` includes it rather than
leaving it to `auto`.

## Vision

Send images as standard OpenAI `image_url` content blocks (base64 `data:` URLs or `http(s)` URLs).
When a request contains an image, the router **restricts itself to vision-capable models** and ignores
text-only ones. If no vision model is enabled, the request returns a clear `422` (`code:
"no_vision_model"`) rather than dropping the image silently. Image input is **chat-completions only**,
not `/v1/responses`.

## Embeddings

`/v1/embeddings` is OpenAI-compatible with one deliberate rule: **failover never crosses models.**
Vectors from different models live in incompatible spaces, so embeddings route by **family** (one model
identity + dimension) and only fail over among providers serving that same family. Pick one family per
vector store and stick with it.

| Family (`model`) | Dims | Providers (failover order) |
| --- | --- | --- |
| `gemini-embedding-001` *(default)* | 3072 | Google |
| `text-embedding-3-large` | 3072 | GitHub Models |
| `llama-nemotron-embed-vl-1b-v2` *(vision-language)* | 2048 | NVIDIA → OpenRouter |
| `llama-nemotron-embed-1b-v2` | 2048 | NVIDIA |
| `text-embedding-3-small` | 1536 | GitHub Models |
| `embed-v4.0` *(disabled by default)* | 1536 | Cohere |
| `bge-m3` | 1024 | Cloudflare → Hugging Face |
| `qwen3-embedding-0.6b` | 1024 | Cloudflare |
| `nv-embedqa-e5-v5` | 1024 | NVIDIA |
| `embeddinggemma-300m` | 768 | Cloudflare |

`model` accepts `auto` (the configured default family — `gemini-embedding-001` out of the box), a family
name, or a provider-specific id (which resolves to its family). The default family and per-provider
toggles live on the dashboard's **Models → Embeddings** page. Worth flagging to the user: **`embed-v4.0`
(Cohere)** shares Cohere's tight 1K-calls/month chat quota, so spending it on embeddings is a real
trade-off — check whether it's enabled before recommending it. And `llama-nemotron-embed-vl-1b-v2` is a
**vision-language** family that can embed
images as well as text — the only multimodal embedder in the catalog. The proxy normalizes each
provider's native embedding quirks (NVIDIA's `input_type`, Cohere's `/v2/embed`, Hugging Face's
feature-extraction shape) behind the OpenAI request format, so the client just sends `{model, input}`.

## Media: image generation & text-to-speech

`POST /v1/images/generations` (image gen) and `POST /v1/audio/speech` (TTS) route across providers that
serve media models, including custom OpenAI-compatible media endpoints. Same **fresh-install-has-no-keys**
rule as chat: they do nothing until you enable a media-capable provider/model on the dashboard's
**Models → Image** / **Models → Audio** tabs. **Version-skew caveat:** these landed relatively recently,
so a container image pulled before that will `404` on those paths — if a media call 404s on an older
install, re-pull `:latest` (SKILL.md Step 1) and retry. Confirm the route exists before promising it to
a project that pins an old image.

## Prompt compression (opt-in)

Long agent sessions re-send system prompts, file reads, tool output, and schemas. The proxy can shrink
the request **before** cache lookup, token budgeting, and routing — so the router sees the reduced
estimate and more small-context models stay eligible. Responses are never rewritten. **Off by default.**
Runs on chat completions, Responses, Anthropic Messages, and Anthropic token counting.

| Mode | What runs |
| --- | --- |
| `off` | No rewriting. Master switch — a request header cannot enable it. |
| `lossless` | Repeated-block dedup, whitespace hygiene, reversible homogeneous-JSON table encoding. |
| `standard` | Lossless + command-aware tool-output filtering + stale file-read supersession. |
| `aggressive` | Standard + older-turn condensation, lexical relevance filtering, optional hard token target. |

Set it on the dashboard (**Settings → Prompt compression**) or bootstrap with
`FREELLMAPI_COMPRESSION=lossless`; once saved in the dashboard the stored value wins. Per request,
`X-FreeLLM-Compress: off|on|lossless|standard|aggressive` can **lower or disable** the operator's mode
but never raise it. The response reports what actually happened —
`X-FreeLLM-Compress: standard; saved~=1840` (the `~=` is honest: savings use the same `chars / 4`
estimate as routing).

The pipeline is **fail-open**: each engine's output is discarded if it grows the request, throws, or
fails a fidelity gate (all numeric literals and diff hunks survive, every explicit constraint / security
instruction / error line survives, ≥90% of JSON keys, ≥95% of other protected spans, tool envelopes stay
valid). Anthropic `cache_control` prefixes are capped at lossless. Compression config is part of the
response-cache fingerprint, so differently-compressed requests can't share a stale entry. Extra filters
load from `~/.freellmapi/filters/*.json`, and from `.freellmapi/filters.json` in-project **only** if
"Trust project filter files" is on (off by default — repos may be untrusted).

## Premium / catalog freshness

The router self-updates its model catalog from a signed feed twice a day — new models, quota changes,
and provider quirk fixes land without a `git pull`. **Free installs sit on a 30-day trail; the live
feed is a paid tier** ($19/yr). This is the answer to "why doesn't my install have model X" or "why am
I getting auth errors from a provider that changed its free tier" — it's catalog lag, not a wiring bug.
There's a **Premium** page in the dashboard and a `/api/premium` route family.

## Not supported yet

These have no route — calls to them fail, so the project still needs the real provider for them:

- **Moderation** (`/v1/moderations`)
- **`n > 1`** (multiple completions per request)
- **Per-user billing** — one operator per install, by design. (Per-client *keys* do exist — see
  Auth — but they attribute and constrain requests; there is no per-user quota or billing.)

Narrower gaps, not whole-endpoint: **image input on `/v1/responses`** (use chat completions) and
**image input to `fusion`** (pin a vision model).

*(Three things have come **off** this list and the skill used to state them wrongly: image generation,
text-to-speech, and **legacy `/v1/completions`** all route now, and **fusion supports tool calling**.
Verify against `GET /v1/docs` on the user's own install before telling them something won't work.)*

## Analytics & observability

The dashboard's **Analytics** page reports over 24h–90d windows: request count, success rate, **p50/p95
latency**, **time-to-first-token** for streams, token counts, **estimated cost savings** (priced against
each model's paid equivalent), and **pin-honor rate** (how often a pinned model actually served, vs. the
router falling over to something else — the number to check when someone says "I asked for model X and
got Y"). Breakdowns exist per model, platform, client, and key, plus an error distribution and
**per-request traces** (`GET /api/analytics/requests/:id`) showing the full failover ladder for one call.

Headline totals come from a durable hourly aggregate so they survive raw-row pruning; latency
percentiles, TTFT, and pin-honor need the raw rows and report **`null`** (rendered as a placeholder, not
a misleading `0`) once a window ages past the prune horizon. Cache and compression aggregates are also
readable over MCP (`usage_summary`, `cache_stats`, `compression_stats`) — useful for an agent that wants
to check its own quota burn mid-session.

## Gotchas worth saying out loud

- **A fresh proxy serves nothing until a provider is enabled.** No keys = every chat request 4xx's with
  "no model available." This looks exactly like a wiring bug but isn't. Add a provider first.
- **Keyless providers** — as of v0.6.9 the ones registered `keyless: true` are **Kilo `:free`**,
  **OVH**, and **AI Horde** (plus local Ollama). The proxy sends no auth header upstream, so enabling
  one is an instant zero-config smoke test. **Pollinations is no longer keyless** — it now validates a
  key against `/account/key`, so don't offer it as the zero-key path. AI Horde is queue-based and can
  take tens of seconds with no upstream streaming; fine for a smoke test, poor for interactive use.
  This roster shifts — confirm against the dashboard rather than trusting this list.
- **Free tiers are rate-limited and uneven.** Latency and quality vary by which provider served a call
  (`X-Routed-Via`). Add several provider keys so the router has headroom to fail over. This is a
  *prototyping* tool, not a production SLA.
- **The unified key is per-install**, stored in the proxy's SQLite, shown on the dashboard Keys header.
  Regenerating it on the dashboard invalidates the old one — update the app's `.env` if you do.
- **Provider keys are individually tunable.** A provider's keys can carry **model scopes** (different
  keys serve different model groups), a **per-key proxy override** (each key exits through its own
  proxy — geo-ban and risk isolation), and bulk enable/disable/delete within a group. Custom
  endpoints have an immediate-probe action to validate a key on the spot.
- **Opt-in response cache.** An exact-match in-memory LRU for identical *non-streaming* requests
  (canonical SHA-256 over the full request, with TTL + temperature gates). **Off by default**; flip it
  per-request with the `X-FreeLLM-Cache: on|off` header. Cache hits consume **zero provider quota** and
  show up in the dashboard's saved-token stats — handy for a test suite that replays the same prompts.
- **Localhost only by default.** The container binds `127.0.0.1`. To reach it from another device, start
  with `HOST_BIND=0.0.0.0` — only on a trusted LAN, since the proxy is single-user.
