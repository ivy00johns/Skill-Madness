# Fields

All 22 Payload field types, shared options, and the ones that carry a website (blocks, relationships, uploads, rich text, slug, conditional logic). Verified against stable **payload 3.90.2**; `v4:` lines are diffs against 4.0.0-canary.37.

## Contents

1. Field catalogue and shared options
2. Blocks (layout builder)
3. Array, group, tabs, row, collapsible
4. Relationship and upload
5. Join
6. Rich text (Lexical) and rendering to JSX
7. Select, radio, text, number, date, point, json, code, checkbox
8. Slug helper
9. Virtual fields
10. Conditional logic, validation, defaults
11. Field-level access and hooks
12. Reserved and generated fields

## 1. Field catalogue and shared options

> Verified against payload v3.90.2 (packages/payload/src/fields/config/types.ts L1851-1873 `Field` union, docs/fields/overview.mdx)

The `Field` union is exactly: `array`, `blocks`, `checkbox`, `code`, `collapsible`, `date`, `email`, `group`, `join`, `json`, `number`, `point`, `radio`, `relationship`, `richText`, `row`, `select`, `tabs`, `textarea`, `text`, `ui`, `upload`. There is no `slug` *type* in 3.90.2 (see section 8).

| Kind | Types | Stores data |
| --- | --- | --- |
| Data | array, blocks, checkbox, code, date, email, group (named), json, number, point, radio, relationship, richText, select, tabs (named tab), text, textarea, upload | yes, under `name` |
| Layout only | row, collapsible, unnamed group, unnamed tabs | no (children store flat in the parent) |
| Virtual | join; any field with `virtual` | no |
| UI | ui | no (custom component only) |

Options shared by data fields: `name` (required, unique among siblings; use identifier-style names - no hyphens, no leading digit, they break GraphQL and dot paths), `label`, `required`, `unique` (DB unique index), `index`, `defaultValue` (value or `({ user, locale, req }) => value`), `hidden` (removed from all APIs and admin, still stored), `localized`, `validate`, `hooks`, `access`, `admin`, `custom`, `saveToJWT` (top-level fields on auth collections), `virtual`, `typescriptSchema`, `disableDuplicate` (do not copy on Duplicate). `hasMany` / `minRows` / `maxRows` on text, number, select, relationship, upload.

`admin` options: `condition`, `components`, `description` (string, or `({ t }) => string`), `position: 'sidebar' | 'main'`, `width`, `style`, `className`, `readOnly` (UI only; API unaffected), `disabled` (omit from admin entirely), `hidden`, `disableBulkEdit`, `disableGroupBy`, `disableListColumn`, `disableListFilter`.

Field names that are reserved and silently stripped: `__v`, `salt`, `hash`, `file`, and `status` (Postgres + drafts).

`v4:` `admin.disabled` becomes `true | { field, column, filter, groupBy, bulkEdit }`; the four `disable*` flags go away. `min`/`max` on hasMany relationship/upload removed (use `minRows`/`maxRows`). `typescriptSchema` renamed `jsonSchema`.

## 2. Blocks (layout builder)

> Verified against payload v3.90.2 (docs/fields/blocks.mdx, packages/payload/src/fields/config/types.ts L1585-1640)

```ts
import type { Block, Field } from 'payload'

export const CallToAction: Block = {
  slug: 'cta',                       // stored as blockType
  interfaceName: 'CallToActionBlock',// optional: named top-level TS/GraphQL type
  labels: { singular: 'Call to Action', plural: 'Calls to Action' },
  admin: { group: 'Marketing', images: { thumbnail: '/blocks/cta.jpg', icon: '/blocks/cta.svg' }, disableBlockName: true },
  fields: [
    { name: 'heading', type: 'text', required: true },
    { name: 'links', type: 'array', maxRows: 2, fields: [/* link field */] },
  ],
}

export const layout: Field = {
  name: 'layout',
  type: 'blocks',
  blocks: [CallToAction, Content, MediaBlock],
  required: true,
  minRows: 1,
  admin: { initCollapsed: true, isSortable: true },
}
```

- Each stored block: `{ id, blockType: '<slug>', blockName?: string, ...fields }`. Render by switching on `blockType` and mapping to a component (see the website template's `RenderBlocks`).
- `imageURL` / `imageAltText` are `@deprecated` in 3.90.2 - use `admin.images.{ thumbnail (3:2), icon (20x20) }`. `graphQL.singularName` is deprecated in favor of `interfaceName`.
- `interfaceName` must be unique across collections/arrays/groups/blocks/tabs; it emits a shared top-level type in `payload-types.ts`. `dbName` shortens SQL table names.
- **Block references** (avoid re-sending the same block config everywhere): define once in root `blocks: []`, then in the field `blockReferences: ['TextBlock'], blocks: []` (blocks must be `[]`). Referenced blocks are identical everywhere and their access control runs once without collection data. The same slug can be reused in Lexical via `BlocksFeature({ blocks: ['TextBlock'] })`.
- `unique: true` on a field *inside* a block is a collection-wide unique index, not per-document; use a `validate` on the blocks field for per-document uniqueness. On Mongo, docs lacking the block collide on `null`.
- Blocks are not fields - they take `slug`, `fields`, `labels`, `interfaceName`, `dbName`, `admin.{ components.Block|Label, disableBlockName, group, images }`, but not `access`/`hooks`.
- Admin supports row and field-level copy/paste (localStorage key `_payloadClipboard`); "Paste Fields" replaces all blocks even when one row was copied.
- `localized: true` on the blocks field localizes the whole layout (no need to mark children).

`v4:` `blockReferences` merged into `blocks` (`blocks: ['hero', CallToAction]`); every block always emits a top-level interface named PascalCase(slug), `interfaceName` only overrides; hash-suffixed names on collision.

## 3. Array, group, tabs, row, collapsible

> Verified against payload v3.90.2 (docs/fields/{array,group,tabs,row,collapsible}.mdx)

- **array**: repeating rows of `fields`. Options `minRows`, `maxRows`, `labels`, `interfaceName`, `dbName`, `admin.{ initCollapsed, isSortable, components.RowLabel }`. Each row gets an `id`. Use for link lists, nav items, FAQs.
- **group**: named object of nested fields; unnamed group is layout-only. `admin.hideGutter`, `interfaceName`. Good for `hero`, `meta`, `link` sub-objects.
- **tabs**: `{ type: 'tabs', tabs: [{ label, name?, fields, description?, interfaceName?, admin? }] }`. A tab with `name` stores as a group; without it, layout only. Unnamed tab with `admin.condition` needs an `id`. Website template uses tabs for Hero / Content / SEO on `pages`.
- **row**: horizontal layout; set `admin.width` (e.g. `'50%'`) on children. **collapsible**: `{ label, admin.initCollapsed, fields }`, layout only.
- Nested `localized` under a localized parent is dropped by sanitize.

## 4. Relationship and upload

> Verified against payload v3.90.2 (docs/fields/relationship.mdx, docs/fields/upload.mdx, docs/queries/depth.mdx)

```ts
{ name: 'categories', type: 'relationship', relationTo: 'categories', hasMany: true, filterOptions: { published: { equals: true } }, maxDepth: 1 },
{ name: 'owner', type: 'relationship', relationTo: ['users', 'organizations'] },   // polymorphic
{ name: 'heroImage', type: 'upload', relationTo: 'media' },                         // target collection must have `upload`
```

- Stored shapes: one/one-collection = the ID; hasMany = array of IDs; **polymorphic = `{ relationTo, value }`** (hasMany polymorphic = array of those). Query polymorphic with `owner.value` / `owner.relationTo`.
- Populated depth: raw ID when depth is exhausted, full doc otherwise. Field-level `maxDepth` caps population regardless of request depth. In 3.x the default depth is 2, so nested references (page -> block -> upload) populate two levels; set depth explicitly (`depth: 1`, `0`) and `select`/`defaultPopulate` to trim payloads.
- `filterOptions`: a `Where` or `({ relationTo, data, siblingData, id, user, req, blockData }) => boolean | Where`. Used for both the UI list and server validation. If you also set a custom `validate`, filterOptions are only enforced when your validate calls the default `relationship` validator from `payload/shared`.
- Admin options: `allowCreate`, `allowEdit`, `isSortable` (hasMany), `sortOptions`, `appearance: 'select' | 'drawer'`, `placeholder`.
- `upload` options add `displayPreview`, and the same `filterOptions`/`hasMany`/`maxDepth`. An upload field points at a collection with `upload: true`; image sizes appear under `doc.sizes.<name>.url`.
- Relationship values in APIs when populated may be a doc *or* an ID; guard with `typeof x === 'object'` in TypeScript (generated types are `string | Doc`).

## 5. Join

> Verified against payload v3.90.2 (docs/fields/join.mdx)

Virtual reverse relationship: `{ name: 'relatedPosts', type: 'join', collection: 'posts', on: 'categories' }` (`on` = the relationship/upload field on the other collection; dot path for nested; `collection` may be an array for polymorphic). Options: `where`, `defaultLimit` (default 10; `0` = all), `defaultSort`, `maxDepth` (default 1), `orderable`, `admin.{ defaultColumns, allowCreate, disableRowTypes }`.

Result shape `{ docs: [...], hasNextPage, totalDocs? }` (`totalDocs` only with `count: true`); polymorphic `docs` are `{ relationTo, value }`. Per-request control: Local `joins: { relatedPosts: { limit: 5, where, sort, count: true } }`, REST `?joins[relatedPosts][limit]=5`, or `joins: false` to skip all joins. `where` on polymorphic joins is limited and unsupported inside arrays/blocks. Joins are not stored - the relationship field on the *other* collection must be indexed for speed.

## 6. Rich text (Lexical) and rendering to JSX

> Verified against payload v3.90.2 (docs/rich-text/{overview,converting-jsx,official-features}.mdx, templates/website/src/fields/defaultLexical.ts)

```ts
import { lexicalEditor, BlocksFeature, LinkFeature, UploadFeature, FixedToolbarFeature, HeadingFeature } from '@payloadcms/richtext-lexical'

editor: lexicalEditor({
  features: ({ defaultFeatures, rootFeatures }) => [
    ...defaultFeatures,
    FixedToolbarFeature(),
    BlocksFeature({ blocks: [Banner, CallToAction] }),   // reuse Block configs (or slugs from root `blocks`)
    LinkFeature({ enabledCollections: ['pages', 'posts'] }),
  ],
})
```

- Set `editor` at root (`buildConfig`) and/or per `richText` field. `features` is an array or `({ defaultFeatures, rootFeatures }) => Feature[]`. Listing features without spreading `defaultFeatures` gives you *only* those features (the website template does this: paragraph, underline, bold, italic, link).
- On by default: Bold, Italic, Underline, Strikethrough, Subscript, Superscript, InlineCode, Paragraph, Heading (h1-h6), Align, Indent, UnorderedList, OrderedList, Checklist, Link, Relationship, Blockquote, Upload, HorizontalRule, InlineToolbar. Off by default: FixedToolbar, Blocks, TreeView, `EXPERIMENTAL_TableFeature`, TextState.
- Stored as serialized Lexical JSON (`SerializedEditorState`); Slate is deprecated in 3.x.
- **Render to JSX**: `import { RichText } from '@payloadcms/richtext-lexical/react'` then `<RichText data={doc.content} converters={jsxConverters} />`. Needs sufficiently high `depth` so uploads/internal links are populated.
  - Internal links need `LinkJSXConverter({ internalDocToHref: ({ linkNode }) => ... })` inside a `converters` function `({ defaultConverters }) => ({ ...defaultConverters, ...LinkJSXConverter(...) })`, otherwise you get "found internal link, but internalDocToHref is not provided". `linkNode.fields.doc` is `{ relationTo, value }` and `value` must be a populated object.
  - Lexical blocks need converters keyed by block slug: `{ blocks: { myBlock: ({ node }) => <X {...node.fields} /> }, inlineBlocks: {...} }`. Type nodes with `SerializedBlockNode<MyBlock>` from generated types.
  - Override e.g. `upload` with a `next/image` component via the same `converters` map.
- Other conversions exist (`converting-html`, `-markdown`, `-plaintext`); `Views` share a node map between admin and frontend.

`v4:` `@payloadcms/richtext-slate` removed; `HTMLConverterFeature`, `lexicalHTML` and per-node `converters.html` removed (use `convertLexicalToHTML` and `lexicalHTMLField` from `@payloadcms/richtext-lexical`); `EXPERIMENTAL_TableFeature` -> `TableFeature`; lexical 0.50; `RichText` adapter `i18n` removed.

## 7. Select, radio, text, number, date, point, json, code, checkbox

> Verified against payload v3.90.2 (docs/fields/{select,radio,text,textarea,number,date,point,json,code,checkbox,email}.mdx)

- **select**: `options: string[] | { label, value }[]`; `hasMany`, `isClearable`, `isSortable`, `filterOptions`, `enumName`/`dbName` (SQL), `interfaceName`. **radio**: `options`, `admin.layout: 'horizontal' | 'vertical'`. Changing option values later does not migrate stored data.
- **text**/**textarea**/**email**: `minLength`, `maxLength`, `unique`, `index`; text supports `hasMany` (array of strings) with `minRows`/`maxRows`. Set `defaultMaxTextLength` at root for public-write forms.
- **number**: `min`, `max`, `hasMany`, `step`. **checkbox**: boolean, `defaultValue: false`.
- **date**: `timezone: true` stores the chosen zone in a companion `<name>_tz` column (e.g. `date_tz`); `admin.date.{ pickerAppearance: 'dayAndTime' | 'timeOnly' | 'dayOnly' | 'monthOnly', displayFormat, minDate, maxDate, timeIntervals }`. Enable timezones in root `admin.timezones` first.
- **point**: `[longitude, latitude]`, gets a `2dsphere` index (`index: false` to disable); queries `near`/`within`/`intersects`; **not supported on SQLite**.
- **json**: arbitrary JSON with a Monaco editor and optional `jsonSchema`. **code**: string with `admin.language`.

## 8. Slug helper

> Verified against payload v3.90.2 (packages/payload/src/fields/baseFields/slug/index.ts, index.ts L1536, templates/website/src/collections/Pages/index.ts L120)

```ts
import { slugField } from 'payload'
fields: [{ name: 'title', type: 'text', required: true }, slugField()]                       // default: slug from `title`, sidebar
slugField({ name: 'slug', useAsSlug: 'name', localized: true, disableUnique: true, required: false, slugify: ({ valueToSlugify }) => ... })
```

`slugField` **exists in 3.90.2**, is exported from `payload`, and is marked `@experimental`. It returns a **row field** containing a hidden `generateSlug` checkbox (default true) and the `slug` text field (`index: true`, `unique: true` unless `disableUnique`, `required: true`, sidebar). Behavior: generated on create unless edited; on update only if autosave is off and no slug exists, or autosave on + unpublished + not manually modified. It then stabilizes so live URLs do not change. `overrides: (rowField) => rowField` for granular edits; `fieldToUse` is a deprecated alias of `useAsSlug`. Use `disableUnique` with a compound `indexes: [{ fields: ['tenant','slug'], unique: true }]` for multi-tenant.

`v4:` becomes a real field type: `{ name: 'slug', type: 'slug', useAsSlug: 'title' }` (docs/fields/slug.mdx); always generated on create with `<singular>-<N>` fallback; static once set.

## 9. Virtual fields

> Verified against payload v3.90.2 (docs/fields/overview.mdx "Virtual Field Configuration")

Any field can be `virtual`. `virtual: true` + an `afterRead` hook computes a value on read (not stored). `virtual: 'author.name'` resolves a path through a relationship at query time (arrays for hasMany: `'categories.title'`); the first path segment must be a relationship field in the same collection. Use it for `admin.useAsTitle` when the title lives on a related doc (a relationship used directly as title shows only the ID).

## 10. Conditional logic, validation, defaults

> Verified against payload v3.90.2 (docs/fields/overview.mdx)

```ts
{ name: 'url', type: 'text', admin: { condition: (data, siblingData, { blockData, operation, path, user }) => siblingData?.type === 'custom' } }
{ name: 'code', type: 'text', validate: (val, { data, siblingData, operation, id, req, event }) => (val ? true : 'Required') }
```

- `condition` is admin-UI only; hidden fields still exist in the API. Enforce with `validate`/hooks if it matters.
- `validate` returns `true` or an error string, runs client and server; `event: 'onChange' | 'submit'` lets you skip expensive checks while typing. Reuse built-ins by importing from `payload/shared` (`text`, `relationship`, `blocks`, `richText`, `upload`, ...) and calling them from your validator (also needed to keep `filterOptions` enforced). Localize messages with `req.t('validation:required')`.
- `defaultValue` static values are applied at the DB schema level; functions receive `{ user, locale, req }` and can be async.
- `beforeDuplicate` hook / `disableDuplicate` control copy behavior; unique+required text gets " - Copy" appended by default.

## 11. Field-level access and hooks

> Verified against payload v3.90.2 (docs/access-control/fields.mdx, docs/hooks/fields.mdx)

- **Access** `{ create, read, update }`, each returns **boolean only** (no `Where`). `create`/`update` false = value silently dropped (no error); `read` false = property omitted from the response. Args: `{ req, id, data, siblingData, doc }` (subset per operation).
- **Hooks** `{ beforeValidate, beforeChange, beforeDuplicate, afterChange, afterRead }`, arrays of functions returning the (possibly changed) value. Args: `value, previousValue, data, siblingData, originalDoc, previousDoc, operation, path, schemaPath, req, context, collection, global, field, findMany, overrideAccess`. Do not change a field's *type* in `afterRead` (breaks GraphQL); use collection hooks for reshaping. `beforeDuplicate` runs per locale, before `beforeValidate`. Order for a write: client `validate` -> `beforeValidate` -> server `validate`. `TypeScript: FieldHook<Doc, ValueType, SiblingData>`.

## 12. Reserved and generated fields

> Verified against payload v3.90.2 (docs/fields/default-fields.mdx)

Payload injects: `id` (override with a top-level `id` field, **number or text only**; text ids may not contain `/` or `.`), `createdAt`/`updatedAt` (keep as `date`), `deletedAt` (trash), auth fields (`email`, `password`, `resetPasswordToken`, `_verified`, `loginAttempts`, `lockUntil`, `sessions`, `apiKey`, ...), upload fields (`filename`, `mimeType`, `filesize`, `width`, `height`, `url`, `thumbnailURL`, `focalX/Y`, `sizes`), and `_status` (drafts). Declaring a top-level field with the same name *deep-merges* config into the generated one (e.g. add `access` to `apiKey`); only fields listed in that doc may be overridden. `salt`, `hash`, `file` are reserved.
