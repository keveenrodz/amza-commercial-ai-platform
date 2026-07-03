# MVP Specification – 000 Technology Stack

## Objetivo

Este documento define el stack tecnológico oficial aprobado para el MVP.

Su propósito es eliminar cualquier ambigüedad técnica durante el desarrollo.

Las tecnologías aquí definidas constituyen decisiones de arquitectura.

No deberán cambiarse durante el MVP salvo que exista una razón técnica de peso y la decisión quede documentada.

Claude Code y cualquier otro asistente de programación deberán utilizar exclusivamente las tecnologías definidas en este documento.

---

# Principios

El stack tecnológico deberá priorizar:

* estabilidad;
* mantenibilidad;
* productividad;
* comunidad activa;
* documentación;
* facilidad de evolución.

Nunca se elegirán tecnologías únicamente por ser nuevas o populares.

---

# Backend

## Lenguaje

Python 3.12

---

## Framework Web

FastAPI

---

## Validación

Pydantic v2

---

## Configuración

Pydantic Settings

---

## ORM

SQLAlchemy 2.x

---

## Migraciones

Alembic

---

## Arquitectura

Hexagonal Architecture

Domain Driven Design (ligero)

Repository Pattern

Unit of Work

Dependency Injection

---

# Base de Datos

## MVP

SQLite

---

## Futuro

PostgreSQL

La migración deberá requerir cambios mínimos.

---

# Inteligencia Artificial

Proveedor oficial:

OpenRouter

La selección del modelo se realizará mediante configuración.

El Core nunca dependerá de un modelo específico.

---

# Canales Conversacionales

Canal inicial:

Telegram

Canales futuros:

* WhatsApp Cloud API
* Instagram
* Facebook Messenger

La incorporación de nuevos canales deberá realizarse mediante nuevos Providers.

---

# Frontend

Framework:

Next.js 15

Lenguaje:

TypeScript

UI:

React 19

Tailwind CSS

shadcn/ui

Gestión de estado remoto:

TanStack Query

Formularios:

React Hook Form

Validación:

Zod

---

# Testing

Backend:

Pytest

pytest-asyncio

httpx

Frontend:

Vitest

Playwright

---

# Calidad de Código

Python:

Ruff

MyPy

Frontend:

ESLint

Prettier

Todos los repositorios deberán utilizar pre-commit.

---

# Logging

Structlog

Todo evento importante deberá registrarse mediante logging estructurado.

Nunca utilizar print() en código productivo.

---

# Documentación

OpenAPI

Swagger UI

ReDoc

La documentación deberá generarse automáticamente desde FastAPI.

---

# Contenedores

Docker

Docker Compose

Todo el proyecto deberá poder ejecutarse localmente mediante un único comando.

---

# Integración Continua

GitHub Actions

Cada Pull Request deberá ejecutar como mínimo:

* lint;
* pruebas;
* validaciones básicas.

---

# Integraciones del MVP

OpenRouter

Telegram

SIIGO (según disponibilidad de APIs necesarias)

---

# Integraciones futuras

WhatsApp Cloud API

CRM

Correo electrónico

Calendario

---

# Tecnologías explícitamente fuera del MVP

No utilizar durante el MVP:

* Redis
* Celery
* RabbitMQ
* Kafka
* RAG
* Embeddings
* Vector Databases
* LangGraph
* CrewAI
* Temporal
* MCP
* Kubernetes
* Microservicios

Estas tecnologías únicamente podrán incorporarse cuando exista una necesidad real y estén contempladas en el Roadmap.

---

# Principio final

El objetivo del MVP no es utilizar el stack tecnológico más moderno.

El objetivo es construir una plataforma sólida, mantenible y preparada para evolucionar durante muchos años sin requerir reescrituras importantes.

