# Databases, Migrations, and Seeding

Baseline: **stable v3.90.2**. Differences on v4 canary are flagged in `v4-delta.md`.

## Contents

1. Choosing an adapter
2. Adapter matrix
3. Adapter options that matter
4. Push (dev) vs migrations (everything else)
5. Migration commands and files
6. Running migrations in CI vs at boot
7. Transactions
8. IDs, indexes, and storage shape
9. Seeding and scripts
10. Known gotchas
11. Sources

## 1. Choosing an adapter

> Verified against payload v3.90.2 (`docs/database/overview.mdx`)

Officially supported: MongoDB (Mongoose), Postgres (Drizzle), SQLite (Drizzle). Nearly every feature works on all of them. The one documented gap is the **`point` field, unsupported in SQLite**.

- **MongoDB**: each Payload document is one Mongo document, including localized values, blocks, and arrays, so the stored shape mirrors the field schema. Prefer it for dynamic schemas, heavy localization, lots of blocks/arrays/`hasMany` selects, and to avoid DDL sync between environments. Migrations are only needed to reshape existing data.
- **Postgres / SQLite**: enforced schema, real relations, consistency at the DB level. Migrations are **required** in every non-dev environment.

For a marketing/content site the template default is Mongo; the Vercel templates use Postgres (Neon) because Vercel hosts it natively. Either works; pick based on where you host and whether you want DDL migrations in the release path.

## 2. Adapter matrix

> Verified against payload v3.90.2 (`docs/database/{mongodb,postgres,sqlite}.mdx`, `packages/db-*/src/index.ts`, `packages/drizzle/src/types.ts`)

| Package | Factory | Connection option | Default id | Transactions default | Push in dev |
|---|---|---|---|---|---|
| `@payloadcms/db-mongodb` | `mongooseAdapter` | `url` (required), `connectOptions` | Mongo `ObjectId` | on, but auto-disabled when the client has no `replicaSet` | n/a |
| `@payloadcms/db-postgres` | `postgresAdapter` | `pool: { connectionString }` (required) | `serial` (`idType`: `serial`, `uuid`; type also allows `uuidv7`) | on (`transactionOptions: false` disables) | yes |
| `@payloadcms/db-vercel-postgres` | `vercelPostgresAdapter` | `pool` or `POSTGRES_URL`; falls back to `pg` for localhost URLs unless `forceUseVercelPostgres: true` | same as Postgres | same | yes |
| `@payloadcms/db-sqlite` | `sqliteAdapter` | `client: { url, authToken }` (libSQL, so Turso works) | `number` (`idType`: `number`, `uuid`) | **off** (enable with `transactionOptions: {}`) | yes |
| `@payloadcms/db-d1-sqlite` (beta) | `sqliteD1Adapter` | `binding: env.D1` | `number` | **off** | yes |

Adapters are separate installs; install exactly one, and keep every `@payloadcms/*` package on the same exact version as `payload`.

## 3. Adapter options that matter

> Verified against payload v3.90.2 (`docs/database/{mongodb,postgres,sqlite}.mdx`, `docs/production/deployment.mdx`)

**Mongo**: `transactionOptions` (`false` disables), `migrationDir`, `collation` (locale threaded automatically; test before prod), `disableIndexHints` (AWS DocumentDB fix), `allowAdditionalKeys` (keeps unknown keys but **bypasses access control** for that data), `allowIDOnCreate`, `useBigIntForNumberIDs`, `useJoinAggregations` (set `false` to avoid correlated subqueries), `usePipelineInSortLookup`, `bulkOperationsSingleTransaction`, `disableFallbackSort`, `collectionsSchemaOptions`, `autoPluralization`. Source-only (not in the docs table): `ensureIndexes` and `prodMigrations`. Models are reachable at `payload.db.collections[slug]`, `payload.db.globals`, `payload.db.versions[slug]`.

Compatibility presets: `import { compatibilityOptions } from '@payloadcms/db-mongodb'` then spread `...compatibilityOptions.cosmosdb | documentdb | firestore`. Cosmos preset sets `bulkOperationsSingleTransaction: true`, `transactionOptions: false`, `useJoinAggregations: false`, `usePipelineInSortLookup: false`; also set `indexSortableFields: true` at config root. DocumentDB additionally needs `connectOptions.useFacet: false` in v3.

**Postgres / SQLite**: `push`, `migrationDir`, `schemaName` (Postgres, experimental, default `public`), `idType`, `transactionOptions`, `disableCreateDatabase` (Postgres; by default a missing database is auto-created), suffixes `localesSuffix` (`_locales`), `relationshipsSuffix` (`_rels`), `versionsSuffix` (`_v`), `blocksAsJSON` (store blocks in a JSON column, faster with many blocks, but not relational), `readReplicas` + `readReplicasAfterWriteInterval` (Postgres, default 2000 ms), `generateSchemaOutputFile` (default `{CWD}/src/payload-generated.schema.ts`), `autoIncrement` (SQLite), `busyTimeout` and `wal` (SQLite; WAL defaults `journalSizeLimit` 64 MB, `synchronous` `'FULL'`), `beforeSchemaInit` / `afterSchemaInit` hooks. `extensions: string[]` exists in the v3.90.2 Postgres types but is only documented on v4 `main`.

Drizzle access: run `payload generate:db-schema` once, then `payload.db.drizzle`, `payload.db.tables`, `payload.db.relations`, `payload.db.enums` (Postgres). Drizzle helpers re-export from `@payloadcms/db-postgres/drizzle` (`eq`, `sql`, `and`, `pg-core`) so you need not install drizzle.

## 4. Push (dev) vs migrations (everything else)

> Verified against payload v3.90.2 (`docs/database/migrations.mdx`, `packages/db-postgres/src/connect.ts`, `packages/drizzle/src/utilities/pushDevSchema.ts`, `packages/drizzle/src/migrate.ts`)

Drizzle `push` auto-syncs the DB to your config **only in development**. Exact rule in `connect.ts`: push runs when `NODE_ENV !== 'production'` **and** `PAYLOAD_MIGRATING !== 'true'` **and** `push !== false`. `payload migrate*` commands set `PAYLOAD_MIGRATING=true`, so migrating never also pushes.

Push records itself in `payload-migrations` with `batch: -1`. If you later run `payload migrate` against that same DB, Payload prompts: "you've run Payload in dev mode... If you'd like to run migrations, data loss will occur." **Do not mix push and migrations on one database.** Treat the local dev DB as a sandbox, or set `push: false` and use migrations only (expect friction).

Recommended SQL workflow:

1. Develop with push on a local DB.
2. When a feature is done: `pnpm payload migrate:create <name>` (generates SQL from the diff against the previous migration snapshot). Review the file; commit it.
3. In CI/build against the target DB: `payload migrate` before `next build`.

Mongo needs no DDL. Only write a migration when you must transform existing data (Shape A to Shape B); run it in CI or locally against the prod connection string.

## 5. Migration commands and files

> Verified against payload v3.90.2 (`docs/database/migrations.mdx`, `packages/payload/src/bin/migrate.ts`, `packages/drizzle/src/migrateFresh.ts`)

Add a `payload` script to `package.json` (`"payload": "cross-env NODE_OPTIONS=--no-deprecation payload"`) and run through the package manager.

| Command | Effect |
|---|---|
| `payload migrate` | run pending migrations (each in its own transaction) |
| `payload migrate:create [name]` | create a migration file; default name is a timestamp |
| `payload migrate:status` | table of ran / pending |
| `payload migrate:down` | roll back the last **batch** |
| `payload migrate:refresh` | roll back all that ran, then run them again |
| `payload migrate:reset` | roll back all |
| `payload migrate:fresh` | **drop everything** and re-run all; prompts unless `--force-accept-warning` |

`migrate:create` flags: `--skip-empty` (Postgres: skip the "no changes, create blank?" prompt, useful in CI), `--force-accept-warning` (accept prompts, create a blank migration even with no diff), and a `--file` argument (present in `bin/migrate.ts`; not in the docs). `migrate:create` does not connect to the DB (`disableDBConnect`).

Migration file shape (default dir `./src/migrations`, override with adapter `migrationDir`; Payload also probes `./dist/migrations`, `./migrations`):

```ts
import { MigrateUpArgs, MigrateDownArgs, sql } from '@payloadcms/db-postgres'

export async function up({ db, payload, req }: MigrateUpArgs): Promise<void> {
  // pass `req` to Local API calls so they join the migration transaction
}
export async function down({ db, payload, req }: MigrateDownArgs): Promise<void> {}
```

Mongo passes `session`; SQLite passes `db.run(sql...)`, Postgres `db.execute(sql...)`. Payload generates `migrations/index.ts` exporting `migrations`, which `prodMigrations` consumes.

Config that varies by environment (a plugin only enabled in production, for example) yields different schemas. Generate migrations with the production env vars present, or hand-edit the file, or keep per-environment migrations. Otherwise dev-generated SQL misses prod-only tables.

## 6. Running migrations in CI vs at boot

> Verified against payload v3.90.2 (`docs/database/migrations.mdx`, `packages/db-postgres/src/connect.ts`, `packages/db-mongodb/src/connect.ts`)

- **CI/build (default)**: `"ci": "payload migrate && pnpm build"` and use it as the platform build command. Needs DB access at build time. A failed migration rejects the deploy.
- **At boot (`prodMigrations`)**: `postgresAdapter({ prodMigrations: migrations, ... })` (also implemented for Mongo). Runs in `connect()` only when `NODE_ENV === 'production'`. Good for long-running containers where the build has no DB; the docs warn it "may slow down serverless cold starts", so avoid it on Vercel.
- **Cloudflare D1**: `deploy:database` script runs `payload migrate` (with `NODE_ENV=production PAYLOAD_SECRET=ignore`) before deploying the Worker.

## 7. Transactions

> Verified against payload v3.90.2 (`docs/database/transactions.mdx`, `packages/db-mongodb/src/connect.ts`, `packages/db-{postgres,sqlite,d1-sqlite}/src/index.ts`)

- Every write op runs in a transaction when the DB supports it; the initial request creates `req.transactionID`. Inside hooks, **pass `req`** into nested Local API calls to stay atomic; omit it and the call commits independently.
- **Mongo needs a replica set.** `connect.ts` sets `transactionOptions = false` and swaps in a no-op `beginTransaction` when the connection has no `replicaSet` (the template `docker-compose.yml` Mongo is a single node, so local dev runs without transactions). Atlas is a replica set already.
- **SQLite and D1 are off by default**; enable with `transactionOptions: {}`.
- Disable globally with `transactionOptions: false` (all official adapters), or per call with `disableTransaction: true`.
- Do not `await`-skip an async hook that shares `req`: it can fail after a 200 was returned. If you do not await, do not pass `req`.
- Manual control in scripts: `payload.db.beginTransaction()` → `payload.db.commitTransaction(id)` / `rollbackTransaction(id)`, pass `req: { transactionID }` to Local API calls. Direct `payload.db.*` methods (bypass hooks and validation, used for speed) do not open a transaction themselves.

## 8. IDs, indexes, and storage shape

> Verified against payload v3.90.2 (`docs/database/indexes.mdx`, `docs/database/overview.mdx`, `docs/database/postgres.mdx`)

- `id`, `createdAt`, `updatedAt` are indexed automatically. Add `index: true` on fields you filter or sort by (slugs, dates, relationship keys). Compound: collection `indexes: [{ fields: ['title', 'createdAt'], unique: true }]`.
- `unique: true` is **collection-wide**, even nested under `array`/`blocks` (dotted path such as `items.key`). On Mongo a nested field that is also `required: true` makes a non-sparse unique index, so a second doc without the array collides on `null`. Enforce per-document uniqueness in a `validate` function instead.
- Localized field + `index`/`unique` on Mongo creates **one index per locale path** (`slug.en`, `slug.de`...), which can approach the per-collection index limit with many locales.
- Relational adapters split data into tables: `<slug>` main, `<slug>_locales` (localized), `<slug>_rels` (relationships), `_<slug>_v` (versions), plus one table per array/block type unless `blocksAsJSON`. Table names collide with any pre-existing tables (an existing `users` table clashes with a `users` collection: rename the slug or set `dbName`).
- To adopt an existing database: introspect with Drizzle (`drizzle-kit pull`) and merge with `beforeSchemaInit`. By default Payload drops schema it does not own.
- Custom IDs: `allowIDOnCreate: true` (Mongo, Postgres, SQLite) lets `create` accept an `id` in `data` without a custom id field.

## 9. Seeding and scripts

> Verified against payload v3.90.2 (`templates/website/src/endpoints/seed/index.ts`, `templates/website/src/app/(frontend)/next/seed/route.ts`, `packages/payload/src/bin/index.ts`, `docs/database/migrations.mdx`)

Options, in increasing control:

1. **Website template seed button**: `POST /next/seed` (authenticated user required, else 403; `maxDuration = 60`). It calls `seed({ payload, req })`, which **first wipes** `categories, media, pages, posts, forms, form-submissions, search` via `payload.db.deleteMany`, deletes their versions, and blanks header/footer nav items, then re-creates demo content and a demo author. Never click "Seed the database" on a site with real content. It passes `context: { disableRevalidate: true }` to avoid revalidation storms; the file's own comment says "Error hitting revalidate route" logs are harmless when seeding without a running server.
2. **`payload run src/seed.ts`**: run any TS script with the Payload environment loaded; add `--cron "<expr>"` to repeat. Inside the script `import { getPayload } from 'payload'; import config from '@payload-config'`. Use `overrideAccess: true` explicitly (default is true in v3, but v4 flips it, so writing it makes scripts portable).
3. **Custom bin scripts (v3 form)**: `bin: [{ key: 'seed', scriptPath: path.resolve(dirname, 'seed.ts') }]` with the module exporting `script(config)`. Replaced by `cli.commands` in v4.
4. **Data migrations**: a migration `up()` with `req` is the auditable way to reshape or backfill content.
5. **Import from another system**: no bulk-import command ships in core. `@payloadcms/plugin-import-export` exists (see `plugins-and-integrations.md`); otherwise write a `payload run` script that maps source records to `payload.create` calls (with `req` for transactions, `context: { disableRevalidate: true }` if your hooks revalidate).

Backups: the Payload docs contain no backup/restore guidance. Use the database's native tooling (`mongodump`, `pg_dump`, D1 exports) and take one before any `migrate:fresh`, `migrate:reset`, or seed.

## 10. Known gotchas

> Verified against payload v3.90.2 (sources cited inline)

- `PAYLOAD_DROP_DATABASE=true` makes the Mongo adapter drop the database on startup (`connect.ts`, skipped during hot reload). Never set it in a shared env.
- Percent-encode special characters in DB passwords (`encodeURIComponent`). The symptom is `Cannot read properties of undefined (reading 'searchParams')` followed by "cannot connect to Postgres" (troubleshooting doc).
- Keep the database in the same region as the server ("database proximity" is the first item in the performance doc).
- SQLite `point` fields are unsupported; do not model geolocation there.
- Changing adapter later is a data migration project, not a config swap (different id types, storage shape).
- Mongo `allowAdditionalKeys: true` exposes non-schema data outside access control.
- `migrate:fresh` and `migrate:reset` are destructive; the former prompts unless `--force-accept-warning`. Never pass that flag in scripts pointed at real data.

## 11. Sources

`docs/database/*.mdx`, `docs/production/deployment.mdx`, `packages/payload/src/bin/{index,migrate}.ts`, `packages/drizzle/src/{migrate,migrateFresh,types}.ts`, `packages/drizzle/src/utilities/pushDevSchema.ts`, `packages/db-*/src/{index,connect}.ts`, `templates/website/src/endpoints/seed/index.ts`. Checkout: tag `v3.90.2`.
