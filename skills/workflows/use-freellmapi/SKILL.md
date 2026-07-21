---
name: use-freellmapi
version: 1.2.0
description: |
  Wire any project to FreeLLMAPI — a local OpenAI-compatible proxy that aggregates ~20 free LLM provider
  tiers (~1.7B+ tokens/month) behind one endpoint — so you can prototype without paying for API calls.
  Use when a user wants to switch a project off paid OpenAI/Anthropic/etc. onto free models, point an app
  at a local LLM proxy, cut their LLM bill for prototyping, or stand up FreeLLMAPI itself. Detects the
  project's current LLM client (OpenAI or Anthropic SDK, LangChain, LlamaIndex, Vercel AI SDK, Continue,
  raw HTTP), ensures the proxy is running (installs it if missing), rewires base_url + api_key behind an
  env toggle so you can flip back, and verifies with a live test call. Trigger on "use the free llm api",
  "use freellmapi", "switch this to free models", "point this at freellmapi", "stop paying for openai
  here", "free llm proxy", "prototype without api costs", "configure this for the free llm api".
requires_agent_teams: false
requires_claude_code: false
min_plan: starter
owns:
  directories: []
  patterns: []
  shared_read: ["*"]
allowed-tools: ["Read", "Write", "Edit", "Bash", "Grep", "Glob"]
composes_with: ["project-profiler", "model-adaptation"]
spawned_by: []
---

# use-freellmapi

Point a project at **FreeLLMAPI** — a local proxy that aggregates the free tiers of ~20 LLM providers
(Google, Groq, Cerebras, NVIDIA, Mistral, OpenRouter, GitHub Models, Cohere, Cloudflare, HuggingFace,
Z.ai, Ollama, Kilo, Pollinations, LLM7, OVH, OpenCode Zen, AI Horde, and more — the exact roster shifts
as providers come and go and the model catalog self-updates) behind a single OpenAI-compatible endpoint.
A router picks the best available model per request and fails over when one is rate-limited. The payoff:
prototype against real models for free, with zero code changes beyond a base URL and a key.

> **Tiering note:** a FreeLLMAPI project is the toolkit's one sanctioned multi-provider setup. The
> model & effort tiering policy (`model-adaptation`, *Model & effort tiering*) is provider-relative —
> within a normal build you pick tiers inside ONE provider's ladder and never mix vendors to save
> tokens — and FreeLLMAPI is its explicit carve-out: here the aggregated free tiers ARE the ladder,
> and the scarce resource is rate/quota headroom, not dollars.

## The whole integration, in three facts

FreeLLMAPI is an **OpenAI-compatible** proxy. Wiring a project to it is almost always just three values:

| What | Value |
| --- | --- |
| **base_url** | `http://localhost:3001/v1` (default; `PORT` may differ) |
| **api_key** (bearer) | `freellmapi-…` — the proxy's single *unified key* |
| **model** | `"auto"` — let the router pick and fail over; pin one like `"gemini-2.5-flash"`; or `"fusion"` to blend a panel of models into one answer |

Because the surface is OpenAI-compatible, any OpenAI client library works unchanged — chat, streaming,
tool calling, vision, and embeddings all route through the same endpoint. The proxy also accepts the
**Anthropic-style `x-api-key` header**, so Anthropic SDK clients can point at it too (use the unified
key as the `x-api-key`). Everything past this point is about doing the swap *cleanly, reversibly, and
verified* — not about anything exotic.

> Read `references/capabilities.md` for the exact supported surface (endpoints, the two virtual models
> `auto` and `fusion`, embeddings families, vision, tools, structured outputs, image generation + TTS,
> the `/mcp` server, the opt-in response cache) and the short list of things it still does **not** do
> (legacy `/v1/completions`, moderation, `n > 1`). Check it before promising a capability.

## Workflow

Work top to bottom. Steps 1–2 stand up the proxy and confirm it can actually serve a request; steps
3–5 rewire the project and prove it works end to end. Don't skip the verify — "it should work" is not
the same as a 200 with a completion in it.

### Step 1 — Make sure the proxy is running

Probe the unauthenticated liveness endpoint:

```bash
curl -fsS http://localhost:3001/api/ping
# {"status":"ok","timestamp":"..."}  → running, go to Step 2
```

If nothing answers, install and start it with the official one-liner (needs Docker running):

```bash
curl -fsSL https://tashfeenahmed.github.io/freellmapi/install.sh | bash
```

This sets up `~/freellmapi`, generates an at-rest `ENCRYPTION_KEY`, pulls
`ghcr.io/tashfeenahmed/freellmapi:latest`, starts the container on `:3001`, and waits for `/api/ping`.
Re-running is safe — it preserves the existing `.env`. When it finishes, probe `/api/ping` again to
confirm. If Docker isn't available, fall back to a source install (`git clone` + `npm install` +
`npm run dev`); see the repo README's *Local development* section.

If the user already runs it on a non-default port or another host, use that `base_url` everywhere below.

### Step 2 — Get the unified key and make sure a provider can serve requests

**Unified key** (`freellmapi-…`): the single bearer token your app uses. Get it from:

- the **Keys page header** at `http://localhost:3001` (the dashboard), or
- the first-run container logs:
  `cd ~/freellmapi && docker compose logs 2>&1 | grep -i "unified api key"`

**A fresh proxy has no provider keys, so chat requests fail until at least one provider is enabled.**
This is the one part you can't do for the user — adding keys and toggling providers happens in the
browser dashboard. Make it explicit and offer to wait. Two paths:

- **Fastest, zero-key smoke test:** on the dashboard, enable a **keyless** provider — Pollinations
  (GPT-OSS 20B), Kilo `:free`, or OVH work with no API key at all. Good enough to prove the pipe end to
  end in under a minute.
- **Real prototyping:** add free provider keys on the **Keys** page (Google AI Studio, Groq, Cerebras,
  etc. — each has a free signup), then reorder the **Fallback Chain** to taste.

Hold here until the user confirms at least one provider is enabled — otherwise Step 5 will fail with a
"no model available" error and look like a wiring bug when it isn't.

### Step 3 — Detect the project's current LLM wiring

Find how the project talks to an LLM today so you pick the right recipe and the smallest diff:

```bash
# language + client library + where the client is built
# (quote the --include globs — zsh expands bare *.py before grep sees it and the command fails)
grep -rniE "openai|anthropic|langchain|llama_?index|@?ai-sdk|base_?url|api_?key" \
  --include="*.py" --include="*.ts" --include="*.tsx" --include="*.js" --include="*.mjs" . \
  | grep -viE "node_modules|/dist/|/build/" | head -40
```

Determine: the language (Python / JS-TS), the client library, the file(s) where the client is
constructed, and where its `base_url` / `api_key` / `model` come from (env vars vs hardcoded). Then open
`references/recipes.md` and read **only the section for the detected stack** — it has copy-paste wiring
for OpenAI (Python/Node), LangChain, LlamaIndex, Vercel AI SDK, Continue, raw HTTP/curl, and the
Anthropic-SDK-via-`x-api-key` case.

### Step 4 — Rewire it, reversibly (the env-toggle pattern)

The point of prototyping with free models is that you'll flip *back and forth* — free models for cheap
iteration, the paid provider for a quality check or a demo. A hardcoded swap forces a code edit every
time and risks losing the original config. So **drive the three values from environment variables and
keep the original provider as a documented fallback**, rather than editing call sites.

Concretely:

1. Introduce (or reuse) env vars for the base URL, key, and model. Many OpenAI clients already read
   `OPENAI_BASE_URL` / `OPENAI_API_KEY` from the environment, so reusing those names is ideal. But "no
   code change at all" only holds when **both** are true: (a) the client is built with no explicit
   `base_url`/`api_key` args, **and** (b) something actually loads `.env` into the process — a shell
   `set -a; source .env`, a process manager's `env_file`, or a dotenv loader the app already calls.
   Plain Python and plain Node do **not** auto-read a `.env` file. If neither is true (very common — a
   prototype with the key hardcoded, and no dotenv), you will edit the call site and/or add a loader;
   that's expected, not a failure. Each recipe in `references/recipes.md` notes how its stack loads env.
2. Point the client constructor at those env vars instead of literals (only if it wasn't already).
3. In `.env`, set them to the FreeLLMAPI values and **keep the original provider's values commented
   right above them**, labeled, so flipping back is uncommenting two lines:

   ```dotenv
   # --- FreeLLMAPI (free, local proxy) — active ---
   OPENAI_BASE_URL=http://localhost:3001/v1
   OPENAI_API_KEY=freellmapi-xxxxxxxxxxxxxxxxxxxxxxxx
   LLM_MODEL=auto

   # --- Original provider (paid) — flip back by swapping which block is active ---
   # OPENAI_BASE_URL=https://api.openai.com/v1
   # OPENAI_API_KEY=sk-...
   # LLM_MODEL=gpt-4o-mini
   ```

4. Default the model to `"auto"` so the router chooses and fails over, but keep the option to pin a
   specific model where a call needs a known capability (e.g. a vision model).
5. Write or update a committed **`.env.example`** with the same two labeled blocks but placeholder
   values (`freellmapi-xxxx`, `sk-...`). Without it, moving a hardcoded key into `.env` leaves the repo
   with no record of which env vars it now needs — the example is the documentation.

Show the user the `.env` block and the (usually tiny) code diff. Never write a real provider key into a
file that's tracked by git — confirm `.env` is gitignored, and if a key was previously hardcoded in
source, move it to `.env` as part of this step.

### Step 5 — Verify with a live call

Prove the pipe works before declaring success. First a direct smoke test (substitute the real key):

```bash
curl -i -s http://localhost:3001/v1/chat/completions \
  -H "Authorization: Bearer freellmapi-xxxx" \
  -H "Content-Type: application/json" \
  -d '{"model":"auto","messages":[{"role":"user","content":"Reply with the single word: ok"}]}'
```

A healthy response is a `200` with a chat completion, and an **`X-Routed-Via: <platform>/<model>`**
header telling you which provider actually served it. Then run the **project's own** code path (its
test, its entry script, a representative call) so you've confirmed the app — not just curl — talks to
the proxy.

Map failures to causes instead of guessing:

| Symptom | Cause | Fix |
| --- | --- | --- |
| `401` invalid API key | wrong/missing unified key | re-copy it from the dashboard Keys header |
| `4xx` no model / no provider | no provider enabled on the proxy | back to Step 2 — enable a provider |
| `429` | the picked key is rate-limited | router fails over; add more provider keys for headroom |
| connection refused | proxy not running / wrong port | back to Step 1; check `PORT` |

### Step 6 — Hand off

Tell the user, briefly: how to flip back (uncomment the original `.env` block), where the dashboard is
(`http://localhost:3001` — manage keys, reorder the fallback chain or save named **routing profiles**
that auto-sort by intelligence/speed/budget, watch analytics, use the playground), what `model:"auto"`
does, that `model:"fusion"` blends a panel of models for a quality bump on hard prompts, and the
relevant **not-supported** caveats from `references/capabilities.md` if their project uses legacy
completions, moderation, or `n > 1` (those won't route — they'll need the real provider for those
calls). Image generation and text-to-speech now *do* route on current releases (a media-capable
provider must be enabled on the dashboard).

## References

- **`references/recipes.md`** — per-framework, copy-paste env-toggle wiring. Read the one section that
  matches the detected stack; ignore the rest.
- **`references/capabilities.md`** — exact supported surface (chat, streaming, tools, vision,
  structured outputs, embeddings + their families, the Responses API shim, image/audio media, the
  `/mcp` server, the opt-in response cache), plus the not-supported list and gotchas (sticky sessions,
  fresh-install-has-no-keys, anonymous providers, the `X-Routed-Via` / `X-Fallback-Trail` headers).
