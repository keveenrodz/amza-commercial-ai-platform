# amza-commercial-ai-platform

Commercial operations platform that combines AI and human advisors into a single hybrid sales workflow.

---

## Requirements

| Tool | Version | Why |
|---|---|---|
| Python | 3.12 | Required by pyproject.toml. The domain model uses modern typing features. |
| Node.js | 20 | Required by Next.js 15. |
| Docker + Docker Compose | any recent | To run the full stack locally without installing dependencies globally. |

---

## Project structure

```
amza-commercial-ai-platform/
├── backend/          Python 3.12 + FastAPI + SQLAlchemy + Alembic
│   ├── app/          FastAPI initialization, config, logging, lifecycle
│   ├── core/         Domain: entities, interfaces, value objects, events (no external dependencies)
│   ├── modules/      Feature modules organized by domain (opportunities, agents, channels, ...)
│   ├── infrastructure/ Concrete implementations (database, AI, channels, ...)
│   ├── tests/        Unit and integration tests
│   └── migrations/   Alembic database migrations
├── frontend/         Next.js 15 + React 19 + TypeScript + Tailwind CSS
│   ├── app/          Next.js App Router pages and layouts
│   ├── components/   Reusable UI components
│   ├── hooks/        Custom React hooks
│   ├── services/     API client layer (all backend calls go through here)
│   └── types/        Shared TypeScript types
├── docker/           Dockerfiles for each service
├── docs/             Product and engineering documentation
├── specifications/   MVP implementation specifications (one per feature)
├── scripts/          Operational and automation scripts
├── .github/          GitHub Actions CI workflows
├── docker-compose.yml
├── Makefile
└── .env.example
```

---

## First-time setup

### Step 1 — Python 3.12

The project requires Python 3.12. The recommended approach is conda:

```bash
conda create -n amza-commercial-ai-platform python=3.12
conda activate amza-commercial-ai-platform
```

Why conda and not the system Python: Ubuntu 22.04 ships Python 3.10.
The `pyproject.toml` enforces `requires-python = ">=3.12"` and will reject older versions.

Verify:
```bash
python --version   # must show 3.12.x
```

### Step 2 — Environment variables

```bash
cp .env.example .env
```

The `.env` file is required by both the backend (Pydantic Settings reads it on startup)
and Docker Compose (`env_file: .env`). Without it, both will fail to start.

The file contains empty keys for `OPENROUTER_API_KEY` and `TELEGRAM_BOT_TOKEN`.
These are not needed for project setup — they will be required when AI and Telegram
integrations are implemented in later specifications.

### Step 3 — Backend dependencies

```bash
cd backend
pip install -e ".[dev]"
```

The `-e` flag installs the package in editable mode, meaning Python resolves imports
directly from the source directory. This avoids having to reinstall after every code change.

`[dev]` installs development tools: Ruff (linter), MyPy (type checker),
Pytest (tests), and pre-commit.

### Step 4 — Frontend dependencies

```bash
cd frontend
npm install
```

This restores `node_modules` from `package-lock.json`.
All packages are already pinned — no version surprises.

### Step 5 — Pre-commit hooks

```bash
cd /path/to/project-root
pre-commit install
```

This installs git hooks that run Ruff automatically before every commit.
Why: prevents committing code with lint errors or wrong formatting.

---

## Running locally (without Docker)

Both services need to run in separate terminals.

**Terminal 1 — Backend:**

```bash
conda activate amza-commercial-ai-platform
cd backend
python main.py
```

Expected output:
```
Started server process [...]
Waiting for application startup.
{"event": "application.started", "level": "info", "timestamp": "..."}
Application startup complete.
Uvicorn running on http://0.0.0.0:8000
```

The logging output is JSON in production mode and human-readable in debug mode (`DEBUG=true` in `.env`).

Verify it's working:
```bash
curl http://localhost:8000/docs -o /dev/null -w "%{http_code}\n"   # must return 200
```

`http://localhost:8000/docs` opens the Swagger UI with the full API documentation.
`http://localhost:8000/openapi.json` returns the raw OpenAPI spec.

**Terminal 2 — Frontend:**

```bash
cd frontend
npm run dev
```

Open `http://localhost:3000`. You will see the default Next.js starter page — this is
correct. No business pages exist yet; they will be added in later specifications.

Note: if you see a React hydration warning in the browser console, check whether a
browser extension (e.g. Scribe, Grammarly, LastPass) is modifying the HTML before
React loads. Open an incognito window to confirm the app works without extensions.

---

## Running with Docker Compose

Docker Compose builds and runs both services in isolated containers.
Use this to validate the full deployment before shipping a feature.

```bash
# Build images (required once, and after any Dockerfile change)
docker compose build

# Start both services in background
docker compose up -d

# Verify both are running and ports are exposed
docker compose ps

# View logs
docker compose logs -f backend
docker compose logs -f frontend

# Stop everything
docker compose down
```

Expected `docker compose ps` output:
```
NAME          ...   PORTS
backend-1     ...   0.0.0.0:8000->8000/tcp
frontend-1    ...   0.0.0.0:3000->3000/tcp
```

Known issue: if the backend process is already running locally on port 8000 and you
run `docker compose up -d`, Docker will fail to bind port 8000 silently and start
the container without the port mapping. Always run `docker compose down` before
restarting, and make sure no local process is using port 8000:

```bash
kill $(lsof -t -i:8000) 2>/dev/null || true
docker compose down
docker compose up -d
```

---

## Code quality

```bash
# Backend lint (Ruff) and type check (MyPy)
make lint-backend

# Frontend lint (ESLint)
make lint-frontend

# Format backend code
make format-backend

# Format frontend code
make format-frontend
```

Why both Ruff and MyPy: Ruff catches style, imports, and common bugs fast (milliseconds).
MyPy verifies that all types are consistent across the codebase — it catches a different
class of errors that Ruff cannot.

---

## Tests

```bash
# Backend
make test-backend

# Frontend (unit tests with Vitest)
make test-frontend

# Frontend end-to-end (Playwright, requires the app running)
make test-e2e
```

At this stage `pytest` will report `collected 0 items` and Vitest will report
`No test files found` — both exit with code 0. This is correct: the test frameworks
are configured and ready; functional tests will be added as each feature is implemented.

---

## Database migrations

```bash
# Apply all pending migrations
make migrate

# Create a new migration after changing a model
cd backend && alembic revision --autogenerate -m "description"
```

Migrations are managed with Alembic. Every schema change must go through a migration
file — never modify the database directly. This ensures every environment (local,
staging, production) stays in sync.

---

## Makefile reference

| Command | What it does |
|---|---|
| `make install` | Install backend + frontend dependencies |
| `make backend` | Start backend locally |
| `make frontend` | Start frontend locally |
| `make test` | Run all tests |
| `make lint` | Run all linters |
| `make format` | Format all code |
| `make docker-build` | Build Docker images |
| `make docker-up` | Start Docker Compose |
| `make docker-down` | Stop Docker Compose |
| `make migrate` | Apply database migrations |
| `make pre-commit-install` | Install git pre-commit hooks |

---

## Architecture

The platform follows Hexagonal Architecture (Ports and Adapters).

The core rule: `core/` never imports from `infrastructure/`, `modules/`, or any
external library (FastAPI, SQLAlchemy, Telegram, OpenRouter). Everything external
is accessed through interfaces defined in `core/interfaces/`.

This means:
- Swapping SQLite for PostgreSQL requires changing only `infrastructure/database/`.
- Adding WhatsApp requires adding only `infrastructure/channels/whatsapp/`.
- The business logic in `core/` never needs to change for infrastructure reasons.

```
Request
  └── FastAPI router (modules/*/api/)
        └── Service (modules/*/services/)
              └── Repository interface (core/interfaces/)
                    └── SQLAlchemy implementation (infrastructure/repositories/)
```

---

## Documentation reading order

1. `docs/product/00_Vision_and_Product_Principles.md`
2. `docs/product/01_Business_Validation.md`
3. `docs/engineering/02_Product_Glossary.md`
4. `docs/engineering/03_Engineering_Principles.md`
5. `docs/engineering/04_Architecture.md`
6. `docs/product/05_Roadmap.md`
7. `docs/product/06_Product_Specification.md`

Each `specifications/MVP/` file describes one implementation milestone.
Never implement more than one specification at a time.
