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
* Next.js
* TypeScript
* OpenRouter
* Telegram (MVP)
* WhatsApp Cloud API (future)

The system is built around **Opportunities**, not conversations.

An Opportunity represents the central business concept.

Conversations are only one part of an Opportunity.

---

# Documentation Status

Completed documents:

✅ Vision and Product Principles

✅ Business Validation

✅ Product Glossary

✅ Engineering Principles

✅ Architecture

✅ Roadmap

✅ Product Specification

✅ Technology Stack

✅ Domain Model

✅ Persistence Model

These documents are considered the source of truth.

---

# Current Repository Structure

```text
docs/
    engineering/
    product/

specifications/
    MVP/

IMPLEMENTATION_ORDER.md
README.md
PROJECT_STATE.md
```

---

# Current Implementation Stage

The project is still in the architecture phase.

No production code has been generated yet.

The documentation is considered sufficiently mature to begin implementation.

Future development should alternate between:

Specification

↓

Implementation

↓

Review

↓

Validation

↓

Next Specification

No large documentation efforts should be added unless strictly necessary.

---
# Metodologia del proyecto

Fase 1 — Producto
-----------------
Vision
Business
Roadmap
Product Specification

↓

Fase 2 — Ingeniería
-------------------
Glossary
Engineering Principles
Architecture
Technology Stack

↓

Fase 3 — Especificaciones
-------------------------
Cada documento describe UNA implementación.

↓

Fase 4 — Desarrollo
-------------------
Claude Code implementa.

↓

Fase 5 — Revisión
-----------------
Validación manual.

↓

Fase 6 — Commit

↓

Repetir
---

# Naming Decisions

Repository:

amza-commercial-ai-platform

Python package:

amza-commercial-ai-platform

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

# Current MVP Goal

Validate that a hybrid commercial workflow improves business performance by:

* reducing response times;
* reducing repetitive work;
* improving commercial follow-up;
* increasing sales without increasing staff.

---

# Working Methodology

Each specification represents one implementation milestone.

The workflow is always:

1. Read project documentation.
2. Read one specification.
3. Implement only that specification.
4. Validate.
5. Commit.
6. Continue.

Never implement multiple specifications simultaneously.

---

# Next Planned Specification

010_Backend_Foundation.md

Goal:

Create the backend skeleton following the approved architecture without implementing business logic.

---

# Long-Term Goal

Build a reusable Commercial Operations Platform capable of serving multiple organizations while keeping the architecture clean, modular and maintainable.

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

Status:

🟢 Ready to begin implementation.
---

# Completed Specifications

000 Technology Stack

Completed

001 Project Setup

Completed

002 Business Domain Model

Completed

003 Persistence Model

Completed

---

# Current Sprint

Goal:

Backend Foundation

Current Specification:

010_Backend_Foundation.md

Status:

Ready to implement.

---

Decisions Pending

- CRM: Pending

Waiting until MVP validation.

- WhatsApp: Pending

Blocked by Meta approval.

---

# Desicion Frozen

Architecture:
✅ Frozen

Technology Stack:
✅ Frozen

Opportunity Model:
✅ Frozen

Hexagonal:
✅ Frozen

Python:
✅ Frozen

FastAPI:
✅ Frozen

SQLAlchemy:
✅ Frozen

SQLite MVP:
✅ Frozen

Telegram MVP:
✅ Frozen
