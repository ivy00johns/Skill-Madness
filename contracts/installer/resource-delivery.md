# Contract: Resource Delivery

**Version:** 1.0.0
**Status:** ACTIVE — approved universal-audit delivery extension UA-09/10/11/20/21/26

## One inventory

Conversion emits `.ats-resources.json` per tool: schema version 1, tool, skills
(slug/category/resource root/prompt paths), and file records with relative path,
owner slug/category, SHA-256 and POSIX mode. Classic and plan installers read the
same inventory and verify all declared bytes/modes before copying. Missing or
changed resources block; inventory is delivery evidence, not host acceptance.
Classic legacy outputs without inventory retain legacy behavior with a warning;
plan installation requires regeneration. Native Claude prompt bytes/metadata and
hook opt-ins remain unchanged.

Resource roots retain `references/`, `scripts/`, `assets/`, `agents/`,
`eval-viewer/`, `template/`, `templates/`, and `sources/`, recursively. Flat
formats receive `<slug>-resources/` beside the prompt, retaining legacy
`<slug>-scripts/`/`<slug>-references/` companions. Aider/Windsurf receive skill
roots below project `.ats-skills/<tool>/skills/<slug>/`; their consolidated
prompts remain separate. Generated nested Markdown is also retained as a file,
not flattened indiscriminately into every prompt.

No `.env*`, `.pem`, `.key`, bytecode, node_modules, Git metadata, build or skill
evaluation workspace is copied from resource directories. Symlink/special-file
resources block. New required resource classes must extend the inventory rather
than rely on copying arbitrary skill-directory debris. Source mode is preserved;
conversion does not mark every Python/shell file executable by guess.

## Runtime roots

Each delivered skill root includes `.ats-runtime.json` declaring root-relative
resources, toolchain and checkout dependencies, and credential policy.
`SKILL_ROOT` is explicit input resolved from the actual host-installed prompt's
resource contract; it is not magically interpolated by hosts and never means
project cwd or hardcoded Claude home. Resolve local imports/templates from that
root. Missing resources/tools are BLOCKED, not a passed check or negative eval.

Repo-maintenance skills declare `ATS_CHECKOUT_ROOT` as an owner-approved checkout
with root helpers available. Do not bundle root administration scripts as if an
installed skill were that checkout. Provider credentials are exported process
variables or an explicitly selected `ATS_ENV_FILE`; native Nano Banana symlinks
retain the canonical root `.env` loader. No home/ancestor/per-skill credential
search for installed copies. Never distribute `.env`; root `.env.example`
remains the single variable template. No automatic dependency installs/provider
calls are authorized by delivery.

## Conversion workers

Parse/validate worker CLI before dispatch. Pass paths as positional arguments,
never interpolate shell source. Parent collects worker status and
processed/skipped/error counts, treats missing/malformed output as failure,
and emits Gemini metadata once. Serial/parallel files and summaries must match.
Reconversion prunes only files owned by the previous generated inventory, not
unrelated output. Failed conversion never seals a successful manifest.

## Reviewed plans (schema 2)

Plan declares the approved absolute root, source bytes/modes, actions and
existing-destination hash/mode preconditions. Apply validates schema, tools,
hashes/modes, duplicate destinations, root containment and symlink parents
before any write. Changed source, missing source or intervening destination edit
blocks the whole operation. Reapply of already-installed reviewed bytes is safe.
Old plans/states require explicit regeneration/reconciliation, not silent trust.

Writes use same-directory atomic replacement and roll back changed files if an
I/O operation fails. State and repair receipts merge prior owned operations
instead of forgetting an earlier subset install. This is bounded offline
rollback, not a transactional filesystem under hostile concurrent mutation;
no lock/sandbox or power-loss whole-tree atomicity is claimed. Drift includes
mode changes. Repair revalidates sources; uninstall refuses edited files and
never removes unowned data. Dry run writes no files, receipts or bytecode caches.

Gemini keeps extension metadata and `skills/<slug>/`. Claude hooks map to
`.claude/ats-hooks/`, not the skills tree; plan `--include-hooks` adds hook files
without activating settings. Classic `--wire-hooks` remains separately opt-in.
Consolidated Aider/Windsurf prompts cannot be category-subsetted; their resource
roots can, but the prompt remains the entire exported eligible catalog.

## Scoped sync

Native CC/Cursor directory adapters retain their supported scope only. They
share converter eligibility and resource policy. Individual entries honor exact
subsets; old category links are left for explicit migration. Ownership receipts
record exact links/copy fingerprints. Unowned/edited collisions block unless
`--replace-with-backup` is explicitly approved. Clean/unlink affect only matching
recorded links; unrelated broken symlinks and local skills remain. Global sync
is a separately approved operation, never implicit catalog maintenance.

## Proof boundary

Offline fixtures verify files, modes, local helper execution and failure paths
in fake HOME/project roots. They do not prove host retrieval, independent QE,
paid-provider results, unattended execution or installation into real HOME.
