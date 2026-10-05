#!/usr/bin/env bash
# Native link/copy adapter; checkout dependency is explicit for installed copies.
set -euo pipefail
export PYTHONDONTWRITEBYTECODE=1
HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT="${ATS_CHECKOUT_ROOT:-}"
if [[ -z "$ROOT" ]]; then
  ROOT="$(python3 - "$HERE" <<'PY'
from pathlib import Path
import sys
here=Path(sys.argv[1]).resolve()
for parent in (here, *here.parents):
    if (parent/'scripts/lib/resource_delivery.py').is_file() and (parent/'skills').is_dir():
        print(parent); break
PY
  )"
fi
if [[ -z "$ROOT" || ! -f "$ROOT/scripts/lib/sync_delivery.py" ]]; then
  printf 'sync blocked: set ATS_CHECKOUT_ROOT to the approved Skill-Madness checkout\n' >&2
  exit 2
fi
exec python3 "$ROOT/scripts/lib/sync_delivery.py" --repo "$ROOT" "$@"
