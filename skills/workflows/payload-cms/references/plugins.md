# Official Payload Plugins, Adapters, and Integrations (v3.90.2)

What each official package does, the options that matter for a marketing/content site, and the traps. Option names come from each package's `src/types.ts` (or `index.ts`) at tag v3.90.2, cross-checked against `docs/plugins/*`. Where docs and code disagree, code wins and the drift is listed.

## Contents

1. How plugins compose
2. SEO
3. Redirects
4. Nested Docs
5. Form Builder
6. Search
7. Import/Export
8. Multi-Tenant
9. MCP
10. Sentry
11. Stripe
12. Ecommerce
13. Storage adapters
14. Email adapters
15. Other packages (admin-bar, payload-cloud, cloud-storage, csm)
16. v4 canary deltas

## 1. How plugins compose

> Verified against payload v3.90.2 (docs/plugins/overview.mdx, docs/plugins/build-your-own.mdx, plugin index.ts files).

- A plugin is `(config: Config) => Config` (or a function returning one). `plugins: [...]` run **in array order, after the incoming config is validated and before it is sanitized**; each plugin sees the output of the previous one. Order matters when plugins read or extend the same collection (e.g. SEO `tabbedUI` merges tabs "smartly" only depending on order) and when a plugin must see collections added by an earlier one (form-builder reads `config.collections` to build redirect options).
- Every plugin here that adds a collection appends it to `config.collections`, and its collection config accepts overrides (`overrides` / `formOverrides` / `formSubmissionOverrides` / `searchOverrides`) where `fields` is a **function** `({ defaultFields }) => Field[]` and everything else is a partial collection config spread over the defaults.
- Regenerate types (`pnpm generate:types`) and the import map (`pnpm generate:importmap`) after adding any plugin; plugin admin components are referenced by import-map path strings.
- Postgres/SQLite adapters: adding a plugin that adds collections/fields is a schema change — create and commit a migration.

## 2. SEO — `@payloadcms/plugin-seo`

> Verified against payload v3.90.2 (packages/plugin-seo/src/{index,types}.ts, docs/plugins/seo.mdx, templates/website/src/plugins/index.ts).

`pnpm add @payloadcms/plugin-seo`

Options (`SEOPluginConfig`): `collections`, `globals`, `fields(({ defaultFields }) => Field[])`, `uploadsCollection`, `tabbedUI` (default false), `generateTitle`, `generateDescription`, `generateImage`, `generateURL`, `interfaceName`. Each `generate*` receives `{ doc, locale, collectionConfig, globalConfig, req, ...docInfo }` (`docInfo` = `id`, `collectionSlug`, `globalSlug`, `initialData`, `title`, ...) and may be async; `generateImage` returns an id/object. Field group is `meta` = `title`, `description`, `image`, plus a live SERP `preview`.

Direct-use exports (`@payloadcms/plugin-seo/fields`): `OverviewField({ titlePath, descriptionPath, imagePath })`, `MetaTitleField({ hasGenerateFn })`, `MetaDescriptionField({ hasGenerateFn })`, `MetaImageField({ relationTo, hasGenerateFn })`, `PreviewField({ hasGenerateFn, titlePath, descriptionPath })`. Types: `@payloadcms/plugin-seo/types` (`GenerateTitle<T>`, `GenerateURL<T>`, ...).

Website-template pattern (put SEO fields in a named `meta` tab by hand, keep plugin only for generators) has a consequence, **found by reading `index.ts`**: the plugin's `/plugin-seo/generate-*` endpoints authorize the target via `authorizeGenerateTarget`, which only resolves `collectionConfig`/`globalConfig` when the slug is in `pluginConfig.collections` / `pluginConfig.globals`, and otherwise `throw new Forbidden`. The template calls `seoPlugin({ generateTitle, generateURL })` with no `collections`, so by code reading the "Auto-generate" button in the template's SEO tab would be refused with 403. (Code-read, not exercised at runtime.) Fix: pass `collections: ['pages','posts']` even when you place the fields manually. The endpoints also require a logged-in user who passes `canAccessAdmin`, and re-check read access on the document (`findByID` with `overrideAccess: false`, `draft: true`).

Other notes: `MetaImageField` needs `relationTo`; the plugin only adds `image` automatically if `uploadsCollection` is set. The generated GraphQL/TS interface name can collide — set `interfaceName`. `tabbedUI: true` wraps existing fields into a `Content` tab unless the first field is already `tabs`; do not use it with a complex/sidebar layout (docs recommend direct field use instead).

## 3. Redirects — `@payloadcms/plugin-redirects`

> Verified against payload v3.90.2 (packages/plugin-redirects/src/{index,types,redirectTypes}.ts, docs/plugins/redirects.mdx, templates/website/src/plugins/index.ts, src/hooks/revalidateRedirects.ts).

`pnpm add @payloadcms/plugin-redirects`

Options: `collections: string[]` (targets for the `to.reference` relationship), `overrides` (`{ fields?: fn } & Partial<CollectionConfig>`), `redirectTypes` (subset of `'301' | '302' | '303' | '307' | '308'`), `redirectTypeFieldOverride` (partial select field).

Behavior read from source:
- Adds a `redirects` collection (slug overridable) with `from` (text, `index`, **`unique`**, required) and `to` group: `type` radio (`reference` default | `custom`), `reference` (relationship to `collections`, required when shown), `url`. The select field `type` (status code) is added **only if `redirectTypes` is provided**.
- Default access: `read: () => true` (public); create/update/delete are not set by the plugin, so Payload's collection defaults apply. Override via `overrides.access`.
- **The plugin does not perform redirects.** Your frontend must query the collection and redirect (Next.js `redirect()` in a server component like the template's `PayloadRedirects`, `redirects()` in `next.config`, or middleware).
- The template bolts on `overrides.hooks.afterChange: [revalidateRedirects]` (`revalidateTag('redirects','max')`) and edits the `from` field's admin description via `overrides.fields`. Because the template caches the whole list with `unstable_cache` tag `redirects`, forgetting that hook means redirects never update until rebuild.
- For a site migration import old URLs as `from` (leading slash, no domain), keep them unique, and prefer permanent status codes via `redirectTypes` + a frontend that honors `type`.

## 4. Nested Docs — `@payloadcms/plugin-nested-docs`

> Verified against payload v3.90.2 (packages/plugin-nested-docs/src/types.ts, docs/plugins/nested-docs.mdx, templates/website/src/plugins/index.ts).

`pnpm add @payloadcms/plugin-nested-docs`

Options (`NestedDocsPluginConfig`): `collections` (required), `generateLabel(docs, currentDoc, collection, req)`, `generateURL(docs, currentDoc, collection, req)`, `parentFieldSlug`, `breadcrumbsFieldSlug`. Adds a self-referencing `parent` relationship and a `breadcrumbs` array (`doc`, `label`, `url`) to each collection; changing a parent recursively re-saves descendants; `breadcrumbs` is localized automatically if localization is on. Helpers: `createParentField(slug, overrides)`, `createBreadcrumbsField(slug, overrides)`.

Traps:
- Overriding the field `name` requires also setting `parentFieldSlug` / `breadcrumbsFieldSlug`; if you opt out of the auto fields, both must be **top-level** fields (not inside a group/array/blocks/tabs-in-group).
- If you override `parent.filterOptions`, keep the "not myself" constraint (`{ id: { not_equals: id } }`).
- `breadcrumbs[].url` is undefined unless `generateURL` is set. The template uses `docs.reduce((url, doc) => `${url}/${doc.slug}`, '')` on `categories` only; pages stay flat.
- Nested pages need a catch-all route and a canonical `fullPath` (see website-template.md section 18); the plugin gives you the data, not the routing.
- Multiple configurations are supported by adding the plugin more than once with different `collections`.

## 5. Form Builder — `@payloadcms/plugin-form-builder`

> Verified against payload v3.90.2 (packages/plugin-form-builder/src/{index,types}.ts, collections/Forms/index.ts, collections/FormSubmissions/index.ts, docs/plugins/form-builder.mdx, templates/website/src/blocks/Form/*).

`pnpm add @payloadcms/plugin-form-builder`

Options (`FormBuilderPluginConfig`): `fields` (per-type boolean or block override), `redirectRelationships: string[]`, `beforeEmail`, `defaultToEmail`, `formOverrides`, `formSubmissionOverrides`, `handlePayment`, `uploadCollections: UploadCollectionSlug[]`.

- Defaults merged in code: `checkbox, country, email, message, number, select, state, text, textarea` = `true`; `payment` and `upload` = `false`; `radio` and `date` are opt-in (docs list them).
- Adds `forms` and `form-submissions`. `forms`: `read: () => true`; the `emails` array field is readable only when `req.user.collection === config.admin.user`. **Do not leak recipient addresses** if you add frontend user accounts — tighten both. `form-submissions`: `create: () => true` (public, no rate limit or CAPTCHA built in), `read` admin-collection users only, `update: () => false`. Add spam protection (honeypot/Turnstile in a `beforeChange`/`beforeValidate` hook or in front of `/api/form-submissions`) yourself.
- Submission body: `{ form: <formId>, submissionData: [{ field: <name>, value }] }` to `POST /api/form-submissions` (this is what the template's client `FormBlock` sends).
- Emails: uses the root `email` adapter (set `email: nodemailerAdapter/resendAdapter`; without one Payload only logs a warning). `defaultToEmail` falls back to the adapter's `defaultFromAddress`. Subject/body support `{{field_name}}`, `{{*}}` (all as key:value) and `{{*:table}}`. Rich-text body is serialized to HTML on the server. `beforeEmail(emailsToSend, beforeChangeParams)` runs after preparation and before sending (wrap in an HTML template here). SendGrid note from docs: with domain authentication the from address must be on your domain — you cannot use `{{email}}` as From.
- `afterChange` sends the email (`sendEmail`); `beforeChange` runs `handleUploads` (only if `uploadCollections` set) and `createCharge` (`handlePayment`).
- Upload fields: enabling `fields.upload` without a non-empty `uploadCollections` logs a warning and the field is not registered. **Docs drift:** the docs' first `fields` example nests `uploadCollections` inside `upload: {...}`; the type and code use a **top-level** `uploadCollections`. Submit files as `multipart/form-data` with the field name as the file key.
- GraphQL/TS name collisions (e.g. a type named `Country`) are fixed with `interfaceName` on the plugin field config and `graphQL.singularName` on the collection.
- Rendering is your job: map `blockType` to your own components. The template maps only nine types (see website-template.md section 14).

## 6. Search — `@payloadcms/plugin-search`

> Verified against payload v3.90.2 (packages/plugin-search/src/{types,index}.ts, Search/index.ts, docs/plugins/search.mdx, templates/website/src/search/*).

`pnpm add @payloadcms/plugin-search`

Options: `collections`, `beforeSync({ originalDoc, searchDoc, req, payload, collectionSlug })`, `defaultPriorities` (number or `(doc) => number` per slug; adds a sortable `priority`), `searchOverrides`, `localize` (localizes `title` when localization is on), `syncDrafts` (default **false**), `deleteDrafts` (default **true**), `skipSync({ collectionSlug, doc, locale, req })`, `reindexBatchSize` (default 50). `apiBasePath` is deprecated (the plugin reads `routes.api`).

- Creates an indexed `search` collection: `create: () => false` (only the plugin creates records), `read: () => true`. Records hold `doc: { relationTo, value }`, `title`, `priority` plus whatever `beforeSync` and field overrides add — store only search-critical data. A **Reindex** button appears in the search list view (needed when adding the plugin to a project that already has content).
- With drafts on, only published docs are indexed unless `syncDrafts: true`; docs moving to draft are removed unless `deleteDrafts: false`.
- The template indexes `posts` only and searches with `like` across `title`, `meta.title`, `meta.description`, `slug` — no ranking or typo tolerance. For real search use Algolia/Meilisearch/Typesense via `beforeSync`/hooks (the payloadcms.com repo depends on `@docsearch/react`).

## 7. Import/Export — `@payloadcms/plugin-import-export`

> Verified against payload v3.90.2 (packages/plugin-import-export/src/types.ts, docs/plugins/import-export.mdx).

`pnpm add @payloadcms/plugin-import-export` — `importExportPlugin({ collections: [{ slug: 'pages' }, ...] })` (defaults to all collections).

- Options: `debug`, `exportLimit`, `importLimit` (0 = unlimited; number or function), `overrideExportCollection`, `overrideImportCollection`. Per collection: `export`/`import` = `false | { batchSize (100), disableJobsQueue, limit, hooks {before, after}, overrideCollection }`; export adds `disableDownload`, `disableSave`, `format ('csv'|'json')`; import adds `defaultVersionStatus ('draft'|'published')`.
- **Requires a jobs runner by default** (imports/exports stay `pending` forever otherwise): set `jobs.autoRun` (`[{ cron: '*/5 * * * *', queue: 'default' }]` or `allQueues: true`), run `payload jobs:run`, or set `disableJobsQueue: true` per collection to run synchronously (blocks the request).
- Import parameters: `collectionSlug`, `importMode` (`create` default | `update` | `upsert`), `matchField` (e.g. `slug` or `email`; default match is `id`), `locale`. Ways in: admin Import drawer, `payload.create({ collection: 'imports', data: {...}, file })`, or `payload.jobs.queue({ task: 'createCollectionImport', input })`. Results land on the import doc (`status`, `summary.total/imported/updated/issues/issueDetails`).
- This is the sanctioned bulk-load path for CSV/JSON when cloning a site's content: `upsert` with `matchField: 'slug'` makes re-runs idempotent. Relationship and localized columns follow the documented CSV naming convention (`docs/plugins/import-export.mdx` "CSV Format").

## 8. Multi-Tenant — `@payloadcms/plugin-multi-tenant`

> Verified against payload v3.90.2 (docs/plugins/multi-tenant.mdx incl. the `MultiTenantPluginConfig` type block; packages/plugin-multi-tenant).

`pnpm add @payloadcms/plugin-multi-tenant` — one Payload serving several sites.

- `multiTenantPlugin<Config>({ collections: { pages: {}, navigation: { isGlobal: true } }, ... })`. You **own the `tenants` collection** (`tenantsSlug` default `'tenants'`) and its fields (name/slug/domain are suggestions).
- Adds a `tenant` field to each listed collection, a tenant selector in the admin, filters list views and relationship pickers by tenant, and adds a `tenants` array field to the users collection (`tenantsArrayField`). `isGlobal: true` makes a collection behave like a per-tenant global (one doc per tenant, e.g. header/footer/settings).
- Options worth knowing: `userHasAccessToAllTenants(user)` (super-admins), `cleanupAfterTenantDelete` (default **true** — deleting a tenant deletes its documents; lock down `tenants` access), per-collection `useTenantAccess`, `useBaseFilter`, `customTenantField`, `tenantFieldOverrides`, `accessResultOverride`, `debug` (shows the tenant field), `basePath`.
- Write enforcement (recent): every create/update is checked against the user's assigned tenants, including drafts/autosave; skipped for `userHasAccessToAllTenants`, other auth collections, unchanged tenants, and Local API calls with no user. Local API calls that pass a `user` are checked **even with `overrideAccess: true`**. Public-create collections must set `tenant` server-side.
- `slugField({ disableUnique: true })` plus a compound unique index on `[tenant, slug]` is the intended way to allow the same slug on different sites.
- Frontend: filter with `'tenant.slug': { equals }` (or by domain) and use Next.js `rewrites()` with `has: [{ type: 'host', value: '(?<tenantDomain>.*)' }]` to route `/[tenantDomain]/[slug]`; there is an official `examples/multi-tenant`.

## 9. MCP — `@payloadcms/plugin-mcp`

> Verified against payload v3.90.2 (docs/plugins/mcp.mdx).

`pnpm add @payloadcms/plugin-mcp` — exposes collections/globals to MCP clients (Claude Code, Cursor, VS Code) at `/api/mcp`.

- `mcpPlugin({ collections: { posts: { enabled: true | { find, create, update, delete }, description, overrideResponse } }, globals: { slug: { enabled: { find, update } } }, userCollection, overrideApiKeyCollection, overrideAuth, disabled, mcp: { tools, prompts, resources, handlerOptions: { verboseLogs, maxDuration (60s), onEvent }, serverOptions } })`.
- **Two gates**: enable in config AND toggle capabilities per key in the admin (**MCP -> API Keys**). All requests need `Authorization: Bearer <key>`. Requests run as the key's owner user, so collection access, hooks, and multi-tenant rules still apply.
- The generated API-key collection denies admin/REST/GraphQL access by default; configure `overrideApiKeyCollection` to see/manage keys in the admin panel.
- Connect Claude Code: `claude mcp add --transport http Payload http://127.0.0.1:3000/api/mcp --header "Authorization: Bearer MCP-USER-API-KEY"`. Test with `npx @modelcontextprotocol/inspector` or the documented `tools/list` curl.
- Keep token use down: write strong descriptions, use `select` in tool definitions, `overrideResponse` to sanitize, and enable only needed operations (docs "Performance" section). Give write access sparingly — an MCP-connected model can create/update/delete documents.

## 10. Sentry — `@payloadcms/plugin-sentry`

> Verified against payload v3.90.2 (packages/plugin-sentry/src/types.ts, docs/plugins/sentry.mdx).

Complete the Sentry-for-Next.js setup first (`npx @sentry/wizard@latest -i nextjs`), then `sentryPlugin({ Sentry })` with `import * as Sentry from '@sentry/nextjs'`. `PluginOptions`: `enabled`, `Sentry` (required unless disabled), `options: { captureErrors: number[] (default only 5xx), context(args), debug }`. **Docs drift:** the docs' "Options" list shows `context`/`captureErrors` at top level; the type and the docs' example nest them under `options`. For Postgres query traces inject the patched driver: `postgresAdapter({ pool, pg })`.

## 11. Stripe — `@payloadcms/plugin-stripe`

> Verified against payload v3.90.2 (docs/plugins/stripe.mdx).

`stripePlugin({ stripeSecretKey, stripeWebhooksEndpointSecret, rest, webhooks, sync, logs })`. Endpoints: `POST /api/stripe/webhooks`, and `POST /api/stripe/rest` **only when `rest: { allowedMethods: [...], access? }` is set** (the old boolean `rest: true` is rejected; omit `rest` to disable). Opening the REST proxy in production is a documented security risk — keep `allowedMethods` minimal or use the server-side `stripeProxy`. `sync` mirrors collections to Stripe objects (one- and two-way).

## 12. Ecommerce — `@payloadcms/plugin-ecommerce` (Beta)

> Verified against payload v3.90.2 (docs/ecommerce/overview.mdx, templates/ecommerce/src/plugins/index.ts).

Docs banner: **Beta, breaking changes possible.** `ecommercePlugin({ access: { adminOnlyFieldAccess, adminOrPublishedStatus, isAdmin, isAuthenticated, isCustomer, isDocumentOwner, customerOnlyFieldAccess }, customers: { slug: 'users' }, orders: { ordersCollectionOverride }, ... })`. You must supply the access functions. Provides products + variants (variant types/options via join), carts (guest or customer), transactions, orders, addresses, multi-currency price fields, a payments adapter interface (Stripe adapter at `@payloadcms/plugin-ecommerce/payments/stripe`), and React utilities. Shipping, taxes, and subscriptions are not handled. The official `templates/ecommerce` wires SEO, form-builder (payment off), and this plugin together.

## 13. Storage adapters

> Verified against payload v3.90.2 (docs/upload/storage-adapters.mdx).

Local disk (`upload.staticDir`) does not work on serverless/ephemeral hosts; use an adapter. All are added to `plugins` with a `collections` map (slug -> `true | { prefix, ... }`); adapters set `disableLocalStorage: true` for those collections.

| Service | Package / factory | Key notes |
| --- | --- | --- |
| Vercel Blob | `@payloadcms/storage-vercel-blob` `vercelBlobStorage` | `token: BLOB_READ_WRITE_TOKEN`; server uploads capped at **4.5MB on Vercel** -> `clientUploads: true`; options `addRandomSuffix`, `cacheControlMaxAge` (1y), `useCompositePrefixes` |
| S3 (and R2 via S3 API) | `@payloadcms/storage-s3` `s3Storage` | `bucket`, `config` (`S3ClientConfig`), `acl`, `clientUploads` (needs CORS `PUT` + `If-None-Match`), `signedDownloads` (presigned URLs, optional per-file `shouldUseSignedURL`) |
| Azure | `@payloadcms/storage-azure` | |
| Google Cloud | `@payloadcms/storage-gcs` | |
| Uploadthing | `@payloadcms/storage-uploadthing` | |
| Cloudflare R2 (Workers binding) | `@payloadcms/storage-r2` | only for Cloudflare Workers; on Vercel/Netlify/Node use `storage-s3` with the R2 endpoint |
| Custom | `@payloadcms/plugin-cloud-storage` `cloudStoragePlugin` | implement `GeneratedAdapter` (`handleUpload`, `handleDelete`, `staticHandler`, optional `generateURL`, `fields`, `onInit`) |

R2 via S3: `region: 'auto'`, `endpoint`, `forcePathStyle: true`; buckets are **private by default** and the S3 endpoint is upload-only — enable the R2.dev subdomain or a custom domain and set `generateFileURL` (with `disablePayloadAccessControl: true`) to serve files. Use `enabled: Boolean(process.env.S3_BUCKET)` to fall back to local storage in dev.

## 14. Email adapters

> Verified against payload v3.90.2 (docs/email/overview.mdx).

Pass `email:` to `buildConfig`. Both adapters require `defaultFromName` and `defaultFromAddress`. `@payloadcms/email-nodemailer` (`nodemailerAdapter`, `transportOptions` or `transport`; any Nodemailer transport incl. SMTP/SendGrid) is the 2.x-compatible path. `@payloadcms/email-resend` (`resendAdapter({ apiKey })`) is lighter and preferred for serverless (Vercel). With no adapter Payload logs a startup warning and on every send attempt. Auth emails (verify, reset password) and form-builder notifications all use this adapter; send your own with `payload.sendEmail({ to, subject, html | text })`.

## 15. Other packages

> Verified against payload v3.90.2 (`ls packages`, templates/website/src/components/AdminBar, docs/migration-guide/overview.mdx, docs/integrations/vercel-content-link.mdx).

- `@payloadcms/admin-bar` (`PayloadAdminBar`): logged-in-editor toolbar for the public site. Props used by the template: `cmsURL`, `collectionSlug`, `collectionLabels`, `logo`, `preview` (draft mode on), `onAuthChange`, `onPreviewExit`, `className/classNames/style`. React peer `^19` supported.
- `@payloadcms/payload-cloud` (`payloadCloudPlugin`): the Payload Cloud plugin (migration guide renames it from `@payloadcms/plugin-cloud` / `payloadCloud`). Only relevant if hosting on Payload Cloud.
- `@payloadcms/live-preview`, `live-preview-react`, `live-preview-vue`: see live-preview-and-drafts.md.
- `@payloadcms/plugin-csm` (Vercel Content Link / content source maps): **enterprise-only and Vercel-only**, requires a sales-provided API key; the docs' snippet still imports from `payload/config` (v2 path) — treat as stale. Pass `encodeSourceMaps=true` only in draft mode/preview deployments.
- Also present in `packages/`: `kv-redis`, `sdk`, `typescript-plugin`, `eslint-config`/`eslint-plugin`, `translations`, `ui`, richtext (`lexical`, `slate`), DB adapters (see deployment reference).

## 16. v4 canary deltas

> Diffed against payload main `5448061a` (4.0.0-canary.37) vs tag v3.90.2 (`diff -rq packages/plugin-*/src`).

- v4: plugins are defined with `definePlugin<Options>({ slug: '@payloadcms/plugin-x', plugin: ({ config, options }) => config })` (seo, redirects, form-builder, nested-docs confirmed in the diff) instead of a bare `(options) => (config) => Config` closure. The call site `seoPlugin({...})` is unchanged for users; custom plugins should adopt `definePlugin`.
- v4: plugin admin styles moved from `.scss` to `.css` files (seo, search, multi-tenant, import-export).
- v4: search plugin drops the deprecated `apiBasePath` and the `ConfigTypes` generic on `SkipSyncFunction` (locale is `TypedLocale | undefined`).
- v4: `plugin-mcp` is restructured (`collections/`, `endpoints/`, `defaults.ts` removed; `defaultAccess.ts`, `defineTool.ts`, `endpoint/`, `exports/` added) — re-read its docs before upgrading.
- v4: form-builder drops `utilities/slate`.
- Same in v4: SEO's `authorizeGenerateTarget` still only resolves configured collections/globals, so the manual-fields-without-`collections` 403 behavior carries over.
