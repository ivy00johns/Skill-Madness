# Payload Website Template — Anatomy (v3.90.2)

The official `website` template is the closest thing to a reference implementation of a marketing site on Payload: pages built from a layout builder, a blog, header/footer globals, draft + live preview, on-demand revalidation, SEO, redirects, search, and a form builder. Read this before scaffolding a site or before cloning one onto Payload.

Scaffold: `pnpx create-payload-app my-project -t website`. Variants that share this source: `templates/with-vercel-website` (same code with `vercelPostgresAdapter` + `vercelBlobStorage` and a daily cron in `vercel.json`), `templates/ecommerce` (same pattern plus `ecommercePlugin`).

## Contents

1. Stack and env
2. Directory map
3. Collections and globals
4. Layout builder: hero + blocks (catalog)
5. Rendering blocks on the frontend
6. Rich text (Lexical) and embedded blocks
7. Slugs
8. Authors and the `populatedAuthors` trick
9. Data fetching, caching, revalidation
10. Preview, live preview, drafts (pointer)
11. SEO, metadata, sitemap, robots
12. Redirects
13. Search
14. Forms
15. Tailwind and shadcn
16. Access-control model
17. Add a new block end to end (checklist)
18. Limits to fix before using it as a base for a real site
19. Doc drift and quirks found while reading
20. v4 canary deltas

## 1. Stack and env

> Verified against payload v3.90.2 (templates/website/package.json, .env.example, src/payload.config.ts, src/environment.d.ts).

- Next.js `16.3.3`, React `19.2.6`, Tailwind `^4.1.18` (+ `@tailwindcss/typography`, `tw-animate-css`), TypeScript `5.7.3`, `sharp`, `geist` fonts, `react-hook-form`, shadcn-style primitives on Radix, `next-sitemap`. Node `^18.20.2 || >=20.9.0`, pnpm 9-11.
- Default database is **MongoDB** (`mongooseAdapter`, `DATABASE_URL`). `.env.example` shows a Postgres URL as an alternative, but the template's config only imports the mongoose adapter; swapping adapters is a code change (see `with-vercel-website`).
- Env vars in `.env.example`: `DATABASE_URL`, `PAYLOAD_SECRET`, `NEXT_PUBLIC_SERVER_URL` (no trailing slash; drives CORS, links, sitemap), `CRON_SECRET` (jobs endpoint), `PREVIEW_SECRET` (draft preview). `environment.d.ts` only types the first four plus `VERCEL_PROJECT_PRODUCTION_URL`; add the other two yourself if you want typed access.
- `getServerSideURL()` resolution order: `NEXT_PUBLIC_SERVER_URL` -> `https://${VERCEL_PROJECT_PRODUCTION_URL}` -> `http://localhost:3000`. `getClientSideURL()` uses `window.location` in the browser.
- `next.config.ts` wraps with `withPayload(nextConfig, { devBundleServerPackages: false })`, whitelists `/api/media/file/**` in `images.localPatterns`, sets `images.qualities: [100]`, and adds a webpack `extensionAlias` for `.js -> .ts/.tsx`. `redirects.ts` only contains an IE (`Trident`) redirect; it is unrelated to the CMS redirects collection.
- Scripts: `generate:types`, `generate:importmap`, `payload` (CLI passthrough). `postbuild` runs `next-sitemap --config next-sitemap.config.cjs`.

## 2. Directory map

> Verified against payload v3.90.2 (`find templates/website/src`).

```
src/
  payload.config.ts            buildConfig: collections, globals, plugins, jobs, livePreview breakpoints
  plugins/index.ts             redirects, nested-docs, seo, form-builder, search
  collections/{Pages,Posts,Media,Categories,Users}
  Header/ Footer/              globals: config.ts + Component(.client).tsx + hooks/revalidate*.ts
  blocks/<Name>/{config.ts,Component.tsx}   + blocks/RenderBlocks.tsx
  heros/{config.ts,RenderHero.tsx,HighImpact,MediumImpact,LowImpact,PostHero}
  fields/{link.ts,linkGroup.ts,defaultLexical.ts}
  access/{anyone,authenticated,authenticatedOrPublished}.ts
  hooks/{populatePublishedAt,revalidateRedirects}.ts
  search/{beforeSync,fieldOverrides,Component}
  endpoints/seed/              demo content + image assets
  utilities/                   getGlobals, getDocument, getRedirects, generateMeta, generatePreviewPath, getURL, ...
  components/                  RichText, Link (CMSLink), Media, AdminBar, LivePreviewListener, PayloadRedirects, ui/* (shadcn)
  app/(frontend)/              [slug]/, posts/, search/, next/{preview,exit-preview,seed}, (sitemaps)/
  app/(payload)/               generated admin + API routes + importMap.js
```

`app/(payload)/*` and `admin/importMap.js` are generated ("DO NOT MODIFY"); regenerate the import map with `pnpm generate:importmap` whenever you add or move a component referenced by path string.

## 3. Collections and globals

> Verified against payload v3.90.2 (src/collections/*, src/Header/config.ts, src/Footer/config.ts, src/access/*).

| Slug | Purpose | Notes |
| --- | --- | --- |
| `pages` | layout-builder pages | tabs: Hero / Content / SEO; `publishedAt`; `slugField()`; drafts + autosave 100ms + `schedulePublish`; `maxPerDoc: 50`; `defaultPopulate: { title, slug }` |
| `posts` | blog | Lexical `content` with embedded blocks; `heroImage`, `relatedPosts`, `categories`, `authors`, hidden `populatedAuthors`; same versions config as pages |
| `media` | uploads | `folders: true`, `focalPoint: true`, `staticDir: public/media`, sizes `thumbnail 300`, `square 500x500`, `small 600`, `medium 900`, `large 1400`, `xlarge 1920`, `og 1200x630 crop center`; fields `alt`, `caption` (Lexical) |
| `categories` | taxonomy | `title` + `slugField({ position: undefined })`; nested-docs plugin adds `parent`/`breadcrumbs` |
| `users` | auth | `auth: true`, field `name`; all access = `authenticated` |
| `header`, `footer` (globals) | nav | `navItems` array (max 6) of `link({ appearances: false })`; `read: () => true`; `afterChange` revalidation |
| `redirects`, `forms`, `form-submissions`, `search` | from plugins | see plugins.md |

Access helpers: `anyone` (`() => true`), `authenticated` (`Boolean(req.user)`), `authenticatedOrPublished` (logged-in -> true, else query constraint `{ _status: { equals: 'published' } }`). Pages/Posts use `create/update/delete: authenticated`, `read: authenticatedOrPublished`. `defaultPopulate` limits what a relationship to pages/posts pulls in (posts also pull `categories`, `meta.image`, `meta.description`).

Root config extras: `editor: defaultLexical`, `sharp`, `cors: [getServerSideURL()]`, `typescript.outputFile: src/payload-types.ts`, and a `jobs.access.run` that allows a logged-in user OR `Authorization: Bearer ${CRON_SECRET}` (the Vercel Cron pattern); `jobs.tasks: []`. Live-preview breakpoints (Mobile 375x667, Tablet 768x1024, Desktop 1440x900) live at root `admin.livePreview`; the per-collection `url` is added on Pages and Posts.

## 4. Layout builder: hero + blocks (catalog)

> Verified against payload v3.90.2 (src/heros/config.ts, src/blocks/*/config.ts, src/fields/link.ts, linkGroup.ts, src/collections/Pages/index.ts).

`pages.hero` is a `group` (`src/heros/config.ts`):
- `type` select (required, default `lowImpact`): `none | highImpact | mediumImpact | lowImpact`
- `richText` (Lexical: root features + Heading h1-h4 + FixedToolbar + InlineToolbar)
- `links` = `linkGroup({ overrides: { maxRows: 2 } })`
- `media` upload -> `media`, `required: true`, shown only when type is `highImpact` or `mediumImpact` (`admin.condition`)

`pages.layout` is a required `blocks` field (`initCollapsed: true`) with exactly five blocks:

| slug (`blockType`) | interfaceName | Fields |
| --- | --- | --- |
| `cta` | `CallToActionBlock` | `richText`; `links` via `linkGroup({ appearances: ['default','outline'], overrides: { maxRows: 2 } })` |
| `content` | `ContentBlock` | `columns` array: `size` (`oneThird` default / `half` / `twoThirds` / `full`), `richText` (h2-h4), `enableLink` checkbox, `link` (shown when `enableLink`) |
| `mediaBlock` | `MediaBlock` | `media` upload (required) |
| `archive` | `ArchiveBlock` | `introContent`, `populateBy` (`collection` default / `selection`), `relationTo` (only `posts`), `categories` (hasMany), `limit` (default 10), `selectedDocs` (relationTo `['posts']`) |
| `formBlock` | `FormBlock` | `form` relationship -> `forms` (required), `enableIntro`, `introContent` (shown when `enableIntro`) |

Not layout blocks despite living in `src/blocks/`: `Banner` (`banner`: `style` info/warning/error/success + `content`) and `Code` (`code`: `language` typescript/javascript/css + `code`) are **Lexical BlocksFeature blocks** for post bodies; `RelatedPosts` is a plain component, no config.

Reusable field factories:
- `link({ appearances, disableLabel, overrides })` -> `link` group: `type` radio (`reference` default | `custom`), `newTab`, `reference` (relationTo `['pages','posts']`, required when shown), `url`, `label` (required unless `disableLabel`), `appearance` select (`default`/`outline`, or `false` to omit). Merged with `deepMerge`.
- `linkGroup({ appearances, overrides })` -> `links` array of `link`.
- Note: to link to another collection type (e.g. `case-studies`) you must edit `relationTo` in `link.ts`, `CMSLink`'s `reference.relationTo` type, `internalDocToHref` in `RichText`, and the Lexical `LinkFeature({ enabledCollections })` in `defaultLexical.ts` (all four hardcode `pages`/`posts`).

## 5. Rendering blocks on the frontend

> Verified against payload v3.90.2 (src/blocks/RenderBlocks.tsx, src/heros/RenderHero.tsx, src/app/(frontend)/[slug]/page.tsx).

```tsx
// RenderBlocks.tsx (abridged)
const blockComponents = { archive: ArchiveBlock, content: ContentBlock, cta: CallToActionBlock,
  formBlock: FormBlock, mediaBlock: MediaBlock }
// per block: <div className="my-16" key={index}><Block {...block} disableInnerContainer /></div>
```

- The map key must equal the block `slug`. Unknown `blockType` silently renders `null` (a new block that is not in the map shows nothing, no error).
- `RenderHero` maps `type` -> `HighImpactHero | MediumImpactHero | LowImpactHero`; `none` returns `null`. Heroes are client components that call `useHeaderTheme().setHeaderTheme('dark'|'light')` so the header restyles over imagery.
- Page composition (`[slug]/page.tsx`): `<article><PageClient/><PayloadRedirects disableNotFound url/>{draft && <LivePreviewListener/>}<RenderHero {...hero}/><RenderBlocks blocks={layout}/></article>`.
- `ArchiveBlock` is an async server component: with `populateBy: 'collection'` it runs `payload.find({ collection: 'posts', depth: 1, limit, where categories in [...] })` (no `overrideAccess: false`; the Local API bypasses access control by default, and never-published drafts are stored in the main collection with `_status: 'draft'` per `docs/versions/drafts.mdx`, so this query can return unpublished posts on a public page — INFERRED from those two documented rules, not run; add `overrideAccess: false` or a `_status` filter); with `selection` it uses the already-populated `selectedDocs[].value`.
- `FormBlock` is a client component posting JSON to `${clientURL}/api/form-submissions` with `{ form: formID, submissionData: [{ field, value }] }`; supports `confirmationType` `message` (renders Lexical) or `redirect`.
- `CMSLink` resolves `reference` to `/<collection>/<slug>` (pages omit the prefix) or falls back to `url`; `appearance` `inline` renders a bare `Link`, otherwise a shadcn `Button asChild`.

## 6. Rich text (Lexical) and embedded blocks

> Verified against payload v3.90.2 (src/fields/defaultLexical.ts, src/components/RichText/index.tsx, src/collections/Posts/index.ts).

- Root editor (`defaultLexical`): Paragraph, Underline, Bold, Italic, and a `LinkFeature` restricted to `enabledCollections: ['pages','posts']` with the default `url` field replaced by one that is required only when `linkType !== 'internal'`. Individual fields extend it via `lexicalEditor({ features: ({ rootFeatures }) => [...rootFeatures, HeadingFeature(...), FixedToolbarFeature(), InlineToolbarFeature()] })`.
- `posts.content` also adds `BlocksFeature({ blocks: [Banner, Code, MediaBlock] })` and `HorizontalRuleFeature`.
- Frontend: `RichText` wraps `@payloadcms/richtext-lexical/react`'s `RichText` with `jsxConverters` = `defaultConverters` + `LinkJSXConverter({ internalDocToHref })` + a `blocks` map (`banner`, `mediaBlock`, `code`, `cta`). `internalDocToHref` throws if the linked doc is not populated (`value` not an object) and maps `posts` -> `/posts/<slug>`, everything else -> `/<slug>`. If you add a Lexical block, add its converter here or it will not render.
- Body classes: `payload-richtext`, `container` when `enableGutter`, `prose md:prose-md dark:prose-invert` when `enableProse`.

## 7. Slugs

> Verified against payload v3.90.2 (packages/payload/src/fields/baseFields/slug/{index,generateSlug}.ts, packages/payload/src/utilities/slugify.ts, docs/fields/text.mdx).

- The template uses the core `slugField()` (import from `'payload'`), marked `@experimental` in source. It returns a `row` with a hidden `generateSlug` checkbox (default true) and the `slug` text field (`index: true`, `unique: true`, `required: true`, sidebar by default, custom `SlugField` admin component).
- Options: `name`, `checkboxName`, `disableUnique` (use with multi-tenant + compound index), `useAsSlug` (default `'title'`), `localized`, `position`, `required`, `slugify`, `overrides(field)`. `fieldToUse` is deprecated.
- Generation rules: on **create**, `slug = slugify(data.slug || data[useAsSlug])` — a slug you supply is respected but still passes through slugify; on **update** it regenerates only while `generateSlug` is checked (with autosave on, only until the doc has more than 2 versions or is published, and never after a manual edit).
- Default `slugify` = `trim -> spaces to '-' -> strip /[^\w-]+/ -> lowercase`. It **removes slashes, dots, and non-ASCII letters** (`about/team` -> `aboutteam`, `café` -> `caf`). Cloning a site with legacy URLs needs a custom `slugify` (or a plain `text` field named `slug`) or you will silently mangle paths.
- Home page convention: slug `home` is served at `/` (`[slug]/page.tsx` defaults `slug = 'home'`; revalidation maps `home` -> `/`; `generateStaticParams` filters `home` out).

## 8. Authors and the `populatedAuthors` trick

> Verified against payload v3.90.2 (src/collections/Posts/index.ts, hooks/populateAuthors.ts).

`users` read access is `authenticated`, so a public `posts` query cannot populate `authors` (a relationship to users). The template adds a hidden, non-updatable `populatedAuthors` array (`id`, `name`) and an `afterRead` hook that `findByID`s each author with `depth: 0` (and default `overrideAccess: true`) and copies only `id` + `name`. Use this pattern to expose a safe subset of a locked collection. Errors are swallowed. The hook does not pass `req`, so it does not join the request's transaction.

`publishedAt`: pages use a `beforeChange` collection hook (`populatePublishedAt`: sets it to now on create/update whenever the incoming `req.data.publishedAt` is empty — so the first save stamps it, drafts and autosaves included, not only publishing); posts use a field-level `beforeChange` that sets it when `siblingData._status === 'published'`.

## 9. Data fetching, caching, revalidation

> Verified against payload v3.90.2 (src/utilities/getGlobals.ts, getDocument.ts, getRedirects.ts, src/*/hooks/revalidate*.ts, src/app/(frontend)/**).

Page query (identical for posts):

```ts
const queryPageBySlug = cache(async ({ slug }) => {
  const { isEnabled: draft } = await draftMode()
  const payload = await getPayload({ config: configPromise })
  const result = await payload.find({ collection: 'pages', draft, limit: 1, pagination: false,
    overrideAccess: draft, where: { slug: { equals: slug } } })
  return result.docs?.[0] || null
})
```

`overrideAccess: draft` is the key: outside draft mode access control applies (anonymous -> published only via `authenticatedOrPublished`); in draft mode (only reachable through the authenticated preview route) access is bypassed so unpublished docs render.

Cache helpers (all `unstable_cache` with tags):
- `getCachedGlobal(slug, depth)` -> tag `global_<slug>` (header/footer, depth 1)
- `getCachedRedirects()` -> tag `redirects` (all redirects, `limit: 0, pagination: false`)
- `getCachedDocument(collection, slug)` -> tag `<collection>_<slug>` — **nothing in the template ever revalidates this tag**; it is only used to resolve a redirect target, so a renamed target can serve a stale slug until the cache is otherwise invalidated.
- Sitemaps: `unstable_cache` tags `pages-sitemap` / `posts-sitemap`.

Revalidation hooks (`context.disableRevalidate` skips them — set it when seeding or bulk-importing):
- `revalidatePage` / `revalidatePost` (`afterChange`): if `_status === 'published'` -> `revalidatePath(path)` + `revalidateTag('<x>-sitemap', 'max')`; if it was published and no longer is -> revalidate the OLD path (`previousDoc.slug`). `afterDelete` revalidates the path. Paths: page `home` -> `/`, else `/<slug>`; post -> `/posts/<slug>`.
- Header/footer `afterChange`: `revalidateTag('global_header' | 'global_footer', 'max')`.
- redirects plugin override: `afterChange: [revalidateRedirects]` -> `revalidateTag('redirects', 'max')`.
- UNVERIFIED: the two-argument `revalidateTag(tag, 'max')` form is the Next 16 signature; semantics of `'max'` were not re-read from Next docs in this session.
- Not revalidated by any hook: the `/posts` index (`export const dynamic = 'force-static'; export const revalidate = 600`) and `/posts/page/[n]` (`revalidate = 600`) — new posts show up on listing pages after up to 10 minutes. A changed image needs the owning page republished (README note).
- Static params: `generateStaticParams` in `[slug]` and `posts/[slug]` queries `limit: 1000, draft: false, overrideAccess: false, pagination: false, select: { slug: true }` — sites with more than 1000 pages/posts silently stop pre-rendering the rest.
- Revalidation calls from `afterChange` only work inside a running Next process. The seed code notes that revalidate errors are expected when seeding from a script without a server.

## 10. Preview, live preview, drafts

> Verified against payload v3.90.2 (src/utilities/generatePreviewPath.ts, src/app/(frontend)/next/preview/route.ts, src/components/LivePreviewListener).

Summary only — full detail and failure modes in `live-preview-and-drafts.md`. Flow: admin `preview`/`livePreview.url` return `/next/preview?path=<encoded>&previewSecret=<PREVIEW_SECRET>` -> route checks the secret, `getSafeRedirect` on `path`, `payload.auth` for a logged-in user, `draftMode().enable()`, redirects to the path -> page renders with `draft: true` and mounts `<LivePreviewListener/>` (`RefreshRouteOnSave` -> `router.refresh`). `/next/exit-preview` disables draft mode; the `AdminBar` calls it.

## 11. SEO, metadata, sitemap, robots

> Verified against payload v3.90.2 (src/plugins/index.ts, src/utilities/generateMeta.ts, mergeOpenGraph.ts, next-sitemap.config.cjs, src/app/(frontend)/(sitemaps)/*, src/app/(frontend)/layout.tsx).

- Each collection embeds the SEO fields **directly** (`OverviewField`, `MetaTitleField({ hasGenerateFn: true })`, `MetaImageField({ relationTo: 'media' })`, `MetaDescriptionField({})`, `PreviewField(...)`) inside a `meta` named tab. See plugins.md for why the template's `seoPlugin({ generateTitle, generateURL })` call (no `collections`) matters.
- `generateMeta({ doc })` builds Next `Metadata`: title = `meta.title + ' | Payload Website Template'`, description, `openGraph` merged with defaults (`mergeOpenGraph`), image = `meta.image.sizes.og.url` (falls back to `meta.image.url`, then `/website-template-OG.webp`). The site name string is hardcoded in `generateMeta.ts`, `mergeOpenGraph.ts`, and `plugins/index.ts` — change all three. Root layout sets `metadataBase`, `twitter.creator: '@payloadcms'`.
- Sitemaps: `pages-sitemap.xml` and `posts-sitemap.xml` are route handlers (`getServerSideSitemap` from `next-sitemap`) querying published docs (`limit: 1000`, `select: slug, updatedAt`); the pages sitemap also lists `/search` and `/posts`. `next-sitemap.config.cjs` generates `robots.txt` (disallow `/admin/*`, adds both sitemap URLs) and excludes the dynamic routes from its own crawl.

## 12. Redirects

> Verified against payload v3.90.2 (src/components/PayloadRedirects/index.tsx, src/utilities/getRedirects.ts, packages/plugin-redirects/src/index.ts).

`PayloadRedirects` (server component) is rendered when a page/post is NOT found (`notFound()` unless `disableNotFound`) and also on found pages (`disableNotFound`) so a redirect can override a live URL. It loads all redirects (cached), finds `from === url`, then `redirect(to.url)` or resolves `to.reference` (fetching by `getCachedDocument` if only an id string) to `/<collection>/<slug>` (pages unprefixed). It uses `redirect()` from `next/navigation` and never reads a redirect `type`: the template does not configure `redirectTypes`, so there is no status-code field. For SEO-grade migrations add `redirectTypes: ['301', ...]` to the plugin and use `permanentRedirect()` for permanent ones (UNVERIFIED: which HTTP status Next emits for `redirect()` vs `permanentRedirect()` was not checked in this session).

## 13. Search

> Verified against payload v3.90.2 (src/search/*, src/app/(frontend)/search/page.tsx, packages/plugin-search/src/Search/index.ts).

`searchPlugin({ collections: ['posts'], beforeSync, searchOverrides.fields += slug, meta{title,description,image}, categories[] })` — **only posts are indexed, not pages**. `beforeSyncWithSearch` copies `slug`, `meta`, and expands categories to `{ relationTo, categoryID, title }`. The `/search` page runs `payload.find({ collection: 'search', depth: 1, limit: 12, pagination: false, where: { or: [title like q, meta.description like q, meta.title like q, slug like q] } })` — a `like` scan, not full-text search; fine for small sites.

## 14. Forms

> Verified against payload v3.90.2 (src/blocks/Form/*, src/plugins/index.ts).

`formBuilderPlugin({ fields: { payment: false }, formOverrides.fields: confirmationMessage editor swapped for a Lexical editor with FixedToolbar + Heading h1-h4 })`. Frontend field components live in `src/blocks/Form/*`; `fields.tsx` maps `blockType` -> component for exactly `checkbox, country, email, message, number, select, state, text, textarea` (`Width` and `Error` are helpers, not field types). Any other enabled plugin field type (`radio`, `date`, `payment`, `upload`) has no renderer and is silently skipped — add a component and a map entry when you enable one.

## 15. Tailwind and shadcn

> Verified against payload v3.90.2 (src/app/(frontend)/globals.css, tailwind.config.mjs, components.json, postcss.config.js, src/cssVariables.js).

Tailwind v4 via `@import 'tailwindcss'` + `@config '../../../tailwind.config.mjs'` (typography plugin via `@plugin`), `@custom-variant dark (&:is([data-theme='dark'] *))` (dark mode keyed on a `data-theme` attribute, set by `InitTheme`/`ThemeSelector`), `@theme` breakpoints (`sm 40rem, md 48rem, lg 64rem, xl 80rem, 2xl 86rem`), Geist fonts as `--font-sans/--font-mono`, and `@source inline(...)` safelists for dynamically composed classes (`lg:col-span-4/6/8/12`, `border-border`, `bg-card`, `border-error`, `bg-error/30`, `border-success`, `bg-success/30`, `border-warning`, `bg-warning/30`). `components.json` (`style: default`, `baseColor: slate`, `cssVariables: true`, aliases `@/components`, `@/utilities/ui`) means `npx shadcn add <component>` works. `cn()` lives in `@/utilities/ui`. The admin panel gets its own `app/(payload)/custom.scss`.

## 16. Access-control model

> Verified against payload v3.90.2 (src/access/*, collections).

Public reads: `media`, `categories`, `header`/`footer` (globals), `redirects`, `forms`, `search` (plugin defaults `read: () => true`), pages/posts only when published. Locked: `users` (authenticated), `form-submissions` (read only for the admin user collection; anyone may create), form `emails` field. Writes: authenticated users only. Every authenticated user is effectively an admin — there are no roles. Add roles before giving editors accounts.

## 17. Add a new block end to end (checklist)

> Verified against payload v3.90.2 (RenderBlocks.tsx, Pages/index.ts, payload-types.ts generation via `generate:types`).

1. `src/blocks/<Name>/config.ts`: `export const Name: Block = { slug: 'name', interfaceName: 'NameBlock', fields: [...] }`. Set `interfaceName` so the generated TS type is stable and shareable.
2. `src/blocks/<Name>/Component.tsx`: props typed from `import type { NameBlock } from '@/payload-types'`. Accept `disableInnerContainer` if the wrapper passes it. Use a client component only when you need hooks.
3. Register the config in `pages.layout.blocks` (`src/collections/Pages/index.ts`); if posts should embed it in rich text, add to `BlocksFeature({ blocks })` instead/as well.
4. Register the component in `blockComponents` in `src/blocks/RenderBlocks.tsx` under the same key as `slug`; for Lexical blocks also add a converter in `src/components/RichText/index.tsx` and extend the `NodeTypes` union.
5. `pnpm generate:types` (updates `src/payload-types.ts`; types are stale until you do) and `pnpm generate:importmap` (needed if the block uses a custom admin component path string, e.g. `RowLabel`).
6. If you use a Postgres/SQLite adapter: `pnpm payload migrate:create` and commit the migration (block tables are schema).
7. Add the block to seed content in `src/endpoints/seed/*` and check it in Live Preview (breakpoints Mobile/Tablet/Desktop).
8. If the block reads other documents (like `ArchiveBlock`), decide its `depth`, `overrideAccess`, and cache/revalidation tag explicitly — the template's archive block does none of that.

## 18. Limits to fix before using it as a base for a real site

> Verified against payload v3.90.2 (src/app/(frontend)/[slug]/page.tsx, src/collections/*, src/fields/link.ts).

- **Single-segment routes only**: `[slug]/page.tsx` handles `/about`, not `/about/team`. Nested URLs need a `[...slug]` catch-all and either a `path`/`fullPath` field or the nested-docs plugin on `pages` (the template applies nested-docs to `categories` only) with `breadcrumbs[last].url` as the canonical path. Revalidation paths, sitemap URLs, `generatePreviewPath`, and `PayloadRedirects` all assume `/<slug>` and must change together.
- Only two linkable collections (`pages`, `posts`) and one archive source (`posts`); add collections in `link.ts`, `CMSLink`, `internalDocToHref`, `LinkFeature`, `Archive.relationTo`.
- No roles/tenancy; no localization; no `sitemap` for custom collections; search indexes posts only.
- Hardcoded "Payload Website Template" strings (title suffix, OG site name, `twitter.creator`, favicons, `website-template-OG.webp`).
- Global slug uniqueness (`slugField` default `unique: true`) — two sections of a site cannot share a slug in one collection.

## 19. Doc drift and quirks found while reading

> Verified against payload v3.90.2 (templates/website/README.md vs src; grep for `_api`, `force-dynamic`, `no-store`).

- README "Cache" section describes `./src/app/_api`, `no-store` fetches and `export const dynamic = 'force-dynamic'`; none of these exist in `src` (grep returned no matches). Treat it as stale; caching is `unstable_cache` + tags + `revalidatePath` as documented in section 9.
- README says the seed user is `demo-author@payloadcms.com`; `endpoints/seed/index.ts` creates and deletes `demo-author@example.com`.
- The seed clears `categories, media, pages, posts, forms, form-submissions, search` via `payload.db.deleteMany` and deletes their versions (and blanks header/footer `navItems`) — destructive on those collections whether you run it from the admin button (`POST /next/seed`, requires a logged-in user) or a script. It fetches its demo images from `raw.githubusercontent.com/.../refs/heads/3.x/...` at runtime.
- `posts` `populatedAuthors` and `populateAuthors` exist purely because of locked `users` access (see section 8).

## 20. v4 canary deltas

> Diffed against payload main `5448061a` (4.0.0-canary.37) vs tag v3.90.2, `templates/website`.

- v4: `slugField()` is replaced by a field type: `{ name: 'slug', type: 'slug', useAsSlug: 'title' }`.
- v4: `payload.config.ts` declares an explicit `folders` collection (`folders: true`, `useAsTitle: 'name'`) ahead of the others.
- v4: `Pages`/`Posts` drop the `CollectionConfig<'pages'>` slug generic (comment cites a TypeScript 6 regression with `defaultPopulate`).
- v4: `getCachedGlobal`'s `findGlobal` adds `overrideAccess: true`.
- v4 main's preview route still uses `if (!path.startsWith('/'))` where v3.90.2 uses `getSafeRedirect` from `payload/shared` — the older check accepts protocol-relative `//host` paths. Use the v3.90.2 form.
- v4: `next.config.ts` drops the `sassOptions.loadPaths` Windows workaround (admin styles moved from `.scss` to `.css` in the packages).
- Unchanged in the diff: `payload.config` plugins block, `revalidatePage`, `RenderBlocks`, `LivePreviewListener`, `heros/config.ts`.
