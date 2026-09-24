# Clone recipes from payloadcms.com

Concrete recipes for rebuilding a site shaped like payloadcms.com on Payload 3.x. Each recipe cites the `payloadcms/website` files it comes from (commit `023c2a5`, payload 3.90.1, Next 16.3.3). For the full picture read `payloadcms-com-anatomy.md` first.

Code below is trimmed from the cited files; treat the repo as the source of truth for exact signatures.

## Contents

1. Map page sections to blocks
2. Pages with a layout builder
3. Renderer map and a parity check
4. Reading a live Payload site's structure
5. Blog with categories and authors
6. Case studies and a partner directory
7. CMS-driven docs
8. Forms and lead capture
9. Redirects
10. SEO and Open Graph
11. Draft preview and revalidation
12. Order of operations

## 1. Map page sections to blocks

> Verified against website repo @ 023c2a5 (`src/blocks/*/index.ts`, `src/components/blocks/*`, `Hero/index.tsx`) and live API census 2026-09-24

Decide the schema from the section's behaviour, not its pixels. This table lists what payloadcms.com actually shipped; the right column is the smallest schema that reproduces the section.

| Section seen on the site | Repo block | Minimal schema to reproduce it |
|---|---|---|
| Full-bleed page opener (headline, sub-copy, buttons, gradient or media) | `hero` group, `type` = `gradient`, `centeredContent`, `contentMedia`, `homeNew`, `form`, `three`, `livestream`, `default` | `hero.type` select + `richText`, `links[]`, `media`, plus `admin.condition` per type |
| Big statement with a code or media asset | `statement` | `richText`, `links[]`, `assetType` (media/code), `media`, `code`, `assetCaption`, `backgroundGlow` |
| Scroll-pinned feature list with a changing right-hand visual | `stickyHighlights` (24 of 44 pages) | `highlights[]`: `richText`, `link?`, `type` (code/media), `code`, `media` |
| Grid of link cards | `cardGrid` | `richText`, `links[]`, `cards[]`: `title`, `description`, `link?` |
| Numbered or side-by-side content cells | `contentGrid` | `style`, `showNumbers`, `content`, `cells[]` (1-8 rich text) |
| Text columns | `content` | `layout` select + up to three `richText` columns |
| Image/text split | `mediaContent` | `alignment`, `mediaWidth`, `richText`, `link?`, `images[]` |
| Standalone image/video with caption | `mediaBlock` | `position`, `media`, `caption` |
| Code beside copy, tabbed | `codeFeature` | `alignment`, `heading`, `richText`, `links[]`, `codeTabs[]` (`language`, `label`, `code`) |
| Testimonial band | `callout` | `richText`, `logo`, `author`, `role`, `images[]` |
| Testimonial carousel | `slider` (min 3 slides) | `quoteSlides[]`: `quote`, `author`, `role`, `logo`, `link?` |
| Logo wall | `logoGrid` | `richText`, `logos[]` (upload) |
| Hover-reveal list with images | `hoverHighlights` | `highlights[]`: `text`, `media.top`, `media.bottom`, `link?` |
| Numbered process | `steps` | `steps[]`: `content`, `media` |
| Accordion with a media panel per item | `mediaContentAccordion` (max 4) | `leader`, `heading`, `accordion[]`: `mediaLabel`, `mediaDescription`, `media`, `link?` |
| Closing call to action | `cta` | `style` (buttons/banner), `richText`, `commandLine`, `links[]`, `bannerImage` |
| Plan cards | `pricing` (used on `/get-started`) | `plans[]` (max 4): `name`, `hasPrice`, `price`, `description`, `link?`, `features[]` |
| Feature comparison | `comparisonTable` (used on `/compare/contentful`) | `header`, `rows[]` (max 10): `feature`, two check+text pairs |
| Lead form | `form` -> `forms` (or `form` hero) | `richText`, relationship to the form-builder `forms` collection |
| Case-study teaser cards | `caseStudyCards` | `cards[]`: `richText`, `caseStudy` relationship |
| Shared footer CTA or repeated stack | `reusableContentBlock` (51 uses on 28 pages) | relationship to a `reusable-content` collection holding a `layout` blocks field |

Rules that fell out of the repo:

- Give every section block a shared `settings` group (`theme` light/dark/blank, `background`) via one helper (`fields/blockFields.ts`). Neighbour-aware spacing then comes for free (recipe 3).
- Put repeated stacks (footer CTA, "talk to us") in a `reusable-content` collection instead of copying blocks. On payloadcms.com this is the most-used block.
- Keep hero and layout separate: the hero is a `group` on the page, the body is a `blocks` field (`Pages.ts` uses two tabs, Hero and Content).
- Cap arrays where the design breaks (`maxRows`/`minRows` in `hoverCards`, `pricing`, `mediaContentAccordion`, `caseStudyParallax`).

## 2. Pages with a layout builder

> Verified against website repo @ 023c2a5 (`src/collections/Pages.ts`, `src/fields/blockFields.ts`, `src/payload.config.ts`, `src/fields/slug.ts`)

Register each block once in the config, reference by slug from every collection, and wrap fields with a settings group.

```ts
// src/fields/blockFields.ts (trimmed)
export const blockFields = ({ name, fields }: { name: string; fields: Field[] }): Field => ({
  name,
  type: 'group',
  label: false,
  admin: { hideGutter: true, style: { margin: 0, padding: 0 } },
  fields: [
    {
      type: 'collapsible',
      label: 'Settings',
      fields: [
        {
          name: 'settings',
          type: 'group',
          label: false,
          admin: { hideGutter: true, initCollapsed: true },
          fields: [
            {
              type: 'row',
              fields: [
                { name: 'theme', type: 'select', options: ['light', 'dark'] },
                {
                  name: 'background',
                  type: 'select',
                  options: ['solid', 'transparent', 'gradientUp', 'gradientDown'],
                },
              ],
            },
          ],
        },
      ],
    },
    ...fields,
  ],
})

// src/blocks/Statement/index.ts
export const Statement: Block = {
  slug: 'statement',
  fields: [blockFields({ name: 'statementFields', fields: [/* richText, linkGroup, ... */] })],
}

// payload.config.ts
buildConfig({ blocks: [Statement, /* ... */], collections: [Pages /* ... */] })

// collections/Pages.ts
{
  name: 'layout',
  type: 'blocks',
  blockReferences: ['statement', 'cta', 'cardGrid', 'reusableContentBlock'],
  blocks: [], // required empty when using blockReferences
  required: true,
}
```

The rest of the `pages` collection: `versions: { drafts: true }`, `access: { read: publishedOnly, create/update/delete: isAdmin, readVersions: isAdmin }`, `defaultPopulate: { slug, breadcrumbs, title }`, `useAsTitle: 'fullTitle'`, `livePreview` + `preview` (recipe 11), `slugField()` in the sidebar, an `afterChange` hook calling `revalidatePath` (recipe 11), and nested-docs + SEO + redirects plugins (recipes 9-10).

Notes:

- Payload 3.90.2 docs (`docs/fields/blocks.mdx`, "blockReferences") state referenced blocks are isolated: the block config cannot be extended per collection, and access control for such blocks runs once without the parent document's data. Plan variants as separate blocks.
- The site hand-rolls `slugField(fieldToUse, overrides)` with a `beforeValidate` slugify hook. Payload 3.90.2 core exports its own `slugField` (`packages/payload/src/fields/baseFields/slug`), documented in source as `@experimental`; prefer core for new work, accept that it may change.
- `defaultPopulate` (and `forceSelect` on `posts`/`categories`) keeps relationship population small when pages reference each other at depth 2.
- Types: run `payload generate:types` (site script wraps it with `NODE_OPTIONS=--no-deprecation`). Renderers rely on the generated `Page['layout'][0]` union.

## 3. Renderer map and a parity check

> Verified against website repo @ 023c2a5 (`src/components/RenderBlocks/index.tsx`, `RenderBlocks/utilities.ts`, `blocks/ReusableContent/index.tsx`, `Hero/index.tsx`)

```tsx
const blockComponents = { statement: Statement, cta: CallToAction, /* ... */ reusableContentBlock: ReusableContentBlock }

blocks.map((block, i) => {
  const Block = blockComponents[block.blockType]
  return Block ? <Block key={i} {...block} padding={getPaddingProps(block, i)} /> : null
})
```

- `getFieldsKeyFromBlock(block)` finds the `*Fields` key; spacing looks at the current, previous and next block's `settings.theme`: equal themes get `small` padding between them, different themes `large`; first block compares against the hero theme; last block gets `large`.
- Unknown `blockType` renders `null`, silently. The site has exactly this bug: `exampleTabs` is in the schema and allowed on four collections/globals but has no renderer. Add a build-time parity check so a schema-only block fails CI:

`UNVERIFIED:` the sketch below was not run. The repo does not export `blockComponents`, `LEXICAL_ONLY` is yours to define (blocks that only appear inside Lexical editors), and the shape of the sanitized `config.blocks` was not checked.

```ts
// scripts/check-block-parity.ts (sketch; adapt paths)
import config from '@payload-config'
import { blockComponents } from '@/components/RenderBlocks'
const c = await config
const slugs = (c.blocks ?? []).map((b) => b.slug)
const missing = slugs.filter((s) => !(s in blockComponents) && !LEXICAL_ONLY.has(s))
if (missing.length) throw new Error(`Blocks without a renderer: ${missing.join(', ')}`)
```

- `reusableContentBlock` renders `<RenderBlocks blocks={reusableContent.layout} />` only when the relationship arrives populated. Fetch pages at `depth: 2` (as `fetchPage` does) or it renders nothing.
- Hero: a `heroes = { gradient: GradientHero, centeredContent: ..., ... }` map keyed by `hero.type`; the page component renders `<Hero page={page} firstContentBlock={page.layout[0]} />` then `<RenderBlocks />`.
- Post pages append a synthetic `relatedPosts` block (`components/Post/index.tsx`) to `content` before `RenderBlocks`; the map has a component for it though no config defines it. A clean pattern for blocks that are computed, not authored.

## 4. Reading a live Payload site's structure

> Verified against live https://payloadcms.com 2026-09-24 (public REST); script tested the same day

To reverse-engineer which blocks a page uses, read the API, not the DOM. DOM class names showed `Callout` and `CardGrid` on `/compare/wordpress`, but the document is `reusableContentBlock` x3 + `cta` + `stickyHighlights`; reusable content inlines other blocks.

```js
// census.mjs - node census.mjs https://example.com
const base = process.argv[2]?.replace(/\/$/, '')
const res = await fetch(`${base}/api/pages?limit=300&depth=0&pagination=false`)
if (!res.ok) throw new Error(`${res.status} from /api/pages`)
const json = await res.json()
const docs = Array.isArray(json) ? json : json.docs
const url = (p) => p.breadcrumbs?.at(-1)?.url ?? `/${p.slug}`
const blocks = docs.flatMap((p) => (p.layout ?? []).map((b) => ({ type: b.blockType, page: url(p) })))
for (const [t, uses] of [...Map.groupBy(blocks, (b) => b.type)].sort((a, b) => b[1].length - a[1].length))
  console.log(`${t}: ${uses.length} uses / ${new Set(uses.map((u) => u.page)).size} pages`)
for (const p of docs) console.log(url(p), '|', p.hero?.type, '|', (p.layout ?? []).map((b) => b.blockType).join(', '))
```

- Works on any Payload site whose `pages` collection allows public read of published docs. Add `&where[slug][equals]=<slug>` (curl needs `-g`) for one page. Use `depth=2` to resolve `reusable-content`.
- Only published documents are visible. Only structure and field names go into your clone's schema; the copy, images and customer names belong to their owner.
- Do not hit mutation-like routes on someone else's site. On payloadcms.com `GET /api/sync-ch` and `GET /api/sync-algolia` run real jobs in code and were deliberately not called.
- Use the census to choose which blocks to build first: on payloadcms.com nine blocks (`reusableContentBlock`, `stickyHighlights`, `statement`, `cardGrid`, `contentGrid`, `cta`, `mediaContent`, `mediaBlock`, `content`) account for 144 of the 167 block uses across 44 pages; build those before the long tail.

## 5. Blog with categories and authors

> Verified against website repo @ 023c2a5 (`Posts.ts`, `Categories.ts`, `_data/index.ts` `fetchArchive`/`fetchBlogPost`, `(pages)/posts/[category]/*`, `redirects.js`) and live `/posts/blog`

- `categories`: `name`, `slug`, `headline`, `description`, and a `join` field to `posts` so the archive page needs one query:

```ts
{ name: 'posts', type: 'join', collection: 'posts', on: 'category', defaultLimit: 0, maxDepth: 2 }
// fetch
payload.find({
  collection: 'categories',
  where: { slug: { equals: category } },
  limit: 1,
  depth: 2,
  joins: { posts: { sort: '-publishedOn', where: { and: [
    { publishedOn: { less_than_equal: new Date() } },
    { _status: { equals: 'published' } },
  ] } } },
})
```

- `posts`: `category` (required relationship), `tags` (text, `hasMany`), `publishedOn` (required date; scheduled posts are hidden by the `<= now` filter, not by a scheduler), `featuredMedia` select with `admin.condition` toggling `image` vs `videoUrl` (+ `dynamicThumbnail`/`thumbnail`), `excerpt`, `content` blocks, `relatedPosts` (`filterOptions` excludes itself), `relatedDocs` (link posts to docs; the docs collection joins back via `guides`).
- Authors: `authorType` (team/guest). Team posts use `authors` -> `users` (`hasMany`); guest posts use `guestAuthor` + `guestSocials` group; each shown by `admin.condition` on `authorType`. Public read of `users` is open but `email` has admin-or-self field access.
- URL shape `/posts/<category>/<slug>`; the category is part of the URL, so preview and revalidate code must resolve the category slug (the site does a `findByID` with `select: { slug: true }` inside `admin.preview`).
- Vanity redirect `/blog` -> `/posts/blog` lives in `redirects.js` (`permanent: true`), not in the CMS.
- Live: `/posts/blog` renders all posts (81 post links) on one page with `FeaturedBlogPost` and `Archive`, and category links to `/posts/guides` and `/posts/releases`. If you expect hundreds of posts, add pagination; the site's `defaultLimit: 0` join does not.
- Invalidate on category change and delete: `Categories.afterChange` revalidates `/posts/<slug>` and tag `archives`; the `category` field's own `afterChange` revalidates old and new category pages. `Posts.afterChange` in the repo revalidates `/<category>/<slug>` without `/posts`; use `/posts/<category>/<slug>` in your clone.

## 6. Case studies and a partner directory

> Verified against website repo @ 023c2a5 (`CaseStudies.ts`, `Partners.ts`, `PartnerFilters.ts`, `globals/PartnerProgram.ts`, `(pages)/partners/page.tsx`, `components/PartnerDirectory`)

Case studies: a collection with `title`, `introContent`, `industry`, `useCase`, `partner` -> `partners`, required `featuredImage`, a `layout` blocks field (same block set as pages minus `comparisonTable`), `slug`, external `url`, drafts, SEO. `/case-studies` (the index) is an ordinary page whose only block is `caseStudyCards`.

Partner directory:

- One factory generates the four filter collections:

```ts
const Filter = (slug: string, label: string): CollectionConfig => ({
  slug,
  admin: { group: 'Partner Program', useAsTitle: 'name' },
  access: { read: () => true, create: isAdmin, update: isAdmin, delete: isAdmin },
  fields: [
    { name: 'name', type: 'text', label: `${label} Label`, required: true, unique: true },
    { name: 'value', type: 'text', required: true, unique: true }, // lowercase, digits, - and _
  ],
})
export const Specialties = Filter('specialties', 'Specialty') // + Industries, Regions, Budgets
```

- `partners`: many-to-many relationships to the four filters, `agency_status` (active/inactive) to hide a partner without deleting, `logo`, banner, rich-text tabs, `contributions[]` and `projects[]` (max 4) arrays, `social[]`. Private fields (`email`, `hubspotID`) use field-level `access.read: isAdminFieldLevel`.
- Listing fetch: `find({ collection: 'partners', depth: 2, limit: 300, overrideAccess: false, where: { AND: [{ agency_status: { equals: 'active' } }, { _status: { equals: 'published' } }] } })`. `overrideAccess: false` is what makes the field-level rule apply in the Local API (the default bypasses access control).
- Filtering runs in the browser: the server maps each partner's relations to `value` strings, drops filter options no partner uses, and `PartnerDirectory` applies `every()` across the selected values per dimension. Fine for hundreds of rows; move to `where` queries beyond that.
- Editorial surface in a global (`partner-program`): featured partners, `contentBlocks.beforeDirectory` / `afterDirectory` blocks, contact form. The `featured` checkbox on each partner is read-only because it is derived from that global.
- Case-study -> partner and partner -> case-study relationships are both one-way fields; use `join` on the other side if you need the reverse list.

## 7. CMS-driven docs

> Verified against website repo @ 023c2a5 (`collections/Docs/*`, `scripts/fetchDocs.ts`, `scripts/syncDocs.ts`, `scripts/generateLLMs.ts`, `(pages)/docs/[topic]/[doc]/page.tsx`, `components/RenderDocs`) and live docs pages

Pick the smaller option unless you truly publish docs from Git.

Option A, docs authored in the CMS (recommended for a clone; this is an adaptation of the site's `docs` collection, not code copied from the repo. The site computes `headings` while parsing MDX):

- `docs` collection: `title`, `description`, `topic`, `topicGroup`, `slug`, `order`, `label`, `version`, Lexical `content`, and `headings` (json) computed in a `beforeChange` hook from the Lexical tree. Sidebar = group by `topicGroup` then `topic`, sort by `order`. URL `/docs/<topic>/<slug>`.
- Page: `find({ collection: 'docs', where: { slug, topic, version } })`, `generateStaticParams` over `select: { slug, topic }`, `export const dynamic = 'force-static'`, `revalidatePath` on save.
- Add machine-readable output at build: `llms.txt` (index), `llms-full.txt`, one `.md` per page, and `<link rel="alternate" type="text/markdown">` in `generateMetadata`. Live payloadcms.com serves exactly these (`/llms.txt` 32 KB, `/docs/v3/llms-full.txt` 1.9 MB, per-doc `.md` as `text/markdown`).
- Feedback widget: a `docs-feedback` collection (`path` unique, `helpful`, `notHelpful`) with a collection endpoint `POST /api/docs-feedback/vote`. Register it as a collection endpoint, not a root one; the repo comment explains root paths would not match.

Option B, the payloadcms.com approach (docs live in a GitHub repo as MDX):

1. Keep an explicit ordered topic map (`topicOrder.ts`) per version; every new folder must be added by hand.
2. `fetchDocs` reads each `docs/<topic>/*.mdx` through the GitHub contents API on the version's branch, `gray-matter` for front matter, heading extraction, relative-link rewrite.
3. `mdxToLexical` (headless Lexical editor + `BlocksFeature` for each custom MDX component + a table-pipe escaping pass) stores Lexical in `content` and raw text in a hidden `mdx` field.
4. A protected endpoint upserts by `slug + topic + version`. The repo then deletes every doc it did not just import; guard that delete with a sanity check (for example abort if the fetched set is under 90% of existing rows) and put the endpoint behind `req.user` admin or a secret.
5. Optional write-back: `beforeChange` on `?commit=true` converts Lexical to MDX and posts it to a commit service.
- Extras the site added: branch preview (`/docs/dynamic/...?branch=`), local-folder preview (`DOCS_DIR_V3`), a version selector gated by `NEXT_PUBLIC_ENABLE_BETA_DOCS` / `NEXT_PUBLIC_ENABLE_LEGACY_DOCS`, and `preview-runtimes` to render real admin UI components per major version. Skip these unless you document a product with parallel majors.

## 8. Forms and lead capture

> Verified against website repo @ 023c2a5 (`payload.config.ts` `formBuilderPlugin`, `blocks/Form`, `components/CMSForm`, `hero.ts` `form` type)

- Use `@payloadcms/plugin-form-builder`; the site extends it through `formOverrides` and `formSubmissionOverrides` (both take `fields: ({ defaultFields }) => [...]`):
  - `forms` gain `hubSpotFormID`, `customID`, `requireRecaptcha` (sidebar) and an `afterChange` that calls `revalidateTag('form-<title>', { expire: 0 })` so the rendered form refreshes.
  - `form-submissions` gain a text `recaptcha` field whose `validate` loads the parent form (`req.payload.findByID` on `siblingData.form`), skips when `requireRecaptcha` is false, otherwise verifies the token against Google's `siteverify` with the secret key.
  - `afterChange` on submissions forwards `submissionData` to the CRM (HubSpot forms API with `hutk`, `pageName`, `pageUri` context) inside try/catch that only logs, so CRM outages never lose the submission.
  - `beforeChange` on submissions resolves routing (partner email) and appends a `toEmail` entry before the plugin's email step.
- Front end: `CMSForm` renders fields from the form document and POSTs `{ form, submissionData, hubspotCookie, pageName, pageUri, recaptcha }` (JSON, `credentials: 'include'`) to `/api/form-submissions`.
- Two ways to place a form: the `form` block (`richText` + `form` relationship) anywhere in a layout, or a `form` hero (`hero.form` relationship) for `/contact` and `/talk-to-us` (live: four form-hero pages).
- Email transport is `nodemailerAdapter` with SendGrid; swap the adapter, keep `defaultFromAddress`.
- Add a honeypot or rate limit to the submissions endpoint in a clone; in the code read, per-form reCAPTCHA is the only anti-abuse measure.

## 9. Redirects

> Verified against website repo @ 023c2a5 (`redirects.js`, `payload.config.ts` `redirectsPlugin`, `components/PayloadRedirects`, `utilities/getRedirects.ts`, `hooks/revalidateRedirects.ts`)

Three layers, use each for its job:

1. Static, deploy-time, in `next.config` via `redirects.js`: docs entry points (`/docs` -> `/docs/getting-started/what-is-payload`), `/blog` -> `/posts/blog`, `/roadmap` -> GitHub, an IE-incompatibility redirect. Cheap, no DB, changed by deploy.
2. Editor-managed via `redirectsPlugin({ collections: ['pages', 'posts', 'case-studies'], overrides: { hooks: { afterChange: [revalidateRedirects] } } })`. The plugin adds a `redirects` collection (`from`, `to` as URL or document reference).
3. Render-time resolution: pages call `<PayloadRedirects url={path} />` when the lookup misses (renders `notFound()` if nothing matches) and `<PayloadRedirects disableNotFound url={path} />` when it hits, so an editor can redirect an existing page too. Cache all redirects together: `unstable_cache(getRedirects, ['redirects'], { tags: ['redirects'] })`, with `limit: 0, pagination: false`, and `revalidateTag('redirects', { expire: 0 })` in the collection's `afterChange`.

Pitfall: the site's component builds `/blog/...` URLs for `posts` references and `/case-studies/...` for case studies, so a post in another category redirects wrongly. Build the target from the referenced document's real path (`/posts/<category>/<slug>`) in a clone.

## 10. SEO and Open Graph

> Verified against website repo @ 023c2a5 (`payload.config.ts` `seoPlugin`, `seo/mergeOpenGraph.ts`, `(pages)/[...slug]/page.tsx`, `case-studies/[slug]/page.tsx`, `next-sitemap.config.cjs`, `next.config.js`) and live 2026-09-24

- `seoPlugin({ collections: ['case-studies', 'pages', 'posts'], globals: ['get-started'], uploadsCollection: 'media' })` gives `meta.title`, `meta.description`, `meta.image` per document. Payload 3.90.2's SEO docs (`docs/plugins/seo.mdx`) list `generateTitle`, `generateDescription`, `generateURL`, `generateImage`; the site uses none of them and relies on editors.
- Root layout: `metadataBase` from `NEXT_PUBLIC_SITE_URL`, default `openGraph` from `mergeOpenGraph()` (site name, description, `/images/og-image.jpg`), `twitter.card = summary_large_image`.
- Per-page `generateMetadata`: `title` and `description` from `meta`, OG image from `meta.image.url`, and a `noindex` checkbox on `pages` that emits `robots: 'noindex'`.
- Live check: `/compare/wordpress` `og:image` = `https://payloadcms.com/images/og-image.jpg` (default), blog post `og:image` = its blob URL (correct).
- Bug to avoid: `case-studies/[slug]/page.tsx` does `${NEXT_PUBLIC_CMS_URL}${meta.image.url}`. With cloud storage `url` is already absolute, so live `/case-studies/microsoft` and `/case-studies/asics` output `og:image` `https://payloadcms.comhttps//l4wlsi8vxy8hre4v.public.blob.vercel-storage.com/...jpg`. Use `image.url` as-is; only prefix when it starts with `/`.
- Dynamic OG: `/api/og` edge route with `next/og` `ImageResponse` and bundled fonts; docs use `?topic=&title=`.
- Sitemap and robots: `next-sitemap` in `postbuild` with `generateRobotsTxt: true` and `siteUrl` from `SITEMAP_URL`. Live `sitemap.xml` is an index pointing at `sitemap-0.xml`, which lists 1,144 URLs. Non-production hosts send `X-Robots-Tag: noindex` unless `NEXT_PUBLIC_IS_LIVE` is set; copy that guard so staging never gets indexed.
- Gaps worth improving in a clone: no JSON-LD on the live blog post checked, and no `canonical` link anywhere (`grep -rn canonical src` finds nothing relevant; the live homepage HTML has no `<link rel="canonical">`). Set `alternates.canonical` in `generateMetadata`.

## 11. Draft preview and revalidation

> Verified against website repo @ 023c2a5 (`utilities/formatPreviewURL.ts`, `formatPagePath.ts`, `api/preview/route.ts`, `api/exit-preview/route.ts`, `api/revalidate/route.ts`, `Pages.ts` hooks, `RefreshRouterOnSave`)

```ts
// collection admin config
admin: {
  livePreview: { url: ({ data }) => formatPreviewURL('pages', data) },
  preview: (doc) => formatPreviewURL('pages', doc),
}
// formatPreviewURL -> `${SITE_URL}/api/preview?url=${path}&secret=${DRAFT_SECRET}`

// app/api/preview/route.ts (essentials)
if (secret !== process.env.NEXT_PRIVATE_DRAFT_SECRET) return new Response('Invalid secret', { status: 401 })
const user = await payload.auth({ headers: req.headers })
if (!user) { (await draftMode()).disable(); return new Response('Not allowed', { status: 403 }) }
;(await draftMode()).enable()
redirect(url)
```

- The page component reads `draftMode()`: draft on means uncached `fetchPage` with `draft: true` and no `_status` filter; draft off means `unstable_cache` plus `_status: 'published'`.
- Mount `RefreshRouteOnSave` (from `@payloadcms/live-preview-react`) on each previewable page, passing `refresh={() => router.refresh()}` and `serverURL`. That re-renders the server tree after each save, which suits server-rendered blocks.
- Invalidation: `afterChange` -> `revalidatePath(<last breadcrumb url>)` when the doc is published or its status changed; `/` also revalidates when the slug is `home`. Tag routes (`redirects`, `archives`, `form-<title>`, `<collection>_<slug>` via `/api/revalidate`) cover data shared across pages.
- Edge caching: the site sets `s-maxage=31536000` for all non-API routes, so revalidation is the only thing keeping content fresh. Verify a publish reaches the CDN before launch.
- Next 16 note from the repo: `revalidateTag(tag, { expire: 0 })` takes a second argument.

## 12. Order of operations

> Verified against website repo @ 023c2a5; ordering is a recommendation derived from the dependencies above

1. Scaffold from the Payload `website` template (`templates/website` in the payload monorepo) or from `create-payload-app`, then diff against recipes 2-3 rather than porting the whole site.
2. Run recipe 4 on the reference site to get the block census and page tree; write the block schemas for the top blocks first (recipe 1).
3. Implement `blockFields`, config-level blocks, `pages` with drafts + nested-docs + SEO + redirects, then `RenderBlocks` + hero map + the parity check.
4. Globals for nav and footer (`main-menu` with per-item `style`, `footer` columns, `topBar`) fetched once in the layout with `depth: 1` and cached.
5. Preview + revalidation (recipe 11) before any editor touches content.
6. Collections with URLs of their own: posts/categories, case studies, partners, docs (recipes 5-7).
7. Forms, then SEO/OG, sitemap and `llms.txt`.
8. Access review: every custom endpoint checks `req.user` or a secret; no `autoLogin` outside development; `overrideAccess: false` wherever a user identity is passed to the Local API.
