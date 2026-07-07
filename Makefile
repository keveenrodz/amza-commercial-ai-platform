.PHONY: install install-backend install-frontend \
        backend frontend \
        test test-backend test-frontend test-e2e \
        lint lint-backend lint-frontend \
        format format-backend format-frontend \
        docker-up docker-down docker-build \
        migrate pre-commit-install

# ── Install ────────────────────────────────────────────────────────────────────

install: install-backend install-frontend

install-backend:
	cd backend && pip install -e ".[dev]"

install-frontend:
	cd frontend && npm install

# ── Run ───────────────────────────────────────────────────────────────────────

backend:
	cd backend && python main.py

frontend:
	cd frontend && npm run dev

# ── Test ──────────────────────────────────────────────────────────────────────

test: test-backend test-frontend

test-backend:
	cd backend && pytest

test-frontend:
	cd frontend && npm run test

test-e2e:
	cd frontend && npm run test:e2e

# ── Lint ──────────────────────────────────────────────────────────────────────

lint: lint-backend lint-frontend

lint-backend:
	cd backend && ruff check . && mypy app core infrastructure modules

lint-frontend:
	cd frontend && npm run lint

# ── Format ────────────────────────────────────────────────────────────────────

format: format-backend format-frontend

format-backend:
	cd backend && ruff format .

format-frontend:
	cd frontend && npm run format

# ── Docker ────────────────────────────────────────────────────────────────────

docker-build:
	docker compose build

docker-up:
	docker compose up -d

docker-down:
	docker compose down

# ── Database ──────────────────────────────────────────────────────────────────

migrate:
	cd backend && alembic upgrade head

# ── Tooling ───────────────────────────────────────────────────────────────────

pre-commit-install:
	pre-commit install
