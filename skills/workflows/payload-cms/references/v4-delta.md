# Payload v3.90.x to v4 (canary): what actually changed

Snapshot date **2026-09-24**. Method: diffed the `v3.90.2` tag against `main` (`4.0.0-canary.37`, commit `5448061a`) for docs, package manifests, config types, and defaults, then read `docs/migration-guide/v4.mdx` (2,040 lines, present only on `main`). Items marked **[diffed]** were confirmed in code or manifests; items marked **[guide only]** come from the migration guide and were not independently diffed; **UNVERIFIED** means neither.

## Contents

1. Release status
2. Runtime floors
3. Silent behaviour changes (highest risk)
4. Config and API changes
5. Package, template, and doc changes
6. Already true in 3.90.2 (do not treat as v4-only)
7. Guide-only items
8. Upgrade mechanics
9. Recommendation: pin v3 or try v4
10. Sources

## 1. Release status

> Verified against payload v3.90.2 (`npm view payload dist-tags`, `gh release list -R payloadcms/payload`, `gh api repos/payloadcms/payload/branches`)

| Fact | Value |
|---|---|
| npm `latest` | `3.90.2` (published 2026-09-23) |
| npm `canary` | `4.0.0-canary.37` (2026-09-24); GitHub marks it **Pre-release** |
| Default branch `main` | v4 line. v3 lives on `3.x`. Other long-lived branches: `1.x`, `2.x`, `4.0-bootstrap`, `4.0-rust-rewrite` (names only; purpose UNVERIFIED) |
| Cadence | v3.90.0 → 3.90.2 across 2026-09-18 → 09-23; canaries roughly every 1–3 days |
| `payloadcms/website` (payloadcms.com source) at `023c2a5`, 2026-09-23 | runs `payload` **3.90.1**, `next` 16.3.3, `react` 19.2.3, TS 5.7.3, Node 24 (`mise.toml`), `next build --webpack` |
| `@payloadcms/codemod` `latest` dist-tag | `4.0.0-canary.15` (older than the canary tag; use `@canary`) |

There is no stable 4.0 yet. `npx create-payload-app` installs `latest` (3.90.2).

## 2. Runtime floors

> Verified against payload v3.90.2 (`packages/{payload,next,ui,create-payload-app}/package.json`, `docs/getting-started/installation.mdx`, `pnpm-workspace.yaml`) **[diffed]**

| | v3.90.2 | v4.0.0-canary.37 |
|---|---|---|
| Node | `^18.20.2 \|\| >=20.9.0` (docs: 20.9.0+) | **`>=24.15.0`** |
| Next.js peer | 15.2.9–15.2.x, 15.3.9–15.3.x, 15.4.11–15.4.x, or `>=16.3.3 <17` | **`>=16.2.6 <17`** only (Next 15 dropped) |
| TypeScript | repo catalog 5.7.3 | **6.0.3+** (docs: types not guaranteed below) |
| React | `^19.0.1 \|\| ^19.1.2 \|\| ^19.2.1` | same |
| Rich text | Lexical or Slate | **Lexical only** |

Inconsistencies noticed on `main`: `templates/website/Dockerfile` and `templates/blank/Dockerfile` still use `node:22.17.0-alpine` while the templates declare `engines.node >=24.15.0`; `@payloadcms/tanstack-start` declares `engines.node ^18.20.2 || >=20.9.0`. Bump the Docker base image yourself if you adopt v4.

## 3. Silent behaviour changes (highest risk)

> Verified against payload v3.90.2 (`packages/payload/src/collections/operations/local/find.ts`, `config/defaults.ts`, `collections/config/defaults.ts`) **[diffed]**

These compile and run after upgrading but behave differently. The codemod covers some.

1. **`overrideAccess` defaults to `false` on Local API calls** (v3: `overrideAccess = true`). Server code that omitted it, including seeds, cron, hooks, and `payload run` scripts, now enforces access control and starts returning empty results or 403-style errors. Also applies to `payload.jobs.queue/run/runByID/cancel/cancelByID`. Fix: add `overrideAccess: true` to trusted server work (codemod transform `add-override-access-true`; it cannot resolve spread args, aliased receivers, or non-literal arguments, so typecheck and grep after). **Write `overrideAccess` explicitly in v3 code today** and it is portable.
2. **`defaultDepth` 2 → 1** (`config.defaultDepth ?? 1`). Templates and frontends that read `post.author.name` or `layout[].image.url` two levels down get IDs. Fix per query (`depth: 2`) or set `defaultDepth: 2` globally. `plugin-search` refetches without explicit depth and inherits it.
3. **Versions on by default** for every collection and global (`versions ?? true`, `maxPerDoc: 100`, drafts off; v3 default `false`). New `_<slug>_versions` tables/collections appear; SQL projects need a migration. Auth collections should set `versions: false`. Codemods: `migrate-versions-default` (adds `versions: false` everywhere it is unset), `remove-versions-true`.
4. **Version read access inherits collection `read`** when `readVersions` is unset (v3: requires login). A public `read` now exposes historical and unpublished versions publicly. Set `readVersions` explicitly to keep the old rule. **[guide only]**
5. **Jobs**: the generated `payload-jobs` collection denies generic CRUD by default; stats global and `meta` field always added; `concurrencyKey`, `processingToken`, and a `processingUntil` lease replace the old `processing` flag; SQL needs a migration. `jobs.depth` and `jobs.runHooks` removed. **[guide only]**
6. **Upload limit truncation**: guide says `abortOnLimit` now defaults to `true`. It is already `true` in 3.90.2 (see §6), so nothing changes if you are on 3.90.x.
7. **Croner strict ranges**: `sloppyRanges` removed. `/10 * * * *` and `5/15 * * * *` now throw `TypeError` at registration; use `*/10 * * * *` and `5-59/15 * * * *`. Affects `jobs.autoRun[].cron`, `schedule.cron`, and `payload ... --cron`. In v3.90.2 `bin/index.ts` still passes `sloppyRanges: true` with a "Remove this compatibility option in 4.0" TODO **[diffed]**.
8. **API keys** created before v3.46.0 and never re-saved stop authenticating (sha1 fallback removed; v3 `auth/strategies/apiKey.ts` still contains `sha1`, `main` does not **[diffed]**). New `apiKeyLast4` column needs a migration; `enableAPIKey` and `hasAPIKey` removed.
9. **Storage adapters always add a hidden `prefix` field** (`alwaysInsertFields` removed): SQL needs a migration adding the column on every storage-backed collection. **[guide only]**
10. **Admin publish button** defaults to the active locale; `localization.defaultLocalePublishOption` removed. **[guide only]**

## 4. Config and API changes

> Verified against payload v3.90.2 (`packages/payload/src/config/types.ts`, `packages/payload/src/fields/config/types.ts`, `packages/db-postgres/package.json`, `packages/db-mongodb/src`, `docs/configuration/cli.mdx`) **[diffed]** unless marked

| Change | v3.90.2 | v4 canary |
|---|---|---|
| Custom CLI commands | `bin: [{ key, scriptPath }]`, module exports `script(config)` | `cli: { commands: { seed: './seed.js#seedCommand' } }` with `defineCLICommand` from `payload/cli` (Zod Mini `z`/`strictObject` from `payload`); `bin` removed. Handler receives `getPayload()`; return an exit code, never `process.exit()` |
| Built-in CLI | `generate:db-schema`, `generate:importmap`, `generate:types`, `info`, `jobs:run`, `jobs:handle-schedules`, `run`, `migrate*` | same plus **`build`** (importmap + types + project build), global `--json` / `PAYLOAD_CLI_JSON` (single JSON object on stdout, logs on stderr), `--input @file.json` / `-` for JSON input (docs); runs on Commander **[guide only]** |
| `migrateCLI` export | present | removed; use `payload.db.migrate()` etc. or `payload.bin({ args })` **[guide only]** |
| Storage adapters | `plugins: [s3Storage(...)]` | **top-level `storage: [s3Storage(...)]`**; declaring them in `plugins` no longer works. Codemod `migrate-storage-adapters-to-config` |
| Shared blocks | `type: 'blocks', blockReferences: ['hero'], blocks: []` | `blocks: ['hero']` (slugs and inline configs mixed); `blockReferences` gone. Codemod `migrate-block-references-to-blocks` |
| DB adapter type imports | `@payloadcms/db-postgres/types`, `.../db-sqlite/types`, `.../drizzle/types`, ... | subpath exports removed; import from the package root. Codemod `migrate-db-types-subpath` |
| Mongo | `connectOptions.useFacet` (DocumentDB workaround) | removed (no `$facet` use anymore) |
| Postgres adapter | options as in v3 | adds `extensions` (documented; present in v3 types) and `query.operatorHandlers` with `postgresUnaccent()` for accent-insensitive `contains`/`like` |
| `defaults` export | `import { defaults } from 'payload'` | replaced by `addDefaultsToConfig` |
| Collection option | — | **`hierarchy: boolean \| HierarchyConfig`** (tree structure, breadcrumbs, descendant queries; docs at `docs/hierarchy`) |
| Types | block interface only if `interfaceName` set | every block emits a top-level interface (PascalCase of slug); `typescriptSchema` → `jsonSchema`; JSON Schema uses `$defs` **[guide only]** |
| Sanitizers | async | `sanitizeConfig`, `sanitizeField(s)`, lexical `sanitizeServerEditorConfig` are synchronous **[guide only]** |
| `@payloadcms/ui/scss`, `--theme-*` tokens | present | removed; plain CSS (`@payloadcms/ui/css`), semantic `--color-*` tokens **[guide only]** |
| `next/link`, `next/navigation` in admin internals | Next-only | framework-agnostic `RouterAdapter` hooks; `@payloadcms/next/{client,rsc,templates}` removed **[guide only]** |
| Plugin API | — | `definePlugin` requires `slug`, options move to a named `options` argument **[guide only]** |

## 5. Package, template, and doc changes

> Verified against payload v3.90.2 (`diff <(ls packages)`, `diff <(ls templates)`, `diff -rq docs`) **[diffed]**

- **Added packages**: `@payloadcms/codemod`, `@payloadcms/tanstack-start` (with `app-tanstack/` at repo root).
- **Removed packages**: `@payloadcms/richtext-slate` (stay on 3.x until you finish the Slate→Lexical migration), `@payloadcms/storage-uploadthing` (move to S3 or another adapter first). `HTMLConverterFeature`/`lexicalHTML` removed in favour of `convertLexicalToHTML` / `lexicalHTMLField` **[guide only]**.
- **Templates**: `blank-tanstack` added (Vite + TanStack Start, `payload build`, `srvx` start); CPA on `main` lists it as "Blank TanStack Start Template". Other templates unchanged in name. The TanStack package requires `vite >=8`, `@tanstack/react-start ^1.168.26`.
- **Docs added on `main`**: `configuration/cli`, `hierarchy/overview`, `fields/slug`, `authentication/rotating-secret`, `authentication/server-functions`, `local-api/server-functions`, `getting-started/ai-tooling`, `migration-guide/{v3,v4}`. Production docs gain an **HTTP Security Headers** section (Payload sets none for you; use Next `headers()`/CSP, or TanStack middleware).
- **Agent skill shipping**: v4 ships the skill inside the package at `node_modules/payload/skills/payload/` (absent from the 3.90.2 package); v3's `create-payload-app` downloads it from the `3.x` branch into `.claude/skills/payload`. The `ai-tooling` doc warns to use **one channel per project** (package pointer or Claude Code plugin `payload@payload-marketplace`), because both provide a skill named `payload` at different versions.
- **Search/other plugins**: `plugin-search` drops `apiBasePath`; `plugin-mcp` config API refactored; `plugin-import-export` `toCSV`/`fromCSV` removed; Stripe/ecommerce confirmations use atomic claims and the Stripe REST proxy needs a method allowlist **[guide only]**.

## 6. Already true in 3.90.2 (do not treat as v4-only)

> Verified against payload v3.90.2 (`packages/payload/src/auth/jwt.ts`, `uploads/fetchAPI-multipart/index.ts`) **[diffed]**

- **JWT `authVersion: 1` protected header** exists in 3.90.2 (`JWT_AUTH_VERSION` exported from `payload`). The guide notes tokens from unpatched releases are rejected, so upgrading from an older 3.x forces re-login; upgrading from 3.90.x does not.
- **`abortOnLimit: true`** default is already in 3.90.2 code and docs.

## 7. Guide-only items (not code-diffed here)

Treat as UNVERIFIED for planning: Lexical 0.50 upgrade and vendored `@lexical/markdown` removal, `EXPERIMENTAL_TableFeature` → `TableFeature`, `useLocale` returning `null`, `useDocumentInfo` `title`/`setDocumentTitle` removal, `forceSelect` → `select` function, `admin.hideAPIURL` removal, `admin.components.elements` → `edit` on globals, `min`/`max` → `minRows`/`maxRows` on relationship and upload fields, `allowLocalizedWithinLocalized` removal, user types consolidated into `User`/`AuthenticatedUser`, `multiTenantPlugin`/`searchPlugin` no longer generic, Azure client uploads via Azure Blob SDK (CORS rules change), direct uploads via a shared `POST /api/upload-instructions` endpoint (old S3/Azure/GCS signing endpoints removed; `upload.limits.fileSize` now checked for Azure/GCS/R2/Vercel Blob).

## 8. Upgrade mechanics

> Verified against payload v3.90.2 (`packages/codemod/README.md`, `docs/migration-guide/v4.mdx` §Codemod) **[diffed: README]**

```bash
npx @payloadcms/codemod@canary            # all transforms; idempotent, safe on partly migrated code
npx @payloadcms/codemod --list            # registered transforms
npx @payloadcms/codemod --transform migrate-versions-default --dry
npx @payloadcms/codemod@canary upgrade    # picks: hand off to claude/codex, run mechanical steps, or print the prompt
npx @payloadcms/codemod@canary upgrade run --dry
```

Notable transforms: `add-override-access-true`, `migrate-versions-default`, `remove-versions-true`, `migrate-storage-adapters-to-config`, `migrate-block-references-to-blocks`, `migrate-db-types-subpath`, `migrate-force-select`, `migrate-hide-api-url`, `migrate-list-view-select-api`, `rename-typescript-schema-to-json-schema`, `migrate-build-script`.

`upgrade run` pins `payload` and every `@payloadcms/*` to one exact version, writes the TypeScript / `@types/node` / `engines.node` floors, installs, then runs every transform. It does **not** upgrade Next.js; do that with Next's own codemods first or alongside. Use `--force` to skip the dirty-git warning; commit before running.

Follow-up work no codemod does: DB migrations (versions tables, jobs columns, storage `prefix`, `apiKeyLast4`), Docker/CI Node bump to 24.15+, TypeScript 6, re-issue API keys older than 3.46.0, regenerate types/importmap, then run the full test suite and a visual pass of every page.

## 9. Recommendation: pin v3 or try v4

| Situation | Choose | Why |
|---|---|---|
| Client/production site, or rebuilding a site "for when we redo it" | **Pin v3.90.x exactly** (`payload`, all `@payloadcms/*`, `react`, `react-dom`) | `latest` on npm; payloadcms.com itself runs 3.90.1; templates, docs, plugins, and community answers all target it |
| Need Slate or Uploadthing | v3 | removed in v4 |
| On Node < 24.15 or Next 15 | v3 | v4 floors |
| Want `hierarchy`, `payload build`, JSON/agent-friendly CLI, or TanStack Start | v4 canary in a **throwaway branch** first | features exist only on `main`; canary means breaking changes between numbers |
| Greenfield internal tool with a tolerance for churn | v4 canary, exact-pinned | you inherit the safer defaults (`overrideAccess: false`, depth 1) from day one |
| Planning a later migration | Stay on v3 but write v4-safe code now | explicit `overrideAccess`, explicit `depth`, explicit `versions`, exact-pinned packages, `select` in queries, cron ranges written strictly (`*/N`), no reliance on Slate |

v4 has no stable release date in the materials read (UNVERIFIED). Re-check `npm view payload dist-tags` and the `v4.mdx` guide before starting.

## 10. Sources

`docs/migration-guide/{overview,v4}.mdx` on `main`; `packages/codemod/README.md`; `docs/configuration/cli.mdx`; `docs/getting-started/{installation,ai-tooling}.mdx`; manifests and sources named in each section. Checkouts: tag `v3.90.2` (`6254c3bf`) and `main` (`5448061a`, 2026-09-24); GitHub API and npm registry queried 2026-09-24.
