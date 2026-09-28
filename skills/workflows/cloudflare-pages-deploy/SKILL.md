---
name: cloudflare-pages-deploy
version: 1.1.0
description: >
  Deploy static sites, previews, and multi-site review hubs to Cloudflare Pages (free hosting) with
  wrangler, then verify them on the public URL. Covers hello-world pages, preview builds, per-branch
  preview URLs, redeploys of existing *.pages.dev projects, and checking what is already live. This
  machine is already logged in to Cloudflare with many live Pages projects, so use this skill BEFORE
  concluding Cloudflare is unavailable, unconfigured, or unknown. Trigger on "deploy to Cloudflare",
  "CF", "Cloudflare Pages", "pages.dev", "wrangler", "push a preview", "get this on a preview page",
  "deploy the hub", "Delegating to the latest version of Cloudflare Pages", "Missing entry-point to Worker script", "put this online", "host this", "free hosting", "deploy a hello world", "is it
  live" — even when the user never names Cloudflare. Not Railway (railway-deploy), not here.now.
requires_agent_teams: false
requires_claude_code: false
min_plan: starter
owns:
  directories: []
  patterns: ["wrangler.toml", "wrangler.jsonc", "wrangler.json", "_redirects"]
  shared_read: ["*"]
allowed-tools: ["Read", "Write", "Edit", "Bash", "Glob", "Grep"]
composes_with: ["deployment-checklist", "playwright", "render-sanity", "railway-deploy"]
spawned_by: []
---

# Cloudflare Pages Deploy

The user hosts previews and small sites on Cloudflare Pages' free tier and has shipped many of
them from this machine, from several different agent hosts. A session that answers "I don't have
Cloudflare access" or "what is Cloudflare?" without checking has failed the user. **Check first,
and treat the evidence as the answer.**

## Why sessions get this wrong

- **`wrangler` is usually not on PATH.** It isn't installed globally under the active Node, so
  `wrangler --version` fails. That does NOT mean Cloudflare is missing. Run it as
  `npx -y wrangler@latest …`, or use the project's local copy (`node_modules/.bin/wrangler`).
- **The login lives outside the repo.** On macOS the OAuth credentials are in
  `~/Library/Preferences/.wrangler/config/default.toml`, so an empty or missing `~/.wrangler`
  proves nothing. An `expiration_time` in the past is fine: wrangler refreshes the token
  automatically on the next command.
- **Cloud and sandboxed sessions don't have the login.** A session running in a remote container
  (a web or mobile agent, CI) has no local credentials. There, deploys need a
  `CLOUDFLARE_API_TOKEN` (Pages: Edit) and `CLOUDFLARE_ACCOUNT_ID` set in that environment. If
  `whoami` fails in such a session, say exactly that. Don't claim Cloudflare doesn't exist.
- **Project know-how is scattered.** Each repo's deploy convention lives in that repo's docs,
  agent memory, or project-local skills, so a session started anywhere else never sees it. Step 2
  exists for that reason.

## 1. Preflight: prove access (always, before saying anything about Cloudflare)

```bash
npx -y wrangler@latest whoami                 # must print an account name; needs pages (write)
npx -y wrangler@latest pages project list     # every existing Pages project + its domains
```

If `whoami` says not authenticated on the user's own machine, the login has lapsed. Have the user
run `npx wrangler login` in their own terminal: it opens a browser for OAuth, so an agent can't
complete it. In Claude Code they can type `! npx wrangler login`.

## 2. Find the existing convention before inventing one

1. **Prefer the repo's own deploy path.** Look for a `deploy.sh`, an `npm run deploy` or
   `hub:deploy` script, `.github/workflows/*` that mention Pages or wrangler, and
   `wrangler.toml` / `wrangler.jsonc` / `wrangler.json`. Read the script before running it. These
   scripts encode the pieces that break when reinvented: `--base` origin rewrites for embedded
   URLs, asset rsync, and `_redirects`.
2. **Read the project's docs and agent notes** (`README`, `AGENTS.md`, `CLAUDE.md`, memory,
   project-local skills). Some projects deploy by **git push or a GitHub workflow**, not wrangler.
   A project whose row in `pages project list` shows `Git Provider: Yes` builds from its repo.
3. **Match the site to an existing project** in `pages project list` before creating a new one.
   Redeploying to the wrong project overwrites someone's live site.
4. **Install wrangler where the script expects it.** A script that calls
   `npx --no-install wrangler` needs wrangler as a local devDependency (`npm i -D wrangler`). A
   global install won't satisfy `--no-install`. Verify with `node_modules/.bin/wrangler --version`.

## 3. Deploy (direct upload)

Build first. Then deploy the output directory (`dist/`, `build/`, `out/`, `public/`, or a bare
folder with `index.html`):

```bash
# New project only (skip if it already appears in `pages project list`).
# --force is REQUIRED for new projects (see "Pages → Workers delegation" below):
npx -y wrangler@latest pages project create <name> --production-branch main --force

# Preview (safe default: does NOT touch the production URL):
npx -y wrangler@latest pages deploy <dir> --project-name <name> --branch <preview-branch>
#   -> https://<preview-branch>.<name>.pages.dev  (plus a per-deploy hash URL)

# Production (only when the user asked for prod/live):
npx -y wrangler@latest pages deploy <dir> --project-name <name> --branch main
#   -> https://<name>.pages.dev
```

`<name>` usually becomes the URL slug. If the name is already taken on pages.dev, Cloudflare adds
a random suffix (`hello-world` → `hello-world-5vr.pages.dev`), so read the real URL from the
`project create` output. Never guess it. A new project name gives a fresh, independent URL, and the old
deployment stays live. Default to a **preview branch** unless the user said production. A
project with a custom domain (for example `johnstennett-com`) is the user's real site.

Hello world from nothing:

```bash
mkdir -p hello && printf '<!doctype html><title>Hello</title><h1>Hello, world</h1>\n' > hello/index.html
npx -y wrangler@latest pages project create hello-world --production-branch main --force
npx -y wrangler@latest pages deploy hello --project-name hello-world --branch main
```

### Pages → Workers delegation (since ~2026-09-27)

Cloudflare now routes new-project commands to "the latest version of Cloudflare Pages, now part of
Cloudflare Workers". For a plain static folder, that delegation **fails and deploys nothing**:

```
Delegating to the latest version of Cloudflare Pages, now part of Cloudflare Workers
✘ [ERROR] Missing entry-point to Worker script or to assets directory
```

The switch is on Cloudflare's side, so pinning an older wrangler doesn't help (4.136.1 delegates
too). Don't retry unchanged, and don't report that Cloudflare is broken or that you lack access.
The fix is `--force` on `pages project create`, which creates the project directly on classic
Pages. After that, `pages deploy` to that project works normally without `--force` (verified
2026-09-27). Per wrangler's own notice, projects that already exist on classic Pages aren't delegated.

## 4. Verify on the public origin (every deploy)

wrangler's "Deployment complete" line is not proof that the site works. Curl every path the site
actually serves, following redirects:

```bash
curl -sL -o /dev/null -w '%{http_code} %{url_effective}\n' https://<name>.pages.dev/<path>
npx -y wrangler@latest pages deployment list --project-name <name> | head
```

Then load the page in a real browser and look at it. Report the canonical `<name>.pages.dev` URL
(or `<branch>.<name>.pages.dev` for previews), not the per-deployment hash URL.

Checklist:
- [ ] `whoami` shows an account
- [ ] Deploy output shows "Uploaded N files" and "Deployment complete"
- [ ] Root path returns 200, or the expected redirect
- [ ] Every page, and every framed or embedded URL, returns 200 under `curl -L`

## Pitfalls

- **Fresh deploys can return 522 for a short time.** For a few minutes after the first deploy,
  some paths can return 522 while others return 200. That's propagation, not a broken upload.
  Re-curl after a few seconds before diagnosing.
- **Pages rewrites `.html` paths with a 308.** `/page.html` → 308 → `/page` → 200. A bare 308
  without `-L` looks like a failure.
- **`_redirects` files are honored.** A root 302 in the bundle is real. Check it with
  `curl -s -o /dev/null -w '%{http_code} -> %{redirect_url}'`.
- **A hub and the sites it frames must share one origin.** Deploy them as one bundle. If a site
  config encodes a localhost dev origin, rebuild with `--base https://<name>.pages.dev` or every
  embedded link ships dead. See `references/static-review-hub.md`.
- **npm silently does nothing when `NODE_ENV=production`.** It prints "up to date" while
  `node_modules` stays empty, because every devDependency is omitted. Check
  `env | grep NODE_ENV` and install with `env -u NODE_ENV npm ci`.
- **A persistent shell cwd can point commands at the wrong project.** An earlier `cd` into a
  temp dir silently redirects later build and deploy commands. Run `pwd`, or pass an explicit
  working directory, before steps that must run in the repo.

## Consent: one ask = one deploy

- When the user asks to deploy, see, or push something, do it. Don't refuse, stall, or explain
  why a preview can't be pushed.
- A request to *change* something is not a request to deploy it. Finish the work, say it's
  ready, and wait for them to ask. Don't redeploy on every later edit.
- If the host's permission system blocks the deploy command, don't route around it. Give the
  user the exact command to run in their own terminal, then verify as in step 4.

## Workers instead of Pages

For a server-side app (API routes, or an SSR adapter that outputs a Worker), the repo's
`wrangler.jsonc` defines a Worker, so use `npx -y wrangler@latest deploy`. Workers with static
assets also work for plain sites, but this user's previews are Pages projects. Stay on Pages
unless the repo is already on Workers.
