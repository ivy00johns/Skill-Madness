# Port conventions — collision-free local dev

This is the single source of truth for which ports a generated project uses and
how it picks them. Every skill that names a localhost port (orchestrator,
agent-spawning, workspace-bootstrap, deployment-checklist, render-sanity,
playwright, infrastructure-agent) points here instead of hardcoding its own.

## Why this exists

A multi-agent build that one-shots a project must come up cleanly on the *first*
`dev` run — including when the human already has another project running. Two
failure modes break that, and they compound:

1. **Everyone defaults to the same framework port.** `3000` (Next.js, CRA),
   `8080`, `5000` — worked examples carry a default, agents paste it into source,
   and every project ends up fighting for the same socket. Within one project two
   services collide; across two projects they collide by construction.
2. **No preflight.** If the preferred port is already held (a leftover `node`, a
   second project, Docker), the new process doesn't step aside — it dies with
   `EADDRINUSE` / "address already in use" and the build reads as broken.

Correct ports alone don't fix this — you also need a process that *checks first
and steps aside*. Both layers below are mandatory.

## Layer 1 — Preferred port map

What each service type tries **first**. These are the toolkit's house defaults;
`contract-author`, `deployment-checklist`, and the role agents already use them.

| Service | Preferred | Notes |
|---|---|---|
| Backend / API (FastAPI, Express, Go, …) | **8000** | never `3000` |
| Frontend dev server | **5173** | Vite. **Force Next.js/CRA off 3000**: `next dev -p 5173` |
| Frontend preview / prod (vite preview, nginx) | **4173** | |
| Worker / gateway / secondary HTTP | **8080** | |
| FreeLLMAPI proxy | **3001** | fixed, shared across projects — see `use-freellmapi` |
| Postgres | **5432** | shared host service |
| Redis | **6379** | shared host service |
| MongoDB | **27017** | shared host service |
| Ollama | **11434** | shared host service |
| OTLP collector (gRPC) | **4317** | |

`3000` is intentionally **not** in this table. It is a frontend framework default
that leaks into source as an API port; the house frontend port is `5173`.

## Layer 2 — Bands + preflight (the part that stops crashes)

Each per-project service owns a small **band**. At dev startup the project prefers
its canonical port; if that port is busy it takes the **next free port in the
band**, records it, and prints the resolved URL. It never hardcodes and never
silently dies.

| Service | Band | Resolution order |
|---|---|---|
| Backend / API | `8000–8049` | 8000 → 8001 → … |
| Frontend dev | `5173–5199` | 5173 → 5174 → … |
| Frontend preview/prod | `4173–4199` | 4173 → … |
| Worker / gateway | `8080–8099` | 8080 → … |

Two projects up at once self-separate: project A's API binds 8000, project B's
preflight sees 8000 busy and takes 8001 — no manual coordination, no crash.

> **Shared services (Postgres/Redis/Mongo):** for concurrent projects, run them in
> `docker-compose` and map the **host** port up its band (`"54320:5432"`,
> `"54330:5432"`, …) while the container keeps the standard port. Same preflight
> idea, applied to the host side.

## The allocation rule (put this in the dev script)

The root `dev` script (workspace-bootstrap's one-command dev) resolves every port
**before** launching services, exports them, and prints what it chose. Services
read the port from env — never a literal.

```bash
# scripts/dev-ports.sh — source this from the root `dev` script.
# free_port BASE BAND_END -> echoes the first free port at/after BASE, capped at BAND_END.
free_port() {
  local p=$1 end=$2
  while [ "$p" -le "$end" ]; do
    if ! lsof -iTCP:"$p" -sTCP:LISTEN >/dev/null 2>&1; then echo "$p"; return 0; fi
    p=$((p+1))
  done
  echo "ERROR: no free port in band $1-$2 — close a stale process or widen the band" >&2
  return 1
}

export API_PORT=$(free_port 8000 8049) || exit 1
export WEB_PORT=$(free_port 5173 5199) || exit 1
echo "→ API  http://localhost:$API_PORT"
echo "→ web  http://localhost:$WEB_PORT"
# e.g.  concurrently "uvicorn app:api --port $API_PORT"  "vite --port $WEB_PORT"
```

Frontend must point at the **resolved** API port (e.g. Vite `VITE_API_URL=http://localhost:$API_PORT`,
proxy config, or `.env`), not a baked-in `localhost:8000` — otherwise the auto-step
breaks the cross-service link the moment a port shifts.

## Hard rules

- **No hardcoded ports in source.** Read from env (`API_PORT`, `WEB_PORT`, …) or a
  framework flag fed by the dev script. A literal `localhost:3000`/`localhost:8000`
  in app code is a finding.
- **Preflight before bind.** A service that can crash on `EADDRINUSE` instead of
  stepping aside is not done. Infra that takes a port the user already holds
  without saying so is also a finding (see `infrastructure-agent`).
- **Print the resolved URLs.** The human should see exactly where each service came
  up, every run.
- **Never `3000` for an API.** It's the frontend-default trap this whole doc exists
  to kill.

## For agent prompts

When spawning an implementation agent, pass the **project's** resolved ports (from
`.env.example` / dev script / `profile.yaml`), not a default. Validation commands
in the prompt use the env var, not a literal — `curl -i localhost:$API_PORT/...`,
never `curl -i localhost:3000/...`.
