# Local API, Queries, REST and GraphQL

Reading and writing content from a Next.js frontend and scripts. Verified against stable **payload 3.90.2**; `v4:` lines are diffs against 4.0.0-canary.37.

## Contents

1. Getting a Payload instance
2. Operations and shared options
3. The `overrideAccess` trap
4. Queries: where, sort, pagination, select, populate, depth, joins, drafts, locale, trash
5. Auth from server components
6. Website data-fetching patterns (draft mode, caching)
7. REST API
8. GraphQL
9. Scripts, seeding, generated types

## 1. Getting a Payload instance

> Verified against payload v3.90.2 (docs/local-api/overview.mdx, docs/local-api/outside-nextjs.mdx, packages/payload/src/index.ts L1142-1182)

```ts
import { getPayload } from 'payload'
import config from '@payload-config'          // tsconfig path alias -> src/payload.config.ts

const payload = await getPayload({ config })   // cached per `key` (default 'default'); HMR-aware in dev
```

- In hooks, access functions, validators and endpoint handlers use `req.payload` instead (also HMR-safe and carries the request/transaction).
- `getPayload({ config, key? , cron?, ... })`: instances are cached in a module map keyed by `key`; `onInit` runs once per key. Pass a different `key` only when using multiple configs.
- Server Components, route handlers, server actions, and `generateStaticParams` can call it directly - no HTTP hop. Never import it in client components.
- Outside Next: write ESM scripts and run with `pnpm payload run src/seed.ts` (loads env like Next does, initializes tsx; do not use dotenv). Flags: `--use-swc` (needs `@swc-node/register`), `--disable-transpile` (bun). `payload run` accepts `--cron "..."`.

## 2. Operations and shared options

> Verified against payload v3.90.2 (docs/local-api/overview.mdx, packages/payload/src/index.ts L414-714)

Collection ops: `find`, `findByID`, `count`, `findDistinct`, `create`, `update` (by `id`, **or** many via `where` -> `{ docs, errors }`), `delete` (by `id` or `where`), `duplicate`, plus `findVersions`, `findVersionByID`, `restoreVersion`, `countVersions`. Globals: `findGlobal`, `updateGlobal`, `findGlobalVersions`, `findGlobalVersionByID`, `restoreGlobalVersion`, `countGlobalVersions`. Auth: `auth`, `login`, `forgotPassword`, `resetPassword`, `unlock`, `verifyEmail`. Also `sendEmail`, `jobs.queue/run/...`, `encrypt/decrypt`, `db.*`.

```ts
const { docs, totalDocs, hasNextPage } = await payload.find({
  collection: 'posts', where: { _status: { equals: 'published' } }, sort: '-publishedAt',
  depth: 1, limit: 12, page: 1, select: { title: true, slug: true }, locale: 'en', fallbackLocale: false,
})
const post   = await payload.findByID({ collection: 'posts', id, depth: 2 })
const header = await payload.findGlobal({ slug: 'header', depth: 1 })
const total  = await payload.count({ collection: 'posts', where: {...} })      // { totalDocs }
const doc    = await payload.create({ collection: 'media', data: { alt }, filePath: '/abs/path/img.jpg' })   // or `file`
await payload.update({ collection: 'posts', id, data: { title: 'x' } })                                     // returns the doc
await payload.update({ collection: 'posts', where: { ... }, data: {...} })                                  // returns { docs, errors }
await payload.delete({ collection: 'posts', id })
await payload.updateGlobal({ slug: 'header', data: { ... } })
```

Options common to most operations:

| Option | Meaning |
| --- | --- |
| `collection` / `slug` | target (`slug` for globals) |
| `data` | payload for create/update |
| `depth`, `select`, `populate`, `joins` | shape of the response (section 4) |
| `locale`, `fallbackLocale` | localization (`locale: 'all'` returns every locale; `fallbackLocale: false` disables fallback) |
| `draft` | read: return latest *version* (incl. drafts); write: skip validation and write only to versions (see `config-and-collections.md` section 4) |
| `overrideAccess`, `user` | access control (section 3) |
| `req` | pass the incoming request to join its transaction and carry `user`/`context`/`locale` |
| `context` | extra data forwarded to `req.context` in hooks |
| `showHiddenFields` | include fields with `hidden: true` (default hidden) |
| `overrideLock` | default `true` (ignore document locks); `false` enforces locks |
| `pagination`, `page`, `limit` | pagination (section 4) |
| `disableErrors` | `findByID` returns `null` / `find` returns empty instead of throwing |
| `disableTransaction` | skip creating a DB transaction |
| `trash` | include soft-deleted docs (trash-enabled collections) |
| `filePath` / `file`, `overwriteExistingFiles` | uploads via Local API; `duplicateFromID` on create clones a doc; `disableVerificationEmail` on create for verify-enabled auth collections |

Local API `find` returns `{ docs, totalDocs, limit, totalPages, page, pagingCounter, hasPrevPage, hasNextPage, prevPage, nextPage }`.

## 3. The `overrideAccess` trap

> Verified against payload v3.90.2 (docs/local-api/access-control.mdx, packages/payload/src/collections/operations/local/find.ts L215, create.ts L203, globals/operations/local/findOne.ts L113)

In 3.x every Local API operation defaults to `overrideAccess = true`: **access control is skipped entirely, even if you pass `user`.** Enforce a user's permissions with both:

```ts
await payload.find({ collection: 'orders', user: req.user, overrideAccess: false })
```

Rules of thumb:
- Trusted server work (seed, cron, migrations, hooks that act as the system): default/`true`.
- Anything on behalf of a visitor or logged-in user (route handlers, server actions, RSC that render user-specific data): `overrideAccess: false` and pass `user`. Anonymous public reads with `overrideAccess: false` and no `user` get exactly the public rules (e.g. `_status: published` only) - use this for public pages so drafts cannot leak.
- Field-level access and hooks' `overrideAccess` arg follow the same flag.

`v4:` the default flips to `overrideAccess = false` on every Local API op (verified in find/create/findOne source); migrate with `npx @payloadcms/codemod` and add `overrideAccess: true` for trusted calls. `payload.jobs.*` also flips and honours `jobs.access.*`.

## 4. Queries

> Verified against payload v3.90.2 (docs/queries/{overview,depth,pagination,select,sort}.mdx, docs/fields/join.mdx, docs/trash/overview.mdx)

### Where

```ts
import type { Where } from 'payload'
const where: Where = {
  or: [
    { and: [{ color: { equals: 'mint' } }, { 'category.slug': { equals: 'news' } }] },  // dot path through a relationship
    { featured: { exists: true } },
  ],
}
```

Operators: `equals`, `not_equals`, `greater_than`, `greater_than_equal`, `less_than`, `less_than_equal`, `like` (all words, any order), `contains`, `in`, `not_in`, `all` (**MongoDB only**), `exists`, and point-field `near` (`'lng,lat,maxMeters,minMeters'`), `within`, `intersects`. Polymorphic relationships query `field.value` and `field.relationTo`. `and`/`or` nest arbitrarily. Index (`index: true`) any field you filter or sort on.

`v4:` documents new has-many nested-query semantics (`equals` = every related doc must match, `contains` = at least one) and a "Relationship queries" section.

### Sort, pagination

- `sort: 'field'` ascending, `'-field'` descending, array for multiple (`['priority', '-createdAt']`; REST: comma-separated). Sorted fields cannot be virtual unless path-linked to a relationship.
- `limit` default **10**, `page` default 1. `limit: 0` or `pagination: false` with no limit returns **all** matching docs and skips count queries (the template uses `pagination: false, limit: 1` for slug lookups and `limit: 0, pagination: false` for redirects). A positive `limit` with `pagination: false` is still honoured.

### select and populate

```ts
select: { title: true, slug: true, hero: { image: true } }   // include mode; `id` always included; select: {} => only id
select: { layout: false, meta: { image: false } }             // exclude mode
populate: { pages: { slug: true, title: true } }              // per-populated-collection select, overrides collection.defaultPopulate
```

`select` is executed in the DB, so `beforeRead`/`afterRead` hooks and access functions may see partial docs; force needed fields with the collection `forceSelect: { title: true }` (3.x). Set `defaultPopulate` on collections that are commonly referenced (pages/posts) to `{ slug: true, title: true }` to cut payload size.

`v4:` `forceSelect` is removed in favor of a `select: ({ select, operation, req }) => select` function on collections/globals.

### depth

`depth: 0` -> IDs only; `1` -> populate direct relationships/uploads; `2` -> also one level deeper. 3.x default depth is **2** (`defaultDepth` in config); max is `maxDepth` (10). Field `maxDepth` caps a single field. Ignored in GraphQL (shape of the query decides). Rich-text upload/link rendering needs enough depth to populate nodes. Use `depth: 0` for lists/IDs and explicit `depth` + `select` for pages.

`v4:` default depth becomes **1** (verified in `config/defaults.ts`); set `defaultDepth: 2` to keep v3 behavior.

### joins, drafts, locale, trash

- `joins: { relatedPosts: { limit: 5, where, sort, count: true } }` per join field, or `joins: false`. REST: `?joins[relatedPosts][limit]=5`. Join docs default to 10 per field.
- `draft: true` on `find`/`findByID` returns the latest version (draft or published). It does **not** enforce visibility - combine with access control (section 3, and `access-and-hooks.md`).
- `locale`/`fallbackLocale` (REST `?locale=es&fallback-locale=none`); `locale: 'all'` / `'*'` returns full locale maps.
- Trash-enabled collections: `trash: true` includes deleted docs; add `where: { deletedAt: { exists: true } }` for trashed-only.
- Local API `find` on `where` with many matches: prefer `select` + `depth: 0` + a `limit`; `payload.count` for totals only.

## 5. Auth from server components

> Verified against payload v3.90.2 (docs/local-api/server-functions.mdx L159-185, docs/local-api/overview.mdx Auth)

```ts
import { headers as getHeaders } from 'next/headers'
import { getPayload } from 'payload'
import config from '@payload-config'

const payload = await getPayload({ config })
const { user, permissions, responseHeaders } = await payload.auth({ headers: await getHeaders(), canSetHeaders: false })
```

`user` is the authenticated doc from the `payload-token` cookie (or `Authorization: JWT <token>` / `Authorization: <collection-slug> API-Key <key>`); it is `null` when anonymous. Use it as the gate before `draftMode().enable()` and to pass `user` + `overrideAccess: false` into subsequent operations. `payload.login({ collection, data: { email, password } })` returns `{ token, user, exp }`; set the cookie yourself in a server action/route handler. Password changes via Local API `update` without `user` end all sessions (see `config-and-collections.md` section 7).

## 6. Website data-fetching patterns

> Verified against payload v3.90.2 (templates/website/src/app/(frontend)/[slug]/page.tsx, utilities/getGlobals.ts, utilities/getDocument.ts, utilities/getRedirects.ts)

Page by slug with draft mode (template):

```tsx
const queryPageBySlug = cache(async ({ slug }: { slug: string }) => {          // React cache(): dedupe within a render
  const { isEnabled: draft } = await draftMode()
  const payload = await getPayload({ config: configPromise })
  const result = await payload.find({
    collection: 'pages',
    draft,                         // latest version when previewing
    limit: 1,
    pagination: false,
    overrideAccess: draft,         // true only in draft mode (preview cookie set by an authenticated preview route)
    where: { slug: { equals: slug } },
  })
  return result.docs?.[0] || null
})
```

Static params: `payload.find({ collection: 'pages', draft: false, limit: 1000, overrideAccess: false, pagination: false, select: { slug: true } })`. Types: `RequiredDataFromCollectionSlug<'pages'>`, `DataFromGlobalSlug<'header'>`, `DataFromCollectionSlug` from `payload`.

Cached globals/redirects with tag invalidation (busted by the `afterChange` hooks in `access-and-hooks.md` section 8):

```ts
export const getCachedGlobal = (slug, depth = 0) =>
  unstable_cache(async () => (await getPayload({ config: configPromise })).findGlobal({ slug, depth }), [slug], { tags: [`global_${slug}`] })
export const getCachedRedirects = () =>
  unstable_cache(async () => getRedirects(), ['redirects'], { tags: ['redirects'] })   // find({ collection: 'redirects', limit: 0, pagination: false })
```

Notes: the Payload docs do not prescribe a Next caching strategy - the above is the template's convention. Preview mode reads must bypass `unstable_cache`. Client components needing the current user in the template call `fetch(`${getClientSideURL()}/api/users/me`, { headers: { Authorization: `JWT ${token}` } })` with the `payload-token` cookie; prefer `payload.auth` in server code.

## 7. REST API

> Verified against payload v3.90.2 (docs/rest-api/overview.mdx L40-560, L758-800, L825+)

Mounted at `/api` (bound by the `(payload)/api/[...slug]` route). Collection slugs are kebab-case.

| Operation | Method and path |
| --- | --- |
| find / count | `GET /api/{collection}` / `GET /api/{collection}/count` |
| findByID | `GET /api/{collection}/{id}` |
| create | `POST /api/{collection}` (multipart for uploads) |
| update many / by id | `PATCH /api/{collection}?where...` / `PATCH /api/{collection}/{id}` |
| delete many / by id | `DELETE /api/{collection}?where...` / `DELETE /api/{collection}/{id}` |
| versions | `GET /api/{collection}/versions`, `GET|POST /api/{collection}/versions/{id}` (POST restores) |
| global | `GET|POST /api/globals/{slug}` (no create/delete) |
| auth | `POST /api/{auth}/login|logout|unlock|refresh-token|forgot-password|reset-password`, `GET /api/{auth}/me`, `POST /api/{auth}/verify/{token}` |
| preferences | `GET|POST|DELETE /api/payload-preferences/{key}` |
| jobs | `GET /api/payload-jobs/run?queue=...` (Vercel Cron target) |

Query params mirror Local API: `where[field][operator]=v`, `sort`, `limit`, `page`, `depth`, `locale`, `fallback-locale`, `draft=true`, `select[...]`, `populate[...]`, `joins[...]`, `trash=true`. Build nested queries with `qs-esm` `stringify`. `X-Payload-HTTP-Method-Override: GET` on a form-encoded POST works around URL-length limits. Browser `fetch` must pass `credentials: 'include'` for the HTTP-only cookie; cross-origin also needs `cors`/`csrf` (see config file). Auth headers: `Authorization: JWT <token>` or `<collection-slug> API-Key <key>` (case-sensitive). The beta `@payloadcms/sdk` (`new PayloadSDK<Config>({ baseURL })`) mirrors Local API methods over REST. Custom endpoints are unauthenticated unless you check `req.user`.

## 8. GraphQL

> Verified against payload v3.90.2 (docs/graphql/overview.mdx)

Served at `/api/graphql`; playground at `/api/graphql-playground` (`graphQL.disablePlaygroundInProduction` defaults true). Requires the `graphql` package. Per collection (singular `Post`, plural `Posts`): queries `Post` (findByID), `Posts` (find), `countPosts`, `mePost` (auth); mutations `createPost`, `updatePost`, `deletePost`, plus auth ops (`loginPost`, `logoutPost`, `refreshTokenPost`, `forgotPasswordPost`, `resetPasswordPost`, `unlockPost`, `verifyPost`). Globals: query `Header`, mutation `updateHeader`. Versions: `versionPost`, `versionsPosts`, `restoreVersionPost`. `depth` is ignored (query shape decides). File uploads are REST-only. Options: `graphQL: { queries, mutations, maxComplexity, disablePlaygroundInProduction, schemaOutputFile, disable }`; per-collection `graphQL: false` or `{ singularName, pluralName, disableQueries, disableMutations }`; block/array `interfaceName` names GraphQL types. Complexity limits guard public endpoints.

## 9. Scripts, seeding, generated types

> Verified against payload v3.90.2 (docs/typescript/*.mdx, docs/local-api/outside-nextjs.mdx, templates/website/src/endpoints/seed/index.ts)

- Generated types: `pnpm payload generate:types` writes `typescript.outputFile`; it adds `declare module 'payload' { export interface GeneratedTypes extends Config {} }` (turn off with `typescript.declare: false`, then declare manually) so every Local API call is typed. Useful helpers: `CollectionSlug`, `GlobalSlug`, `DataFromCollectionSlug<T>`, `RequiredDataFromCollectionSlug<T>`, `SelectFromCollectionSlug<T>`, `DataFromGlobalSlug<T>`, `Where`. `strictDraftTypes: true` recommended. Regenerate after any config change; commit the file.
- Seeding: write an ESM script using `getPayload({ config })` and `payload.create` (upload with `filePath`), run with `payload run`. Pass `context: { disableRevalidate: true }` if the site's `afterChange` hooks call `revalidatePath`/`revalidateTag`. Seed order: uploads -> taxonomies -> pages/posts -> globals (nav links reference pages). Raise `upload.limits` (`files`, `fileSize`) if seeding through REST multipart; the Local API path is unaffected.
- The template seed (`src/endpoints/seed/index.ts`) is triggered by a `POST` route handler at `app/(frontend)/next/seed/route.ts` that calls `payload.auth({ headers })`, returns 403 without a user, and builds a request with `createLocalReq({ user }, payload)` (exported from `payload`) to pass into `seed({ payload, req })`; it clears the listed collections/globals, then recreates demo content with `context: { disableRevalidate: true }` on its writes. Its own comment notes revalidation errors are expected when seeding with no running Next server.
