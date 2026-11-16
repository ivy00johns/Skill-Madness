---
title: Environment Variables for Skills
tags: [environment-variables-for-skills]
paths: []
updated: 2026-11-16
---

Imported from `AGENTS.md:29` by Andon (import AGENTS.md:29 94ccfbf5396bfb66); the original stays there.

All API keys and credentials for skills live in a **single root `.env` file** at the repo root — never in per-skill `.env` files. This keeps secrets centralized and avoids confusion as the skill count grows.

- **`.env`** — The live credentials file (gitignored, never committed)

- **`.env.example`** — Template documenting every variable across all skills (committed, no real values)

When a skill needs a new env var:

1. Add the variable (with empty value and a comment) to `.env.example`

2. Have the skill's scripts read from the repo root `.env`

3. Document which skill uses it in the `.env.example` section header

Scripts should walk up from their location to find the repo root `.env`. Pattern:

```python
import pathlib, os
_repo_root = pathlib.Path(__file__).resolve().parent
while _repo_root != _repo_root.parent:
    if (_repo_root / ".env.example").exists():
        break
    _repo_root = _repo_root.parent
# Then load _repo_root / ".env"
```
