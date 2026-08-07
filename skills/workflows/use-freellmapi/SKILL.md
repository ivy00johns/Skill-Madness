---
name: use-freellmapi
version: 1.3.0
description: |
  Wire any project or coding agent to FreeLLMAPI — a local proxy that aggregates ~29 free LLM provider
  tiers (~4B tokens/month across 251 model families) behind one endpoint — so you can prototype without
  paying for API calls. Use when a user wants to switch a project off paid OpenAI/Anthropic/etc. onto
  free models, point an app or CLI agent at a local LLM proxy, cut their LLM bill for prototyping, or
  stand up FreeLLMAPI itself. Speaks OpenAI, Anthropic Messages, native Gemini, and Ollama wire formats,
  so it also covers pointing Claude Code, Codex CLI, Gemini CLI, Cline, Aider, Continue, Zed, or
  JetBrains AI at free models. Detects the project's current LLM client (OpenAI or Anthropic SDK,
  LangChain, LlamaIndex, Vercel AI SDK, Continue, raw HTTP), ensures the proxy is running (installs it
  if missing), rewires base_url + api_key behind an env toggle so you can flip back, and verifies with a
  live test call. Trigger on "use the free llm api", "use freellmapi", "switch this to free models",
  "point this at freellmapi", "stop paying for openai here", "free llm proxy", "prototype without api
  costs", "configure this for the free llm api", "run claude code on free models", "point claude
  code/codex/gemini cli at freellmapi", "free models for my coding agent".
requires_agent_teams: false
requires_claude_code: false
min_plan: starter
owns:
  directories: []
  patterns: []
  shared_read: ["*"]
allowed-tools: ["Read", "Write", "Edit", "Bash", "Grep", "Glob"]
composes_with: ["project-profiler", "model-adaptation", "use-pxpipe"]
spawned_by: []
---

# use-freellmapi

Point a project at **FreeLLMAPI** — a local proxy that aggregates the free tiers of ~29 LLM providers
(Google, Groq, Cerebras, NVIDIA, Mistral, OpenRouter, GitHub Models, Cohere, Cloudflare, Z.ai,
ModelScope, Ollama, Kilo, OVH, AI Horde, and more) behind a single endpoint — roughly **4B tokens/month
across 251 model families / 358 endpoints**. A router picks the best available model per request and
fails over when one is rate-limited. The payoff: prototype against real models for free, with zero code
changes beyond a base URL and a key.

> **Don't hardcode the roster or the numbers into advice.** Providers come and go, the catalog
> self-updates from a signed feed, and free installs run on a 30-day catalog trail. Read the live
> `/v1/models` and the dashboard rather than trusting any list — including this one.

> **Tiering note:** a FreeLLMAPI project is the toolkit's one sanctioned multi-provider setup. The
> model & effort tiering policy (`model-adaptation`, *Model & effort tiering*) is provider-relative —
> within a normal build you pick tiers inside ONE provider's ladder and never mix vendors to save
> tokens — and FreeLLMAPI is its explicit carve-out: here the aggregated free tiers ARE the ladder,
> and the scarce resource is rate/quota headroom, not dollars.

## The whole integration, in three facts

FreeLLMAPI is an **OpenAI-compatible** proxy. Wiring a project to it is almost always just three values:

| What | Value |
| --- | --- |
| **base_url** | `http://localhost:3001/v1` (default; `PORT` may differ). **Anthropic, Gemini, and Ollama clients use the bare origin** — `http://localhost:3001`, no `/v1` |
| **api_key** (bearer) | `freellmapi-…` — the proxy's single *unified key* |
| **model** | `"auto"` — let the router pick and fail over. Steer it per request with `"auto:fast"` / `"auto:smart"` / `"auto:reliable"` / `"auto:<profile-name>"`; pin one like `"gemini-2.5-flash"`; or `"fusion"` to blend a panel of models into one answer |

Because the surface is OpenAI-compatible, any OpenAI client library works unchanged — chat, streaming,
tool calling, vision, and embeddings all route through the same endpoint. But it is **not only**
OpenAI-shaped: the proxy also speaks the **native Anthropic Messages API** (`/v1/messages` — Claude Code
and the Anthropic SDKs), the **native Gemini API** (`/v1beta` — Gemini CLI), and an opt-in **Ollama**
surface (`/api/*` — Zed, JetBrains AI). Point each client at the wire format it already speaks instead
of forcing everything through chat completions. Everything past this point is about doing the swap
*cleanly, reversibly, and verified* — not about anything exotic.

> Read `references/capabilities.md` for the exact supported surface (all six wire formats, the virtual
> models `auto`/`fusion` and `auto:*` steering, embeddings families, vision, tools, structured outputs,
> media, the `/mcp` server, prompt compression, the response cache, analytics) and the short list of
> things it still does **not** do (moderation, `n > 1`, multi-tenant auth). Check it before promising a
> capability — and when it matters, confirm against `GET /v1/docs` on the user's own install, since
> older pinned images lag the catalog.

## Workflow

Work top to bottom. Steps 1–2 stand up the proxy and confirm it can actually serve a request; steps
3–5 rewire the project and prove it works end to end. Don't skip the verify — "it should work" is not
the same as a 200 with a completion in it.

### Step 1 — Make sure the proxy is running

Probe the unauthenticated liveness endpoint:

```bash
curl -fsS http://localhost:3001/api/ping
# {"status":"ok","timestamp":"..."}  → something is answering, but see the check below
```

> **A 200 on `/api/ping` does not prove the *container* answered.** A stray host-side `npm run dev`
> from a source checkout binds `*:3001` on the IPv6 wildcard, which the OS prefers over the container's
> `127.0.0.1:3001` when resolving `localhost`. That dev server answers `/api/ping` happily but has no
> built client (`ENOENT … client/dist/index.html`, with a **host** path in the error) and its own empty
> database (a bogus "create an account" page) — which reads exactly like a wiped install after a
> rebuild. If the dashboard looks freshly-installed or errors on refresh, check who owns the port
> **before** touching any data:
>
> ```bash
> lsof -nP -iTCP:3001 -sTCP:LISTEN   # a `node` row next to `com.docker` is the bug
> ```
>
> Kill the `npm run dev` parent (not just the node child — `tsx watch` respawns it), then re-probe.
> Never reach for `docker compose down -v` to "reset" this; that is what actually destroys keys.

If nothing answers, install and start it with the official one-liner (needs Docker running):

```bash
curl -fsSL https://freellmapi.co/install.sh | bash
```

This sets up `~/freellmapi`, generates an at-rest `ENCRYPTION_KEY`, pulls
`ghcr.io/tashfeenahmed/freellmapi:latest`, starts the container on `:3001`, and waits for `/api/ping`.
Re-running is safe — it preserves the existing `.env`. When it finishes, probe `/api/ping` again to
confirm. If Docker isn't available, fall back to a source install (`git clone` + `npm install` +
`npm run dev`); see the *Local development* section of the [repo README](https://github.com/tashfeenahmed/freellmapi).

If the user already runs it on a non-default port or another host, use that `base_url` everywhere below.

### Step 2 — Get the unified key and make sure a provider can serve requests

**Unified key** (`freellmapi-…`): the single bearer token your app uses. Get it from:

- the **Keys page header** at `http://localhost:3001` (the dashboard), or
- the first-run container logs:
  `cd ~/freellmapi && docker compose logs 2>&1 | grep -i "unified api key"`

**A fresh proxy has no provider keys, so chat requests fail until at least one provider is enabled.**
This is the one part you can't do for the user — adding keys and toggling providers happens in the
browser dashboard. Make it explicit and offer to wait. Two paths:

- **Fastest, zero-key smoke test:** on the dashboard, enable a **keyless** provider — as of v0.6.5
  that's **Kilo `:free`**, **OVH**, or **AI Horde**, which need no API key at all. Good enough to prove
  the pipe end to end in under a minute. (**Pollinations is no longer keyless** — it validates a key
  now, so don't offer it as the zero-key path. AI Horde is queue-based and can take tens of seconds.)
- **Real prototyping:** add free provider keys on the **Keys** page (Google AI Studio, Groq, Cerebras,
  etc. — each has a free signup), then reorder the **Fallback Chain** to taste.

Hold here until the user confirms at least one provider is enabled — otherwise Step 5 will fail with a
"no model available" error and look like a wiring bug when it isn't.

### Step 3 — Detect the target: coding agent, or application code?

**First ask which kind of target this is — the two paths diverge completely.**

**If the target is a coding agent or CLI** (Claude Code, Codex, Gemini CLI, Cline, Aider, Continue,
OpenCode, Goose, Qwen, Roo, Kilo, Crush, Cursor, Zed, JetBrains AI) — **do not hand-edit its config.**
The proxy ships generators that read the live catalog, merge with existing config, and write a
timestamped backup first:

```bash
npx freellmapi setup-claude --url http://localhost:3001 --dry-run   # show the diff
npx freellmapi setup-claude --url http://localhost:3001             # apply, with backup
```

Read `references/agent-clients.md` for the full command table, the per-client base URLs, and the traps
that waste the most time (Claude Code needs the **origin** not `/v1`, and `ANTHROPIC_AUTH_TOKEN` **not**
`ANTHROPIC_API_KEY` or it refuses to start; Ollama emulation is off by default and `open-loopback`
doesn't work in Docker). Then skip to Step 5 and verify — Step 4's env-toggle pattern is for
application code, not agent config.

**If the target is application code**, continue here. Find how the project talks to an LLM today so you
pick the right recipe and the smallest diff:

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

Tell the user, briefly:

- **How to flip back** — uncomment the original `.env` block (or re-run the agent's own config backup).
- **Where the dashboard is** (`http://localhost:3001`) and what's on it: **Models** (Chat / Embeddings /
  Image / Audio / Fusion tabs, with editable intelligence-and-speed ranks and per-model rate limits),
  **Playground** (now accepts image and text-file attachments), **Keys**, **Agents** (per-tool setup
  blocks, Anthropic/Gemini family maps, Ollama emulation mode, URL tokens), **Analytics**, and
  **Premium**. Named **routing profiles** auto-sort a chain by intelligence/speed/budget and are
  selectable per request as `auto:<profile>`. Settings live in a sidebar dialog; the UI ships in 60
  languages.
- **What the model values do** — `auto` routes and fails over, `auto:fast` / `auto:smart` /
  `auto:reliable` steer one request without touching the dashboard, `fusion` blends a panel of models
  for a quality bump on hard prompts.
- **What analytics will tell them later** — p50/p95 latency, time-to-first-token, success rate,
  estimated savings, and **pin-honor rate** (the number that answers "I asked for model X, why did I get
  Y?"), plus per-request failover traces.
- **The relevant not-supported caveats** from `references/capabilities.md` — moderation, `n > 1`, and
  multi-tenant auth won't route, so those calls still need the real provider. Legacy
  `/v1/completions`, image generation, text-to-speech, and fusion tool-calling **do** work on current
  releases; only image *input* to `/v1/responses` and to `fusion` is still missing.
- **If the catalog looks stale** — free installs run on a 30-day catalog trail (the live signed feed is
  the paid tier), so a missing new model or a provider whose free tier changed is usually catalog lag,
  not a wiring bug.
- **Optionally, prompt compression** — off by default, but worth mentioning for long agent sessions:
  it shrinks re-sent context before routing so more small-context models stay eligible.

## References

- **`references/recipes.md`** — per-framework, copy-paste env-toggle wiring for **application code**.
  Read the one section that matches the detected stack; ignore the rest.
- **`references/agent-clients.md`** — wiring for **coding agents and CLIs**: the `npx freellmapi
  setup-*` generator table, Claude Code / Codex / Gemini CLI / Ollama-client / headerless setups, the
  MCP server, and the per-client traps. Read this whenever the target is a tool rather than a codebase.
- **`references/capabilities.md`** — exact supported surface across all six wire formats (chat,
  streaming, tools, vision, structured outputs, embeddings + families, Responses, legacy completions,
  media, transcription, Anthropic Messages, native Gemini, Ollama, `/mcp`, URL tokens, ops endpoints),
  plus routing behavior and `auto:*` steering, prompt compression, the response cache, analytics, the
  not-supported list, and the gotchas (sticky sessions, fresh-install-has-no-keys, which providers are
  actually keyless, catalog lag, the `X-Routed-Via` / `X-Fallback-Trail` / `X-Request-ID` headers and
  their percent-encoding trap).
