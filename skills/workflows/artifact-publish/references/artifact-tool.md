# The Artifact tool contract

Everything the `Artifact` tool needs, and the constraints that break a page if you miss them. Read this before your first publish. Reference: code.claude.com/docs/en/artifacts.

## What the tool does

Renders an HTML or Markdown **file** to an **Artifact** — a default-private web page hosted on claude.ai that the user can later choose to share with teammates. You do not hand it a string; you write the page to a file with `Write`/`Edit`, then call `Artifact` with that file's path.

Reach for it when communicating **visually** is clearer than terminal text. For plain answers, source code, or repo-canonical documents, don't publish.

## Before you publish

**Load the `artifact-design` skill first.** It calibrates how much design effort the request warrants and holds the visual fundamentals. `artifact-publish` deliberately does not duplicate that — it covers the *mechanics*, `artifact-design` covers the *look*.

## The file you write

The file is wrapped in a `doctype … head … body` skeleton **at publish time**, and a minimal CSS reset is included. So:

- Write the page **content directly** — no `doctype`, no `html`/`head`/`body` tags of your own.
- Set the page title with a `title` element (it names the browser tab and the gallery card). Keep it **stable** across redeploys.
- Put a short, distinctive basename on the file — it's the fallback title if the HTML has no title element.

Markdown files are accepted too. Prefer **Markdown** when the deliverable is essentially a formatted document (a report, a spec, notes) and you don't need custom layout or interactivity. Prefer **HTML** when you need layout, color, charts, or interaction.

## Parameters

| Parameter | Required | What it does |
|---|---|---|
| `file_path` | yes | Path to the `.html` or `.md` file to render. The basename is the fallback title and, in this session, identifies the Artifact — reusing it redeploys to the same URL; a new path claims a new URL |
| `favicon` | yes | One or two emoji for the browser-tab icon (e.g. `"📊"`, `"🐛"`). Emoji only — no markup, no SVG. Keep it the **same** across redeploys; change only on a hard topic pivot |
| `description` | recommended | One sentence describing what the page is or does — becomes the gallery card's subtitle |
| `label` | optional | Short human-readable name for *this version* (max ~60 chars, e.g. `"fixed-header"`), shown in the version picker. A version label, not a description |
| `url` | optional | An existing Artifact URL to redeploy to. Pass this when the user gives you a link for an Artifact you did **not** publish in the current session; omit for new Artifacts or same-session redeploys |
| `force` | optional | Overwrite without the concurrent-write conflict check. Use **only** after a `409` once you've reconciled with the other version and intend to replace it. Omit normally so a concurrent write conflicts instead of being silently clobbered |

## Self-contained only — the CSP

A **strict Content Security Policy blocks requests to any external host.** There is no partial allowance and no runtime warning — an external reference just fails and the page renders broken. Blocked:

- CDN or remote `script` tags
- external stylesheets and `@import`
- remote fonts (Google Fonts, etc.)
- remote images
- `fetch` / `XHR` / `WebSocket` to any host

So: **inline all CSS and JS**, and **embed every asset as a `data:` URI** (images, fonts). If a producing skill hands you a page that pulls a chart library or font from a CDN, replace it with an inlined build or a `data:` URI before publishing. This is the single most common reason a published Artifact looks broken.

## Responsive rules

- Use relative units, flexbox/grid, and `max-width:100%` on images.
- The **page body must never scroll horizontally.** Wide content — tables, diagrams, wide code blocks — goes inside its own `overflow-x:auto` container so *it* scrolls, not the page.

## Updating an Artifact

- **Same session, same file path → same URL.** Edit the file and call `Artifact` again with the same `file_path`; it redeploys to the same URL as a new version. This is how you iterate.
- **Different file path → new URL.** Only use a new path when you intend a separate, new Artifact.
- **An Artifact from a previous session** (the user pasted a link): pass that link as `url`. Without it, a fresh session always mints a new URL — there is no other way to target the existing one.
- **Reading an existing Artifact's content:** `WebFetch` its URL.

## Conflict handling (`409`)

By default the tool sends a base version so a concurrent write from another session **conflicts (`409`) instead of silently clobbering** the other version. If you get a `409`: fetch/reconcile with the other version first, then re-publish with `force: true` to intentionally replace it. Don't reach for `force` pre-emptively — the conflict check is a safety net.

## A minimal publish, end to end

1. `artifact-design` loaded for design calibration.
2. Write `dashboard.html` — content only (no `html`/`head`/`body` wrappers), a `title` element, all CSS in a `style` tag, all JS in a `script` tag, images as `data:` URIs, wide tables wrapped in an `overflow-x:auto` div.
3. Call `Artifact` with `file_path` = the file, `favicon` = a stable emoji, `description` = one sentence.
4. Return the URL. To revise: edit `dashboard.html`, call `Artifact` again with the same path → same URL, new version, optionally a `label`.
