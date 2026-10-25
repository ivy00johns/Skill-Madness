# Documentation Templates

## README.md Template

The root README must contain the required sections in `skills/orchestrator/references/workspace-bootstrap.md` (What the project is, Stack, Prerequisites, Setup, Start, Tests, Deploy, Project structure, Known issues, Documentation map). Use this skeleton and omit a section only when it is genuinely irrelevant. Every command must be a real command from the project; verify it runs before writing it down.

````markdown
# [Project Name]

[What the project is: one paragraph, no marketing]

## Stack

- **Language / framework:** [language + framework]
- **Data / infra:** [database, queue, Docker, etc.]

## Prerequisites

- [Runtime + version, e.g. Node.js LTS]
- [Package manager]
- [Database or Docker, if needed]

## Setup

```bash
[exact install command]
[infra-up command, if any]
cp .env.example .env
[migrate / seed commands, if any]
```

## Start

```bash
[dev command per service, or one aggregate dev command]
```

## Environment Variables

| Variable | Description | Default | Required |
|----------|-------------|---------|----------|
| `PORT` | Backend server port | `8000` | No |
| `DATABASE_URL` | Database connection string | `sqlite:///app.db` | Yes |
| `FRONTEND_ORIGIN` | CORS allowed origin | `http://localhost:5173` | No |

## API Overview

Base URL: `http://localhost:8000/api/v1`

| Method | Endpoint | Description |
|--------|----------|-------------|
| `POST` | `/<resource>` | Create a new <resource> |
| `GET` | `/<resource>` | List all <resource> |
| `GET` | `/<resource>/:id` | Get <resource> by ID |

See [API Documentation](docs/api.md) for full details.

## Tests

```bash
[unit / integration / e2e commands]
```

## Deploy

```bash
[actual deploy command, or "none (local-only)"]
```

## Project Structure

```
├── backend/          # API server
├── frontend/         # Web UI
├── contracts/        # Shared type definitions
├── tests/            # Integration tests
└── docker-compose.yml
```

## Known issues

- [Failing checks, latent bugs, deferred work the human will hit on first run]

## Documentation map

| Doc | Purpose |
|---|---|
| [CLAUDE.md](CLAUDE.md) | Agent instructions |
| [docs/](docs/) | Plans, ADRs, reports |

## License

[License type]

````

## API Endpoint Documentation Template

````markdown
### [METHOD] [path]

[One-line description]

**Request:**
```bash
curl -X [METHOD] http://localhost:8000[path] \
  -H "Content-Type: application/json" \
  -d '{"field": "value"}'
```

**Response (success):**

```json
{
  "id": "uuid",
  "field": "value",
  "createdAt": "2024-01-01T00:00:00Z"
}
```

**Response (error):**

```json
{
  "error": "Description",
  "code": "ERROR_CODE",
  "details": []
}
```

| Status | Meaning |
|--------|---------|
| 201 | Created successfully |
| 422 | Validation error |
| 404 | Not found |

````

## Documentation Quality Checklist

- [ ] README has the workspace-bootstrap sections, with Setup, Start, Tests, Known issues, and Documentation map filled in
- [ ] All environment variables documented with defaults
- [ ] Every API endpoint has a curl example
- [ ] Project structure overview is accurate
- [ ] No broken internal links
- [ ] No stale/outdated information
- [ ] CHANGELOG follows Keep a Changelog format
