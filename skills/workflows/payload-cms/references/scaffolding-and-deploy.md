# Scaffolding, Build, and Deployment

Operational reference for creating a Payload project and shipping it. Baseline is **stable v3.90.2** (`npm view payload dist-tags` → `latest: 3.90.2`, checked 2026-09-24). `main` on GitHub is the **v4 canary** line (`4.0.0-canary.37`); v3 lives on the `3.x` branch. See `v4-delta.md` before choosing a version.

## Contents

1. Requirements
2. create-payload-app (CPA)
3. Templates
4. Adding Payload to an existing Next.js app
5. The `payload` CLI and project scripts
6. Environment variables
7. Build-time database connection
8. Docker and self-hosting
9. Vercel
10. Cloudflare Workers + D1
11. File storage, uploads, email
12. Production checklist
13. Sources

## 1. Requirements

> Verified against payload v3.90.2 (`docs/getting-started/installation.mdx`, `packages/next/package.json`, `packages/payload/package.json`)

| Item | Docs say | Package metadata says |
|---|---|---|
| Node | 20.9.0+ | `engines.node: ^18.20.2 \|\| >=20.9.0` |
| Next.js | 15.2.9–15.2.x, 15.3.9–15.3.x, 15.4.11–15.4.x, or 16.2.6+ | `@payloadcms/next` peer: `>=15.2.9 <15.3.0 \|\| >=15.3.9 <15.4.0 \|\| >=15.4.11 <15.5.0 \|\| >=16.3.3 <17.0.0` |
| Package manager | pnpm preferred; npm; yarn 2+; **yarn 1.x unsupported** | templates: `pnpm ^9 \|\| ^10 \|\| ^11` |
| React | — | template pins `19.2.6`; `@payloadcms/ui` peer `^19.0.1 \|\| ^19.1.2 \|\| ^19.2.1` |
| Database | MongoDB, Postgres, or SQLite | adapters: see `database-and-migrations.md` |

The docs and the peer range disagree on the Next 16 floor (16.2.6 vs 16.3.3). Package managers enforce the peer range, so **use Next `16.3.3`+ for v3.90.x** (that is what every template ships). Not all Next 15/16 releases work; stay inside the listed ranges.

Next `cacheComponents` "can be enabled alongside Payload without causing errors in the admin panel, full compatibility is not guaranteed" (docs banner).

## 2. create-payload-app (CPA)

> Verified against payload v3.90.2 (`packages/create-payload-app/src/main.ts`, `lib/templates.ts`, `lib/select-db.ts`, `lib/select-agent.ts`, `utils/messages.ts`)

```bash
npx create-payload-app                       # prompts
npx create-payload-app my-site -t website    # name + template
npx create-payload-app -n my-site -t website -d postgres --use-pnpm
```

Flags parsed by `main.ts`:

| Flag | Alias | Purpose |
|---|---|---|
| `--name` | `-n` | project name |
| `--template` | `-t` | template name (see §3) |
| `--example` | `-e` | one of the `examples/*` folders (fetched from the GitHub contents API) |
| `--db` | `-d` | `mongodb`, `postgres`, `sqlite`, `vercel-postgres`, `d1-sqlite` (invalid value throws with the list) |
| `--db-connection-string` | | skip the connection-string prompt |
| `--db-accept-recommended` | | accept the suggested default connection string |
| `--secret` | | set `PAYLOAD_SECRET` instead of generating one |
| `--agent` / `--no-agent` | `-a` | install the Payload agent skill for `claude`, `codex`, or `cursor` (see below) |
| `--use-npm/-yarn/-pnpm/-bun`, `--no-deps`, `--no-git` | | package manager / skip install / skip `git init` |
| `--version` | | override the Payload version installed (default: latest from npm) |
| `--branch` | | template/example git ref (source default `3.x`) |
| `--local-template`, `--dry-run`, `--debug` | | CPA developer aids (use a template from disk; skip creation; verbose logging) |
| `--init-next`, `--beta` | | UNVERIFIED semantics (declared in `main.ts`; a source TODO questions whether `--init-next` is needed since Next projects are auto-detected) |

Default DB prompt choice is MongoDB (`initialValue: 'mongodb'`). Suggested connection strings: `mongodb://127.0.0.1/<name>`, `postgres://postgres:<password>@127.0.0.1:5432/<name>`, `file:./<name>.db` (SQLite).

Behaviours worth knowing:

- Run **inside an existing Next.js project** and CPA switches to init mode (detects `next.config`, refuses Next < 15, warns if a top-level `layout.tsx` exists and tells you to move the app into a route group such as `(app)`).
- Run in a project where Payload is already installed and it offers to **upgrade Payload** instead.
- **Agent skill**: CPA downloads `tools/claude-plugin/skills/payload/` from the repo's `3.x` branch into `.claude/skills/payload` (Claude Code) or `.agents/skills/payload` (Codex, Cursor) and writes `CLAUDE.md` / `AGENTS.md` pointing at it. Pass `--no-agent` to skip. This is the official skill; this repo's `payload-cms` skill complements it (website/CMS workflow) and does not replace it.
- **pnpm v11**: installs fail with `ERR_PNPM_IGNORED_BUILDS` unless build scripts are approved in `pnpm-workspace.yaml`. CPA writes `allowBuilds` for `esbuild`, `sharp`, `unrs-resolver`, `workerd`. If you scaffold by hand, approve `sharp` (and `esbuild`, `unrs-resolver`) or image resizing breaks.

## 3. Templates

> Verified against payload v3.90.2 (`packages/create-payload-app/src/lib/templates.ts`, `templates/*/package.json`, `templates/*/src/payload.config.ts`)

CPA offers exactly five names (`getValidTemplates()`): `blank`, `website`, `ecommerce`, `with-cloudflare-d1` (forces `d1-sqlite`), `plugin`. The other folders under `templates/` are Vercel one-click deploy targets, not CPA choices.

| Template | DB adapter in its config | Storage | Notes |
|---|---|---|---|
| `blank` | `mongooseAdapter` | local disk | `sharp` passed; scripts include `devsafe` |
| `website` | `mongooseAdapter` (`.env.example` shows a Postgres URL as the alternative) | local disk | layout builder, SEO, redirects, search, form builder, live preview, seed button; `.env.example` has `NEXT_PUBLIC_SERVER_URL`, `CRON_SECRET`, `PREVIEW_SECRET` |
| `ecommerce` | `mongooseAdapter` | local disk | `sharp` commented out; `stripe-webhooks` script |
| `with-postgres` | `postgresAdapter` | local | `ci` script = `payload migrate && pnpm build` |
| `with-vercel-postgres` | `vercelPostgresAdapter` (`POSTGRES_URL`) | `vercelBlobStorage` | `ci` script |
| `with-vercel-mongodb` | `mongooseAdapter` | `vercelBlobStorage` | no `ci` script |
| `with-vercel-website` | `vercelPostgresAdapter` | `vercelBlobStorage` | `vercel.json` cron, `ci` script, `postbuild: next-sitemap` |
| `with-cloudflare-d1` | `sqliteD1Adapter` (`@payloadcms/db-d1-sqlite`) | `r2Storage` | OpenNext + Wrangler, see §10 |
| `plugin` | — | — | scaffold for publishing a plugin |

Also under `examples/`: `astro`, `auth`, `custom-components`, `custom-server`, `draft-preview`, `email`, `form-builder`, `live-preview`, `localization`, `multi-tenant`, `remix`, `tailwind-shadcn-ui`, `whitelabel`.

Template `.npmrc` (website): `legacy-peer-deps=true`, `enable-pre-post-scripts=true` (the latter is why `postbuild` runs under pnpm).

## 4. Adding Payload to an existing Next.js app

> Verified against payload v3.90.2 (`docs/getting-started/installation.mdx`, `docs/admin/admin-panel-location.mdx`)

1. `pnpm i payload @payloadcms/next` + `@payloadcms/richtext-lexical` + `sharp` (only if you use image sizes/crop/focal point) + `graphql` (only for the GraphQL API) + exactly one db adapter.
2. Copy the `(payload)` route group from `templates/blank/src/app/(payload)` into `app/`. Move your existing frontend, root layout included, into its own route group such as `(frontend)`. Payload cannot coexist with a top-level `layout.tsx`.
3. Wrap `next.config` with `withPayload(nextConfig)` from `@payloadcms/next/withPayload`. It is ESM, so the config must be `.mjs`/`.ts` or the package `"type": "module"`. The shipped templates use `withPayload(nextConfig, { devBundleServerPackages: false })` (faster dev compile).
4. Create `payload.config.ts` (`buildConfig({ editor, collections, secret, db, sharp })`) and add a tsconfig path: `"@payload-config": ["./payload.config.ts"]`.
5. `pnpm dev`, open `/admin`, create the first user.

Files in `(payload)`: `layout.tsx`, `admin/[[...segments]]/page.tsx`, `not-found.tsx`, `api/[...slug]/route.ts`, `custom.scss` are created once and are safe to edit despite the "DO NOT MODIFY" banner in `layout.tsx`; only `admin/importMap.js` is auto-generated (at startup, on HMR, and via `payload generate:importmap`) and must never be hand-edited. Moving the admin to another path requires `routes.admin/api/graphQL/graphQLPlayground` plus `admin.importMap.baseDir` and `importMapFile` (absolute paths).

## 5. The `payload` CLI and project scripts

> Verified against payload v3.90.2 (`packages/payload/src/bin/index.ts`, `bin/migrate.ts`, `bin/loadEnv.ts`, `config/find.ts`, `templates/website/package.json`)

Built-in commands in 3.90.2 (`availableScripts`): `generate:db-schema`, `generate:importmap`, `generate:types`, `info`, `jobs:run`, `jobs:handle-schedules`, `run`, and `migrate`, `migrate:create`, `migrate:down`, `migrate:refresh`, `migrate:reset`, `migrate:status`, `migrate:fresh`. There is **no `payload build`** in v3 (that is a v4 command).

Standard template scripts (all wrap with `cross-env NODE_OPTIONS=--no-deprecation`): `dev`, `devsafe` (`rm -rf .next` first, use when the dev cache misbehaves), `build`, `start`, `payload`, `generate:importmap`, `generate:types`. Run CLI commands through the package manager (`pnpm payload migrate`); Payload must not be installed globally.

- `payload run src/scripts/foo.ts` runs a script in the Payload environment (used for seeds/imports). `--cron "<expr>"` on any bin script keeps the process alive and re-runs it on a schedule (`protect: true` so runs never overlap).
- Config discovery: `PAYLOAD_CONFIG_PATH` (absolute, or relative to cwd) wins; otherwise tsconfig `paths["@payload-config"]`, then `srcPath`, `rootPath` (production also checks `outDir`). Scripts that run outside Next (`migrate`, `generate:*`) need this to resolve, otherwise you get "cannot find config".
- `.env*` files are loaded with Next's own loader (`.env.local`, `.env.production`, ...), searching upward from cwd if none is found in cwd.
- Bin runs set `DISABLE_PAYLOAD_HMR=true`.

## 6. Environment variables

> Verified against payload v3.90.2 (`templates/*/.env.example`, `docs/troubleshooting/troubleshooting.mdx`, `docs/upload/storage-adapters.mdx`, `packages/payload/src/bin`)

| Variable | Used by | Notes |
|---|---|---|
| `PAYLOAD_SECRET` | all | signs JWTs; long and unguessable in production |
| `DATABASE_URL` | blank/website/with-postgres | Mongo or Postgres connection string |
| `POSTGRES_URL` | Vercel templates | `vercelPostgresAdapter` default; a `localhost`/`127.0.0.1` URL falls back to the `pg` pool unless `forceUseVercelPostgres: true` |
| `NEXT_PUBLIC_SERVER_URL` | website templates | no trailing slash; drives CORS, links, preview |
| `PREVIEW_SECRET` | website templates | validates draft-preview requests |
| `CRON_SECRET` | website/Vercel templates | bearer secret checked in `jobs.access.run` for cron calls |
| `BLOB_READ_WRITE_TOKEN` | Vercel Blob | set automatically when a Blob store is connected |
| `PAYLOAD_CONFIG_PATH` | CLI | see §5 |
| `PAYLOAD_LOG_LEVEL` | Cloudflare template logger | `debug`/`info`/`warn`/`error` |
| `USE_HTTPS=true`, `PAYLOAD_HMR_URL_OVERRIDE=wss://…/_next/hmr` | dev with `--experimental-https` | fixes HMR websocket protocol |
| `PAYLOAD_DROP_DATABASE=true` | Mongo adapter connect (source) | **drops the database on start**; never set outside throwaway envs |
| `S3_BUCKET`, `S3_ACCESS_KEY_ID`, `S3_SECRET_ACCESS_KEY`, `S3_REGION` | docs S3 example | names are the docs' convention, not enforced |

## 7. Build-time database connection

> Verified against payload v3.90.2 (`docs/production/building-without-a-db-connection.mdx`, `templates/website/src/app/(frontend)/**`, `docs/database/migrations.mdx`)

Payload itself does not need a DB to build. **Next static generation does**, whenever a route segment is statically generated and calls the Local API. The website template does exactly this (`generateStaticParams` in `[slug]`, `posts/[slug]`, `posts/page/[pageNumber]`; `dynamic = 'force-static'`, `revalidate = 600` on `posts`), so its build needs a reachable DB with the schema already migrated. Options:

1. Provide the DB to the build and run migrations first. Templates expose `"ci": "payload migrate && pnpm build"`; set that as the platform build command (Vercel: `pnpm run ci`).
2. `pnpm next build --experimental-build-mode compile` (no static generation, no DB), then `--experimental-build-mode generate` later when a DB exists. In `compile` mode `NEXT_PUBLIC_*` are not inlined; use `generate` or `generate-env`.
3. Opt out of SSG per route with `export const dynamic = 'force-dynamic'` (slower, no static optimization).

Docker builds hit this most. Prefer (1) with a build-time DB, or (2).

## 8. Docker and self-hosting

> Verified against payload v3.90.2 (`docs/production/deployment.mdx`, `templates/website/Dockerfile`, `templates/website/docker-compose.yml`)

- Set `output: 'standalone'` in `next.config` (the template Dockerfile says it is required).
- Multi-stage build: `deps` (`libc6-compat`, lockfile-driven install) → `builder` (`npm/yarn/pnpm run build`) → `runner` (non-root `nextjs` user, copies `.next/standalone`, `.next/static`, `public`, `CMD HOSTNAME="0.0.0.0" node server.js`, `EXPOSE 3000`).
- Base image differs by source: docs example `node:24-alpine`; template Dockerfile `node:22.17.0-alpine`. Both satisfy v3's engines; **v4 requires Node 24.15.0+** (its templates still ship the 22.x Dockerfile, so bump it if you adopt v4).
- Runtime env: `PAYLOAD_SECRET`, `DATABASE_URL`, and `PAYLOAD_CONFIG_PATH` if the config is not discoverable.
- `docker-compose.yml` in templates is **dev only** (Mongo `--storageEngine=wiredTiger`, no replica set, so Mongo transactions are off locally; see `database-and-migrations.md`). The template compose file uses `node:18-alpine` and `yarn`, which is stale next to the docs' `node:24-alpine` + corepack pnpm example.
- Self-hosting (template README): any host that runs Node/Next, "VPS, DigitalOcean's Apps Platform, via Coolify". Long-running servers can run migrations at boot with `prodMigrations` (see `database-and-migrations.md`). This repo's `railway-deploy` skill covers Railway; Payload's own docs do not mention Railway.
- Persistent vs ephemeral filesystems: Heroku and DigitalOcean Apps are ephemeral (local uploads vanish on restart); DigitalOcean Droplets, EC2, and traditional hosts are persistent. Ephemeral host + uploads ⇒ cloud storage adapter (§11).

## 9. Vercel

> Verified against payload v3.90.2 (`templates/with-vercel-website/{package.json,vercel.json,src/payload.config.ts,README.md}`, `docs/upload/storage-adapters.mdx`, `docs/jobs-queue/overview.mdx`)

The `with-vercel-website` config (the closest thing to a reference deploy):

```ts
db: vercelPostgresAdapter({ pool: { connectionString: process.env.POSTGRES_URL || '' } }),
plugins: [...plugins, vercelBlobStorage({ collections: { media: true }, token: process.env.BLOB_READ_WRITE_TOKEN || '' })],
jobs: { access: { run: ({ req }) => {
  if (req.user) return true
  const secret = process.env.CRON_SECRET
  if (!secret) return false
  return req.headers.get('authorization') === `Bearer ${secret}`
} }, tasks: [] },
```

- One-click flow: Neon Postgres + Vercel Blob attached as integrations; secrets `PAYLOAD_SECRET`, `CRON_SECRET`, `PREVIEW_SECRET`; build command `pnpm run ci`; after deploy visit `/admin`, create the first user, click "Seed the database" (see seed caveat in `database-and-migrations.md`).
- Serverless uploads through the function are capped at **4.5 MB**; set `clientUploads: true` on the storage adapter (S3 additionally needs CORS `PUT` and the `If-None-Match` header allowed).
- `vercel.json` schedules `GET /api/payload-jobs/run` with `"schedule": "0 0 * * *"` (daily). Jobs on serverless must be driven by external cron hitting `/api/payload-jobs/run` and `/api/payload-jobs/handle-schedules`; docs: "Never use `autoRun` on serverless platforms."
- `prodMigrations` "may slow down serverless cold starts on platforms such as Vercel"; run `payload migrate` in the build instead.
- Email: `@payloadcms/email-resend` is "preferred for serverless platforms such as Vercel" because it is lighter than nodemailer.
- `next.config` derives `NEXT_PUBLIC_SERVER_URL` from `VERCEL_PROJECT_PRODUCTION_URL` and uses it for `images.remotePatterns`; `images.localPatterns` allows `/api/media/file/**`.

## 10. Cloudflare Workers + D1

> Verified against payload v3.90.2 (`templates/with-cloudflare-d1/{README.md,package.json,wrangler.jsonc,next.config.ts,src/payload.config.ts}`, `docs/database/sqlite.mdx`)

- Stack: `@payloadcms/db-d1-sqlite` (documented as **beta**), `@payloadcms/storage-r2`, `@opennextjs/cloudflare`, Wrangler. `wrangler.jsonc` binds `D1`, `R2`, `ASSETS`, flags `nodejs_compat` + `global_fetch_strictly_public`.
- Config resolves bindings with `getCloudflareContext` in production and `getPlatformProxy` (Wrangler) for CLI/dev. `db: sqliteD1Adapter({ binding: cloudflare.env.D1 })`; optional `readReplicas: 'first-primary'` (experimental, must also be enabled in the Cloudflare dashboard).
- Scripts: `build` uses `next build --webpack`; `deploy` = `deploy:database` (`payload migrate` with `PAYLOAD_SECRET=ignore`, then `wrangler d1 execute D1 --command 'PRAGMA optimize'`) + `deploy:app` (`opennextjs-cloudflare build && deploy`). Create migrations first: `pnpm payload migrate:create`. `CLOUDFLARE_ENV` selects a Wrangler environment.
- `next.config`: `serverExternalPackages: ['jose', 'pg-cloudflare']`.
- Known limits from the template README: paid Workers plan only (3 MB bundle limit), **no `sharp`** (image resizing, crop, focal point, `imageSizes` unavailable), GraphQL not guaranteed (upstream workerd issue), default `pino-pretty` logger breaks (`fs.write is not implemented`), so the template swaps in a JSON `console` logger in production; Media uses `skipSafeFetch: true` to avoid undici diagnostic-channel noise.
- Because there is no connection string, `DATABASE_URL` does not apply; the only env var in `.env.example` is `PAYLOAD_SECRET`.

## 11. File storage, uploads, email

> Verified against payload v3.90.2 (`docs/upload/storage-adapters.mdx`, `docs/upload/overview.mdx`, `docs/email/overview.mdx`, `packages/*`)

Official storage packages present in v3.90.2: `storage-s3`, `storage-azure`, `storage-gcs`, `storage-vercel-blob`, `storage-r2`, `storage-uploadthing` (plus `plugin-cloud-storage`). In v3 they are registered in `plugins: []`, `collections: { media: true }` (or `{ prefix }`), and they set `disableLocalStorage: true` on those collections automatically. Without local storage the admin thumbnails need the adapter's URLs or `upload.adminThumbnail`.

Uploads: pass `sharp` in `buildConfig` for resizing/crop/focal point. Payload-wide `upload` options: `abortOnLimit` (default `true` in v3.90.2 code and docs, so oversize files return 413), `requestSizeLimit` (default 50 MiB), `limits.fileSize` (20 MiB), `limits.files` (3), `limits.fields` (20), `limits.fieldSize` (1 MiB), `uploadTimeout` (60 s), `useTempFiles`, `safeFileNames`.

Email: none configured ⇒ a startup warning and a warning on send attempts. `@payloadcms/email-nodemailer` (SMTP or any transport; with no options in dev it uses ethereal.email) and `@payloadcms/email-resend`. Required adapter fields: `defaultFromName`, `defaultFromAddress`.

## 12. Production checklist

> Verified against payload v3.90.2 (`docs/production/deployment.mdx`, `docs/production/preventing-abuse.mdx`)

- [ ] `secret` is long and random; not committed.
- [ ] Access control reviewed. Default is "must be logged in"; anything with public registration needs stricter rules.
- [ ] `next build` + `next start` (not `next dev`) in the platform start command.
- [ ] HTTPS in front; enable secure cookies on auth collections. CORS/CSRF lists contain only your real origins (a `*` CORS list is a known cause of "Unauthorized, you must be logged in" on login).
- [ ] Auth collections set `maxLoginAttempts` and `lockTime` (ms).
- [ ] `maxDepth` set as low as workable (default `10`).
- [ ] GraphQL: `graphQL.disable: true` if unused, else `graphQL.maxComplexity` (each field costs 1, relationship/upload 10).
- [ ] Uploads: restrictive create/update access, email verification on public sign-up, consider AV scanning in a hook.
- [ ] Persistent storage or a cloud adapter for uploads.
- [ ] `DATABASE_URL`/`POSTGRES_URL` set on the platform; DB in the same region as the server.
- [ ] Migrations run in CI/build (SQL databases) before deploy.
- [ ] Cron secret and jobs runner wired if you use jobs or scheduled publish.
- [ ] Amazon DocumentDB: set `connectOptions.useFacet: false` (v3 only). Azure Cosmos DB: spread `compatibilityOptions.cosmosdb` and set `indexSortableFields: true`; it is "not fully compatible".

## 13. Sources

- Docs: `docs/getting-started/installation.mdx`, `docs/production/{deployment,building-without-a-db-connection,preventing-abuse}.mdx`, `docs/upload/*.mdx`, `docs/email/overview.mdx`, `docs/admin/admin-panel-location.mdx`, `docs/jobs-queue/overview.mdx`.
- Code: `packages/create-payload-app/src/**`, `packages/payload/src/bin/**`, `packages/payload/src/config/find.ts`, `templates/**`.
- Checkout: tag `v3.90.2` (commit `6254c3bf`, 2026-09-23).
