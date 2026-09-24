# Drafts, Preview, Live Preview, Scheduled Publish (v3.90.2)

The editorial loop for a content site: edit -> autosave a draft -> see it on the real frontend (preview or live preview) -> publish -> the public site updates. Each stage is a separate mechanism with its own prerequisites; most "live preview is broken" reports are a missing prerequisite in an earlier stage.

## Contents

1. The four mechanisms and how they differ
2. Versions and drafts prerequisites
3. The `draft` parameter, `_status`, and who can read drafts
4. Autosave
5. Preview button and draft mode (Next.js)
6. Live preview
7. Server vs client live preview
8. Publish and revalidation
9. Scheduled publish
10. Failure modes and fixes
11. Minimal working wiring (copy/paste)
12. v4 canary deltas

## 1. The four mechanisms and how they differ

> Verified against payload v3.90.2 (docs/admin/preview.mdx, docs/live-preview/overview.mdx, docs/versions/drafts.mdx).

| Mechanism | Config | What the editor gets | Data source on the frontend |
| --- | --- | --- | --- |
| Drafts | `versions.drafts` | Save draft vs Publish, `_status` field | `draft: true` reads latest version |
| Preview | `admin.preview(doc, { req, locale, token })` | A "Preview" button linking to a frontend URL | Frontend enters draft mode, queries with `draft: true` |
| Live preview | `admin.livePreview.url` (+ `breakpoints`, `collections`, `globals`) | An iframe of the frontend inside the editor that updates as you edit | Refresh-on-save (server) or `postMessage` form state (client) |
| Scheduled publish | `versions.drafts.schedulePublish` | "Schedule" publish/unpublish at a time | A `payload-jobs` job that updates `_status` |

Preview and Live Preview are independent: Preview is a direct link; Live Preview is an iframe. The website template wires both to the same `/next/preview` route.

## 2. Versions and drafts prerequisites

> Verified against payload v3.90.2 (docs/versions/drafts.mdx, docs/versions/autosave.mdx, packages/payload/src/versions/types.ts, templates/website/src/collections/Pages/index.ts).

```ts
versions: {
  drafts: {
    autosave: { interval: 100 },   // template value; default is 800ms
    schedulePublish: true,          // optional; requires a jobs runner
    // validate: true,              // default false: drafts skip required-field validation
  },
  maxPerDoc: 50,                    // default 100; 0 keeps everything
}
```

- Drafts require versions. Enabling drafts **injects a `_status` field** (`draft` | `published`). The admin shows Draft / Published / Changed (published with newer draft).
- Options (`IncomingDrafts`): `autosave` (`boolean | { interval, showSaveDraftButton }`), `schedulePublish` (`boolean | { timeFormat, timeIntervals }`, default `'h:mm aa'` and `5`), `validate`, `localizeStatus` (beta).
- Adding drafts to a collection that already has documents: old docs have **no `_status`** until re-saved. Anonymous read access written as `{ _status: { equals: 'published' } }` hides them — use `{ or: [{ _status: { equals: 'published' } }, { _status: { exists: false } }] }` during the transition (documented pattern).
- SQL adapters: enabling versions/drafts changes the schema (`_<slug>_versions` tables) — create and run a migration.

## 3. The `draft` parameter, `_status`, and who can read drafts

> Verified against payload v3.90.2 (docs/versions/drafts.mdx "Draft API" and "Controlling who can see Collection drafts").

`draft` is exposed on `create`, `update`, `find`, `findByID` in Local, REST (`?draft=true`), and GraphQL (`draft: true`).

Writes:
- `draft: true` -> skips required-field validation and, on **update**, writes **only to the versions table** (main document unchanged). First create always writes the main collection (with `_status: 'draft'` unless set).
- `_status: 'published'` in the data always publishes (updates the main collection) even if `draft: true` was passed. `draft` does not publish anything by itself; `_status: 'draft'` does not bypass required validation — you need `draft: true` for incomplete docs.
- Unpublish = set `_status: 'draft'`. "Revert to published" creates a new version equal to the last published state; drafts are kept.

Reads:
- Default `find`/`findByID` return the **main-collection** document (the published one, or a never-published draft that lives there).
- `draft: true` returns the **most recent version** from the versions table (draft or published).
- **`draft` alone does not restrict access.** Documents with `_status: 'draft'` are returned to anyone unless access control blocks them. The canonical guard (used by the template as `authenticatedOrPublished`):

```ts
access: { read: ({ req }) => req.user ? true : { _status: { equals: 'published' } } }
```

- Restricting who can publish: return a query constraint from `update` access (e.g. non-admins may only update `{ _status: { equals: 'draft' } }`); the admin then hides Publish/Unpublish, and scheduled publish jobs run as the scheduling user are blocked for them too.
- Local API bypasses access unless you pass `overrideAccess: false`. A Local API read used on a public page (e.g. an archive/related-posts block) with default `overrideAccess` can therefore return never-published drafts; the template's `ArchiveBlock` does this (see website-template.md section 5).

## 4. Autosave

> Verified against payload v3.90.2 (docs/versions/autosave.mdx, docs/live-preview/server.mdx).

- `autosave: true` or `{ interval (ms, debounced, default 800), showSaveDraftButton (default false) }`. Requires drafts.
- Autosaves are stored as **one** updating draft version rather than a new version per save (docs), so they do not multiply the `_versions` table.
- Autosaves are `update` operations with an `autosave` argument (Admin UI sets it). INFERENCE (not run): they go through the normal update path, so `beforeChange`/`afterChange` hooks fire with a draft doc — consistent with the template's revalidation hook acting only when `_status === 'published'`.
- Autosave interacts with `slugField`: slugs regenerate during autosave only until the doc has more than 2 versions, is published, or the user edits the slug manually.
- For server-side live preview, a **shorter interval makes the preview feel faster**; the template uses `100`. Cost: a write every 100ms of typing pause — fine locally, watch load on shared/serverless databases.

## 5. Preview button and draft mode (Next.js)

> Verified against payload v3.90.2 (docs/admin/preview.mdx, templates/website/src/utilities/generatePreviewPath.ts, src/app/(frontend)/next/preview/route.ts, next/exit-preview/route.ts, packages/payload/src/utilities/getSafeRedirect.ts).

Flow used by the template (all three pieces are required):

1. **URL builder** (`admin.preview` and `admin.livePreview.url`): returns a *relative* URL to a preview route with the target path and a shared secret; return `null` when there is no slug yet to hide the button.

```ts
const encoded = new URLSearchParams({
  path: `${collectionPrefixMap[collection]}/${encodeURIComponent(slug)}`,  // posts -> '/posts', pages -> ''
  previewSecret: process.env.PREVIEW_SECRET || '',
})
return `/next/preview?${encoded.toString()}`
```

2. **Preview route** (`GET /next/preview`): checks `previewSecret === process.env.PREVIEW_SECRET` (403), requires `path` (404), sanitizes it with `getSafeRedirect({ fallbackTo: '', redirectTo: path })` from `payload/shared` (500 if unsafe), authenticates with `payload.auth({ req, headers })` (403 on failure or no user, and calls `draftMode().disable()` when unauthenticated), then `draftMode().enable()` and `redirect(safePath)`.
3. **Frontend query**: `const { isEnabled: draft } = await draftMode()`, then `payload.find({ collection, draft, overrideAccess: draft, where, limit: 1, pagination: false })`. `overrideAccess: draft` lets the (already authenticated) previewer see drafts; anonymous visitors keep normal access rules.

`GET /next/exit-preview` calls `draftMode().disable()`; the template's `AdminBar` calls it from `onPreviewExit` and then `router.push('/'); router.refresh()`.

Security notes:
- Anyone with the secret plus a valid Payload session can enter draft mode; the secret alone is not enough because the route also requires `payload.auth` to return a user. The secret is embedded in the URL the admin hands to the editor (INFERENCE from the URL-builder design), so treat it as shared among editors, not confidential from them; never prefix it `NEXT_PUBLIC_`.
- **Use `getSafeRedirect` (or equivalent), not `path.startsWith('/')`.** The docs' sample route and v4 canary's template use `startsWith('/')`, which accepts protocol-relative `//evil.example` (open redirect). `getSafeRedirect` also rejects control characters, `/\\`, `/%2F`, `/javascript:` and `/http` prefixes, and requires the URL to resolve to the same origin.
- The `admin.preview` function also receives `token` (the user's JWT) and `req`, `locale`; do not put the JWT in a URL.
- Draft mode is per browser via Next's cookie. To preview a page you also need any per-page allow rules (add checks in the route: "You can add additional checks here to see if the user is allowed to preview this page").

## 6. Live preview

> Verified against payload v3.90.2 (docs/live-preview/overview.mdx, templates/website/src/payload.config.ts).

Config can live at the root (`admin.livePreview = { url, breakpoints, collections, globals }`) or per collection/global (`admin.livePreview`), where collection-level settings merge over the root. The template puts only `breakpoints` (Mobile 375x667, Tablet 768x1024, Desktop 1440x900) at the root and `url` on Pages/Posts.

- `url`: string or `({ data, req, locale, collectionConfig, globalConfig }) => string | null | undefined`. `data` includes **unsaved** changes. Return a relative URL (Payload builds the absolute one from the browser's protocol/host/port — good for Vercel preview deployments) or an absolute one (use `req.protocol`/`req.host` if needed). **Returning `null`/`undefined` hides the Live Preview button**; use it for access-style gating (`req.user?.role === 'admin' ? url : null`).
- `breakpoints`: each `{ label, name, width, height }`; "Responsive" (100% x 100%) is always present and default; users can also type custom dimensions or pop the preview into its own window.
- It is an iframe communicating via `window.postMessage`. The frontend must let the admin origin frame it (CSP `frame-ancestors "self" localhost:* https://your-site.com;` — see failure modes).

## 7. Server vs client live preview

> Verified against payload v3.90.2 (docs/live-preview/{frontend,server,client}.mdx, packages/live-preview-react/src/{RefreshRouteOnSave.tsx,useLivePreview.ts}, packages/live-preview/src/isDocumentEvent.ts).

Docs recommendation: **server-side live preview for frameworks with Server Components (Next.js App Router); client-side only for client-only frameworks** (Pages Router, React Router, Vue 3/Nuxt, etc.).

| | Server-side (`RefreshRouteOnSave`) | Client-side (`useLivePreview`) |
| --- | --- | --- |
| Package | `@payloadcms/live-preview-react` | `@payloadcms/live-preview-react` or `-vue`; base `@payloadcms/live-preview` for custom |
| Trigger | Admin emits a document event **after a save** (draft save, autosave, publish) | Admin emits debounced **form-state** events on every change |
| Update mechanism | `router.refresh()` -> RSC re-renders with fresh Local API data | Hook merges form state into `initialData` and populates relationships client-side |
| Latency | Depends on autosave `interval` (lower = snappier) | Instant, no save |
| Correctness | Renders exactly what production would (same queries, access, `depth`) | Must keep `depth` identical to the initial fetch or relations/uploads vanish; needs CORS/CSRF for cross-domain populate |
| Cost | A server round trip + write per autosave | No writes; extra client fetches to populate relations |

Server-side wiring (the template's `LivePreviewListener`):

```tsx
'use client'
import { RefreshRouteOnSave as PayloadLivePreview } from '@payloadcms/live-preview-react'
import { useRouter } from 'next/navigation'
export const LivePreviewListener = () => {
  const router = useRouter()
  return <PayloadLivePreview refresh={router.refresh} serverURL={getClientSideURL()} />
}
// page.tsx:  {draft && <LivePreviewListener />}   // only render it in draft mode
```

Component props: `refresh` (required), `serverURL` (required), `apiRoute?`, `depth?`. Behavior read from source: it listens for `message` events, calls `ready({ serverURL })` once to tell the admin the frontend is listening, then calls `refresh()` once after ready to pick up the latest data. **`isDocumentEvent` requires `event.origin === serverURL` and `event.data.type === 'payload-document-event'`** — `serverURL` must exactly equal the admin's origin (scheme + host + port); the template gets this right by using `window.location` in the browser.

Client-side hook: `useLivePreview<T>({ initialData, serverURL, depth = 0, apiRoute = '/api' }) -> { data, isLoading }`. Fetch the page in a server component, pass it as `initialData`, and make `depth` **match the initial request exactly**. Write UI defensively (`data?.relatedPosts?.[0]?.title`) because removing a required relation in the editor produces transient invalid shapes.

Building your own (any framework): `@payloadcms/live-preview` exports `ready`, `isDocumentEvent` (server-style) and `subscribe`, `unsubscribe`, `isLivePreviewEvent` (client-style, does merging + population). Vue: `@payloadcms/live-preview-vue` `useLivePreview` composable.

Docs typo to ignore: `docs/live-preview/server.mdx` once calls the component `RefreshRouteOnChange`; the exported name is `RefreshRouteOnSave`.

## 8. Publish and revalidation

> Verified against payload v3.90.2 (templates/website/src/collections/Pages/hooks/revalidatePage.ts, src/collections/Posts/hooks/revalidatePost.ts).

The public site only changes when a **published** document changes, so the revalidation hook keys off `_status`:

```ts
afterChange: ({ doc, previousDoc, req: { payload, context } }) => {
  if (!context.disableRevalidate) {
    if (doc._status === 'published') { revalidatePath(pathFor(doc)); revalidateTag('pages-sitemap', 'max') }
    if (previousDoc?._status === 'published' && doc._status !== 'published') {   // unpublish or slug change
      revalidatePath(pathFor(previousDoc)); revalidateTag('pages-sitemap', 'max')
    }
  }
  return doc
}
```

- The template revalidates the **old path** only when a doc stops being published. A **slug rename while it stays published** revalidates only the new path (read from `revalidatePage.ts`: the second branch requires `doc._status !== 'published'`), so the old URL can keep serving cached HTML. Add a `previousDoc.slug !== doc.slug` branch.
- Set `context: { disableRevalidate: true }` on Local API writes made by seeds/imports to avoid revalidating hundreds of paths (the template's seed does this for globals).
- Revalidation only works inside the Next runtime; from a standalone script it fails (the template's seed notes revalidate errors are expected without a running server).

## 9. Scheduled publish

> Verified against payload v3.90.2 (docs/versions/drafts.mdx, packages/payload/src/versions/schedule/job.ts, packages/ui/src/utilities/schedulePublishHandler.ts, packages/payload/src/config/sanitize.ts, docs/jobs-queue/queues.mdx, templates/with-vercel-website/vercel.json).

- Enable with `versions.drafts.schedulePublish: true` (or `{ timeFormat, timeIntervals }`). Payload auto-registers a `schedulePublish` task in `config.jobs.tasks` and the admin gets a Schedule drawer (publish or unpublish, with optional locale and timezone).
- Scheduling queues a `payload-jobs` job (`task: 'schedulePublish'`, `waitUntil: date`, input includes `doc`, `type`, `locale`, `timezone`, and the scheduling **user** as `{ relationTo, value }`). The queue handler starts with `canAccessAdmin`; listing a document's upcoming events additionally requires update permission for `_status: 'published'` on it.
- The task runs `payload.update({ id, collection, data: { _status }, depth: 0, overrideAccess: user === null, publishSpecificLocale, user })` — so it runs **as the scheduling user** with normal access rules and fires collection hooks (your revalidate hook included). Jobs queued by older Payload versions without the stored auth collection fail closed and must be re-scheduled.
- **Nothing runs the job unless you run jobs.** Options (docs/jobs-queue/queues.mdx): `jobs.autoRun: [{ cron, queue }]` inside the Next process (dedicated servers), `pnpm payload jobs:run --cron "*/5 * * * *"` as a separate worker, or call `GET /api/payload-jobs/run` (optional `?queue=` and `limit`) from a scheduler. The template authorizes that endpoint with a logged-in user or `Authorization: Bearer ${CRON_SECRET}` (`jobs.access.run`), matching Vercel Cron; `with-vercel-website` ships `vercel.json` cron `path: /api/payload-jobs/run, schedule: "0 0 * * *"` (**once a day**), so scheduled publishes there fire at most daily on that schedule. Vercel plan tiers may limit cron frequency (README note).
- INFERENCE (not run): a separate `payload jobs:run` worker is not a Next request context, so `revalidatePath`/`revalidateTag` inside your `afterChange` hook will not purge the web app's cache when a scheduled publish fires there. Prefer running jobs via the in-app endpoint/`autoRun` for content sites, or trigger revalidation by calling a Next route from the hook.

## 10. Failure modes and fixes

> Verified against payload v3.90.2 (docs/live-preview/{overview,server,client}.mdx, docs/authentication/cookies.mdx, docs/versions/drafts.mdx, template + package sources). Items marked INFERENCE follow from those sources but were not run.

| Symptom | Cause | Fix |
| --- | --- | --- |
| No Live Preview / Preview button | `url`/`preview` returned `null` (e.g. slug not set yet) or collection not enabled (root config needs `collections`/`globals`) | Set slug first; add per-collection `admin.livePreview`; check return values |
| Iframe blank / "refused to connect" | CSP or `X-Frame-Options` on the frontend | `frame-ancestors "self" <admin origin>` (docs) |
| Iframe loads but never updates | `serverURL` prop != admin origin (`isDocumentEvent` compares `event.origin`), `<RefreshRouteOnSave>` not rendered (template renders it only when `draftMode` is enabled), or autosave/drafts not enabled | Pass the exact admin origin; render listener in draft mode; enable drafts + autosave |
| Preview shows published content, not the draft | Page query lacks `draft: true`, or draft mode cookie not set | Query with `draft: isDraftMode` and go through the preview route |
| Preview 403 | Wrong/missing `PREVIEW_SECRET`, or no valid Payload cookie (not logged in; cross-site cookie blocked) | Same env on server and admin; log in on the same site |
| Cross-domain frontend never authenticates the preview | Cookies are third-party | Use subdomains, or `auth.cookies: { sameSite: 'None', secure: true }` + `csrf`/`cors` allow-lists (docs; `secure` needs HTTPS, turn off on localhost) |
| Draft visible to the public | Read access does not filter `_status`; or a Local API query without `overrideAccess: false` | Use the `_status` constraint; set `overrideAccess: false` on public queries |
| Old documents vanish after enabling drafts | No `_status` on legacy docs | Allow `_status: { exists: false }` or re-save |
| Client live preview drops images/relations | `depth` mismatch between initial fetch and hook; CORS/CSRF for a separate frontend | Same `depth`; configure `cors`/`csrf` |
| Page not updating after publish | Revalidation hook missing, `context.disableRevalidate` set, running outside Next, or a listing page on a fixed `revalidate` (template `/posts` = 600s) | Hook on `afterChange`/`afterDelete`; revalidate listings too |
| Renamed slug still serves old URL | Only new path revalidated | Revalidate `previousDoc` path when the slug changes |
| Scheduled publish never fires | No jobs runner | `autoRun`, `payload jobs:run`, or cron -> `GET /api/payload-jobs/run` |
| Scheduled publish fires late | Cron cadence (template Vercel cron is daily) | Increase cron frequency |
| Home page previews at `/home` instead of `/` | `generatePreviewPath` builds `path` as prefix `''` + `/home`; the `[slug]` route serves it | Acceptable, or special-case `home` -> `/` |
| Autosave floods DB in prod | `interval: 100` | Raise interval on shared/serverless DBs (default 800ms) |

## 11. Minimal working wiring (copy/paste)

> Verified against payload v3.90.2 (assembled from the template files cited above).

1. Collection: `versions: { drafts: { autosave: { interval: 300 }, schedulePublish: true }, maxPerDoc: 50 }`, `access.read` = published-or-authenticated, `admin.preview` and `admin.livePreview.url` = `generatePreviewPath(...)`, `hooks.afterChange/afterDelete` = revalidate hooks.
2. Root: `admin.livePreview.breakpoints`; `cors`/`csrf` include the frontend origin if it differs.
3. Env: `PREVIEW_SECRET`, `NEXT_PUBLIC_SERVER_URL`, `CRON_SECRET` (if using scheduled publish via HTTP), plus `PAYLOAD_SECRET`.
4. Frontend routes: `/next/preview` (secret + `getSafeRedirect` + `payload.auth` + `draftMode().enable()`), `/next/exit-preview`.
5. Page: `draftMode()` -> `find({ draft, overrideAccess: draft })`; render `<LivePreviewListener />` when draft.
6. Jobs: choose a runner if `schedulePublish` is on.
7. Test the loop end to end with a Playwright/browser session: log in, edit a page, watch autosave, open Live Preview at Mobile/Desktop, publish, confirm the public URL changed, unpublish, confirm 404, then schedule a publish two minutes out and confirm the runner fires it.

## 12. v4 canary deltas

> Diffed against payload main `5448061a` (4.0.0-canary.37) vs tag v3.90.2 (template files under `templates/website`).

- v4 template `next/preview/route.ts` reverts to `if (!path.startsWith('/'))` and `redirect(path)` instead of `getSafeRedirect` — do not copy that form.
- v4 template `LivePreviewListener`, `revalidatePage`, `generatePreviewPath`-related files are otherwise unchanged in the diff.
- v4 template replaces `slugField()` with a `{ type: 'slug', useAsSlug: 'title' }` field type; the draft/autosave behavior of slugs was not re-diffed.
