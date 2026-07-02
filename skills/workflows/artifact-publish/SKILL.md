---
name: artifact-publish
version: 1.0.0
description: |
  Publish a visual or interactive deliverable as a Claude Code Artifact — a self-contained HTML/Markdown file rendered to a hosted, default-private claude.ai web page the user can share with a link — instead of leaving it as a local file or dumping it in the terminal. Use whenever a result reads better as a page than as text: a dashboard, a rendered report, a chart or diagram, a comparison, a prototype, a walkthrough, a mockup you built in code. Trigger on "publish this as an artifact", "make a shareable link", "host this page", "turn this into a web page", "claude artifact", "publish the dashboard", "share this report as a page", "give me a link to this", "put this on claude.ai". This is the Claude Code Artifact feature (code.claude.com), NOT the claude.ai design canvas (that is claude-design-brief). It is the publish step for the visual-output skills — interactive-doc, mermaid-charts, dataviz, nano-banana — and defers all look-and-feel to the artifact-design skill.
requires_agent_teams: false
requires_claude_code: true
min_plan: pro
owns:
  directories: []
  patterns: []
  shared_read: ["*"]
allowed-tools: ["Read", "Write", "Edit", "Artifact", "WebFetch"]
composes_with: ["artifact-design", "interactive-doc", "mermaid-charts", "dataviz", "nano-banana", "ui-brief", "claude-design-brief"]
spawned_by: []
---

# Artifact Publish

Publishing an **Artifact** renders a self-contained HTML (or Markdown) file to a **hosted, default-private web page on claude.ai** — one the user can open in a browser and later choose to share by link. It is the Claude Code Artifact feature documented at code.claude.com/docs/en/artifacts, and it turns "here's a file, open it locally" or a wall of terminal text into a real, shareable page.

This skill is about **the decision (when to publish) and the mechanics (how to publish correctly)** — not visual design.

> **Load `artifact-design` first.** It calibrates how much design investment a request warrants and carries the look-and-feel fundamentals. This skill deliberately does *not* reinvent that guidance — it defers to it. `artifact-design` is the *how it looks*; `artifact-publish` is the *should-I-publish-and-how-do-I-ship-it*.

**Announce at start:** "Using artifact-publish to ship [thing] as a hosted Artifact."

## When to publish — and when not to

Publishing is the right move when the deliverable is **visual or interactive and reads better as a page** than as terminal text or a file the user has to find and open:

- a dashboard, KPI board, or analytics view
- a rendered report or a formatted document meant to be *read*, not *grepped*
- a chart, a diagram, a data visualization
- a side-by-side comparison of options, designs, or approaches
- an interactive prototype or a code-built mockup
- a walkthrough or explainer with live elements

Do **not** publish when:

- the output is **source code the user will edit** — attach the file instead
- the output is the **canonical copy of something that lives in the repo** (e.g. `interactive-doc`'s `.md`) — the Artifact is a shared *view*, never the source of truth
- a **plain-text answer** is enough — just answer inline
- the content contains **secrets, credentials, or data the user hasn't okayed** for an external service

**Publishing is outward-facing.** Even a default-private Artifact is hosted on claude.ai and may be cached or indexed. For anything the user might consider private or sensitive, confirm before you publish — the same discipline you'd apply to any action that sends content off the machine.

## The mechanics (short version)

The full tool contract — every parameter, the CSP rules, conflict handling, and how to read or re-target an existing Artifact — lives in `references/artifact-tool.md`. Read it before your first publish. The load-bearing points:

- **Write page *content* to a file.** No `doctype`, `html`, `head`, or `body` wrappers of your own — the tool wraps the file in that skeleton at publish time and applies a minimal CSS reset. Set the page title with a `title` element in the head you *do* write.
- **Self-contained only.** A strict Content Security Policy blocks **every external host** — no CDN scripts, no external stylesheets or fonts, no remote images, no fetch/XHR/WebSocket. Inline all CSS and JS; embed images and fonts as `data:` URIs. An external reference doesn't warn — it silently fails and the page breaks.
- **Favicon is required and must stay stable.** Pass one or two emoji. Keep the *same* emoji across every redeploy of the same Artifact — users find their tab by its icon; a changed favicon reads as a different page. Only change it on a hard topic pivot.
- **Concise title + one-sentence description.** The title names the browser tab and gallery entry; the description is the gallery card's subtitle. Keep the title stable across redeploys.
- **Responsive, no horizontal body scroll.** Use relative units and `max-width:100%` on media. Wide content (tables, diagrams, code) scrolls inside its own `overflow-x:auto` container — the page body itself must never scroll sideways.
- **Update in place vs. mint a new URL.** Re-publishing the **same file path** redeploys to the **same URL** — that's how you iterate. A **different path claims a new URL**. To update an Artifact the user hands you a link for (not one you published this session), pass its `url`; otherwise a fresh session always mints a new URL.

## How a publish goes

1. **Load `artifact-design`** for design calibration.
2. **Get the content** — build it, or take it from a producing skill (see Composition).
3. **Write it to a file** as self-contained HTML (or Markdown). Put scratch pages in the session scratchpad unless the user wants the source kept somewhere specific.
4. **Confirm if it's sensitive** — publishing is outward-facing.
5. **Call the Artifact tool** with the file path, an emoji `favicon`, a one-sentence `description`, and a stable title in the file.
6. **Return the URL.** To iterate: edit the *same* file and re-publish to the *same* path → same URL, new version.

## Composition — the publish step for the visual skills

Most of the time you're not authoring a page from scratch — you're finishing what another skill produced:

| Producing skill | What it makes | How `artifact-publish` finishes it |
|---|---|---|
| `interactive-doc` | a canonical `.md` (stays in the repo/vault) + a self-contained `.html` companion | publish the `.html` as a shareable hosted view. The `.md` stays the source of truth — do not let the Artifact become canonical |
| `mermaid-charts` | one or more diagrams | render to SVG, inline it in a page, publish. (Mermaid needs its runtime — inline the rendered SVG, not a CDN `mermaid.js` call, or the CSP blocks it) |
| `dataviz` | a chart or dashboard | publish the dashboard as a hosted page; inline every script, style, and asset |
| `nano-banana` | generated images | embed them as `data:` URIs — the CSP blocks external image URLs |
| `ui-brief` | a Markdown *brief* (text, stays a file) | usually **not** published — the brief is a hand-off doc. Publish only a *rendered mockup* built from it, never the brief text itself |
| `claude-design-brief` | a prompt for the claude.ai **design canvas** — a *different surface* | **not this.** If the user conflates the two, point them at the canvas. `artifact-publish` is the Claude Code Artifact tool; the design canvas is where `claude-design-brief` sends them |
| `artifact-design` | the design authority | load it for look-and-feel and defer to it — don't duplicate its guidance here |

## Anti-patterns

| Anti-pattern | Why it fails |
|---|---|
| External CDN / font / image / fetch reference | Silently blocked by the CSP; the page breaks with no error. Inline and embed everything |
| Changing the favicon on a redeploy | Reads as a different page — users lose the tab. Keep it stable; change only on a hard pivot |
| Minting a new URL when you meant to update | Reuse the *same file path* to redeploy to the same URL |
| Publishing source code or a plain-text answer | Attach the file or answer inline — a hosted page adds nothing |
| Publishing sensitive content without confirming | It's outward-facing and may be cached/indexed — confirm first |
| Letting the Artifact become the canonical copy | The Artifact is a shared *view*; the repo file (e.g. `interactive-doc`'s `.md`) stays the source |
| Reinventing design fundamentals | Defer to `artifact-design`; this skill is decision + mechanics |
| Horizontal body scroll | Wrap wide tables/diagrams in an `overflow-x:auto` container |

## Reference files

- `references/artifact-tool.md` — the full Artifact tool contract: every parameter (`file_path`, `favicon`, `description`, `label`, `url`, `force`), the complete CSP constraint list, title/description/favicon rules, update-in-place and `url` re-targeting, `409`/version-conflict handling, reading an existing Artifact via `WebFetch`, and when Markdown beats HTML. Read it before your first publish.
