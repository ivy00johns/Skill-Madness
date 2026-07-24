---
name: use-pxpipe
version: 1.0.1
description: |
  Wire the Claude Code agent harness to pxpipe — a local, loopback-only proxy that renders re-sent
  bulk (system prompt, tool docs, older history) into dense PNGs so long sessions cost roughly half
  to a third as much in input tokens, with a live savings dashboard and a one-line off switch. Use
  when the user wants to cut Claude Code's own token bill, enable the token-saver proxy for a long or
  multi-agent run, point the harness at pxpipe, or check whether compression is actually paying.
  Opt-in and reversible: ANTHROPIC_BASE_URL behind an env toggle, model scope deferred to
  model-adaptation's allowlist, verification that compression fired AND the prompt cache stayed warm.
  Trigger on "use pxpipe", "token saver proxy", "compress my context", "cut session input tokens",
  "optical context compression", "my Claude Code sessions are expensive". Sibling use-freellmapi
  rewires an app's LLM client; this one rewires the agent harness itself.
compatibility: "Claude Code; requires Bash + Node/npx (proxy runs via npx pxpipe-proxy)"
requires_agent_teams: false
requires_claude_code: true
min_plan: starter
owns:
  directories: []
  patterns: []
  shared_read: ["*"]
allowed-tools: ["Read", "Write", "Edit", "Bash", "Grep", "Glob"]
composes_with: ["model-adaptation", "use-freellmapi", "madness"]
spawned_by: []
---

# use-pxpipe

Point the **agent harness** at [pxpipe](https://github.com/teamchong/pxpipe) — a local proxy on
`127.0.0.1:47821` that rewrites the bulky, re-sent parts of every Claude Code request (system
prompt, tool docs, collapsed older history) into dense PNG image blocks before the request leaves
the machine. An image's token cost is fixed by pixel area, not character count, so token-dense
material (code, JSON, logs) carries roughly 3× more characters per token as pixels than as text.
Measured end to end on real sessions: **~59–70% fewer input tokens** (one live A/B: 856k → 277k).
Responses stream back untouched — pxpipe compresses the request, never the model's output.

This is the harness-level sibling of `use-freellmapi`, one level up the stack:

| | `use-freellmapi` | `use-pxpipe` |
| --- | --- | --- |
| What gets rewired | The **app's** LLM client (base_url + key in source) | The **agent harness** (`ANTHROPIC_BASE_URL` env) |
| Goal | Prototype the app for free | Cut the coding *session's* input tokens |
| Loss profile | None (real models, just free) | Lossy gist on old bulk; recent turns stay text |
| Flip back | Env toggle in the app | `unset ANTHROPIC_BASE_URL` — one line |

> **Opt-in, never vendored.** Upstream is young (~8 weeks of history, v0.8.x). This skill wires it
> as a reversible environment in front of the harness; it never embeds pxpipe code into a build or
> makes it a project dependency. If upstream breaks, one `unset` restores stock behavior.

## The whole integration, in three facts

| What | Value |
| --- | --- |
| **base_url** | `http://127.0.0.1:47821` → `ANTHROPIC_BASE_URL` (Claude Code) |
| **model scope** | `PXPIPE_MODELS` — default `claude-fable-5` only; widen ONLY per the allowlist in `model-adaptation` |
| **dashboard / kill switch** | `http://127.0.0.1:47821/` — live savings, passthrough toggle (`POST /api/compression`) |

## Workflow

### Step 1 — Check the model allowlist first

pxpipe images context that the model must then *read back from pixels*, and models differ sharply
at that: the technique is safe only for models measured to read production-density renders. The
governed allowlist lives in **`model-adaptation`** (the toolkit's model-and-effort authority) —
read its **"Image-proxy model allowlist"** section, and the current list with measured read rates
in its `references/model-effort-tiering.md` (*Image-proxy allowlist — current state*), before
wiring anything, and never widen `PXPIPE_MODELS` beyond it. Imaging a model that misreads the render produces confident wrong
answers, not errors. The upstream default (`claude-fable-5` only) is the measured-safe floor; if
the session's model isn't on the allowlist, pxpipe passes requests through uncompressed
(`reason: unsupported_model`) — harmless, but pointless, so stop here and say so.

### Step 2 — Make sure the proxy is running

```bash
curl -fsS http://127.0.0.1:47821/api/stats.json > /dev/null && echo "pxpipe up"
```

If nothing answers, start it (Node 18+):

```bash
npx pxpipe-proxy
```

It binds `127.0.0.1:47821` and serves the dashboard at `/`. Leave it running in its own terminal
or a background process; re-probe the stats endpoint to confirm.

**Security posture — loopback only.** The dashboard is unauthenticated and serves captured request
context plus a kill switch. Never set `HOST=0.0.0.0` on a shared machine; off-host exposure is
deliberate opt-in upstream and logs a warning. (A Cloudflare Workers deployment exists but requires
`PXPIPE_WORKER_SECRET`; it is out of scope for this skill — local wiring only.)

### Step 3 — Wire the harness behind a one-line-reversible toggle

Set the env var in the shell that launches Claude Code — never in checked-in project config:

```bash
# on — this shell's Claude Code sessions route through pxpipe
export ANTHROPIC_BASE_URL=http://127.0.0.1:47821

# off — one line, full stock behavior restored
unset ANTHROPIC_BASE_URL
```

Scope it to the session: an `export` in the launching shell (or a wrapper alias the user opts
into) beats writing it into `~/.zshrc`, because the whole point is that any given session chooses.
If the user wants it durable, put the pair in their shell profile as two labeled lines they can
comment-swap — same pattern as `use-freellmapi`'s `.env` blocks.

**Byte-exact escape hatch:** work that must be verbatim-faithful can run on a subagent model
outside the image scope — e.g. `CLAUDE_CODE_SUBAGENT_MODEL=claude-sonnet-5` (the Mid tier in
`model-adaptation`'s tiering ladder) routes that subagent's traffic through the proxy untouched —
a genuine passthrough as long as that model stays off the image-proxy allowlist, so re-check the
allowlist when picking the hatch model.

### Step 4 — Verify: compression fired AND the cache stayed warm

"It's wired" is not the claim; "it's saving" is. Two checks, both against
`~/.pxpipe/events.jsonl` or the dashboard — read `references/verification.md` for the exact
fields and the failure signatures:

1. **Compression fired.** After a couple of real turns, recent event rows must show compression
   applied — not passthrough with `reason: unsupported_model` (wrong model scope) or a gate
   decline (session too small; fine, it will kick in as history grows).
2. **The prompt cache stayed warm.** A mis-set history boundary re-keys Anthropic's prompt cache
   every turn and pays the 1.25× `cache_create` rate on the whole history repeatedly — the
   historical **−250% "savings"** regression. Warm looks like: `history_image_sha8` stable across
   consecutive turns, `cache_read_tokens` dominating `cache_create_tokens` after the first turn.
   The dashboard reports savings **unfloored** — a negative number is honest and means turn the
   toggle off and investigate, not "close enough".

### Step 5 — Hand off

Tell the user, briefly:

- **Dashboard:** `http://127.0.0.1:47821/` — live per-session savings, image previews, model-scope
  chips (chips mutate scope in-memory only; a restart reverts to `PXPIPE_MODELS`/default).
- **Kill switches, fastest first:** `unset ANTHROPIC_BASE_URL` (hard off, this shell);
  dashboard passthrough toggle or `PXPIPE_DISABLE=1` (proxy stays up, compression off, no
  restart); `PXPIPE_MODELS=off` (scope-level off).
- **The gist-only caveat — say it every time:** imaged bulk is safe to navigate by *gist*
  (decisions, paths, names, state) but must **never be the sole copy of anything needed
  byte-exact** — secrets, hashes, exact IDs, numeric ledgers. Vision is not OCR: misreads surface
  as confident plausible values, not errors. pxpipe's defenses (recent turns stay text; a text
  "factsheet" of exact identifiers rides beside each image) mitigate but do not repeal this.
  Byte-exact work belongs on the text tail or a non-imaged model (Step 3's escape hatch).

## When NOT to use it

- **Byte-exact-critical workloads** where imaged history would be the only copy of secrets,
  hashes, or exact numbers — the loss profile is wrong for them.
- **Short sessions** — the profitability gate needs enough history to amortize; tiny sessions pass
  through anyway, so the wiring is pure overhead.
- **Prompts already ~98% cache-read** — there's little uncached bulk left to image.
- **Latency-sensitive one-shot calls** — PNG encoding adds noticeable latency to a single large
  request; it disappears into long agent sessions.

## Triggering test

- MUST fire: "enable the token-saver proxy for this overnight build" · "my Claude Code sessions
  are burning tokens, compress the context" · "point the harness at pxpipe".
- Must NOT fire: "switch this project to free models" (that's `use-freellmapi` — it rewires the
  app's client, not the harness).

## References

- **`references/verification.md`** — the events.jsonl fields to check, warm-vs-shredded cache
  signatures, the −250% regression story, the full kill-switch matrix, and how to read the
  dashboard's savings numbers honestly (pctInput vs pctTotal, unfloored negatives, refusal-flagged
  rows).
