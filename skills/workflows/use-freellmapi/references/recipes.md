# Wiring recipes

Per-framework, env-toggle wiring for FreeLLMAPI. Read **only** the section matching the project's
detected stack. Every recipe uses three values from the environment so the swap is reversible (see
SKILL.md Step 4):

- `OPENAI_BASE_URL` → `http://localhost:3001/v1`
- `OPENAI_API_KEY` → `freellmapi-…` (the unified key)
- model → `auto` (router picks + fails over) or a pinned id

Anything not listed here still works via the same base-url swap — these are just the common cases.

## Contents

- [OpenAI Python SDK](#openai-python-sdk)
- [OpenAI Node / TypeScript SDK](#openai-node--typescript-sdk)
- [LangChain (Python)](#langchain-python)
- [LangChain (JS/TS)](#langchain-jsts)
- [LlamaIndex (Python)](#llamaindex-python)
- [Vercel AI SDK](#vercel-ai-sdk)
- [Continue (VS Code / JetBrains)](#continue-vs-code--jetbrains)
- [Raw HTTP / curl / fetch / requests](#raw-http--curl--fetch--requests)
- [Embeddings (vector stores / RAG)](#embeddings-vector-stores--rag)
- [Anthropic SDK via x-api-key](#anthropic-sdk-via-x-api-key)

---

## OpenAI Python SDK

The SDK already reads `OPENAI_BASE_URL` and `OPENAI_API_KEY` from the environment — **but only if
those vars are actually in the process environment.** Plain Python does not read a `.env` file on its
own. So "only the `.env`, no code change" holds when the app is started through something that injects
env (Docker `env_file`, a framework, or `set -a; source .env && python app.py`). For a standalone
script with no loader, add `python-dotenv` (one line) so the `.env` is honored:

```dotenv
OPENAI_BASE_URL=http://localhost:3001/v1
OPENAI_API_KEY=freellmapi-xxxx
LLM_MODEL=auto
```

```python
from dotenv import load_dotenv   # add `python-dotenv` to requirements
load_dotenv()                    # call once at startup, before constructing the client
```

If the client passes them explicitly, route through the env (and prefer `model=auto`):

```python
import os
from openai import OpenAI

client = OpenAI(
    base_url=os.environ["OPENAI_BASE_URL"],   # http://localhost:3001/v1
    api_key=os.environ["OPENAI_API_KEY"],     # freellmapi-...
)

resp = client.chat.completions.create(
    model=os.getenv("LLM_MODEL", "auto"),
    messages=[{"role": "user", "content": "..."}],
)
print("routed via:", resp.headers.get("x-routed-via"))   # which provider served it
```

Streaming, `tools`/`tool_choice`, and `image_url` content blocks all pass through unchanged.

## OpenAI Node / TypeScript SDK

Same idea — the SDK reads `OPENAI_BASE_URL` / `OPENAI_API_KEY` from `process.env`, **if they're loaded**.
Node doesn't read `.env` by default either: start with `node --env-file=.env app.js` (Node 20.6+), add
`import "dotenv/config";` at the top, or rely on your framework (Next.js loads `.env` automatically).

```ts
import OpenAI from "openai";

const client = new OpenAI({
  baseURL: process.env.OPENAI_BASE_URL,   // http://localhost:3001/v1
  apiKey: process.env.OPENAI_API_KEY,     // freellmapi-...
});

const resp = await client.chat.completions.create({
  model: process.env.LLM_MODEL ?? "auto",
  messages: [{ role: "user", content: "..." }],
});
```

## LangChain (Python)

`ChatOpenAI` honors `OPENAI_BASE_URL` / `OPENAI_API_KEY`, or pass `base_url` / `api_key` directly:

```python
import os
from langchain_openai import ChatOpenAI

llm = ChatOpenAI(
    base_url=os.environ["OPENAI_BASE_URL"],   # http://localhost:3001/v1
    api_key=os.environ["OPENAI_API_KEY"],     # freellmapi-...
    model=os.getenv("LLM_MODEL", "auto"),
)
```

For embeddings, use `OpenAIEmbeddings(base_url=..., api_key=..., model="auto")` — but pin **one**
embeddings family for a given vector store (see `capabilities.md` → Embeddings; failover never crosses
models, so vectors stay compatible).

## LangChain (JS/TS)

```ts
import { ChatOpenAI } from "@langchain/openai";

const llm = new ChatOpenAI({
  configuration: { baseURL: process.env.OPENAI_BASE_URL }, // http://localhost:3001/v1
  apiKey: process.env.OPENAI_API_KEY,                      // freellmapi-...
  model: process.env.LLM_MODEL ?? "auto",
});
```

Note the base URL goes inside `configuration` for the JS client.

## LlamaIndex (Python)

```python
import os
from llama_index.llms.openai import OpenAI

llm = OpenAI(
    api_base=os.environ["OPENAI_BASE_URL"],   # http://localhost:3001/v1  (note: api_base)
    api_key=os.environ["OPENAI_API_KEY"],     # freellmapi-...
    model=os.getenv("LLM_MODEL", "auto"),
)
```

LlamaIndex sometimes validates model names against a known list and may reject `auto` or a non-OpenAI
id with a context-window lookup error. The proxy now advertises `context_window`/`context_length` on
`/v1/models` (so most clients stop truncating), but LlamaIndex's *name* validation is a separate check —
if it still trips, pin a known OpenAI-shaped id the proxy serves (e.g. a GitHub Models `gpt-4o`) or pass
`context_window=...` explicitly to bypass the metadata lookup.

## Vercel AI SDK

Use the OpenAI-compatible provider factory so you control the base URL:

```ts
import { createOpenAI } from "@ai-sdk/openai";
import { generateText } from "ai";

const freellm = createOpenAI({
  baseURL: process.env.OPENAI_BASE_URL,   // http://localhost:3001/v1
  apiKey: process.env.OPENAI_API_KEY,     // freellmapi-...
});

const { text } = await generateText({
  model: freellm(process.env.LLM_MODEL ?? "auto"),
  prompt: "...",
});
```

`@ai-sdk/openai-compatible` works too; either way the only thing that matters is `baseURL` + `apiKey`.

## Continue (VS Code / JetBrains)

Edit `~/.continue/config.json` (or `config.yaml`) and add an OpenAI-compatible model entry:

```json
{
  "models": [
    {
      "title": "FreeLLMAPI (auto)",
      "provider": "openai",
      "model": "auto",
      "apiBase": "http://localhost:3001/v1",
      "apiKey": "freellmapi-xxxx"
    }
  ]
}
```

Keep the original model entry in the list — Continue lets you switch models from its dropdown, so both
the free proxy and the paid provider can coexist with no flipping required.

## Raw HTTP / curl / fetch / requests

If the project hand-rolls requests, change the URL, the `Authorization` header, and the `model` field.
Nothing else about the OpenAI request/response shape changes.

```bash
curl http://localhost:3001/v1/chat/completions \
  -H "Authorization: Bearer freellmapi-xxxx" \
  -H "Content-Type: application/json" \
  -d '{"model":"auto","messages":[{"role":"user","content":"hi"}]}'
```

Pull the base URL and key from env (`os.environ`, `process.env`) rather than inlining them, so the
env-toggle still applies.

## Embeddings (vector stores / RAG)

The same base-url swap routes `/v1/embeddings`, so any OpenAI-style embeddings client works unchanged.
The one rule that makes or breaks an embeddings swap: **failover never crosses embedding models** —
vectors from different models live in incompatible spaces. So the proxy routes embeddings by *family*
(one model identity + dimension) and only fails over among providers serving that same family. The
practical consequence for the project: **pick one family, write it down, and reuse it for every vector
that lands in the same store.** A store half-embedded with `gemini-embedding-001` (3072-dim) and half
with `bge-m3` (1024-dim) can't even be queried — the dimensions don't match. See `capabilities.md` →
Embeddings for the full family table.

The cleanest pattern is a dedicated env var for the embedding model, separate from the chat model, so
the family is pinned explicitly and never silently drifts to the default:

```dotenv
OPENAI_BASE_URL=http://localhost:3001/v1
OPENAI_API_KEY=freellmapi-xxxx
LLM_MODEL=auto                         # chat: let the router pick
EMBED_MODEL=gemini-embedding-001       # embeddings: pin ONE family for the whole store
```

**OpenAI Python SDK:**

```python
import os
from openai import OpenAI

client = OpenAI(
    base_url=os.environ["OPENAI_BASE_URL"],   # http://localhost:3001/v1
    api_key=os.environ["OPENAI_API_KEY"],     # freellmapi-...
)

resp = client.embeddings.create(
    model=os.getenv("EMBED_MODEL", "gemini-embedding-001"),  # pinned family, not "auto"
    input=["first chunk", "second chunk"],    # string or list of strings; batch when you can
)
vectors = [d.embedding for d in resp.data]
```

**OpenAI Node / TypeScript SDK:**

```ts
const resp = await client.embeddings.create({
  model: process.env.EMBED_MODEL ?? "gemini-embedding-001",
  input: ["first chunk", "second chunk"],
});
const vectors = resp.data.map(d => d.embedding);
```

**LangChain / LlamaIndex:** point `OpenAIEmbeddings(base_url=..., api_key=..., model="<family>")`
(LangChain) or the framework's embedding class at the same base URL and key, with the family pinned.

Notes that save a debugging session:

- **`auto` for embeddings resolves to the default family** (`gemini-embedding-001`). That's fine for a
  fresh store, but pinning the family explicitly is safer — if someone changes the dashboard default
  later, `auto` would start writing incompatible vectors into an existing store.
- **Match the family to the provider keys that are enabled.** `gemini-embedding-001` needs a Google
  key; `text-embedding-3-*` needs GitHub Models; `bge-m3` is keyless-ish via Cloudflare. If the chosen
  family's providers aren't enabled, the call 4xx's exactly like the fresh-install-no-keys case.
- **Re-embedding cost is real but free here** — if you must switch families, re-embed the *entire*
  store, don't mix. Being on a free proxy is what makes that bulk re-embed painless.
- **`llama-nemotron-embed-vl-1b-v2` can embed images too** (vision-language) — reach for it only if the
  store genuinely needs multimodal vectors; for plain text the default is simpler.

## Anthropic SDK via x-api-key

FreeLLMAPI's `/v1` surface also accepts the Anthropic-style `x-api-key` header — but it speaks the
**OpenAI** wire format, not Anthropic's `/v1/messages` schema. So:

- A client that just needs *an* LLM and was using the Anthropic SDK is cleanest to **switch to the
  OpenAI SDK** pointed at the proxy (use one of the recipes above). Pass the unified key; it's accepted
  via either `Authorization: Bearer` or `x-api-key`.
- The Anthropic Messages API shape (`/v1/messages`, `content` blocks, `system` top-level) is **not**
  translated by the proxy. Don't promise a drop-in Anthropic-SDK swap that keeps `/v1/messages`.

For Claude Code / Anthropic-wire agents specifically, routing tools (e.g. CC Switch) send the key as
`x-api-key`, which the proxy handles — but the request body must still be OpenAI-shaped chat
completions to route.
