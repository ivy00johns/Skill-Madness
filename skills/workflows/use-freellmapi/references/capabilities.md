# FreeLLMAPI capabilities & gotchas

What the proxy can serve, what it can't, and the behaviors that surprise people. Check this before
promising a project a capability — if the project's LLM calls need something on the **not-supported**
list, those specific calls won't route through the proxy and still need the real provider.

## Supported endpoints

| Endpoint | Notes |
| --- | --- |
| `POST /v1/chat/completions` | The main surface. Streaming + non-streaming. |
| `POST /v1/responses` | OpenAI **Responses API** shim (the wire format current Codex CLI needs), translated over the same router. Image *input* not supported here yet — use chat completions for vision. |
| `POST /v1/embeddings` | Family-based routing (see below). |
| `POST /v1/images/generations` | Image generation — routes to providers serving media models (see **Media** below). Enable one on the dashboard's **Models → Image** tab first. |
| `POST /v1/audio/speech` | Text-to-speech — same routing, dashboard **Models → Audio** tab. |
| `POST /mcp` | **Model Context Protocol** (Streamable HTTP). MCP-capable agents can ask the router which models are usable right now (with per-model `supported_parameters`), check provider/key health + cooldowns, read usage/cache stats, and switch routing strategy mid-session. |
| `GET  /v1/models` | Lists available models. |
| `GET  /api/ping` | Unauthenticated liveness — `{"status":"ok"}`. Use this to detect "is it running". |

**Auth:** every `/v1` call needs the unified key (`freellmapi-…`), accepted as either
`Authorization: Bearer <key>` or `x-api-key: <key>`. The `/api/*` dashboard routes use a separate
email+password session and are not what apps talk to.

## Routing behavior

- **`model: "auto"`** (or omitting `model`) → the router scores enabled models and picks the best one
  that's under its rate caps, then **fails over** to the next in the fallback chain on a 429/5xx/timeout
  (up to ~20 attempts). You can also pin a specific id like `gemini-2.5-flash`.
- **`X-Routed-Via: <platform>/<model>`** response header tells you which provider actually served the
  call; `X-Fallback-Attempts: N` appears if it fell over between providers, and `X-Fallback-Trail`
  carries the ordered list of what was tried. Great for debugging "why is this answer weird" — check
  which model you actually got. On exhaustion, the error body carries the same full attempt trail.
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
  **Fusion does not support image input or tool calling yet** — those return a clear `422`
  (`fusion_no_vision` / `fusion_no_tools`); use a vision/tool-capable model directly for those.

## Tool calling

OpenAI-style `tools` / `tool_choice` pass through, and the full multi-step flow round-trips
(assistant `tool_calls` → `tool` role follow-up → final answer) across every provider the router
reaches. OpenAI-compatible providers get the request passed through; Gemini requests are translated to
Google's `functionDeclarations` shape and back. Works with `stream: true`. A Gemini-only extra: pass a
tool named `google_search` (aliases `googlesearch` / `google_search_retrieval`) and the proxy maps it to
Gemini's native Google Search grounding, so a Gemini route can answer with fresh web results.

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
toggles live on the dashboard's **Models → Embeddings** page. Two things worth flagging to the user:
**`embed-v4.0` (Cohere) ships disabled** — it shares Cohere's tight 1K-calls/month chat quota, so enable
it deliberately. And `llama-nemotron-embed-vl-1b-v2` is a **vision-language** family that can embed
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

## Not supported yet

These have no route — calls to them fail, so the project still needs the real provider for them:

- **Legacy completions** (`/v1/completions`) — only the *chat* endpoint exists
- **Moderation** (`/v1/moderations`)
- **`n > 1`** (multiple completions per request)
- **Per-user billing / multi-tenant auth** — single-user by design

*(Image generation and text-to-speech used to be on this list — they now route; see **Media** above.)*

## Gotchas worth saying out loud

- **A fresh proxy serves nothing until a provider is enabled.** No keys = every chat request 4xx's with
  "no model available." This looks exactly like a wiring bug but isn't. Add a provider first.
- **Keyless providers** (Pollinations GPT-OSS 20B, Kilo `:free`, OVH) need no API key at all — the proxy
  sends no auth header upstream. Enable one on the dashboard for an instant zero-config smoke test.
  (LLM7 also has an anonymous free tier but isn't registered keyless — it may carry a shared key.)
- **Free tiers are rate-limited and uneven.** Latency and quality vary by which provider served a call
  (`X-Routed-Via`). Add several provider keys so the router has headroom to fail over. This is a
  *prototyping* tool, not a production SLA.
- **The unified key is per-install**, stored in the proxy's SQLite, shown on the dashboard Keys header.
  Regenerating it on the dashboard invalidates the old one — update the app's `.env` if you do.
- **Opt-in response cache.** An exact-match in-memory LRU for identical *non-streaming* requests
  (canonical SHA-256 over the full request, with TTL + temperature gates). **Off by default**; flip it
  per-request with the `X-FreeLLM-Cache: on|off` header. Cache hits consume **zero provider quota** and
  show up in the dashboard's saved-token stats — handy for a test suite that replays the same prompts.
- **Localhost only by default.** The container binds `127.0.0.1`. To reach it from another device, start
  with `HOST_BIND=0.0.0.0` — only on a trusted LAN, since the proxy is single-user.
