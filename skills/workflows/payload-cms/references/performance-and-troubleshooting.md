# Performance and Troubleshooting

Baseline: **stable v3.90.2**. Where behaviour changes in v4 canary it is noted inline and detailed in `v4-delta.md`.

## Contents

1. Performance checklist (build time)
2. Query performance
3. Hooks, validation, and custom components
4. Bundle, dev-server, and image performance
5. Troubleshooting: documented entries
6. Symptom to cause to fix table
7. Debugging checklist
8. Sources

## 1. Performance checklist (build time)

> Verified against payload v3.90.2 (`docs/performance/overview.mdx`)

The performance doc's own ordering, which is also a good triage order:

1. **Database proximity**: same region as the server.
2. **Index** fields you query or sort by (`index: true`; `id`, `createdAt`, `updatedAt` are automatic). See `database-and-migrations.md` §8 for `unique` and per-locale index caveats.
3. **Query options** combined (§2).
4. **Lightweight hooks**: no memory leaks, offload long work, cache expensive results (§3).
5. **Cheap validations**: async or heavy validators should skip `onChange` (§3).
6. **Block references** for blocks shared across many fields (§4).
7. **One cached Payload instance**: always `const payload = await getPayload({ config })`, never construct new instances per request.
8. **Direct DB calls** (`payload.db.updateOne`, `find`, ...) only when you deliberately skip hooks and validation. They do not start a transaction; pass `returning: false` if you do not need the doc back (direct methods only, not the Local API).

## 2. Query performance

> Verified against payload v3.90.2 (`docs/queries/overview.mdx` §Performance, `docs/database/indexes.mdx`, `docs/production/preventing-abuse.mdx`)

Combine as many as apply:

```ts
const { docs } = await payload.find({
  collection: 'posts',
  where: { slug: { equals: 'my-post' } },
  depth: 0,            // relationships return IDs only
  limit: 1,            // when you can predict the count (unique field)
  pagination: false,   // skips the total-count query; best with limit: 1 on unique fields
  select: { title: true, slug: true }, // load and process only these fields
})
```

- **`depth`**: default is **2** in v3 (`config.defaultDepth ?? 2`), **1** in v4. Set the smallest depth that satisfies the page; use `depth: 0` for IDs. `maxDepth` (root config, default `10`) caps client-requested depth and defends against circular populate loops.
- **`select`**: reduces payload size and also **skips field hooks for unselected fields**. In the Admin list view it is opt-in in v3 (`admin.enableListViewSelectAPI`) and always on in v4. On v4 docs, GraphQL can also pass `select: true` so Payload projects only needed columns.
- **`limit` + `pagination: false`**: avoids the count query.
- **`sort`** on a non-indexed field forces a scan; index it.
- Mongo `collation` changes sorting semantics; test before enabling.
- For Mongo with joins, `useJoinAggregations: false` swaps correlated subqueries for multiple finds (a compatibility switch, not a general speedup).
- For SQL with many blocks, `blocksAsJSON: true` avoids the per-block-type table fan-out at the cost of relational structure.

## 3. Hooks, validation, and custom components

> Verified against payload v3.90.2 (`docs/hooks/overview.mdx` §Performance, `docs/fields/overview.mdx` §Validation Performance, `docs/custom-components/overview.mdx` §Performance)

- Do not put expensive work in `beforeRead`/`afterRead`; they run on every read. Prefer `beforeChange`/`afterChange`.
- Use `context` to share an expensive result across hooks in one request (`context.something = await expensive()`), and to prevent hook loops.
- Offload non-blocking work: `await req.payload.jobs.queue({ task: ..., input: ... })` from `afterChange`.
- Validation runs on **every change** in the Admin Panel. For expensive checks, branch on `event`: `validate: async (val, { event }) => { if (event === 'onChange') return true; ... }`.
- Custom components: only send necessary props across the server/client boundary (props serialize into HTML); use `useFormFields(([fields]) => fields[path])` instead of `useFields` to avoid re-render storms; use Suspense.
- **Import rule** (also a top cause of errors, §6): inside the Admin Panel import from `@payloadcms/ui`; in the public frontend import deep paths (`@payloadcms/ui/elements/Button`) so tree-shaking works. The unbundled deep entries exist only for the frontend.

## 4. Bundle, dev-server, and image performance

> Verified against payload v3.90.2 (`docs/performance/overview.mdx`, `templates/website/next.config.ts`, `docs/upload/overview.mdx`)

- **Block references** (v3 form):

  ```ts
  // root config
  blocks: [{ slug: 'TextBlock', fields: [/* ... */] }],
  // any blocks field
  { name: 'content', type: 'blocks', blockReferences: ['TextBlock'], blocks: [] } // blocks must be [] in v3
  ```
  In v4 this becomes `blocks: ['TextBlock']` (see `v4-delta.md`). Benefit: fewer fields to traverse for permissions, much less config sent to the Admin client.
- **Dev speed**: `withPayload(nextConfig, { devBundleServerPackages: false })` (default in CPA since v3.28.0) skips bundling Payload's thousands of server modules in dev. Turbopack is default in Next 16 (`--webpack` opts out); on Next 15 add `--turbo` to `dev`.
- `@next/bundle-analyzer` to find heavy client imports.
- **Images**: `sharp` in the config enables resize/crop/focal point. Use `imageSizes` deliberately (each size is generated per upload). Website template's `next.config` allows `images.localPatterns: [{ pathname: '/api/media/file/**' }]` and `images.qualities: [100]`; add remote patterns for your CDN/blob host.
- Serving media through cloud storage with a CDN is faster than proxying through `/api/media/file/*`; S3 also supports `signedDownloads` for large files.

## 5. Troubleshooting: documented entries

> Verified against payload v3.90.2 (`docs/troubleshooting/troubleshooting.mdx`, `docs/custom-components/overview.mdx`, `docs/admin/admin-panel-location.mdx`)

The troubleshooting doc has exactly four sections. All of them:

### 5.1 Dependency mismatches (the most common root cause)

`payload` and every `@payloadcms/*` package must be on **exactly the same version and installed once**; `react`/`react-dom` likewise. Two copies produce a broken React context, typically `TypeError: Cannot destructure property 'config' of...` (a hook such as `useConfig` from version A with the provider from version B). Same family: `Assignment cannot be destructured`, `value ... of useConfig is undefined`, and `useAuth`/`useLocale` returning undefined.

Detect: `pnpm why @payloadcms/ui` (more than one version, or one version under different paths, is a duplicate); manual `find node_modules -name package.json -exec grep -H '"name": "@payloadcms/ui"' {} \;` (pnpm symlinks show up; edit-and-check to tell copies from links). Do the same for `react` and `react-dom`. `@payloadcms/ui` legitimately ships two bundles, so seeing dual paths is not by itself a bug.

Fix, in order:
1. Pin exact versions (remove `^`/`~`) for `payload`, `@payloadcms/*`, `react`, `react-dom`.
2. Delete `node_modules`, reinstall.
3. Still failing: `pnpm store prune`, delete lockfile **and** `node_modules` together, reinstall (this floats any unpinned deps to latest, so retest), then `pnpm dedupe`.
4. Also: switch npm to pnpm; inspect lockfile for peer violations; check `.npmrc` / `.pnpmfile.cjs` overrides; run Syncpack to enforce identical versions; last resort webpack `resolve.alias` for `react` (temporary).

**Monorepos**: `useUploadHandlers must be used within UploadHandlersProvider` (or similar hook errors) usually means mismatched `next` too. Keep `payload`, `@payloadcms/*`, `next`, `react`, `react-dom` identical across workspaces, install Payload deps at the monorepo root where possible, delete `.next`, `node_modules`, and regenerate the lockfile.

### 5.2 "Unauthorized, you must be logged in to make this request" on login

The auth cookie is not being set or is rejected. Check root config: **CORS** (replace `'*'` with explicit origins including the one in use), **CSRF** (whitelist the domain if set), **cookie settings** (a wrong `domain` breaks it). Verify in DevTools Network: the login response must carry `Set-Cookie`; the browser's warning icon explains a rejection.

### 5.3 `--experimental-https`

HMR websocket breaks. Set `USE_HTTPS=true` in `.env`, or `PAYLOAD_HMR_URL_OVERRIDE=wss://localhost:3000/_next/hmr`. Payload picks the right HMR path itself (`/_next/hmr` from Next 16.3, `/_next/webpack-hmr` before).

### 5.4 Database password encoding

Generic errors such as `Cannot read properties of undefined (reading 'searchParams')` then "cannot connect to Postgres" mean the connection string failed to parse. First confirm the connection with a client; then percent-encode the password (`encodeURIComponent()`).

## 6. Symptom to cause to fix table

> Verified against payload v3.90.2 (source references in the last column)

| Symptom | Cause | Fix | Source |
|---|---|---|---|
| `getFromImportMap: PayloadComponent not found in importMap` (console) | a custom component path is not in `importMap.js` | run `pnpm payload generate:importmap`; check the path is relative to `admin.importMap.baseDir` | `bin/generateImportMap/utilities/getFromImportMap.ts` |
| "Import map not found" after moving `(payload)` | wrong `admin.importMap.importMapFile`, relative path, or stale `layout.tsx` import | absolute `importMapFile`; `layout.tsx` imports `./admin/importMap.js` relative to itself; regenerate | `docs/admin/admin-panel-location.mdx` |
| Admin 404 after relocating the folder | `routes.admin` does not match the folder, or only `admin` was moved | move the whole `(payload)` group; align `routes.*` | same |
| `Error: cannot find Payload config...` from CLI/scripts | script cannot locate config | `payload.config.ts` at cwd/`src`, tsconfig `paths["@payload-config"]`, or `PAYLOAD_CONFIG_PATH=src/payload.config.ts` | `config/find.ts` |
| `import config from '@payload-config'` fails to resolve | tsconfig path alias missing or pointing at the wrong file (exact error text UNVERIFIED) | add `"@payload-config": ["./payload.config.ts"]` (or `./src/...`) under `compilerOptions.paths`; the CLI reads the same alias | installation doc, `config/find.ts` |
| Custom components missing after a config change | import map is regenerated only at startup / HMR / manual, never at runtime | restart or run `generate:importmap`; never hand-edit `importMap.js` | `custom-components/overview.mdx` |
| Types stale, `payload-types.ts` missing new fields | Payload regenerates types on startup and on config HMR only when `NODE_ENV !== 'production'` and `typescript.autoGenerate !== false` | `pnpm generate:types` (run it in CI too); pass `PAYLOAD_CONFIG_PATH` if config lives in `src/` | `payload/src/index.ts`, `typescript/generating-types.mdx` |
| `ERR_PNPM_IGNORED_BUILDS` on install | pnpm v11 blocks unapproved build scripts | approve `sharp`, `esbuild`, `unrs-resolver` (and `workerd` for Cloudflare) in `pnpm-workspace.yaml` `allowBuilds`; CPA does this for you | `create-payload-app/src/lib/configure-pnpm-builds.ts` |
| Sharp missing / image resize broken | `sharp` not installed, not passed in config, or build script blocked | `pnpm add sharp`, add `sharp` to `buildConfig`, approve its build | upload docs, templates |
| `next build` fails or hangs with no DB | static generation calls Local API | run migrations + provide DB, or `--experimental-build-mode compile`, or `dynamic = 'force-dynamic'` | `production/building-without-a-db-connection.mdx` |
| Upload returns 413 | `abortOnLimit` defaults to `true` (v3.90.2) with 20 MiB per-file, 50 MiB request | raise `upload.limits.fileSize` / `requestSizeLimit` | `docs/upload/overview.mdx`, `uploads/fetchAPI-multipart` |
| Upload fails on Vercel above ~4.5 MB | function body limit | storage adapter `clientUploads: true` (+ S3 CORS `PUT`, `If-None-Match`) | storage-adapters doc |
| Uploaded files disappear after restart | ephemeral host filesystem | cloud storage adapter | deployment doc |
| Admin thumbnails broken with cloud storage | local storage disabled | adapter provides URLs; else `upload.adminThumbnail` | upload doc |
| Transactions silently absent on Mongo | connection has no replica set (adapter disables them) | run a replica set (Atlas is one) | `db-mongodb/src/connect.ts` |
| `migrate` warns about "data loss" | DB was pushed in dev (`batch: -1` record) | do not mix push and migrations; use a fresh DB for migrations | `drizzle/src/migrate.ts` |
| `Failed to publish diagnostic channel message` (Workers) | undici in Workers | Media `skipSafeFetch: true` (safe in workerd's SSRF-isolated env) | Cloudflare template README |
| `fs.write is not implemented` (Workers) | default `pino-pretty` logger | custom `console` JSON logger in production | same |
| Windows + Turbopack Sass resolution failure | Next issue vercel/next.js#86431 | `sassOptions: { loadPaths: ['./node_modules/@payloadcms/ui/dist/scss/'] }` (present in the template, marked temporary; the `@payloadcms/ui/scss` export is removed in v4) | `templates/website/next.config.ts` |
| Login works locally, fails behind a proxy/CDN | CORS/CSRF/cookie domain | see §5.2 | troubleshooting doc |
| `Error hitting revalidate route` while seeding via script | no running Next server to revalidate | ignore, or set `context: { disableRevalidate: true }` | `templates/website/src/endpoints/seed/index.ts` |

## 7. Debugging checklist

> Verified against payload v3.90.2 (`packages/payload/src/bin/info.ts`, troubleshooting doc)

1. `pnpm payload info` prints Node, npm/yarn/pnpm, versions of `payload`, `next`, `react`, `react-dom` and every `@payloadcms/*`, plus OS/memory. Attach it to bug reports and use it to spot version skew first.
2. Confirm all Payload packages are one exact version; confirm Next and React are inside the supported ranges (`scaffolding-and-deploy.md` §1).
3. `pnpm why @payloadcms/ui` and `react` for duplicates.
4. Delete `.next` (`pnpm devsafe` does this), restart.
5. Regenerate: `pnpm payload generate:importmap && pnpm payload generate:types`.
6. Reproduce outside the admin with the Local API in a `payload run` script to isolate hooks/access from UI.
7. Check the env: `PAYLOAD_SECRET`, DB URL, `NEXT_PUBLIC_SERVER_URL`, storage tokens.
8. Auth issues: DevTools Network → login response → `Set-Cookie`; then CORS/CSRF/cookie domain.
9. Data issues: run with `depth: 0` and no `select` to see raw stored values; check `overrideAccess` (v3 default `true`, v4 default `false`) when results differ between server code and API.
10. Only then reach for lockfile deletion or `resolve.alias`.

## 8. Sources

`docs/performance/overview.mdx`, `docs/troubleshooting/troubleshooting.mdx`, `docs/queries/overview.mdx`, `docs/hooks/overview.mdx`, `docs/fields/overview.mdx`, `docs/custom-components/overview.mdx`, `docs/admin/admin-panel-location.mdx`, `docs/production/*.mdx`, `packages/payload/src/{bin,config}/**`, `packages/db-mongodb/src/connect.ts`, `packages/drizzle/src/migrate.ts`, `templates/**`. Checkout: tag `v3.90.2`.
