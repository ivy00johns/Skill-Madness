# Static review-hub deploy pattern

A multi-site review hub (one page that frames several sites — a live-site
clone plus design directions, e.g. the preview-hub directory reused across
projects) deploys to Pages with a few load-bearing rules. The repo that owns
an instance documents its exact commands; this file is the reusable shape.

## Anatomy of the bundle

- One static dir (e.g. `dist/`) holds the hub shell AND every site it frames —
  hub and framed pages MUST share one origin or iframes hit mixed-content
  blocks.
- Site list lives in one JSON per site; each entry's `url` is what the hub
  iframes and links out to.
- `robots.txt` disallows the whole hub (it embeds other people's pages).

## The localhost-origin trap

During development the site JSONs point at the local server origin
(`http://127.0.0.1:8126/...`). A deploy that forgets to rewrite them ships a
hub whose every link and iframe is dead. The deploy build therefore passes
`--base https://<project>.pages.dev` and the builder rewrites each absolute
URL's origin, keeping the path. If the build supports `--base`, always use it;
never sed the JSONs in place.

## Verification after deploy

- Root `/` → 302 to the hub path (via `_redirects` in the bundle).
- Hub index 200, and EACH site URL 200 under `curl -L` (Pages clean-URL 308s
  are expected and fine).
- A 522 on a few paths right after first deploy is propagation — retry.
- Re-deploying the same project updates the same URL; a new project name is
  how you get a second, independent preview URL.
