# Coding agents & non-OpenAI wire formats

FreeLLMAPI speaks **six** wire protocols over one router. Point a client at the surface it already
speaks rather than forcing everything through OpenAI chat completions.

| Client speaks | Surface | Base URL to configure |
| --- | --- | --- |
| OpenAI | `/v1/chat/completions`, `/v1/responses`, `/v1/completions` | `http://localhost:3001/v1` |
| Anthropic Messages | `/v1/messages` | `http://localhost:3001` **(origin, no `/v1`)** |
| Google Gemini | `/v1beta/models/{model}:generateContent` | `http://localhost:3001` |
| Ollama | `/api/chat`, `/api/generate`, `/api/tags` | `http://localhost:3001` |
| MCP | `/mcp` (Streamable HTTP) | `http://localhost:3001/mcp` |
| Headerless | `/v1/t/{token}/…` | `http://localhost:3001/v1/t/<token>` |

## Prefer the generator over hand-wiring

For coding agents, **don't hand-edit config** — the proxy ships generators that read the live
`/v1/models` catalog, merge with existing config, and write a timestamped backup first:

```bash
npx freellmapi setup-claude --url http://localhost:3001 --dry-run   # prints a diff
npx freellmapi setup-claude --url http://localhost:3001             # writes, with backup
```

`--profile <name>` creates a named Claude/Codex profile instead of touching the default.

| Agent | Command | Base URL | Wire |
| --- | --- | --- | --- |
| Claude Code | `setup-claude` / `launch` | `http://localhost:3001` | Anthropic Messages |
| Codex CLI | `setup-codex` / `launch-codex` | `…/v1` | Responses (`wire_api = "responses"`) |
| Cline | `setup-cline` | `…/v1` | OpenAI Chat |
| Continue | `setup-continue` | `…/v1` | OpenAI Chat + legacy Completions |
| Aider | `setup-aider` | `…/v1` | OpenAI Chat |
| OpenCode | `setup-opencode` | `…/v1` | OpenAI Chat |
| Goose | `setup-goose` | `…/v1` | OpenAI Chat |
| Qwen Code | `setup-qwen` | `…/v1` | OpenAI Chat (native Gemini also works) |
| Roo Code | `setup-roo` | `…/v1` | OpenAI Chat |
| Kilo Code | `setup-kilo` | `…/v1` | OpenAI Chat |
| Crush | `setup-crush` | `…/v1` | OpenAI Chat |
| Cursor | `setup-cursor` (prints a guide) | public `https://…/v1` | OpenAI Chat |
| Anything else | `setup-generic` (prints a block) | `…/v1` | OpenAI Chat |

`freellmapi launch` / `launch-codex` are **zero-persistence launchers** — they inject credentials into
the child process only, writing nothing to disk. Prefer them when the user doesn't want a key landing
in a config file.

## Claude Code — the two traps

```bash
export ANTHROPIC_BASE_URL=http://localhost:3001         # origin, NOT /v1
export ANTHROPIC_AUTH_TOKEN=freellmapi-your-key         # NOT ANTHROPIC_API_KEY
claude
```

1. **Origin, not `/v1`.** Anthropic clients append `/v1/messages` themselves. Adding `/v1` yields
   `/v1/v1/messages` and a 404.
2. **`ANTHROPIC_AUTH_TOKEN`, never `ANTHROPIC_API_KEY`.** Claude Code treats a set `ANTHROPIC_API_KEY`
   as a conflicting first-party credential and **refuses to start**. This is the single most common
   failure and the error message doesn't point at it.

Claude model names map to the free pool on the dashboard's **Agents** page: each family (`default`,
`opus`, `sonnet`, `haiku`) routes to `auto` or a model you pin. `POST /v1/messages/count_tokens` and a
content-negotiated `GET /v1/models` (Anthropic shape when `anthropic-version` is sent) are implemented.
Streaming, system prompts, tool use, and image input all translate.

## Gemini CLI

```bash
export GOOGLE_GEMINI_BASE_URL=http://localhost:3001
export GEMINI_API_KEY=freellmapi-your-key
gemini
```

Native surface: `GET /v1beta/models`, `GET /v1beta/models/{model}`, and
`POST /v1beta/models/{model}:generateContent` / `:streamGenerateContent` (`?alt=sse` for the CLI) /
`:countTokens`. Auth accepts `x-goog-api-key`, Bearer, or Gemini's `?key=` query fallback — **prefer a
header**; query credentials leak into shell history and proxy logs. Gemini family names resolve through
the Agents-page Gemini map; catalog ids work verbatim.

## Ollama clients (Zed, JetBrains AI)

Ollama emulation is **off by default**. Enable a mode on the dashboard's **Agents** page:

- `open-loopback` — no key, but the socket peer must be `127.0.0.1`/`::1`.
  **In Docker this refuses even host-local traffic** (the peer is the bridge IP), so a containerized
  install — the default — needs `key-required`.
- `key-required` — clients send `Authorization: Bearer <unified-key>`.

Endpoints: `/api/tags`, `/api/chat`, `/api/generate`, `/api/show`, `/api/version`, `/api/embed`, and
legacy `/api/embeddings`. Streaming is **NDJSON, not SSE**. Point the client at `http://localhost:3001`.

## Headerless clients — revocable URL tokens

For clients that can't set headers, mint a token on the **Agents** page:

```text
http://localhost:3001/v1/t/<token>/chat/completions
http://localhost:3001/v1/t/<token>/responses
http://localhost:3001/v1/t/<token>/models
```

The same prefix also exposes `/api/chat` and `/api/tags`. Tokens are random, stored only as hashes,
and independently revocable. **Never put the unified key in a URL** — URLs leak into shell history,
reverse-proxy logs, browser history, and telemetry. Treat tokens as sensitive for the same reason;
revocation is immediate.

## MCP server

```bash
claude mcp add --transport http freellmapi http://localhost:3001/mcp \
  --header "Authorization: Bearer freellmapi-your-key"
```

Tools: `list_models`, `provider_health`, `usage_summary`, `routing_info`, `set_routing_strategy`,
`cache_stats`, `compression_stats`. Any Streamable-HTTP MCP client works the same way.

## VS Code ghost-text (Continue)

`/v1/completions` exists specifically for legacy prompt/suffix autocomplete:

```yaml
models:
  - name: FreeLLMAPI Autocomplete
    provider: openai
    model: auto
    apiBase: http://localhost:3001/v1
    apiKey: freellmapi-your-key
    useLegacyCompletionsEndpoint: true
    roles:
      - autocomplete
```

## Context handoff

When the router fails over mid-conversation, the new model doesn't know it inherited a task. Enable a
compact handoff note in `.env`:

```env
FREELLMAPI_CONTEXT_HANDOFF=on_model_switch
```

Injected only when the model actually changes for a session key (`X-Session-Id`, else SHA-1 of the
first user message). In-memory only, 3-hour TTL, nothing written to disk. It can't recover
provider-internal hidden state — only what passed through the proxy.
