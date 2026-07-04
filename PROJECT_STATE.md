# PROJECT_STATE.md

# Project State

**Project Name**

amza-commercial-ai-platform

---

# Project Purpose

amza-commercial-ai-platform is an AI-assisted commercial operations platform designed to help small and medium-sized businesses increase their sales capacity by combining Artificial Intelligence and human advisors into a single commercial workflow.

The platform is not a chatbot.

It is not a CRM replacement.

It is a Commercial Operations Platform where AI automates repetitive work while humans focus on high-value commercial activities.

The first implementation will be developed for **Amza Empaques**, but the platform is designed to become reusable for other companies with similar needs.

---

# Current Development Philosophy

The project follows four fundamental principles.

1. Business first.
2. Architecture before implementation.
3. Simplicity over unnecessary complexity.
4. Incremental development.

Every technical decision must support the business, never the opposite.

---

# Current Architecture

The platform is based on:

* Python 3.12
* FastAPI
* Hexagonal Architecture
* Domain Driven Design (lightweight)
* SQLAlchemy 2.x
* SQLite (MVP)
* PostgreSQL (future)
* Next.js 15
* TypeScript
* OpenRouter
* Telegram (MVP)
* WhatsApp Cloud API (future)

The system is built around **Opportunities**, not conversations.

An Opportunity represents the central business concept.

Conversations are only one part of an Opportunity.

---

# Documentation Status

All documentation is complete and frozen.

✅ Vision and Product Principles
✅ Business Validation
✅ Product Glossary
✅ Engineering Principles
✅ Architecture
✅ Roadmap
✅ Product Specification
✅ Technology Stack (000)

These documents are the source of truth.

They must NOT be modified unless a formal architecture decision is made.

---

# Specifications Status

| Spec | Document | Implementation | Validated | Committed |
|---|---|---|---|---|
| 000 Technology Stack | ✅ | N/A | N/A | ✅ |
| 001 Project Setup | ✅ | ✅ | ✅ | ✅ |
| 002 Domain Model | ✅ | ✅ | ✅ | ✅ |
| 003 Persistence Model | ✅ | ✅ | ✅ | — |

---

# Current State

**What exists in the repository:**

* Complete project skeleton (backend + frontend + Docker + CI)
* FastAPI app initialized and running
* SQLAlchemy + Alembic configured
* Ruff + MyPy + pre-commit configured
* Vitest + Playwright configured
* Docker Compose working
* All tools validated locally

**What does NOT exist yet:**

* Any business logic
* Any API endpoints
* Any frontend pages

---

# Next Step

**Write and implement specification 004 (next to be defined).**

Spec 003 is fully implemented:
- 7 ORM models across `modules/*/models/`
- `infrastructure/database/` (base, engine, session)
- Migration `0001_initial_schema.py` applied to `data/amza.db`
- 46 source files passing `ruff check .` and `mypy app core infrastructure`

---

# Working Methodology

Each specification represents one implementation milestone.

The workflow is always:

1. Read `PROJECT_STATE.md` and `IMPLEMENTATION_ORDER.md`.
2. Read the current specification.
3. Implement only that specification.
4. Validate (run lint, type check, tests).
5. Commit.
6. Update `PROJECT_STATE.md`.
7. Continue with the next specification.

Never implement multiple specifications simultaneously.

Never write code not covered by the current specification.

---

# Naming Decisions

Repository:

amza-commercial-ai-platform

Python package:

amza-commercial-ai-platform

Conda environment:

amza-commercial-ai-platform (Python 3.12.13)

Architecture:

Hexagonal

Main Business Entity:

Opportunity

Primary communication model:

Hybrid AI + Human

---

# Channels

Current implementation:

Telegram

Future implementations:

* WhatsApp Cloud API
* Instagram
* Facebook Messenger

Telegram exists only as the initial development adapter.

The platform itself is channel-independent.

---

# AI Philosophy

Artificial Intelligence is an assistant.

It is not the product.

It should automate repetitive work and transfer conversations to human advisors whenever business judgment is required.

The customer should never notice when the conversation changes between AI and a human.

---

# Frozen Decisions

These decisions must not be changed during the MVP without explicit approval.

Architecture:
✅ Hexagonal (Ports and Adapters)

Technology Stack:
✅ Frozen (see 000_Technology_Stack.md)

Domain Model:
✅ Frozen (see 002_Domain_Model.md)

Opportunity as aggregate root:
✅ Frozen

Python version:
✅ 3.12

FastAPI:
✅ Frozen

SQLAlchemy 2.x:
✅ Frozen

SQLite for MVP:
✅ Frozen

Telegram for MVP:
✅ Frozen

---

# Decisions Pending

CRM integration: pending until MVP validation.

WhatsApp: blocked by Meta approval process.

---

# Authority Order

If documentation conflicts, the following priority applies:

1. Vision
2. Product Glossary
3. Engineering Principles
4. Architecture
5. Product Specification
6. Current Specification

---

# Project Status

🟡 In progress — 003 complete, pending commit and next spec.
