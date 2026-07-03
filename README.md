# amza-commercial-ai-platform

Commercial operations platform that combines AI and human advisors into a single hybrid sales workflow.

---

## Requirements

- Python 3.12
- Node.js 20
- Docker and Docker Compose

---

## Project structure

```
amza-commercial-ai-platform/
├── backend/          Python 3.12 + FastAPI + SQLAlchemy + Alembic
├── frontend/         Next.js 15 + React 19 + TypeScript + Tailwind CSS
├── docker/           Dockerfiles for each service
├── docs/             Product and engineering documentation
├── specifications/   MVP implementation specifications
├── scripts/          Operational and automation scripts
├── .github/          GitHub Actions CI workflows
├── docker-compose.yml
├── Makefile
└── .env.example
```

---

## Local setup

**1. Copy environment variables**

```bash
cp .env.example .env
```

**2. Install backend dependencies**

```bash
make install-backend
```

**3. Install frontend dependencies**

```bash
make install-frontend
```

**4. Install pre-commit hooks**

```bash
make pre-commit-install
```

---

## Running locally

**Backend** (requires Python 3.12 virtual environment active):

```bash
make backend
```

Runs on `http://localhost:8000`. API docs available at `http://localhost:8000/docs`.

**Frontend:**

```bash
make frontend
```

Runs on `http://localhost:3000`.

**Via Docker Compose:**

```bash
make docker-up
```

---

## Testing

```bash
make test-backend
make test-frontend
make test-e2e
```

---

## Code quality

```bash
make lint
make format
```

---

## Database migrations

```bash
make migrate
```

---

## Architecture

The platform follows Hexagonal Architecture (Ports and Adapters).

```
backend/
├── app/              FastAPI initialization, config, logging
├── core/             Domain: entities, interfaces, value objects, events
├── modules/          Feature modules (opportunities, agents, channels, ...)
├── infrastructure/   Concrete implementations (database, AI, channels, ...)
├── tests/            Unit and integration tests
└── migrations/       Alembic database migrations
```

The domain (`core/`) never depends on infrastructure. All external systems are accessed through provider interfaces.

---

## Documentation

Read order:

1. `docs/product/00_Vision_and_Product_Principles.md`
2. `docs/product/01_Business_Validation.md`
3. `docs/engineering/02_Product_Glossary.md`
4. `docs/engineering/03_Engineering_Principles.md`
5. `docs/engineering/04_Architecture.md`
6. `docs/product/05_Roadmap.md`
7. `docs/product/06_Product_Specification.md`
