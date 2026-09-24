# Access Control and Hooks

Who can do what, and the document lifecycle. Verified against stable **payload 3.90.2**; `v4:` lines are diffs against 4.0.0-canary.37.

## Contents

1. Access control basics and signatures
2. Query-constraint (Where) returns
3. Field-level access
4. Common patterns (public site, roles, tenants)
5. Hook catalogue and signatures
6. Execution order
7. `req.context`, loop prevention, transactions
8. Next.js revalidation pattern
9. Gotchas

## 1. Access control basics and signatures

> Verified against payload v3.90.2 (docs/access-control/{overview,collections,globals}.mdx, packages/payload/src/config/types.ts L343-366)

```ts
type Access<TData = any> = (args: {
  req: PayloadRequest            // req.user, req.payload, req.locale, req.context, req.headers
  id?: string | number           // present for findByID/update/delete of one doc
  data?: TData                   // create/update: incoming data; null for list reads
  collectionConfig?: SanitizedCollectionConfig
  isReadingStaticFile?: boolean  // true when serving an upload file
}) => boolean | Where | Promise<boolean | Where>
```

| Scope | Functions |
| --- | --- |
| Collection | `create`, `read` (find + findByID), `update`, `delete` |
| Auth collections | plus `admin` (may enter /admin), `unlock` |
| Version-enabled | plus `readVersions` |
| Global | `read`, `update`, plus `readVersions` |

- **Default** (no function set): allow only if `req.user` exists. A collection with no `access` is private - a public frontend needs explicit `read: () => true` (the blank template does this for `media`).
- `create`/`update` receive `data`; `update`/`delete` receive `id`; on trash-enabled collections `delete` gets `data.deletedAt` so you can allow soft delete but forbid permanent delete.
- `admin` gates the Admin Panel for the `admin.user` collection; the default only checks a user exists.
- **Admin UI probing**: Payload calls every access function at login (the "Access Operation") *without* `id`, `data`, `siblingData`, `blockData`, `doc`, and it does **not run returned `Where`** queries (treated as no access). Guard uses of those args (`if (!id) return true` for delete-permission UI) or admin buttons disappear.
- `req.locale` is available for locale-scoped access.
- Media/upload collections: `read` also gates file serving (`isReadingStaticFile`), so a private `read` breaks public image URLs.
- Types: `Access<Page>` / `AccessArgs<User>` from `payload`; keep reusable functions in `src/access/` (template: `anyone`, `authenticated`, `authenticatedOrPublished`).

`v4:` collection and global access callbacks additionally receive `slug`; version reads inherit the collection `read` when `readVersions` is unset; Local API `overrideAccess` defaults to `false` (see `local-api-and-queries.md`).

## 2. Query-constraint (Where) returns

> Verified against payload v3.90.2 (docs/access-control/collections.mdx, docs/versions/drafts.mdx)

For `read`, `update`, `delete` return a `Where` to *scope* which documents match instead of a bare boolean. Payload ANDs it onto the operation's own query, so denied docs simply vanish (find) or 404/no-op (byID/update).

```ts
// template: templates/website/src/access/authenticatedOrPublished.ts
export const authenticatedOrPublished: Access = ({ req: { user } }) =>
  user ? true : { _status: { equals: 'published' } }

// docs that predate drafts have no _status until re-saved:
{ or: [{ _status: { equals: 'published' } }, { _status: { exists: false } }] }

// row-level ownership
({ req: { user } }) => (user ? { author: { equals: user.id } } : false)
```

`update` can gate *publishing*: return `{ _status: { equals: 'draft' } }` for editors; the admin hides Publish/Unpublish and scheduled-publish jobs are blocked for them. `create` cannot return a query (no doc to match) - check `data` instead (e.g. `data._status !== 'published'`).

## 3. Field-level access

> Verified against payload v3.90.2 (docs/access-control/fields.mdx, packages/payload/src/fields/config/types.ts L236-263)

`access: { create, read, update }` returning **boolean only** (`FieldAccess` = `(args: { req, id, data, doc, siblingData, blockData }) => boolean | Promise<boolean>`). No `Where`. `read: false` omits the property from responses; `create`/`update: false` silently discards the incoming value (no error thrown). Field access is skipped when `overrideAccess: true`. Use `saveToJWT: true` on a role field to read it from `req.user` without a lookup.

## 4. Common patterns

> Verified against payload v3.90.2 (docs/access-control/*.mdx, docs/authentication/overview.mdx, templates/website/src/access/*)

```ts
import type { Access, FieldAccess } from 'payload'

export const anyone: Access = () => true
export const authenticated: Access = ({ req: { user } }) => Boolean(user)
export const isAdmin: Access = ({ req: { user } }) => Boolean(user?.roles?.includes('admin'))
export const adminOrSelf: Access = ({ req: { user } }) =>
  user?.roles?.includes('admin') ? true : user ? { id: { equals: user.id } } : false
export const adminFieldOnly: FieldAccess = ({ req: { user } }) => Boolean(user?.roles?.includes('admin'))
```

- **Public marketing site**: collections `read: authenticatedOrPublished` (needs `versions.drafts`) or `read: anyone`; writes `authenticated`; `Media` `read: anyone`; globals `read: anyone`.
- **RBAC**: `roles` select field with `hasMany: true`, `saveToJWT: true`, `access: { create/update: adminFieldOnly }`; then `req.user.roles` is available in every access fn without a DB hit. Split editors (`users`, `admin.user`) from members (`customers`, separate auth collection) so members cannot enter `/admin`.
- **Preview/draft reads**: authenticated `req.user` (from the preview cookie via `payload.auth`) is what lets `draft: true` reads see unpublished docs; anonymous callers still only get `_status: published`.
- **Multi-tenant**: use `@payloadcms/plugin-multi-tenant` rather than hand-rolling; use `slugField({ disableUnique: true })` plus a compound `indexes` entry.
- Test the Local API path: `overrideAccess: false` + `user` (see `local-api-and-queries.md`) to prove rules work.

## 5. Hook catalogue and signatures

> Verified against payload v3.90.2 (docs/hooks/{overview,collections,globals,fields}.mdx)

**Collection hooks** (`hooks: {...}`, each an array of sync/async fns):

| Hook | Args (besides `req`, `context`, `collection`) | Return |
| --- | --- | --- |
| `beforeOperation` | `args`, `operation` | modified `args` |
| `beforeValidate` | `data`, `operation`, `originalDoc` | `data` |
| `beforeChange` | `data`, `operation` ('create'/'update'), `originalDoc` | `data` |
| `afterChange` | `doc`, `previousDoc`, `data`, `operation` | `doc` |
| `beforeRead` | `doc`, `query` | `doc` |
| `afterRead` | `doc`, `query`, `findMany`, `overrideAccess` | `doc` |
| `beforeDelete` | `id` | - |
| `afterDelete` | `doc`, `id` | `doc` |
| `afterOperation` | `args`, `operation`, `result` | `result` |
| `afterError` | `error`, `graphqlResult`, `result` | optional transform |
| Auth only | `beforeLogin` (`user`), `afterLogin` (`user`, `token`), `afterLogout`, `afterRefresh`, `afterMe`, `afterForgotPassword`, `refresh`, `me` | |

Typed helpers: `CollectionBeforeValidateHook<Post>`, `CollectionBeforeChangeHook`, `CollectionAfterChangeHook`, `CollectionAfterReadHook`, `CollectionAfterDeleteHook`, `CollectionBeforeOperationHook`, `CollectionAfterOperationHook`, `GlobalAfterChangeHook`, `FieldHook`.

**Global hooks**: `beforeOperation`, `beforeValidate`, `beforeChange`, `afterChange`, `beforeRead`, `afterRead` (no delete hooks). **Root hook**: `hooks.afterError`. **Field hooks**: `beforeValidate`, `beforeChange`, `beforeDuplicate`, `afterChange`, `afterRead` (see `fields.md`).

Semantics worth knowing:
- On **update**, `data` is only the *delta* being saved (and no `id`); read `originalDoc` for current values and the id. On **create**, there is no id until `afterChange` - use `doc.id` there.
- `beforeChange` data is **unvalidated user input** (validation runs after it). Do not assume required fields exist.
- A hook that returns a Promise (any `async` function) is awaited, in series; a hook returning nothing synchronously is fire-and-forget. Un-awaited work can be cut off on serverless hosts - use the Jobs queue for anything long-running.
- Throw `new APIError('message', 429)` (from `payload`) for a controlled error response.
- Hooks are server-only and stripped from the client bundle.
- `afterOperation` `result` is the value before your modification; return the (possibly changed) result.

`v4:` `afterOperation` no longer reports `operation: 'read'` (use `'find'`/`'findByID'`); `transactionIDPromise` removed from `PayloadRequest`; `forceSelect` replaced by a collection/global `select` function.

## 6. Execution order

> Verified against payload v3.90.2 (packages/payload/src/collections/operations/create.ts L133-575, collections/operations/utilities/update.ts L70-95 and L205-545, fields/hooks/beforeChange/promise.ts L141-183, operations/find.ts L297-376, operations/deleteByID.ts L117-233)

create / update (order of *execution*):

1. `beforeOperation` (collection)
2. access check (`create`/`update`), file handling for uploads (`generateFileData`)
3. `beforeValidate` - **fields**, then **collection**
4. `beforeChange` - **collection** hooks first, then **fields**: within the field traversal each field's own `beforeChange` hooks run, *then that field's server-side `validate`* (so validation happens after collection `beforeChange`)
5. DB write, file upload, `saveVersion`
6. `afterRead` - fields, then collection (runs on the write result too)
7. `afterChange` - fields, then collection
8. `afterOperation`; transaction commits **after** these (create.ts commits at L575)

find: `beforeOperation` -> access -> `beforeRead` (collection) -> `afterRead` fields -> `afterRead` collection -> `afterOperation`. delete: `beforeOperation` -> access -> `beforeDelete` -> DB delete -> `afterRead` -> `afterDelete` -> `afterOperation`.

Consequences: (a) a collection `beforeChange` that reads a field validated later must validate itself; (b) `afterChange` side effects (revalidation, webhooks, emails) run **before the transaction commits**, so an external system reacting instantly may read old data, and a later failure rolls the DB back after the side effect already fired - keep side effects idempotent or push them to Jobs.

## 7. `req.context`, loop prevention, transactions

> Verified against payload v3.90.2 (docs/hooks/context.mdx, docs/database/transactions.mdx)

- `req.context` (`{ [key: string]: unknown }`) lives for the whole request and is passed to every hook. Pass extra context in via Local API `context: { flag: true }`. Augment the type with `declare module 'payload' { export interface RequestContext { disableRevalidate?: boolean } }`.
- **Infinite loops**: calling `payload.update()` on the same collection from its own `afterChange` re-triggers the hook. Guard with a context flag:

```ts
afterChange: [async ({ context, doc, req }) => {
  if (context.skipAfterChange) return doc
  await req.payload.update({ collection: 'pages', id: doc.id, data: { ... }, context: { skipAfterChange: true }, req })
  return doc
}]
```

- **Transactions**: every write runs in a transaction when the DB supports it (Mongo needs a replica set; SQLite transactions are **off by default** - pass `transactionOptions: {}`). The transaction id rides on `req.transactionID`. A hook that writes must pass `req` to join the same transaction (`req.payload.create({ collection, data, req })`) - omit it and the write is committed independently, so a later rollback leaves it behind. Conversely, if you fire an operation **without awaiting** it, do *not* pass `req` (a failure would otherwise report success on uncommitted data).
- Scripts: `payload.db.beginTransaction()` / `commitTransaction(id)` / `rollbackTransaction(id)` with `req: { transactionID }`.

## 8. Next.js revalidation pattern

> Verified against payload v3.90.2 (templates/website/src/collections/Pages/hooks/revalidatePage.ts, Footer/hooks/revalidateFooter.ts, endpoints/seed/index.ts L56-167, templates/website/package.json next 16.3.3)

The official website template's approach - copy it:

```ts
import type { CollectionAfterChangeHook, CollectionAfterDeleteHook } from 'payload'
import { revalidatePath, revalidateTag } from 'next/cache'

export const revalidatePage: CollectionAfterChangeHook<Page> = ({ doc, previousDoc, req: { payload, context } }) => {
  if (!context.disableRevalidate) {
    if (doc._status === 'published') {
      const path = doc.slug === 'home' ? '/' : `/${doc.slug}`
      payload.logger.info(`Revalidating page at path: ${path}`)
      revalidatePath(path)
      revalidateTag('pages-sitemap', 'max')
    }
    // slug/unpublish: also revalidate the OLD path
    if (previousDoc?._status === 'published' && doc._status !== 'published') {
      const oldPath = previousDoc.slug === 'home' ? '/' : `/${previousDoc.slug}`
      revalidatePath(oldPath)
      revalidateTag('pages-sitemap', 'max')
    }
  }
  return doc
}
export const revalidateDelete: CollectionAfterDeleteHook<Page> = ({ doc, req: { context } }) => {
  if (!context.disableRevalidate) { revalidatePath(doc?.slug === 'home' ? '/' : `/${doc?.slug}`); revalidateTag('pages-sitemap', 'max') }
  return doc
}
// wired: hooks: { afterChange: [revalidatePage], afterDelete: [revalidateDelete] }
```

- Globals use tags: `revalidateTag('global_footer', 'max')` in a `GlobalAfterChangeHook`; the frontend reads them through `getCachedGlobal(slug)` = `unstable_cache(() => payload.findGlobal({ slug, depth }), [slug], { tags: [`global_${slug}`] })` (utilities/getGlobals.ts). Redirects use `unstable_cache(getRedirects, ['redirects'], { tags: ['redirects'] })` and are busted by `revalidateRedirects` wired onto the redirects collection's `afterChange` in `plugins/index.ts`.
- `context.disableRevalidate` exists so **seed/import code** can skip revalidation: the template's seed endpoint passes `context: { disableRevalidate: true }` on its Local API calls (endpoints/seed/index.ts). Do the same in any bulk import. UNVERIFIED: whether `revalidatePath` throws when called outside a Next request scope (e.g. `payload run` scripts) - skip it via the flag regardless.
- Only revalidate when `_status === 'published'` (drafts/autosaves must not bust the cache), and revalidate the previous path when a slug changes or a page is unpublished.
- The template targets Next 16.3.3 and calls the **two-argument** `revalidateTag(tag, 'max')`. The two-arg signature is a Next.js 16 API; the template does not document it and this repo does not contain Next's source, so on Next 15 (`15.2.9`-`15.4.x`, also supported by Payload) check the single-argument form. UNVERIFIED against Next docs in this session.

## 9. Gotchas

> Verified against payload v3.90.2 (sources cited above)

1. No `access` set = authenticated-only. Public sites must opt in per collection, per global, and for `media`.
2. Field access cannot return `Where`; only collection/global `read`/`update`/`delete` can.
3. Returned `Where` is not executed during the Admin access probe - permission-based admin UI can differ from API results for query-constrained rules.
4. `draft: true` on a read never hides drafts by itself; it is `read` access that must filter `_status`.
5. Local API skips access by default (`overrideAccess: true`) - passing `user` alone enforces nothing. In v4 the default flips.
6. Collection `beforeChange` runs before validation; do not trust its data.
7. Missing `req` in nested hook writes breaks atomicity; passing `req` to un-awaited writes hides failures.
8. Same-collection `payload.update` in `afterChange` loops forever without a context flag.
9. `afterChange` runs before the DB transaction commits.
10. Changing a password via a Local API `update` without `user` logs the user out everywhere (see `config-and-collections.md` section 7).
