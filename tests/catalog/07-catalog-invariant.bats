#!/usr/bin/env bats
# 07-catalog-invariant.bats — Validate scripts/catalog.sh.
#
# Contract: contracts/installer/catalog-invariant.md v1.2.0
#
# Builds a self-contained fake repo in a temp dir (scripts/catalog.sh + libs,
# a skills/ tree, README.md, plugin.json, marketplace.json) so the count
# assertions can be driven from disk without touching the real repo.

setup() {
  REPO_ROOT="$(cd "$(dirname "$BATS_TEST_FILENAME")/../.." && pwd)"
  CATALOG="$REPO_ROOT/scripts/catalog.sh"

  FAKE="$(mktemp -d "${TMPDIR:-/tmp}/ats-catalog-test.XXXXXX")"

  mkdir -p "$FAKE/scripts/lib" "$FAKE/.claude-plugin"
  cp "$CATALOG"                     "$FAKE/scripts/catalog.sh"
  cp "$REPO_ROOT/scripts/lib/term.sh" "$FAKE/scripts/lib/term.sh"

  # ---- Build a small, deterministic skills tree -----------------------------
  # 5 active skills total: orchestrator(1) + roles(2) + workflows(2).
  _mk_skill "$FAKE/skills/orchestrator" orchestrator
  _mk_skill "$FAKE/skills/roles/backend-agent" backend-agent
  _mk_skill "$FAKE/skills/roles/frontend-agent" frontend-agent
  _mk_skill "$FAKE/skills/workflows/plan-builder" plan-builder
  _mk_skill "$FAKE/skills/workflows/mermaid-charts" mermaid-charts

  # Excluded trees: must NOT be counted.
  _mk_skill "$FAKE/skills/archive/old-skill" old-skill
  _mk_skill "$FAKE/skills/in-progress/wip-skill" wip-skill

  # ---- Asserted-count files, written to match disk -------------------------
  # Disk per-category: contracts=0 roles=2 meta=0 git=0 workflows=2 -> total 5.
  _write_readme "$FAKE/README.md" 5 0 2 0 0 2
  _write_plugin "$FAKE/.claude-plugin/plugin.json" 5
  _write_marketplace "$FAKE/.claude-plugin/marketplace.json" 5

  FCATALOG="$FAKE/scripts/catalog.sh"
}

teardown() {
  rm -rf "$FAKE"
}

# _mk_skill <dir> <name>
_mk_skill() {
  mkdir -p "$1"
  cat > "$1/SKILL.md" <<EOF
---
name: $2
version: 1.0.0
description: test skill
---
# $2
body
EOF
}

# _write_readme <file> <total> <contracts> <roles> <meta> <git> <workflows>
_write_readme() {
  local f="$1" total="$2" contracts="$3" roles="$4" meta="$5" git="$6" wf="$7"
  cat > "$f" <<EOF
<img src="https://img.shields.io/badge/skills-${total}-success.svg" alt="${total} skills" />

- 🧰 **${total} skills, seven categories, all CI-linted** — stuff.
- 🪜 A ${total}-skill library stays cheap to host.

> - **The orchestrator + ${total}-skill library is the mature part.**

That installs all ${total} skills into Claude Code's plugin storage.

\`\`\`mermaid
    subgraph contracts["📜 contracts/ — ${contracts} skills"]
    subgraph roles["🤖 roles/ — ${roles} agents · exclusive file ownership"]
    subgraph meta["🧠 meta/ — ${meta} skills"]
    subgraph gitcat["🔁 git/ — ${git} skills"]
    subgraph workflows["⚙️ workflows/ — ${wf} skills"]
\`\`\`

${total} skills organized into seven categories. All bodies under 500 lines.

| 47 | \`railway-deploy\` | workflow | Deploy to Railway |

<summary><b>"My non-Claude-Code host doesn't see all ${total} skills"</b></summary>

- [x] **Skill library** — ${total} skills, seven categories, all linted
EOF
}

# _write_plugin <file> <total>
_write_plugin() {
  cat > "$1" <<EOF
{
  "name": "skill-madness",
  "description": "Contract-first multi-agent orchestrator with $2 skills: stuff.",
  "skills": ["./skills/orchestrator"]
}
EOF
}

# _write_marketplace <file> <total>
_write_marketplace() {
  cat > "$1" <<EOF
{
  "metadata": {
    "description": "All the chaos — the $2-skill library it draws from."
  },
  "plugins": [
    { "description": "Install all $2 Skill-Madness skills: the orchestrator." }
  ]
}
EOF
}

# ---------------------------------------------------------------------------
# --text: total == sum of per-category counts
# ---------------------------------------------------------------------------
@test "catalog --text prints total equal to sum of categories" {
  run env NO_COLOR=1 bash "$FCATALOG" --text
  [ "$status" -eq 0 ]
  echo "$output" | grep -qE 'TOTAL[[:space:]]+5'
  echo "$output" | grep -qE 'orchestrator[[:space:]]+1'
  echo "$output" | grep -qE 'roles[[:space:]]+2'
  echo "$output" | grep -qE 'workflows[[:space:]]+2'
  # contracts/meta/git are zero here -> sum (1+2+0+0+0+2)=5 == total
}

# ---------------------------------------------------------------------------
# --check PASSES on a matching fixture
# ---------------------------------------------------------------------------
@test "catalog --check passes (exit 0) when prose matches disk" {
  run env NO_COLOR=1 bash "$FCATALOG" --check
  [ "$status" -eq 0 ]
  echo "$output" | grep -qi "clean"
}

# ---------------------------------------------------------------------------
# --check FAILS (exit 1) on an off-by-one README count
# ---------------------------------------------------------------------------
@test "catalog --check fails (exit 1) on off-by-one README count" {
  # README total claims 6 skills; disk has 5 (categories stay disk-true).
  _write_readme "$FAKE/README.md" 6 0 2 0 0 2
  run env NO_COLOR=1 bash "$FCATALOG" --check
  [ "$status" -eq 1 ]
  echo "$output" | grep -qi "drift"
}

@test "catalog --check fails on off-by-one plugin.json count" {
  _write_plugin "$FAKE/.claude-plugin/plugin.json" 4
  run env NO_COLOR=1 bash "$FCATALOG" --check
  [ "$status" -eq 1 ]
}

# ---------------------------------------------------------------------------
# --sync makes a failing fixture pass
# ---------------------------------------------------------------------------
@test "catalog --sync makes a failing fixture pass (--sync then --check = 0)" {
  # Corrupt every asserted file.
  _write_readme "$FAKE/README.md" 6 9 9 9 9 9
  _write_plugin "$FAKE/.claude-plugin/plugin.json" 1
  _write_marketplace "$FAKE/.claude-plugin/marketplace.json" 99

  run env NO_COLOR=1 bash "$FCATALOG" --check
  [ "$status" -eq 1 ]

  run env NO_COLOR=1 bash "$FCATALOG" --sync
  [ "$status" -eq 0 ]

  run env NO_COLOR=1 bash "$FCATALOG" --check
  [ "$status" -eq 0 ]
}

@test "catalog --sync rewrites per-category mermaid labels from disk" {
  # roles has 2 on disk; corrupt the label to 9 (total stays correct at 5).
  _write_readme "$FAKE/README.md" 5 0 9 0 0 2
  run env NO_COLOR=1 bash "$FCATALOG" --sync
  [ "$status" -eq 0 ]
  grep -q 'roles/ — 2 agents' "$FAKE/README.md"
}

# ---------------------------------------------------------------------------
# archive/ and in-progress/ are excluded from the count
# ---------------------------------------------------------------------------
@test "catalog excludes archive/ and in-progress/ from the count" {
  # We created 5 active + 1 archive + 1 in-progress = 7 SKILL.md on disk,
  # but the count must be 5.
  run env NO_COLOR=1 bash "$FCATALOG" --text
  [ "$status" -eq 0 ]
  echo "$output" | grep -qE 'TOTAL[[:space:]]+5'
  # A naive count would be 7; assert 7 does not appear as the total.
  ! echo "$output" | grep -qE 'TOTAL[[:space:]]+7'
}

# ---------------------------------------------------------------------------
# Table-row index ("| 47 |") must never be rewritten by --sync.
# ---------------------------------------------------------------------------
@test "catalog --sync leaves the skill-table row index untouched" {
  _write_plugin "$FAKE/.claude-plugin/plugin.json" 1
  run env NO_COLOR=1 bash "$FCATALOG" --sync
  [ "$status" -eq 0 ]
  grep -qF '| 47 | `railway-deploy`' "$FAKE/README.md"
}

# ---------------------------------------------------------------------------
# node_modules SKILL.md scaffolds (bundled npm deps) must NOT be counted.
# ---------------------------------------------------------------------------
@test "catalog ignores node_modules SKILL.md scaffolds" {
  mkdir -p "$FAKE/skills/workflows/plan-builder/scripts/node_modules/dep/inner"
  printf -- '---\nname: dep\n---\n' \
    > "$FAKE/skills/workflows/plan-builder/scripts/node_modules/dep/inner/SKILL.md"
  run env NO_COLOR=1 bash "$FCATALOG" --text
  [ "$status" -eq 0 ]
  echo "$output" | grep -qE 'TOTAL[[:space:]]+5'        # still 5, not 6
  ! echo "$output" | grep -qE 'TOTAL[[:space:]]+6'
}

# ---------------------------------------------------------------------------
# CLAUDE.md / PLAN.md / START-HERE.md live counts are checked + synced; a
# missing file is a no-op (not every fixture carries them).
# ---------------------------------------------------------------------------
@test "catalog checks + syncs CLAUDE.md / PLAN.md / START-HERE.md live counts" {
  printf -- '— 6 OSS-publishable skills in `skills/`.\n'        > "$FAKE/CLAUDE.md"
  printf -- 'a mature **6-skill** library — stuff.\n'           > "$FAKE/PLAN.md"
  printf -- 'A mature library of **6 skills** (contracts).\n'   > "$FAKE/START-HERE.md"

  run env NO_COLOR=1 bash "$FCATALOG" --check
  [ "$status" -eq 1 ]

  run env NO_COLOR=1 bash "$FCATALOG" --sync
  [ "$status" -eq 0 ]
  grep -q '5 OSS-publishable skills'   "$FAKE/CLAUDE.md"
  grep -q '\*\*5-skill\*\* library'    "$FAKE/PLAN.md"
  grep -q 'library of \*\*5 skills\*\*' "$FAKE/START-HERE.md"

  run env NO_COLOR=1 bash "$FCATALOG" --check
  [ "$status" -eq 0 ]
}

# ---------------------------------------------------------------------------
# Historical count phrasings ("reshaped to 47 skills", "across 49 skills") must
# survive --sync untouched — only the live phrasing is reconciled.
# ---------------------------------------------------------------------------
@test "catalog --sync leaves historical count notes untouched" {
  printf -- '— 6 OSS-publishable skills now.\nHistory: reshaped to 47 skills; across 49 skills.\n' \
    > "$FAKE/CLAUDE.md"
  run env NO_COLOR=1 bash "$FCATALOG" --sync
  [ "$status" -eq 0 ]
  grep -q '5 OSS-publishable skills' "$FAKE/CLAUDE.md"   # live count reconciled
  grep -q 'reshaped to 47 skills'    "$FAKE/CLAUDE.md"   # history preserved
  grep -q 'across 49 skills'         "$FAKE/CLAUDE.md"
}

# ---------------------------------------------------------------------------
# plugin.json `skills` array is reconciled with disk (register missing, drop
# stale). Requires python3 + the reconciler copied into the fixture.
# ---------------------------------------------------------------------------
@test "catalog registers on-disk skills missing from the plugin.json array" {
  command -v python3 >/dev/null 2>&1 || skip "python3 not available"
  cp "$REPO_ROOT/scripts/sync-catalog-skills.py" "$FAKE/scripts/sync-catalog-skills.py"
  # Fixture plugin.json registers only orchestrator; disk has 5 skills.
  run env NO_COLOR=1 bash "$FCATALOG" --check
  [ "$status" -eq 1 ]
  echo "$output" | grep -qi "not registered"

  run env NO_COLOR=1 bash "$FCATALOG" --sync
  [ "$status" -eq 0 ]
  grep -q 'backend-agent'  "$FAKE/.claude-plugin/plugin.json"
  grep -q 'mermaid-charts' "$FAKE/.claude-plugin/plugin.json"

  run env NO_COLOR=1 bash "$FCATALOG" --check
  [ "$status" -eq 0 ]
}

@test "catalog drops a stale plugin.json array entry" {
  command -v python3 >/dev/null 2>&1 || skip "python3 not available"
  cp "$REPO_ROOT/scripts/sync-catalog-skills.py" "$FAKE/scripts/sync-catalog-skills.py"
  printf '{\n  "description": "x with 5 skills",\n  "skills": ["./skills/orchestrator", "./skills/workflows/ghost"]\n}\n' \
    > "$FAKE/.claude-plugin/plugin.json"
  run env NO_COLOR=1 bash "$FCATALOG" --check
  [ "$status" -eq 1 ]
  echo "$output" | grep -qi "stale entry"

  run env NO_COLOR=1 bash "$FCATALOG" --sync
  [ "$status" -eq 0 ]
  ! grep -q 'ghost' "$FAKE/.claude-plugin/plugin.json"
}

# ---------------------------------------------------------------------------
# README catalog TABLE check (CL3): one row per on-disk skill.
# ---------------------------------------------------------------------------

# _append_readme_table <file> <skill...> — append a catalog table with one
# row per named skill (the header is what keys the check).
_append_readme_table() {
  local f="$1"; shift
  {
    printf '\n| # | Skill | Category | What it does |\n'
    printf '|---|-------|----------|--------------|\n'
    local i=1 s
    for s in "$@"; do
      printf '| %d | `%s` | cat | stuff |\n' "$i" "$s"
      i=$(( i + 1 ))
    done
  } >> "$f"
}

@test "catalog --check passes when the README catalog table matches disk" {
  _append_readme_table "$FAKE/README.md" \
    orchestrator backend-agent frontend-agent plan-builder mermaid-charts
  run env NO_COLOR=1 bash "$FCATALOG" --check
  [ "$status" -eq 0 ]
}

@test "catalog --check fails when the README catalog table is missing a row" {
  # 4 rows vs 5 disk skills (mermaid-charts has no row).
  _append_readme_table "$FAKE/README.md" \
    orchestrator backend-agent frontend-agent plan-builder
  run env NO_COLOR=1 bash "$FCATALOG" --check
  [ "$status" -eq 1 ]
  echo "$output" | grep -q "missing row for on-disk skill 'mermaid-charts'"
}

@test "catalog --check fails on a stale README catalog table row" {
  _append_readme_table "$FAKE/README.md" \
    orchestrator backend-agent frontend-agent plan-builder mermaid-charts ghost-skill
  run env NO_COLOR=1 bash "$FCATALOG" --check
  [ "$status" -eq 1 ]
  echo "$output" | grep -q "stale row 'ghost-skill'"
}

# ---------------------------------------------------------------------------
# Previously-unguarded README count phrasings: "N portable skills",
# "out of all N", "skill library (N)" — the 67-vs-68 drift class.
# ---------------------------------------------------------------------------
@test "catalog checks + syncs hero / out-of-all / tree count phrasings" {
  printf -- '**9 portable skills**; out of all 9; skills/  # the canonical skill library (9)\n' \
    >> "$FAKE/README.md"
  run env NO_COLOR=1 bash "$FCATALOG" --check
  [ "$status" -eq 1 ]
  echo "$output" | grep -q 'portable skills'

  run env NO_COLOR=1 bash "$FCATALOG" --sync
  [ "$status" -eq 0 ]
  grep -q '\*\*5 portable skills\*\*'  "$FAKE/README.md"
  grep -q 'out of all 5'               "$FAKE/README.md"
  grep -q 'skill library (5)'          "$FAKE/README.md"

  run env NO_COLOR=1 bash "$FCATALOG" --check
  [ "$status" -eq 0 ]
}

# ---------------------------------------------------------------------------
# CLAUDE.md per-category "(N)" breakdown.
# ---------------------------------------------------------------------------
@test "catalog checks + syncs CLAUDE.md per-category counts" {
  printf -- '— 5 OSS-publishable skills in `skills/`.\n- **`skills/roles/`** (9) — backend, frontend.\n' \
    > "$FAKE/CLAUDE.md"
  run env NO_COLOR=1 bash "$FCATALOG" --check
  [ "$status" -eq 1 ]
  echo "$output" | grep -q 'CLAUDE.md category skills/roles'

  run env NO_COLOR=1 bash "$FCATALOG" --sync
  [ "$status" -eq 0 ]
  grep -qF -- '- **`skills/roles/`** (2) —' "$FAKE/CLAUDE.md"

  run env NO_COLOR=1 bash "$FCATALOG" --check
  [ "$status" -eq 0 ]
}

# ---------------------------------------------------------------------------
# Marketplace per-category breakdown (the 41-era-counts drift class): every
# category number in the plugin description is asserted, not just the total.
# ---------------------------------------------------------------------------
@test "catalog checks + syncs the marketplace per-category breakdown" {
  cat > "$FAKE/.claude-plugin/marketplace.json" <<'EOF'
{
  "metadata": { "description": "the 5-skill library it draws from." },
  "plugins": [
    { "description": "Install all 5 Skill-Madness skills: 9 role agents, 3 contract skills, 5 git workflow skills, 9 meta/skill-management skills, 13 cross-cutting workflows, and 4 autonomous-loop skills." }
  ]
}
EOF
  run env NO_COLOR=1 bash "$FCATALOG" --check
  [ "$status" -eq 1 ]
  echo "$output" | grep -q 'role agents'

  run env NO_COLOR=1 bash "$FCATALOG" --sync
  [ "$status" -eq 0 ]
  # Disk: roles=2 contracts=0 git=0 meta=0 workflows=2 loops=0.
  grep -q '2 role agents'               "$FAKE/.claude-plugin/marketplace.json"
  grep -q '0 contract skills'           "$FAKE/.claude-plugin/marketplace.json"
  grep -q '0 git workflow skills'       "$FAKE/.claude-plugin/marketplace.json"
  grep -q '0 meta/skill-management'     "$FAKE/.claude-plugin/marketplace.json"
  grep -q '2 cross-cutting workflows'   "$FAKE/.claude-plugin/marketplace.json"
  grep -q '0 autonomous-loop skills'    "$FAKE/.claude-plugin/marketplace.json"

  run env NO_COLOR=1 bash "$FCATALOG" --check
  [ "$status" -eq 0 ]
}

# ---------------------------------------------------------------------------
# Architecture-diagram boxes: named nodes + "+ N more" must equal disk, and
# node ids must be unique within a mermaid block.
# ---------------------------------------------------------------------------
@test "catalog checks + syncs the mermaid box overflow node" {
  cat >> "$FAKE/README.md" <<'EOF'

```mermaid
flowchart TB
    subgraph workflows["⚙️ workflows/ — 2 skills"]
        direction TB
        pb[plan-builder]
        more["+ 3 more"]
    end
```
EOF
  run env NO_COLOR=1 bash "$FCATALOG" --check
  [ "$status" -eq 1 ]
  echo "$output" | grep -q 'workflows/ box: 1 named + 3 more'

  run env NO_COLOR=1 bash "$FCATALOG" --sync
  [ "$status" -eq 0 ]
  grep -qF 'more["+ 1 more"]' "$FAKE/README.md"

  run env NO_COLOR=1 bash "$FCATALOG" --check
  [ "$status" -eq 0 ]
}

@test "catalog --check fails when a mermaid box's named nodes miss disk" {
  cat >> "$FAKE/README.md" <<'EOF'

```mermaid
flowchart TB
    subgraph roles["🤖 roles/ — 2 agents · exclusive file ownership"]
        direction TB
        be[backend-agent]
    end
```
EOF
  run env NO_COLOR=1 bash "$FCATALOG" --check
  [ "$status" -eq 1 ]
  echo "$output" | grep -q 'roles/ box: 1 named nodes, disk says 2'
}

@test "catalog --check flags duplicate mermaid node ids" {
  cat >> "$FAKE/README.md" <<'EOF'

```mermaid
flowchart TB
    subgraph roles["🤖 roles/ — 2 agents · exclusive file ownership"]
        be[backend-agent]
        perf[frontend-agent]
    end
    subgraph workflows["⚙️ workflows/ — 2 skills"]
        perf[plan-builder]
        mc[mermaid-charts]
```
EOF
  run env NO_COLOR=1 bash "$FCATALOG" --check
  [ "$status" -eq 1 ]
  echo "$output" | grep -q "node id 'perf' defined more than once"
}
