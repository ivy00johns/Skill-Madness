# Clone a site onto Payload: end-to-end workflow

Procedure for taking an existing website (a public reference site such as payloadcms.com, or your own current site ahead of a redo) and reproducing it on Payload so the CMS is already in place. This file is the process; the per-section schemas and code live in `clone-recipes.md` and `payloadcms-com-anatomy.md`, and version/API detail in the other references.

## Contents

1. Decide what "clone" means
2. Phase 0: pin the stack and scaffold
3. Phase 1: inventory the source site
4. Phase 2: turn sections into blocks and pages into collections
5. Phase 3: design tokens and styling
6. Phase 4: build the CMS and renderers
7. Phase 5: import content
8. Phase 6: parity verification
9. Phase 7: hardening before editors touch it
10. Composing with other skills

## 1. Decide what "clone" means

Ask which of these it is; the rules differ.

| Kind | What you copy | What you must not copy |
|---|---|---|
| Rebuild your own site on Payload (the redo) | Structure, content, assets you own | nothing restricted |
| Structural clone of someone else's site (payloadcms.com as a pattern) | Page structure, section taxonomy, field names, information architecture | Their copy, images, logos, customer names, brand assets, fonts without a license |
| Reuse of an open-source site repo | Code, under its license | Anything the license or brand rules exclude |

For payloadcms.com specifically: the `payloadcms/website` repo is MIT-licensed code, contains no content export, and ships fonts and brand assets with no separate license (see `payloadcms-com-anatomy.md` section 1). Take the architecture, replace the brand.

Content and brand belong to their owner. Only structure and field names of a third-party site go into your schema.

## 2. Phase 0: pin the stack and scaffold

1. Pin Payload v3.90.x exactly for a real project (see `v4-delta.md` section 9); every `@payloadcms/*` package, `react` and `react-dom` at one version. Re-check `npm view payload dist-tags` first; versions move.
2. Scaffold from the `website` template (`npx create-payload-app@latest my-site -t website`; flags in `scaffolding-and-deploy.md` section 2) rather than blank. It gives pages, posts, layout builder, drafts, live preview, SEO, redirects, forms, search. Diff against the recipes instead of porting a bigger site wholesale.
3. Pick the database once (Postgres or Mongo for production; `database-and-migrations.md` section 1) and commit migrations from day one if SQL.
4. Get the template running and open `/admin` before changing anything, so later breakage is yours, not the template's.

## 3. Phase 1: inventory the source site

Goal: a list of URLs, the page-type taxonomy, and the section taxonomy, taken from the live source rather than guessed.

1. URL list: `sitemap.xml` (and nested sitemap files), then `robots.txt`. Note redirects and 404s.
2. If the source is a Payload site, read structure from the API, not the DOM: run the census script in `clone-recipes.md` section 4 against `/api/pages`. DOM class names mislead when reusable content inlines other blocks. Only published documents are visible; only fetch read-only routes and never call routes that look like jobs or syncs on someone else's site.
3. If the source is not Payload: drive the site with Playwright (the `playwright` skill; Playwright only), capture full-page screenshots at desktop and mobile widths, and record for each page the ordered list of sections. The `website-walkthrough-video` skill captures every page deterministically and its screenshots double as the parity baseline.
4. Group pages into types (marketing page, blog post, blog index, case study, directory, docs page, form page, legal). Each type is a collection or a page template.
5. Group sections into a taxonomy by behaviour, not pixels: a "testimonial band" and a "testimonial carousel" differ in behaviour, two differently colored CTAs do not. Count uses per section across pages.
6. Write the inventory to a file in the repo (URL, page type, ordered sections, notes). It is the checklist Phase 6 verifies against.

## 4. Phase 2: turn sections into blocks and pages into collections

1. Start from the top of the usage count. On payloadcms.com nine blocks cover 144 of 167 block uses, so build those first and leave the long tail for later.
2. Map each section to the smallest block schema that reproduces its behaviour (`clone-recipes.md` section 1 has the mapping table with real schemas). Give every block a shared settings group (theme, background) through one helper so spacing and theming come from one place.
3. Repeated stacks (footer CTA, "talk to us") become a reusable-content collection referenced by a block, not copied blocks.
4. Page types with their own URLs become collections (posts + categories, case studies, directory items); everything else is `pages` with `hero` + `layout`. Navigation and footer are globals.
5. Cap arrays where the design breaks (`maxRows`/`minRows`), and use `admin.condition` for type-specific fields rather than separate blocks.
6. Record the section-to-block decision in the inventory file so a reviewer can see why each block exists.

## 5. Phase 3: design tokens and styling

1. Extract tokens from the source with computed styles (colors, font sizes, spacing scale, radii, breakpoints, shadows) through Playwright `evaluate`, not by eyeballing screenshots. Put them in CSS custom properties or the template's Tailwind config once.
2. If the source is payloadcms.com, its approach is SCSS Modules plus `--color-*` tokens mapped to `--theme-*` under `data-theme`, with block-level `settings.theme` (`payloadcms-com-anatomy.md` section 8). The template you scaffolded uses Tailwind and shadcn instead; choose one system and stay in it.
3. Run the `design-token-guard` and `class-extraction-guard` gates before calling styling done; a hardcoded hex or repeated utility soup passes a visual review unnoticed.
4. Fonts: use only fonts you are licensed for. Do not copy a source site's font files.

## 6. Phase 4: build the CMS and renderers

Follow this order; each step has its dependencies satisfied by the previous one (`payloadcms-com-anatomy.md` section 12):

1. Block configs, registered once in the top-level config (`config-and-collections.md`, `fields.md` section 2).
2. `pages` collection: drafts, nested-docs breadcrumbs, SEO, redirects; access helpers (`access-and-hooks.md`).
3. `RenderBlocks` with a `blockType` to component map, a hero type map, and a parity check so a schema-only block fails CI (`clone-recipes.md` section 3).
4. Header and footer globals, fetched once in the layout and cached.
5. Draft preview, live preview and revalidation before any editor touches content (`live-preview-and-drafts.md`). Verify a publish reaches the CDN, not just the dev server.
6. Collections with their own URLs: posts and categories, case studies, directories, docs (`clone-recipes.md` sections 5-7).
7. Forms, then SEO metadata, sitemap and robots (and `llms.txt` for docs-heavy sites).
8. Regenerate types and the import map after every schema change: `payload generate:types`, `payload generate:importmap`. Stale generated files are a common source of "works in dev, breaks in build".

For a large build, split by file ownership (block configs + collections, renderers + styling, plugins + preview) and use the `orchestrator` skill; contracts are the block schemas and generated types.

## 7. Phase 5: import content

1. Write a seed or import script and run it with `payload run ./src/seed.ts` (it loads the config and gives you `getPayload`). Keep scripts idempotent: look up by a natural key (slug) and update, not create again.
2. Upload assets first. Create `media` documents with the Local API (`payload.create({ collection: 'media', data: { alt }, filePath })`) and keep a map from source URL to media ID.
3. Convert rich text with the official converters, verified in the v3.90.2 docs (`docs/rich-text/converting-html.mdx`, `converting-markdown.mdx`):
   - HTML: `convertHTMLToLexical({ editorConfig: await editorConfigFactory.default({ config }), html, JSDOM })` from `@payloadcms/richtext-lexical`; requires `jsdom`. `img` tags are not uploaded automatically; pre-upload and add `data-lexical-upload-id` and `data-lexical-upload-relation-to` attributes or images are dropped.
   - Markdown: `convertMarkdownToLexical({ editorConfig, markdown })`. Standard image syntax is not turned into upload nodes; rewrite to the `![media:ID]()` placeholder after uploading.
4. Import in dependency order: media, categories and filter collections, authors, then pages and posts, then relationship fields, then globals.
5. Set `overrideAccess: true` explicitly in import scripts (the v3 default, and required semantics on v4), and write drafts as drafts (`draft: true`) or published as intended so nothing goes live by accident.
6. Beware the website template's "Seed the database" button and any `deleteMany`-based seed: it wipes content. Never point a destructive seed at a database with real content.
7. Compare counts after import: pages, posts, media, redirects versus the inventory.

## 8. Phase 6: parity verification

Verify against the running site, not from memory (Playwright only):

1. For each URL in the inventory, screenshot the clone and the source at the same viewports and compare. Check structure first (sections present, in order, right block), then spacing, typography, color.
2. Every internal link on list pages resolves; no `undefined`, lone `?`, empty sections or "Couldn't load" shells (the `render-sanity` skill checks these).
3. Preview works: open a draft from the admin, change a field, see it update; publish and confirm the public page changes.
4. Redirects from the old URLs work (import the source's redirect map into the redirects collection or `next.config`).
5. SEO parity: titles, descriptions, canonical, OG images, sitemap entries, robots. Do not trust an auto-generate button without testing it (see the SEO plugin note in `plugins.md`).
6. Keep before/after evidence in the repo scratch or `.playwright/<run-id>/`; use `website-walkthrough-video` for a stakeholder-friendly tour.

## 9. Phase 7: hardening before editors touch it

1. Every custom endpoint checks `req.user` role or a shared secret. payloadcms.com's own repo has sync and redeploy endpoints with no check in code; do not copy that pattern.
2. No `admin.autoLogin` outside development, and gate it by `NODE_ENV` with `prefillOnly`.
3. `overrideAccess: false` wherever a user identity is passed to the Local API.
4. Preview secret and revalidation key set in production env; secrets never in client bundles.
5. Production checklist in `scaffolding-and-deploy.md` section 12; performance pass in `performance-and-troubleshooting.md`.
6. Write v4-safe code now (explicit `overrideAccess`, `depth`, `versions`) so the later upgrade is small.

## 10. Composing with other skills

| Need | Skill |
|---|---|
| Browser capture, screenshots, click-through | `playwright` |
| Video tour of source and clone | `website-walkthrough-video` |
| Token and styling gates | `design-token-guard`, `class-extraction-guard` |
| Broken-page and dead-link sweep | `render-sanity` |
| Design brief for a redesign rather than a copy | `ui-brief` |
| Multi-agent build of a large site | `orchestrator`, `contract-author` |
| Publishing a plan or report | `artifact-publish` |
