# Freebuff host for trigger evals

Use `--host freebuff` on `run_eval.py` / `run_loop.py` to measure whether a
skill triggers under **Freebuff**, the free coding agent built on the
open-source Codebuff platform (`github.com/CodebuffAI/codebuff`).

## Why it is built this way

- **The `freebuff` CLI cannot be scripted.** It deliberately takes no prompt
  argument and has no headless mode, so no eval loop can drive the hosted free
  tier itself.
- **The Codebuff SDK runs the same engine.** Same skill loader, same `skill`
  tool, same `disable-model-invocation` rule, same event stream. Its BYOK mode
  ("bring your own key") talks to OpenRouter or any OpenAI-compatible endpoint
  and needs no Codebuff account.
- **BYOK is only in the source tree.** The published `@codebuff/sdk` requires a
  paid Codebuff API key, so the runner loads the SDK from a Codebuff checkout
  with `bun`.
- **Freebuff's root agent is plain data**, so `assets/freebuff-root-agent.json`
  reproduces it exactly: system prompt and tool list from
  `createBase3CliRoot({ isFreebuff: true, noAskUser: true, noWeb: true })`, the
  same switches Codebuff's own eval harness uses (an `ask_user` call would stall
  a headless run; web results can leak answers). The snapshot records its
  source commit and Apache-2.0 license.

## One-time setup

```bash
git clone --depth 1 https://github.com/CodebuffAI/codebuff ~/.cache/codebuff-src
(cd ~/.cache/codebuff-src && bun install --frozen-lockfile --ignore-scripts)
```

Requires `bun` on PATH. Re-snapshot the root agent after updating the checkout:

```bash
bun run scripts/freebuff/snapshot_root.ts --codebuff ~/.cache/codebuff-src --out assets/freebuff-root-agent.json
```

## Running

```bash
python -m scripts.run_eval --host freebuff \
  --codebuff-dir ~/.cache/codebuff-src \
  --base-url http://localhost:3001/v1 --provider openai-compatible \
  --api-key-env FREELLMAPI_KEY --model <endpoint-model-id> \
  --eval-set evals/trigger.json --skill-path <skill>
```

`run_loop.py` takes the same host flags; with `--host freebuff` its description
optimizer also calls that endpoint instead of Hermes.

| Endpoint | Flags | Trade-off |
|---|---|---|
| FreeLLMAPI (local proxy) | `--base-url http://localhost:3001/v1 --provider openai-compatible` | $0; the model may differ from Freebuff's hosted ones |
| OpenRouter | `--base-url https://openrouter.ai/api/v1 --provider openrouter --model deepseek/deepseek-v4-flash` | closest to Freebuff's hosted default model; paid per call |

Every query is a real model call on that endpoint. Get the owner's approval for
the endpoint, model and number of runs first.

## What counts as a trigger

Only a correlated `skill` tool call for the exact candidate name whose result
is the skill itself. A refusal (`Error: Skill '…' can only be invoked by the
user.` or `not found`), a text mention, a `read_files` of the SKILL.md, a model
change, a fatal error, a timeout or an unfinished tool call is an **error**,
never a pass or a fail.

## Isolation

Each query runs in a fresh temp HOME and project. The candidate is placed at
`<project>/.agents/skills/<name>/` and is the only skill loaded; the user's
`~/.claude/skills` and `~/.agents/skills` are never read. Codebuff's public
build values are placeholders (BYOK makes no Codebuff, analytics or billing
request; the analytics host points at a closed local port).

## Freebuff quirks that change results

- **Discovery is one folder deep.** Freebuff finds `<dir>/<name>/SKILL.md` in
  `~/.claude/skills`, `~/.agents/skills`, `<project>/.claude/skills` and
  `<project>/.agents/skills` (project wins). `skills/<category>/<name>/` is not
  found unless linked flat.
- **`name` must equal the folder name**, or the skill is silently skipped.
- **Descriptions over 1024 characters are truncated**, not rejected.
- **`disable-model-invocation: true` means the model can never load the skill**
  through the `skill` tool; only the user can. The runner refuses to score such
  a candidate. An orchestrator that needs such a skill on Freebuff must read its
  SKILL.md file directly.
- **The SDK redacts the API key's value from every string.** A very short key
  (e.g. `k`) corrupts tool names (`s[redacted]ill`); the runner rejects keys
  under 12 characters.
- **The skill list lives in the `skill` tool's description**, added by the
  engine, so trigger behaviour depends on that description plus the root
  agent's system prompt — both reproduced here.
