---
name: payload-cms
version: 1.0.0
description: |
  Build, extend, deploy and debug websites on Payload CMS (payloadcms.com): collections, blocks and layout builder, live preview, drafts, plugins, Postgres or Mongo, Vercel, migrations, plus cloning or rebuilding an existing site (including payloadcms.com itself) onto Payload. Use this skill whenever the user mentions Payload, Payload CMS, payload.config.ts, @payloadcms packages, a headless CMS or CMS for their websites, moving a site onto a CMS, cloning payloadcms.com, or asks how to model pages, blocks, a blog, redirects, SEO, forms or preview in Payload, even without saying "Payload". Complements Payload's own official payload skill with the website workflow, version pinning and verified pitfalls.
compatibility: "Any coding agent host; needs shell, file access and web access. Browser checks use Playwright."
composes_with: ["playwright", "website-walkthrough-video", "design-token-guard", "class-extraction-guard", "render-sanity", "orchestrator", "ui-brief"]
---

# Payload CMS for websites

Payload is a TypeScript-first, code-configured headless CMS that installs inside a Next.js app: one project serves the admin panel, the REST and GraphQL APIs, and your frontend. That shape is why it suits "a CMS for all our websites": a site's content model lives in reviewable code, editors get an admin UI, and the frontend reads content through an in-process Local API.

This skill is a routing layer over verified reference files. The references were written by reading the Payload source and docs at v3.90.2, the `payloadcms/website` repo (the code behind payloadcms.com), and the live site, on 2026-09-24. Payload's own official skill (named `payload`, installed by `create-payload-app`) covers generic app development; this one adds the website workflow, cloning, deployment and the traps found while reading. They coexist.

## Step 0: establish the version before anything else

Payload's `main` branch is a v4 canary while npm `latest` is v3. Advice for one can silently break the other (v4 flips `overrideAccess`, `defaultDepth`, versions defaults and drops Next 15 and Slate).

1. Read the project's `package.json` for `payload` and every `@payloadcms/*` version (they must all match exactly).
2. For a new project, default to v3.90.x pinned exactly. Choose v4 only if the user asks and accepts canary churn (`references/v4-delta.md` section 9).
3. Re-check `npm view payload dist-tags` if the work is more than a few weeks after 2026-09-24; the references are a dated snapshot. When a reference and the installed package disagree, trust the installed package's types and docs.

## Route the task

| The user wants | Read |
|---|---|
| Build or rebuild a site on Payload, or clone a site (payloadcms.com or their own) | `references/clone-a-site-workflow.md`, then `references/clone-recipes.md` |
| How payloadcms.com is actually built (collections, blocks, docs pipeline, styling) | `references/payloadcms-com-anatomy.md` |
| Scaffold from the official website template, add a block end to end | `references/website-template.md` |
| Config, collections, globals, versions, uploads, auth, localization | `references/config-and-collections.md` |
| A field type, blocks, relationships, Lexical rich text, slugs | `references/fields.md` |
| Access control, hooks, revalidation | `references/access-and-hooks.md` |
| Querying, Local API, REST, GraphQL, seeding | `references/local-api-and-queries.md` |
| Drafts, preview button, live preview, scheduled publish | `references/live-preview-and-drafts.md` |
| SEO, redirects, nested pages, forms, search, multi-tenant, storage, email | `references/plugins.md` |
| Scaffold, env vars, Docker, Vercel, Cloudflare, production checklist | `references/scaffolding-and-deploy.md` |
| Database choice, migrations, push vs migrate, transactions | `references/database-and-migrations.md` |
| Slow queries, build problems, an error message, "works in dev only" | `references/performance-and-troubleshooting.md` |
| v3 vs v4, upgrading, whether to pin | `references/v4-delta.md` |

Load only what the task needs; each file is dense and has its own contents list. Every H2 in a reference names the source it was verified against. Items marked `UNVERIFIED` were not confirmed; say so instead of presenting them as fact.

## Mental model

- **Config is code.** `payload.config.ts` (`buildConfig`) declares collections (many documents: pages, posts, media, users), globals (one document: header, footer), fields, access rules, hooks, plugins and the database adapter. Types come from `payload generate:types`; the admin's custom-component map comes from `payload generate:importmap`. Regenerate both after schema or component changes.
- **Pages are a layout builder.** A `pages` collection with a `hero` group and a `layout` field of type `blocks`. Each block is a schema plus a React renderer chosen by `blockType`. New section = new block config + renderer + map entry + regenerated types.
- **The frontend reads with the Local API** (`getPayload({ config })` then `payload.find(...)`) inside Server Components, no HTTP hop. Cache with Next primitives and invalidate in `afterChange` hooks.
- **Drafts are separate from published.** With `versions.drafts`, a `_status` field exists, public reads must be limited to published, and preview uses Next draft mode.
- **Plugins are config functions** (`(config) => config`). The official ones cover SEO, redirects, nested pages, forms, search, import/export, multi-tenant, storage and email.

## Rules that prevent the expensive mistakes

Each rule has the reason attached so you can judge edge cases. Details and citations are in the references.

1. **Pin versions exactly and keep them in lockstep.** Mixed `@payloadcms/*` versions produce admin and hydration breakage that looks unrelated. Upgrades are deliberate.
2. **Local API skips access control by default in v3.** `overrideAccess` defaults to `true` even when you pass `user`. Pass `overrideAccess: false` whenever acting for a user, and write `overrideAccess` explicitly everywhere so code survives v4, where the default flips.
3. **Thread `req` through nested operations in hooks.** Without it the nested call runs outside the transaction and can leave partial data. Guard hook-triggered writes with a `context` flag or the hook re-fires forever.
4. **Public reads of drafted collections must filter `_status: published`** in the access function, or drafts leak through REST, GraphQL and the Local API.
5. **`depth` decides whether relationships are objects or IDs.** Reusable-content and upload blocks render nothing when fetched too shallowly. Set depth per query rather than trusting defaults (v4 changes the default).
6. **Unknown `blockType` renders nothing, silently.** payloadcms.com itself ships a block (`exampleTabs`) registered in the schema with no renderer. Add a parity check so a schema-only block fails CI.
7. **Do not infer a Payload site's blocks from its DOM.** Reusable content inlines other blocks. Read the page document from the API (`clone-recipes.md` section 4), and only use read-only public routes on sites you do not own.
8. **`push` is for development; production uses committed migrations.** Dev push records itself in the migrations table in a way that makes a later `payload migrate` on that database warn about data loss. MongoDB transactions need a replica set.
9. **The website template's "Seed the database" button and any `deleteMany` seed wipe content.** Never run it against a database with real content.
10. **Check the SEO plugin config before trusting auto-generate.** Read from the plugin source (not run): the generate endpoints reject collections that are not in `seoPlugin({ collections })`, and the template's call omits that option. Test the button in the admin.
11. **The default slugify strips everything outside letters, digits, underscore and hyphen.** Legacy URLs with slashes, dots or non-ASCII characters mangle on import. Import slugs verbatim through a custom `slugify` or `unique` fields, and model nested paths with the nested-docs plugin.
12. **Guard every custom endpoint, and never ship `admin.autoLogin` outside development.** payloadcms.com's own repo has sync and redeploy endpoints with no check in code and an unconditional `autoLogin`. Do not copy either.
13. **Preview and revalidation secrets stay server-side**; the preview secret in a URL is visible to any admin, which is acceptable only for admin-only use.
14. **Images do not import themselves.** HTML and Markdown to Lexical converters drop or ignore image references unless you upload first and mark them with the documented attributes or placeholders.
15. **Copy structure, not brand.** A clone of someone else's site takes the information architecture and field names; their copy, logos, customer names and fonts stay theirs. payloadcms/website code is MIT but ships no content and no font license.

## Standard workflows

**New website on Payload.** Step 0, then scaffold (`npx create-payload-app@latest my-site -t website`), choose the database, then follow `clone-a-site-workflow.md` phases 0-7 with your own design brief instead of a source site (the `ui-brief` skill writes one).

**Clone or rebuild an existing site.** Follow `references/clone-a-site-workflow.md`: inventory the source with Playwright or the API, map sections to blocks and pages to collections, extract tokens from computed styles, build in the documented order, import content, verify parity against the running site, harden.

**Add a block.** `website-template.md` section 17 is the end-to-end checklist (block config, renderer, map entry, types, import map, preview).

**Deploy.** `scaffolding-and-deploy.md`: env vars, build-time database connection, migrations in CI, storage adapter, production checklist. Verify the deployed site, not the dev server: publish a change and confirm it reaches the public page.

**Debug.** Start with the symptom table in `performance-and-troubleshooting.md`. The usual suspects are stale generated types or import map, mismatched package versions, missing `req` in hooks, wrong `depth`, and draft versus published reads.

## Verification stance

State a Payload fact as true only after tracing it to the installed package, the docs for that version, or the running app. When you cannot, write "unverified". Run the app and look at it (Playwright, visible browser) before reporting UI work done; type-checks and tests do not prove that a page renders its blocks or that preview works. When a user complaint is "smaller" or "tighter", measure before claiming it.

## Maintenance

The references are a snapshot (Payload v3.90.2, v4.0.0-canary.37, payloadcms/website at commit 023c2a5, checked 2026-09-24). To refresh: re-run the version checks in `v4-delta.md` section 1, then re-verify the sections whose cited paths changed in the Payload repo. Update the snapshot lines and this skill's version together.
