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
| 003 Persistence Model | ✅ | ✅ | ✅ | ✅ |
| 004 Repository Implementations | ✅ | ✅ | ✅ | ✅ |
| 005 Application Services | ✅ | ✅ | ✅ | ✅ |
| 006 Conversation Memory & Providers | ✅ | ✅ | ✅ | ✅ |
| 007 API Layer | ✅ | ✅ | ✅ | ✅ |
| 008 (por definir) | ❌ | — | — | — |

---

# Current State

**What exists in the repository:**

* Complete project skeleton (backend + frontend + Docker + CI)
* FastAPI app initialized and running on port 8000
* Ruff + MyPy + pre-commit configured (86 source files passing clean)
* Vitest + Playwright configured
* Docker Compose working (backend:8000, frontend:3000)
* GitHub Actions CI configured
* Complete domain layer in `core/` (spec 002)
* Complete persistence layer in `infrastructure/database/` and `modules/*/models/` (spec 003)
* First Alembic migration applied — `data/amza.db` created with all 7 tables

**Persistence layer details (spec 003):**

* `infrastructure/database/base.py` — `DeclarativeBase`
* `infrastructure/database/engine.py` — `AsyncEngine` (sqlite+aiosqlite URL transform)
* `infrastructure/database/session.py` — `AsyncSessionFactory` + `get_session()` dependency
* `modules/configuration/models/organization.py` — `OrganizationModel`
* `modules/opportunities/models/contact.py` — `ContactModel` (unique: external_id + channel_type + org)
* `modules/opportunities/models/opportunity.py` — `OpportunityModel`
* `modules/opportunities/models/conversation.py` — `ConversationModel`
* `modules/opportunities/models/message.py` — `MessageModel` (campo: `extra_metadata` → columna DB: `metadata`)
* `modules/users/models/internal_user.py` — `InternalUserModel`
* `modules/agents/models/agent.py` — `AgentModel`
* `migrations/versions/0001_initial_schema.py` — aplicada con `alembic upgrade head`

**Repository layer (spec 004):**

* `modules/opportunities/repositories/` — OpportunityRepository, ContactRepository, ConversationRepository, MessageRepository
* `modules/configuration/repositories/organization.py` — OrganizationRepository
* `modules/users/repositories/internal_user.py` — InternalUserRepository
* `modules/agents/repositories/agent.py` — AgentRepository
* `infrastructure/database/unit_of_work.py` — SQLAlchemyUnitOfWork
* Migración `0002_fix_entity_model_alignment.py` aplicada

**Application Services (spec 005):**

* `app/use_cases/receive_incoming_message.py` — `ReceiveIncomingMessageUseCase` + `IncomingMessageInput`
* `app/use_cases/assign_to_advisor.py` — `AssignToAdvisorUseCase`
* `app/use_cases/return_to_ai.py` — `ReturnToAIUseCase`
* `app/use_cases/get_conversation_history.py` — `GetConversationHistoryUseCase` + `ConversationHistory`
* `app/exceptions.py` — handlers HTTP para todas las excepciones de dominio (404/422/400)
* 3 excepciones nuevas en `core/exceptions/domain.py`: `OrganizationSlugNotFoundError`, `InternalUserNotFoundError`, `NoActiveAgentError`
* `_build_context()` en `ReceiveIncomingMessageUseCase` — extension point documentado para el resumen por inactividad (spec 006)

**Conversation Memory & Providers (spec 006):**

* `core/interfaces/providers.py` — `AIProvider.generate(context, agent_id)` ahora recibe
  `ConversationContext` (resumen + mensajes recientes) en vez de `list[Message]` crudo; nuevo
  `AIProvider.complete(request: CompletionRequest)` como primitiva de texto libre, sin atarse a
  ningún `Agent` — usada por tareas de IA que no son "conversar" (hoy: resumir)
* Principio arquitectónico frozen: los servicios de aplicación deciden qué tarea de IA ejecutar;
  `AIProvider` únicamente ejecuta inferencias, nunca contiene lógica de negocio
* `core/entities/conversation_summary.py` — `ConversationSummary`, entidad propia (no
  `Message(SYSTEM)`), append-only y versionada (`version` monótono, nunca UPDATE)
* `modules/memory/` — `ConversationSummaryModel` + `SQLAlchemyConversationSummaryRepository`
* `MessageRepository` gana `list_since`/`count_since` (cursor `after` exclusivo)
* `app/services/conversation_context_assembler.py` — `ConversationContextAssembler`: ensambla
  contexto de respuesta (últimos `working_memory_size` mensajes + último resumen)
* `app/services/conversation_summarization_service.py` — `ConversationSummarizationService`:
  sabe generar un resumen, nunca decide cuándo — esa decisión vive en cada caller
* `ReceiveIncomingMessageUseCase` dispara resumen por umbral (`summary_trigger_messages`,
  default 30) en una segunda transacción post-commit, best-effort (try/except, sin
  `asyncio.create_task`)
* `AssignToAdvisorUseCase`/`ReturnToAIUseCase` disparan resumen incondicionalmente al cambiar de
  modo (evento de negocio, no de tamaño)
* `infrastructure/ai/openrouter.py` — `OpenRouterAIProvider` (primera implementación de
  `AIProvider`); `infrastructure/channels/telegram.py` — `TelegramChannelProvider` (primera
  implementación de `ChannelProvider`)
* Migración `0003_add_conversation_summaries.py` — nueva tabla + reemplaza los 2 índices simples
  de `messages` por un compuesto `(conversation_id, sent_at)`
* ADR documentado en el spec (no bloqueante, a evaluar si el acoplamiento molesta en la práctica):
  mover la resolución de `Agent`/`Contact` fuera de los providers hacia los servicios de
  aplicación, para que `OpenRouterAIProvider`/`TelegramChannelProvider` no dependan de
  repositorios

**API Layer (spec 007):**

* `app/api/dto/telegram.py` — `TelegramUpdate`/`TelegramMessage`/`TelegramUser`/`TelegramChat`
  (modelan solo lo que el MVP necesita, `extra="ignore"`); `app/api/dto/opportunity.py` —
  `OpportunityResponse`/`MessageResponse`/`ConversationHistoryResponse` con `from_domain()`,
  `AssignAdvisorRequest`. Tres capas separadas: Request/Response HTTP → Input del caso de uso →
  entidad de dominio, nunca se reutiliza una para otra
* `app/api/routers/telegram_webhook.py` — `POST /webhooks/telegram/{organization_slug}`. Siempre
  200 salvo secreto inválido (401): body malformado, tipo de update no soportado
  (`edited_message`, `callback_query`, etc.), o fallo de procesamiento (org inexistente, agente no
  configurado, error del `AIProvider`) — todos se loguean y absorben, nunca se deja que Telegram
  reintente. Decisión de negocio documentada: se privilegia evitar procesamiento duplicado sobre
  garantizar la entrega ante fallos de infraestructura (sin cola de reintentos en el MVP)
* `app/api/routers/opportunities.py` — REST anidado bajo `/organizations/{slug}/opportunities/...`
  (recurso en la URL, no query param). `organization_slug` se ignora intencionalmente (comentado
  en código) en las rutas por-ID — `opportunity_id` (UUID) ya es suficiente identificador en MVP
* `app/api/routers/health.py` — `GET /health` (liveness) y `GET /health/ready` (DB + 
  `AIProvider.health()` + `ChannelProvider.health()`, con detalle por dependencia)
* `app/use_cases/list_open_opportunities.py` — `ListOpenOpportunitiesUseCase`, única lógica nueva
  de este spec (para que el router de listado no toque `OpportunityRepository` directo)
* `app/security.py` — `verify_telegram_secret` (nuevo setting `telegram_webhook_secret`)
* `app/dependencies.py` — cableado completo, providers/servicios/use cases vía `@lru_cache`
  (lazy, no construcción eager al importar)
* `app/config.py` corregido: `.env` se resuelve contra la raíz del repo (ruta absoluta desde
  `__file__`), no contra el cwd — bug preexistente desde spec 001, encontrado al validar
  credenciales reales
* Principio: "un bot pertenece a una organización, no al revés" — para MVP resuelto por
  configuración operativa (URL del webhook), no por modelo de datos
* Smoke-tested con credenciales reales: `@AmzaCommercialBot` (Telegram) y OpenRouter responden
  correctamente; los 4 casos del webhook (sin secreto→401, tipo no soportado→200, fallo de
  negocio→200 sin 404, endpoint REST normal→404 sí propaga) verificados con `curl`

**Validación end-to-end real (post spec 007) — camino feliz confirmado con Telegram real:**

* Seed de datos: `backend/scripts/seed_dev_data.py` — crea `Organization` (`amza-empaques`) +
  `Agent` (`openai/gpt-4.1-nano`, elegido tras comparar costo real contra un modelo de
  razonamiento — ver "Decisiones de esta validación" abajo). Idempotente
* `backend/scripts/register_telegram_webhook.py <url>` — registra el webhook contra una URL
  pública (ngrok en desarrollo local) sin copiar el bot token/secreto a mano
* `backend/scripts/inspect_conversations.sql` — dos queries de solo lectura para revisar
  contactos y conversaciones completas directo en la BD (más confiable que los logs para
  confirmar que algo realmente se persistió, no solo que el webhook devolvió 200)
* **Bug real encontrado y corregido:** `ChannelProvider.send()` resolvía `Contact` vía una sesión
  de BD separada de la transacción del use case — al escribir un contacto nuevo por primera vez,
  esa sesión no veía la fila todavía sin commit, lanzaba `ContactNotFoundError`, y la transacción
  completa (contacto, oportunidad, conversación, mensajes) hacía rollback. Cero mensajes al
  cliente, sin error visible salvo el log. Fix: `send()` ahora recibe el `Contact` ya resuelto por
  el use case — el provider queda completamente stateless (`core/interfaces/providers.py`,
  `infrastructure/channels/telegram.py`, `app/use_cases/receive_incoming_message.py`)
* Fix relacionado: `database_url` con ruta sqlite relativa fallaba ("unable to open database
  file") al correr scripts desde un directorio distinto a `backend/` — mismo patrón que el bug de
  `.env` ya corregido, resuelto igual (resolver contra `backend/`, no contra el cwd)
* **Confirmado con mensajes reales de dos contactos de Telegram distintos**, con respuestas
  coherentes generadas por el agente y persistidas correctamente en `messages`

**Decisiones de esta validación:**

* `openai/gpt-4.1-nano` elegido sobre `deepseek/deepseek-v4-flash` para el agente: aunque
  `deepseek` tiene tarifa por token más barata, es un modelo de razonamiento que generó ~110
  tokens ocultos de "pensamiento" por respuesta — costo real medido ~2.3x mayor para la misma
  calidad de respuesta en este caso de uso (mensajes cortos de atención al cliente). El campo
  `usage.cost` de la respuesta de OpenRouter es la fuente de verdad para comparar costo real, no
  la tabla de precios por token
* Telegram Bot API no entrega número de teléfono del usuario (solo lo comparte si el usuario usa
  un botón explícito de "compartir contacto", no implementado). `Contact.phone_number` existe en
  la entidad pero queda vacío para contactos de Telegram
* Gap identificado, no corregido (pendiente de decisión de producto): `TelegramUser.username` se
  recibe en el DTO del webhook pero se descarta — nunca se guarda en `Contact`. Hoy solo se
  persiste `first_name` (como `display_name`) y `chat_id` (como `external_id`)

**What does NOT exist yet:**

* Captura de `username` de Telegram (gap identificado arriba, decisión de producto pendiente)
* Frontend pages con lógica de negocio

---

# Next Step

**Definir spec 008.**

La plataforma está operable de punta a punta y **validada con mensajes reales**: Telegram →
webhook → use cases → OpenRouter/Telegram providers → respuesta al cliente, más endpoints de
gestión para que un asesor humano tome/devuelva oportunidades.

La hoja de ruta de evoluciones futuras (Memory Extraction, Knowledge Base, AI Task Framework,
Embedding Search, Background Jobs, Model Routing, Prompt Management, Context Optimization) queda
registrada en la sección "Future Evolution" de `006_Conversation_Memory_and_Providers.md` —
deliberadamente fuera de alcance hasta que exista evidencia de negocio, no antes.

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

🟢 Plataforma operable de punta a punta, validada con mensajes reales de Telegram (dos contactos
distintos, respuestas coherentes del agente, todo persistido correctamente). Un bug real
encontrado y corregido en el proceso (`ChannelProvider.send()`, ver detalle arriba) — committed
(52a5359). Siguiente: definir spec 008.
