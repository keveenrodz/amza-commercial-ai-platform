# PROJECT_STATE.md

**Para correr y probar todo lo construido (Telegram + Advisor Workspace), ver
`docs/ops/running_the_advisor_workspace.md`. Para dar/quitar acceso a un `InternalUser`, ver
`docs/ops/onboarding_internal_users.md`.** Este archivo (`PROJECT_STATE.md`) es "qué existe y qué
sigue", no un manual operativo — no dupliques instrucciones de esos dos documentos aquí.

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
| 008 Security & Identity | ✅ | ✅ | ✅ | ✅ |
| 009 Advisor Workspace | ✅ | ✅ | ✅ | ✅ |
| 010 Advisor Reply | ✅ | ✅ | ✅ | ✅ |
| 011 Navigation Shell & Theming | ✅ | ✅ | ✅ | ✅ |
| 012 Chat Panel Redesign | ✅ | ✅ | ✅ | ✅ |
| 013 Contact Enrichment & Follow-ups | ✅ | ✅ | ✅ | ✅ |
| 013b Design System Alignment | ✅ | ✅ | ✅ | ✅ |
| 014 Admin Governance & Access Control | ✅ | ✅ | ✅ | ✅ |
| 015 Channel Provider Routing | ✅ | ✅ | ✅ | ✅ |
| 016 WhatsApp Integration (Evolution API) | ✅ | ✅ | ✅ | ✅ |
| 017 Admin Panel | ✅ | ✅ | ✅ | ✅ |

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

**What does NOT exist yet (previo a spec 008):**

* Captura de `username` de Telegram (gap identificado arriba, decisión de producto pendiente)
* Frontend pages con lógica de negocio
* Autenticación/autorización — `/organizations/*` estaba completamente abierto

**Security & Identity (spec 008):**

* Hallazgo que motivó el spec: auditoría real confirmó cero autenticación en toda la API, cero
  tests en 7 specs previos, sin forma de crear `Organization`/`InternalUser` vía la aplicación
  (solo scripts de ops), y el producto ya describe al Advisor como actor central sin que el
  software tuviera manera de representarlo
* Principio arquitectónico: *"Authentication never creates identities"* — autenticarse con
  Google prueba que controlas un email, no otorga acceso. Solo un `InternalUser` **activo
  preexistente** lo hace. Sin registro público, sin auto-provisioning — es el único control de
  acceso real del sistema (no hay restricción de dominio posible, el MVP acepta cualquier cuenta
  de Google)
* `core/interfaces/auth.py` — `AuthProvider` Protocol + `AuthenticatedIdentity` (incluye
  `provider` para auditoría). Justificado como Protocol bajo la regla post-spec-006: Google ahora,
  Microsoft ya es un roadmap comprometido, no especulativo
* `infrastructure/auth/google.py` — `GoogleOAuthProvider`. Sin `authlib`: `httpx` + `PyJWT`
  (`PyJWKClient`) bastan para Authorization Code + verificación OIDC (`issuer`/`audience`/
  `email_verified`). Sin PKCE — cliente confidencial, esa protección es para clientes públicos
* `app/security.py` — JWT propio (`PyJWT`, no `python-jose`, historial de CVEs), 24h sin refresh
  token. `get_current_user()` **consulta la BD en cada request** (no solo los claims del JWT) —
  decisión revisada explícitamente: el costo es insignificante a esta escala, y evita hasta 24h
  de acceso con privilegios viejos tras desactivar o cambiar el rol de alguien. `require_role()`
  construido, sin uso real todavía (ningún endpoint hoy distingue Advisor de Administrator)
  cookie `HttpOnly; SameSite=Lax; Secure` (deshabilitado solo si `settings.debug`)
* `app/use_cases/authenticate_with_provider.py` — `AuthenticateUseCase`, genérico sobre
  `AuthProvider` (misma clase sirve para Google y, más adelante, Microsoft). Loguea
  `auth.access_denied` y `auth.login_success` como eventos de auditoría, no logs técnicos
* `core/interfaces/repositories.py` — `InternalUserRepository` gana `get_by_email()`/`save()`.
  Email único **global** (no por org, ya existía `UniqueConstraint` desde spec 001) y
  case-insensitive (normalizado a minúsculas en el repositorio, sin migración nueva)
* `app/api/routers/auth.py` — `GET /auth/google/login`, `GET /auth/google/callback` (con `state`
  de un solo uso, en memoria, consumido al validar), `GET /auth/me`
* `/organizations/*` (spec 007) protegido con `Depends(get_current_user)` a nivel de router;
  `/webhooks/*` y `/health*` siguen públicos
* `scripts/create_user.py` — bootstrap genérico (Advisor o Administrator, mismo comando, sin
  contraseña que gestionar)
* **Primera suite de tests del proyecto** (`tests/test_security_and_identity.py` +
  `tests/conftest.py`) — cubre los 6 escenarios de validación con un `AuthProvider` fake (nunca
  llama a Google real). Nueva regla formal en `03_Engineering_Principles.md`: toda spec nueva
  debe incluir tests de lo que introduce
* **Validado también manualmente con Google OAuth real**, dos cuentas reales
  (`keveenrodriguez@gmail.com` administrator, `krodriguez@stratio.com` advisor): login completo,
  `/auth/me` correcto, `/organizations/*` 401 sin sesión y funcional con sesión válida,
  desactivación en caliente confirmada — pierde acceso de inmediato en `/auth/me` **y** en el
  endpoint de negocio real, sin esperar a que expire el JWT

**Advisor Workspace (spec 009):**

* Primera interfaz de usuario real del proyecto. No es un CRM: login con Google → lista de
  oportunidades (3 pestañas: Sin asignar / Mías / Todas) → historial de conversación → Tomar /
  Devolver a IA. Nada de reportes, configuración, ni gestión de usuarios (sigue siendo
  `create_user.py`)
* **Principio arquitectónico**: el navegador se comunica exclusivamente con Next.js — Next.js es
  el único consumidor HTTP del backend (Backend-for-Frontend). `frontend/next.config.ts` hace
  proxy puro (`rewrites()`) de `/api/*` hacia FastAPI; el navegador nunca conoce la URL real del
  backend, cero `CORSMiddleware`
* Corrección de contrato, no feature nueva: `OpportunityResponse.assigned_advisor_id` y
  `CurrentUserResponse.organization_slug` — ambos DTOs estaban incompletos, no es que el frontend
  "necesitara algo extra"
* **Detalle crítico encontrado durante implementación**: `GOOGLE_REDIRECT_URI` debe apuntar al
  proxy de Next.js (`:3000/api/auth/google/callback`), nunca directo al backend (`:8000/...`) — si
  no, la cookie de sesión queda con el origen equivocado y nunca viaja en los `fetch("/api/...")`
  reales del frontend. Cambiado también en Google Cloud Console
  Ver `docs/ops/onboarding_internal_users.md` si hace falta recordar cómo se actualiza esto
* `POST /auth/logout` agregado — faltaba en el flujo original, un workspace real lo necesita
* React Query como única fuente de datos del cliente (`useQuery`/`useMutation`, nunca
  `useEffect`+`fetch` directo); estado derivado siempre `.filter()`, nunca `useState` propio
* Primer test e2e del proyecto (Playwright, `frontend/tests/e2e/`) — intercepta `/api/*` a nivel
  de navegador en vez de requerir backend+Google reales; la lógica de auth ya está probada a
  fondo en `tests/test_security_and_identity.py` (backend), este e2e cubre lo que esos tests no
  pueden: que el frontend consuma el contrato correctamente
* **Dos bugs reales encontrados en validación manual, corregidos:**
  1. `/auth/logout` respondía `200` con body vacío; `apiFetch()` del frontend siempre intenta
     `.json()` salvo `204` — un `200` vacío rompía ese parseo y la mutación fallaba en silencio
     antes de llegar a `onSuccess` (el botón "Cerrar sesión" no hacía nada visible). Fix en ambos
     lados: el backend ahora siempre responde JSON en 200, y `apiFetch()` ya no asume que todo 200
     trae body
  2. Al Tomar/Devolver, el botón mostraba por un instante el estado del *otro* lado antes de
     navegar — causa: `invalidateQueries` sobre una query sin observador activo (la lista, mientras
     se está en la página de detalle) solo marca la caché como vieja, el refetch de verdad ocurre
     al volver a montar `/opportunities`, mostrando el dato viejo un instante antes de refrescar.
     Fix: `removeQueries` en vez de `invalidateQueries` — sin dato viejo que mostrar, solo loading
     normal
* Validado manualmente de punta a punta: login real con Google, las tres pestañas, tomar/devolver
  sin parpadeo, logout funcional

**Advisor Reply (spec 010):**

* Gap encontrado *antes* de arrancar el piloto con Amza Empaques (no una feature planeada desde
  009): el Advisor Workspace dejaba tomar y devolver una conversación, pero un asesor no tenía
  ninguna forma de escribirle al cliente — el workspace era de solo lectura para el humano
* Regla de negocio: un asesor solo puede enviar un mensaje manual si la oportunidad está en modo
  `HUMAN` **y** asignada a ese asesor específico. Un solo chequeo de dominio cubre los dos casos
  (`opportunity.assigned_advisor_id != advisor_id`) — `Opportunity.assign_to_advisor()`/
  `return_to_ai()` siempre fijan/limpian `attention_mode` y `assigned_advisor_id` juntos, así que
  ese único campo basta sin necesitar dos excepciones
* `core/enums/message.py` — nuevo `MessageRole.ADVISOR`; `SendAdvisorReplyUseCase`
  (`app/use_cases/send_advisor_reply.py`) — persiste el mensaje y lo entrega por
  `ChannelProvider.send()` en la misma transacción (mismo patrón que
  `ReceiveIncomingMessageUseCase`, spec 006); nuevo endpoint
  `POST /organizations/{slug}/opportunities/{id}/messages`
* Sin resumen incondicional en este caso de uso — a diferencia de tomar/devolver, un mensaje
  individual no cambia quién atiende; `ReturnToAIUseCase` ya genera un resumen que cubre todo lo
  ocurrido desde el último, incluyendo los mensajes de asesor
* **Bug real encontrado y corregido antes de que ocurriera en producción**:
  `OpenRouterAIProvider.generate()` (`infrastructure/ai/openrouter.py`) armaba el payload de
  OpenRouter usando `sender_role.value` directo como rol de la API — válido mientras
  `MessageRole` solo tenía `user`/`assistant`/`system`. Con `ADVISOR` nuevo, un mensaje de asesor
  dentro de la ventana de `working_memory_size` al volver a modo IA habría mandado
  `{"role": "advisor", ...}`, un rol que OpenRouter/OpenAI no reconoce. Fix: mapeo explícito
  `ADVISOR → "assistant"` (el turno de un asesor humano es funcionalmente el turno del
  "assistant" desde el punto de vista del modelo). Cubierto con test de regresión
  (`tests/test_openrouter_provider.py`) que verifica el payload real enviado
* Frontend: textarea + botón "Enviar" en `/opportunities/[id]`, visible solo cuando `isMine`;
  `useSendMessage` usa `invalidateQueries` (no `removeQueries`) porque, a diferencia de
  tomar/devolver, esta página sigue montada con un observador activo sobre `conversationHistory`
  cuando la mutación resuelve — sin la ventana de dato viejo que sí existía en spec 009
* **Encontrado en validación manual, ya corregido**: ni "Tomar"/"Devolver"/"Enviar" mostraban
  ningún error visible si el backend fallaba — un fallo real se sentía igual que "no hace nada".
  Se agregó manejo de error visible a las tres acciones
* Validado manualmente de punta a punta con Telegram real: tomar una conversación, responder
  desde el Advisor Workspace, confirmar que el mensaje llega al cliente por Telegram con
  `sender_role="advisor"` persistido correctamente

**Navigation Shell & Theming (spec 011) — primera del rediseño post-010 ya implementada:**

* `frontend/app/(workspace)/` — route group con `layout.tsx` que centraliza `useRequireAuth()` y
  envuelve todo en `WorkspaceShell` (`frontend/components/workspace-shell.tsx`): logo, 4 ítems de
  navegación (`/opportunities`, `/knowledge-base`, `/media`, `/admin` — rutas reales, no estado de
  React), nombre + rol + "Cerrar sesión", toggle de tema. `opportunities/` y `opportunities/[id]/`
  se movieron con `git mv` (misma URL, spec 011 lo explica); ya no llaman `useRequireAuth()` por su
  cuenta, usan `useCurrentUser()` (misma query cacheada)
* Tema claro/oscuro con `data-theme` en `<html>` + script anti-parpadeo antes de hidratar
  (`app/layout.tsx`, `suppressHydrationWarning` necesario ahí); `globals.css` con el patrón de tres
  estados (sistema por defecto, override explícito gana en ambas direcciones)
* `/knowledge-base`, `/media`, `/admin` — placeholders reales ("Próxima spec"), listos para que
  las specs 013/017/018 les pongan contenido sin tocar el shell
* **Dos bugs reales encontrados corriendo el e2e existente, no solo por inspección:**
  1. El contenedor de contenido del shell era un segundo `<main>` anidado dentro del `<main>` de
     cada página — HTML inválido, y hacía que `getByRole("link")` sin acotar en los tests contara
     también los enlaces de la barra lateral. Fix: el contenedor del shell es un `<div>`, cada
     página sigue siendo la única fuente de `<main>`
  2. El indicador de desarrollo de Next.js se dibuja en la esquina inferior izquierda — el mismo
     lugar donde quedó el toggle de tema — e interceptaba los clics reales ahí, no solo en
     Playwright. Fix: `devIndicators: false` en `next.config.ts`
* Gap de tooling encontrado de paso: `vitest run` recolectaba también `tests/e2e/**` (usan el
  runner de Playwright, no vitest) y fallaba con "did not expect test.beforeEach() to be called
  here" — nadie había corrido `vitest run` desde que existe el primer e2e. Fix: `exclude:
  ["tests/e2e/**"]` en `vitest.config.ts`
* Validado: `tsc --noEmit`, `eslint`, `vitest run`, `next build`, y el suite completo de Playwright
  (6/6, incluyendo dos tests nuevos: persistencia de tema tras recargar, rutas placeholder)

**Chat Panel Redesign (spec 012) ya implementado:**

* Corrección de contrato primero: `ContactRepository.list_by_ids` (evita N+1 en el listado),
  `OpenOpportunityResponse`/`ConversationHistoryResponse.contact` nuevos, `OpportunityResponse`
  **sin tocar** — `assign-advisor`/`return-to-ai`/`messages` devuelven exactamente el mismo shape
  que antes (test de regresión explícito en `test_opportunity_contact_summary.py`)
* Frontend: filas de lista estilo WhatsApp Web (avatar, nombre real, chip de canal, chip
  IA/Mía/Asignada), pestaña "Sin asignar" renombrada a "IA", búsqueda por nombre de contacto;
  encabezado del detalle con el nombre real en vez de un UUID; burbujas distinguiendo
  cliente/IA/asesor, separadores de día, selector de emojis (buscador + frecuentes vía
  `localStorage`, portado del mockup), búsqueda dentro de la conversación con `<mark>` (el texto
  se escapa antes de resaltar — lo único que puede producir HTML es el propio `<mark>`, nunca el
  contenido del mensaje); adjuntos no-texto como tarjeta compacta, sin visor real todavía
* Validado: `ruff`, `mypy`, `pytest` (18 tests) en backend; `tsc`, `eslint`, `vitest` (3 tests
  nuevos del selector de emojis), `next build`, y Playwright (8/8, dos tests nuevos: búsqueda por
  nombre y búsqueda dentro de la conversación) en frontend

**Contact Enrichment & Follow-ups (spec 013) ya implementado:**

* Domino nuevo de esta tanda (a diferencia de 011/012, solo frontend): 2 entidades (`ContactNote`
  append-only, `FollowUp` mutable con `.resolve()`), 2 tablas nuevas (migración
  `0004_add_contact_enrichment_and_follow_ups`), ~10 casos de uso, 2 routers nuevos
  (`contacts.py`, `advisors.py`)
* `Contact.tags`/`is_favorite` — columna `JSON`, no tabla N:M (mismo criterio que
  `MessageModel.extra_metadata`, revisar solo si el volumen real lo justifica);
  `AddContactTagUseCase`/`RemoveContactTagUseCase` idempotentes, `ToggleContactFavoriteUseCase`
  invierte el valor
* `ContactNote` — siempre autoría humana (`author_id` obligatorio, no `advisor_id`: si algún día
  la IA genera notas, el tipo no debería mentir sobre quién escribió); `save()` usa `add()`, nunca
  `merge()` (append-only, mismo patrón que `ConversationSummary`); `ListContactNotesUseCase`
  resuelve nombres de autor con `get_by_id()` en loop — aceptado a esta escala, sin agregar
  `list_by_ids()` a `InternalUserRepository` solo para esto
* `FollowUp` — ligado a `Opportunity`, no a `Contact` (la asignación vive ahí); regla de negocio:
  un solo seguimiento activo por oportunidad (`FollowUpAlreadyScheduledError` → 422);
  `list_active_by_opportunity_ids` evita N+1 en el listado; "Vencido" se calcula en el frontend
  comparando `due_at` contra la hora actual, no se guarda en BD
* `Opportunity.has_unread_messages` — automático en `ReceiveIncomingMessageUseCase` (mensaje
  entrante) y en `GetConversationHistoryUseCase` (excepción deliberada a "los casos de uso de
  lectura no escriben": abrir la conversación *es* la señal de "ya lo vi"); manual vía
  `SetOpportunityUnreadUseCase` (recibe `unread: bool` explícito, no invierte, para que
  marcar-leída/no-leída sea la misma llamada con distinto valor)
* Reasignación entre asesores — **no hizo falta backend nuevo**: `AssignToAdvisorUseCase` (spec
  009) ya sobreescribía `assigned_advisor_id` sin comprobar el valor anterior. Lo que faltaba era
  el selector de nombres (`InternalUserRepository.list_advisors_by_organization`, desde spec 008,
  nunca conectado a un endpoint) — `GET /organizations/{slug}/advisors` es la única pieza nueva
* Búsqueda — `OpportunityRepository.search_open_by_organization` agrega contenido de mensajes
  (`MessageModel.content ILIKE`) a la búsqueda por nombre/teléfono de spec 012; limitación aceptada:
  `ILIKE` en SQLite es case-insensitive solo ASCII
* Frontend: panel de información del cliente (`contact-panel.tsx`, abre al hacer clic en el
  avatar) con etiquetas, notas, y seguimiento (selector de fecha/hora `date-time-picker.tsx`,
  portado del mockup ya validado); barra de herramientas de la lista (orden cíclico, menú de
  filtros de tres puntos); estrella de favorito no-clicable en la fila de lista (evita anidar un
  botón dentro del `<button>` de la fila); reasignar y marcar no-leída en el encabezado del chat;
  búsqueda cambia de filtro client-side a `useSearchOpportunities` cuando hay texto
* Menús flotantes nuevos (filtros de la lista, reasignar, tres-puntos del chat) cierran al hacer
  clic afuera **en fase de captura**, no burbuja — mismo bug ya corregido en el mockup (un botón
  dentro del propio menú que lo cierra de forma síncrona deja el nodo desconectado del árbol antes
  de que un listener en burbuja lo revise)
* Validado: `ruff`, `mypy`, `pytest` (29 tests, 11 nuevos en `test_contact_enrichment.py`) en
  backend; `tsc`, `eslint`, `vitest`, `next build`, y Playwright (13/13, 6 tests nuevos: panel de
  cliente + etiqueta + nota, programar/resolver seguimiento, reasignar, marcar no-leída, buscar por
  contenido de mensaje) en frontend

**Design System Alignment (spec 013b) ya implementado:**

* Gap real encontrado por el usuario al revisar spec 013 en el navegador (no un pedido de mejora):
  la interfaz implementada en specs 011-013 no se parecía al mockup validado
  (`docs/design/amza_workspace_mockup/`) — y la causa no era solo de ejecución. Specs 011/012, tal
  como quedaron escritas, ya usaban clases Tailwind genéricas (`bg-emerald-900`) y el boilerplate de
  Next.js (fuente Geist, `--background: #ffffff`) en vez de transcribir la paleta/tipografía reales
  que el mockup validó con el usuario. Spec correctiva escrita e implementada de inmediato, antes
  de seguir con spec 014, para no seguir construyendo sobre una base visual equivocada
* Dos gaps distintos, mismo origen: (1) paleta/tipografía/tokens nunca portados, (2) el mockup es
  una vista única de 3 columnas simultáneas (lista + chat + panel de cliente), pero lo implementado
  eran dos rutas separadas (`/opportunities` y `/opportunities/[id]`, heredadas de spec 009,
  anterior al mockup) que se reemplazan una a la otra en vez de convivir
* `frontend/app/globals.css` — tokens reales del mockup (`--paper`, `--surface`, `--accent`,
  `--warn`, `--info`, `--whatsapp`, `--gold`, `--overdue`, colores de burbuja, `--app-shadow`) en
  los 3 estados de tema ya establecidos desde spec 011, mapeados a utilidades Tailwind v4 vía
  `@theme inline` (`bg-accent`, `text-ink-muted`, `shadow-card`, etc.)
* Fuente Manrope vía `next/font/google` (pesos 500-800, igual que el mockup) reemplaza Geist —
  aplicada solo a texto estructural (`font-heading`: nombres, encabezados, chips, botones), no al
  cuerpo de mensajes/notas, replicando a propósito el mismo efecto que el mockup lograba sin
  proponérselo (su `@font-face` de rango 500-800 hace que el texto sin peso explícito caiga fuera
  del rango y use la fuente sans del sistema — `next/font` con pesos discretos no reproduce ese
  fallback automático, así que se aplicó `font-heading` explícitamente en los mismos lugares)
* Rail nav (`workspace-shell.tsx`) rediseñado para calzar con `.rail` del mockup: fondo
  `bg-accent-deep`, logo en tarjeta con sombra, tooltips flotantes por ítem al hover. El
  encabezado superior con nombre/rol/"Cerrar sesión" (no existe en el mockup) se reemplazó por un
  avatar circular con iniciales al final del rail que abre un menú flotante al clic — pérdida de
  visibilidad permanente del nombre, aceptada a cambio de fidelidad real con el mockup
* `frontend/app/(workspace)/opportunities/layout.tsx` (nuevo) — la columna de lista (tabs,
  buscador, orden/filtros) se movió del `page.tsx` a un layout compartido entre `/opportunities` y
  `/opportunities/[id]` (hermanos bajo el mismo layout de Next.js), sin romper el principio ya
  frozen de spec 011 ("cada sección es una ruta real, nunca un `if` decidiendo qué mostrar"). Efecto
  colateral positivo: la lista ya no se remonta al abrir/cerrar una conversación, y su estado de
  tabs/búsqueda/filtros sobrevive la navegación — algo que antes se perdía
* `opportunities/page.tsx` pasó a ser el estado vacío (`.placeholder-panel` del mockup); no se
  agregó ningún endpoint ni caso de uso nuevo — cero cambios en `backend/`
* Recoloreo de todos los componentes ya construidos en specs 011-013 (burbujas, composer, chips,
  panel de cliente, selector de fecha/hora, emoji picker, placeholders, login) a los tokens nuevos,
  sin tocar su lógica
* Validado visualmente con un script de Playwright ad-hoc (capturas de pantalla en claro/oscuro de
  lista, detalle, panel de cliente, y menú de cuenta) además de la validación automatizada
  estándar: `tsc`, `eslint`, `vitest`, `next build`, y Playwright (13/13, dos tests existentes
  ajustados para el layout compartido — el nombre/rol ya no está en una barra siempre visible, y
  los links de la lista ya no viven dentro de `<main>`)
* **Tres problemas reales encontrados por el usuario al validar en el navegador, corregidos de
  inmediato:**
  1. "Reasignar"/"Devolver a IA" quedaron debajo del composer en vez de en el encabezado del chat
     junto a buscar/más-opciones (así están en el mockup). Al mover el bloque se corrigió también
     un gap real con spec 013: "Reasignar" ahora aparece siempre que la oportunidad esté en modo
     `human` (sin importar quién la tenga asignada), no solo cuando ya es mía — el desplegable
     lista a todos los asesores y solo deshabilita al que ya está asignado (marcado "· actual"),
     igual que el mockup. Antes, tomar una conversación de OTRO asesor exigía usar el botón
     "Tomar conversación" (que en realidad solo llama a `assign-advisor` con mi propio id) porque
     "Reasignar" estaba oculto para cualquier oportunidad que no fuera ya mía
  2. La conversación abierta nunca se refrescaba sola — un mensaje nuevo del cliente o una
     respuesta de la IA solo aparecían cambiando de conversación o recargando la página. Sin
     WebSocket/SSE todavía, se agregó polling (`refetchInterval`) a `useConversationHistory` (4s) y
     `useOpportunities` (5s); el hilo también hace auto-scroll al fondo cuando llega un mensaje
     nuevo, pero solo si ya se estaba cerca del final — si el asesor subió a leer historial viejo,
     un mensaje nuevo no lo arrastra de vuelta abajo
  3. La búsqueda dentro de una conversación resaltaba coincidencias pero nunca llevaba la vista
     hasta ellas — si el match estaba arriba (mensaje viejo), quedaba invisible hasta hacer scroll
     manual. Ahora muestra un contador ("N coincidencias"/"Sin coincidencias") y hace scroll al
     primer match cada vez que cambia la búsqueda (no en cada refresco del polling, para no
     arrastrar la vista mientras el asesor lee otra parte del hilo)

**Admin Governance & Access Control (spec 014) ya implementado:**

* Reglas de gobernanza ya acordadas antes de escribir el spec: un administrador **principal**
  (el primer Administrator creado por organización); cualquier administrador puede crear
  administradores o asesores; **solo** el principal puede desactivar a otro administrador; nadie
  puede desactivarse a sí mismo, ni siquiera el principal
* Migración `0005_add_admin_governance` — `internal_users.is_primary` (bool) + un índice único
  parcial (`sqlite_where=is_primary=1`) por organización, la red de seguridad real contra la
  condición de carrera de crear dos administradores "principales" a la vez — el caso de uso no
  llega a comprobarlo a tiempo, la BD sí lo rechaza. Incluye backfill: si ya existía un
  Administrator (ej. el sembrado en spec 008 para validar OAuth), el más antiguo por organización
  queda marcado principal
* `CreateInternalUserUseCase`/`DeactivateInternalUserUseCase`/`ActivateInternalUserUseCase`/
  `ListInternalUsersUseCase` nuevos; **primer uso real de `require_role()`** (spec 008, nunca
  conectado a ningún endpoint hasta ahora) protegiendo `/organizations/{slug}/users`
* Detalle deliberado, distinto a todos los endpoints anteriores del proyecto: el actor de
  `deactivate` viene de `current_user` (la sesión autenticada real vía `Depends`), nunca del
  body — a diferencia de `advisor_id` en assign-advisor/messages (sin implicación de privilegios
  ahí). Dejar que el frontend declarara quién actúa permitiría que cualquier administrador se
  hiciera pasar por el principal
* Las tres excepciones nuevas (`InternalUserEmailAlreadyExistsError`, `CannotRemoveSelfError`,
  `OnlyPrimaryAdminCanDeactivateAdminsError`) van a 422, no 403, aunque dos son reglas de permiso
  — mismo criterio que `OpportunityNotAssignedToAdvisorError` (spec 010): el handler de 403
  siempre devuelve "Access denied" genérico, perdiendo el motivo; 422 conserva el mensaje
  específico
* `scripts/create_user.py` reescrito para llamar al mismo caso de uso que el endpoint (evita que
  la lógica de `is_primary` viva en dos lugares); `scripts/reassign_primary_admin.py` (nuevo) —
  única forma de mover la insignia de principal, deliberadamente sin endpoint (caso raro y de
  alto riesgo)
* Frontend: `/admin` deja de ser el placeholder de spec 011 — tabla de usuarios, formulario
  "Agregar usuario", botón activar/desactivar por fila (deshabilitado en el cliente cuando la
  fila es uno mismo o es un Administrator y el usuario actual no es principal — solo cortesía de
  UX, quien de verdad lo impide es el backend); el ítem "Administración" del rail nav solo se
  renderiza para `role === "administrator"`
* **Bug real, no relacionado con este spec, encontrado por el usuario al intentar validar en el
  navegador justo cuando arrancaba esta implementación**: login con Google fallando con 500
  genérico. Causa real en el log: `jwt.exceptions.ImmatureSignatureError` — `PyJWT.decode()`
  valida `iat` con cero tolerancia de desfase de reloj por defecto, y unos pocos segundos de
  diferencia entre la emisión del token por Google y su validación aquí (red, no necesariamente
  reloj desincronizado) ya lo rechaza. Fix: `leeway=10` en `infrastructure/auth/google.py`.
  Corregido y el backend reiniciado de inmediato, sin esperar a terminar spec 014, porque
  bloqueaba al usuario por completo
* Validado: `ruff`, `mypy`, `pytest` (39 tests, 9 nuevos en `test_admin_governance.py`, incluido
  un test que ejecuta la sentencia SQL de backfill de la migración de forma aislada — los tests
  usan `Base.metadata.create_all`, no Alembic de verdad) en backend; `tsc`, `eslint`, `vitest`,
  `next build`, y Playwright (15/15, 2 tests nuevos en `admin.spec.ts`) en frontend, más
  verificación visual con un script de Playwright ad-hoc (claro/oscuro)

**Admin panel y refinamientos de chat post-014 (feedback del usuario validando en el navegador):**

* Panel de administración: formulario "Agregar usuario" detrás de un botón (antes siempre
  visible); botón "Editar" por fila (nombre/rol para cualquier admin, email solo el principal) vía
  `PUT .../users/{id}` nuevo; se registra quién creó a cada usuario (`created_by`, columna nueva,
  **solo para auditoría — nunca se expone en la respuesta**); se quitó el subtítulo del panel
  (ya no aplica, van a convivir varias secciones ahí, no solo usuarios)
* `Opportunity.has_unread_messages` (booleano, decisión explícita de spec 013) se reemplazó por
  `unread_count` (entero real) — sube uno por cada mensaje entrante, se resetea a 0 al leer. La
  lista ahora muestra el número real, no solo un punto
* Vista previa del último mensaje en el listado (`last_message_preview`) — nuevo método de
  `MessageRepository` que resuelve el último mensaje por oportunidad en lote (evita N+1), truncado
  a 60 caracteres si es texto, o una etiqueta legible ("📷 Imagen", etc.) si no
* Notas de sistema en el hilo — reasignar (o tomar de la IA), devolver a IA, y programar/resolver
  un seguimiento ahora escriben un `Message(sender_role=SYSTEM)` describiendo qué pasó, igual que
  el mockup validado (`ChatBubble` ya sabía renderizar `system` desde spec 012, solo faltaba que
  el backend los generara). `ResolveFollowUpUseCase` ganó un parámetro `advisor_id` que no tenía
  antes, para poder nombrar a quién resolvió
* Header del chat: nombre real del asesor asignado + punto verde, en vez de "Mía"/"Asignada" —
  mismo criterio que el mockup (el chip de asignación siempre muestra a quién, sin distinguir si
  ese quién es el usuario actual)
* Composer bloqueado con mensaje explicativo ("La IA está respondiendo..." / "Asignada a
  {nombre}...") en vez de simplemente desaparecer cuando el asesor actual no puede responder
* Buscador dentro de la conversación: contador de coincidencias + navegación con flechas
  arriba/abajo, cada una con su propio scroll. La búsqueda general (lista) ahora pasa su query a
  la conversación abierta vía `?q=` para que llegue ya resaltada
* Contador por pestaña (IA/Mías/Todas) en la barra lateral
* **Bug real de migración encontrado al aplicar 0006 a la BD de desarrollo real** (no lo detectó
  ningún test — los tests construyen el esquema con `Base.metadata.create_all`, nunca corren
  Alembic de verdad): SQLite no soporta `ALTER TABLE ADD COLUMN` con una constraint (el FK de
  `created_by`) fuera de modo batch, y modo batch a su vez exige que el FK tenga nombre explícito.
  Corregido en la migración; quedó documentado en memoria como el mismo patrón de riesgo ya visto
  antes (specs 013b/014) — verificar siempre contra la BD real, no solo contra los tests
* Validado: `ruff`, `mypy`, `pytest` (51 tests, 12 nuevos entre `test_admin_governance.py` y
  `test_chat_refinements.py`) en backend; `tsc`, `eslint`, `vitest`, `next build`, y Playwright
  (16/16, 2 tests nuevos en `admin.spec.ts`) en frontend, más verificación visual con capturas
  ad-hoc de cada pieza (header, composer bloqueado, buscador, fila de edición)

**Buscador general post-014, segunda ronda (feedback del usuario validando en el navegador,
después de la ronda de refinamientos de arriba):**

* Bug real: los resultados de búsqueda general seguían filtrándose por la pestaña activa
  (IA/Mías/Todas) — un resultado asignado a un humano desaparecía si la pestaña activa era "IA"
  (la de por defecto al entrar), dando la impresión de que el buscador "no encontraba nada". La
  búsqueda es global por diseño; ahora se le hace bypass al filtro de tab
* Bug real: `/opportunities/[id]` es la misma instancia de componente para cualquier id (rutas
  hermanas bajo el layout compartido, spec 013b) — el estado de búsqueda interna (`showSearch`/
  `searchQuery`, precargado desde `?q=`) solo se sembraba una vez al montar, así que navegar de un
  resultado de búsqueda a otro sin desmontar la página lo dejaba desactualizado. Ahora se
  resincroniza cada vez que cambia el id o el query param
* Bug real de auto-scroll: el efecto que hace scroll al match dependía solo de
  `searchQuery`/`matchIndex` (ninguno cambia al cargar), así que corría una vez mientras el hilo
  todavía era el placeholder "Cargando..." (ref nulo) y nunca de nuevo una vez el hilo real se
  montaba. Ahora depende también de `isLoading` (pasa de true a false una sola vez por
  conversación, no en cada poll de refetch)
* Confirmado con el usuario en vivo que, con esos tres bugs corregidos, el flujo de clic (buscar →
  clic en el resultado → conversación abierta con el match resaltado y con scroll) ya funcionaba
  bien — lo único que faltaba era que un único resultado siguiera exigiendo el clic. Se agregó
  apertura automática cuando la búsqueda resuelve a exactamente un resultado (con más de uno,
  sigue exigiendo clic — no hay forma de adivinar cuál sin ambigüedad)
* Botón de limpiar (X) en el buscador general — al principio solo vaciaba el texto, dejando al
  asesor varado en la conversación a la que la búsqueda lo hubiera llevado. Ahora recuerda en qué
  conversación estaba antes de empezar a buscar (capturado una sola vez, en la transición de vacío
  a no vacío) y vuelve ahí al limpiar
* Validado: `tsc`, `eslint`, `vitest`, Playwright (20/20, 4 tests nuevos en
  `advisor-workspace.spec.ts`) en frontend, más varios scripts de Playwright ad-hoc contra el
  backend y frontend reales (no solo mockeados) para reproducir cada bug exactamente como lo
  reportó el usuario antes de confirmarlo corregido

**Channel Provider Routing (spec 015) ya implementado:**

* Backend-only, sin superficie de frontend. Prerrequisito real de spec 016 (WhatsApp
  Integration): antes de este spec, `app/dependencies.py::get_channel_provider()` construía **un
  solo** `TelegramChannelProvider`, inyectado tanto en `ReceiveIncomingMessageUseCase` como en
  `SendAdvisorReplyUseCase` — funcionaba porque solo existe un canal real hoy, pero en el momento
  en que existiera un `Contact` de WhatsApp, responderle seguiría intentando enviar por la API de
  Telegram, silenciosamente mal
* `app/services/channel_provider_registry.py` (nuevo) — `ChannelProviderRegistry`, clase concreta
  de composición (no un `Protocol` nuevo), resuelve el `ChannelProvider` correcto por
  `contact.channel_type` en el momento de enviar. `UnsupportedChannelError` nueva en
  `core/exceptions/domain.py` — deliberadamente sin bucket en `app/exceptions.py` (cae en el
  handler genérico de `DomainError`, 400 + warning): es un error de configuración de despliegue
  (canal nuevo sin provider registrado), no una respuesta esperada del usuario
* `ReceiveIncomingMessageUseCase`/`SendAdvisorReplyUseCase` reciben `channel_provider_registry`
  en vez de `channel_provider`; ninguna otra lógica de negocio cambia
* `GET /health/ready` generalizado — itera `channel_registry.all()` en vez de reportar una clave
  `"telegram"` fija; con un solo canal registrado (el caso de hoy) la respuesta no cambia
* Cuando spec 016 agregue `WhatsAppChannelProvider`, el único cambio en `app/dependencies.py` es
  una línea más en el diccionario del registro — ninguno de los dos casos de uso se vuelve a tocar
* Validado: `ruff`, `mypy` (los 5 errores preexistentes en `scripts/seed_dev_data.py` no
  relacionados, confirmado con `git stash`), `pytest` (56 tests, 5 nuevos entre
  `test_channel_provider_registry.py` y `test_health.py`) en backend. Sin cambios de frontend, sin
  necesidad de Playwright

**WhatsApp Integration (spec 016) ya implementado:**

* Segundo canal real, registrado en `ChannelProviderRegistry` (spec 015 era exactamente el
  prerrequisito para esto — ningún caso de uso se tocó de nuevo, solo `app/dependencies.py`)
* Problema arquitectónico real que motivó la mitad del spec: `send()` se llama **dentro** de la
  transacción que persiste el mensaje (decisión de spec 006), y el ritmo anti-baneo necesario
  (30s en la primera respuesta automática de una conversación, 2-15s aleatorios después, más una
  separación mínima entre envíos consecutivos) puede tardar más de lo que SQLite con un solo
  escritor tolera con una transacción abierta. Resuelto sin tocar esa garantía para Telegram:
  `WhatsAppChannelProvider.send()` encola y retorna casi de inmediato; un único worker
  supervisado en segundo plano (arrancado/detenido en `app/lifecycle.py`, nunca un
  `asyncio.create_task()` por request — ese patrón se descartó explícitamente en spec 006)
  drena la cola con el ritmo real
* `ChannelProvider.send()` gana `is_first_reply: bool = False` (con default, no rompe a
  Telegram, que lo acepta y lo ignora); `ReceiveIncomingMessageUseCase` lo calcula contando
  mensajes de la conversación **antes** de guardar la respuesta de la IA — el proveedor nunca
  consulta la BD por su cuenta (mismo principio que ya corrigió el bug real de
  `TelegramChannelProvider` en spec 006)
* `POST /webhooks/whatsapp/{organization_slug}` (evento `MESSAGES_UPSERT`), mismo patrón que
  `telegram_webhook.py`: siempre 200 salvo secreto inválido, cualquier fallo de procesamiento se
  loguea y se absorbe. `verify_whatsapp_secret` — header propio (`X-Webhook-Secret`), no
  confirmado al 100% en la documentación de Evolution API que se reenvíe tal cual, con un plan B
  documentado (mover el secreto a la URL) si en producción no fuera así
  * Los DTOs del payload (`app/api/dto/whatsapp.py`) son un **modelo tentativo** — la
    documentación de Evolution API no publicó un ejemplo real de payload; se ajusta contra uno
    real capturado al conectar un número de verdad, mismo criterio que ya usa `TelegramUpdate`
* `scripts/register_whatsapp_instance.py` (nuevo) — crea la instancia + registra el webhook en
  la misma llamada, guarda el QR como `.png` para escanear. Sin UI de conexión/QR en `/admin`
  todavía — deliberadamente fuera de alcance, es spec 017
* Riesgo aceptado, mismo espíritu que "sin cola de reintentos para fallos de infraestructura"
  (ya en la tabla de Production Risks de abajo): la cola vive en memoria del proceso — si se cae
  con mensajes encolados sin enviar, esos mensajes ya están en la BD pero el cliente nunca los
  recibió
* Validado: `ruff`, `mypy` (los 5 errores preexistentes en `scripts/seed_dev_data.py`, no
  relacionados), `pytest` (69 tests, 13 nuevos entre `test_whatsapp_provider.py` —incluida la
  separación mínima entre envíos consecutivos, verificada con delays encogidos a milisegundos en
  vez de parchar `asyncio.sleep`/`time.monotonic` globalmente, más riesgoso al ser módulos
  compartidos por todo el proceso— y `test_whatsapp_webhook.py`) en backend. Backend reiniciado y
  confirmado arrancando limpio con el worker arrancando/deteniéndose sin warnings; `GET
  /health/ready` ya reporta `whatsapp: false` (sin credenciales reales de Evolution API todavía)
  sin haber tenido que tocar `health.py` de nuevo. Sin cambios de frontend

**Admin Panel (spec 017) ya implementado:**

* Cierra `/admin` con las dos piezas que faltaban del pedido original: editar el prompt del
  agente (principal + reglas de escalamiento) y conectar/desconectar WhatsApp — lo que spec 016
  dejó deliberadamente fuera
* `Agent.escalation_rules` (migración 0007, columna simple sin constraint) — campo separado de
  `system_prompt`, no porque cambie cómo el modelo las recibe (se concatenan igual al armar el
  mensaje de sistema: prompt, luego reglas de escalamiento, luego resumen de la conversación),
  sino porque un administrador editando el prompt necesita distinguir "cómo debe hablar el
  agente" de "cuándo debe ceder a un humano" sin desenredar un solo bloque de texto
* `GET`/`PUT /organizations/{slug}/agent`, protegido con `require_role(ADMINISTRATOR)` (mismo
  criterio que `/users` en spec 014 — cambiar cómo responde la IA no es una acción de asesor).
  Sin versionado ni historial del prompt — no se pidió
* `WhatsAppChannelProvider` gana `get_qr_code()`/`disconnect()` — administración de la
  instancia, deliberadamente fuera del `ChannelProvider` Protocol (mismo criterio que
  `start()`/`stop()` en spec 016: `TelegramChannelProvider` no los necesita).
  `GET`/`POST /organizations/{slug}/whatsapp/{status,connect,disconnect}` resuelven el provider
  del mismo `ChannelProviderRegistry` (spec 015) que ya usan los casos de uso de mensajería
* Frontend: `/admin` se reorganiza en pestañas (Usuarios sin cambios, nuevas Agente y Canales).
  Agente: dos `<textarea>` + input de modelo (texto libre — no existe ningún catálogo de modelos
  definido en el proyecto para justificar un `<select>` con opciones inventadas) + botón
  "Guardar", sin autoguardado (un prompt mal guardado a mitad de escritura afecta a la IA
  respondiéndole a clientes reales de inmediato). Canales: Telegram solo lectura
  ("Configurado"); WhatsApp con insignia Conectado/Desconectado, refresco manual (sin polling,
  coherente con "nunca reconectar sola"), botón Conectar que muestra el QR devuelto, botón
  Desconectar con confirmación (es destructivo — corta el servicio real hasta que alguien vuelva
  a escanear)
* Validado: `ruff`, `mypy` (5 errores preexistentes en `scripts/seed_dev_data.py`, no
  relacionados), `pytest` (75 tests, 6 nuevos en `test_admin_panel.py`) en backend; `tsc`,
  `eslint`, `vitest`, `next build`, y Playwright (22/22, 2 tests nuevos en `admin.spec.ts`) en
  frontend, más verificación visual con capturas ad-hoc de las tres pestañas contra el backend
  real. Migración aplicada a la BD de desarrollo real y backend reiniciado; `GET`/`PUT /agent` y
  `GET /whatsapp/status` probados en vivo contra la BD real (sin instancia real de Evolution API
  todavía — `/whatsapp/connect` responde el error genérico esperado, mostrado correctamente en
  la UI sin romper nada)

**Production Risks** (decisiones conscientes, no pendientes a resolver ahora — visibles antes de
preparar un despliegue más robusto):

| Riesgo | Estado |
|---|---|
| SQLite (contención de escritura) | Aceptado para MVP — con frontend, Telegram y asesor escriben potencialmente sobre las mismas oportunidades |
| `_pending_states` en memoria sin expiración activa (spec 008) | Aceptado para MVP |
| Secretos en `.env` sin rotación ni vault | Aceptado para MVP — adecuado solo para despliegues de una sola máquina |
| Sin cola de reintentos para fallos de infraestructura | Aceptado para MVP |
| Sin revocación explícita de JWT | Mitigado — `get_current_user()` valida contra BD en cada request |
| Protección CSRF pendiente | Mitigación parcial — cookies `HttpOnly` + `SameSite=Lax` |
| WhatsApp (Evolution API/Baileys): error 463 "reach-out time-lock" al responder a números nuevos | **🔴 CRÍTICO, no resuelto — ver detalle abajo. No es un riesgo aceptable-y-listo como los demás de esta tabla: sin esto, el canal que en la práctica más le importa al piloto (WhatsApp, no Telegram) queda inservible para el caso de uso real — un cliente nuevo escribiéndole por primera vez a la empresa. Pendiente de resolución, no cerrado.** |

**Detalle del error 463 (WhatsApp/Evolution API/Baileys), por qué se acepta como riesgo (por
ahora) en vez de seguir invirtiendo tiempo en resolverlo:**

El mensaje del cliente entra perfecto (webhook, contacto, oportunidad, respuesta de la IA — todo
funciona y se ve en la app). `POST /message/sendText` responde 201, pero WhatsApp bloquea la
entrega en silencio: `"status": 0, "messageStubParameters": ["463"]`. Confirmado contra los
issues reales de los mantenedores, no adivinado: [WhiskeySockets/Baileys#2441](https://github.com/WhiskeySockets/Baileys/issues/2441)
(fix parcial, no resuelto del todo) y [evolution-foundation/evolution-api#2653](https://github.com/evolution-foundation/evolution-api/issues/2653)
(mismo síntoma exacto en v2.3.7, sin solución del mantenedor). Es un rate-limit del lado de
WhatsApp contra contactos "en frío", por falta de tokens `tctoken`/`cstoken` en la implementación
actual de Baileys.

Se probó, con evidencia empírica real en cada caso (no solo teoría):
1. Subir a `2.4.0-rc2` (requiere activación gratuita vía `/manager`, completada) — mismo error,
   sin mejora. Revertido a `v2.3.7`.
2. Mitigaciones sugeridas en foros de la comunidad: marcar el mensaje entrante como leído +
   mostrar "escribiendo..." antes de responder (`mark_as_read`/`send_presence_composing`, nuevos
   en `WhatsAppChannelProvider`, llamados desde `whatsapp_webhook.py`); variables
   `DATABASE_SAVE_DATA_NEW_MESSAGE`/`DATABASE_SAVE_MESSAGE_UPDATE` — ninguna cambió el resultado.
3. El "truco de la reacción" (enviar un 👍 antes del texto, sugerido como forma de "desbloquear"
   el canal de privacidad) — probado directo contra la instancia real: la reacción en sí también
   falló con 463, lo cual además descarta la teoría de que fuera una condición de carrera de
   caché local (llegó bien después de que cualquier escritura async ya hubiera terminado).
4. Downgrade a `v2.3.6` — mismo error exacto. Revertido a `v2.3.7` (sin diferencia real entre
   ambas).
5. **La prueba más determinante:** un número que nunca le había escrito a este WhatsApp también
   falló con el mismo 463 — descarta que fuera un bloqueo específico al contacto ya sobre-probado
   durante el debugging; es un bloqueo general contra cualquier contacto nuevo/en frío desde esta
   instancia. Guardar el contacto en el teléfono y volver a escribir tampoco cambió nada
   (confirma que es del lado del servidor de WhatsApp, no algo que un truco del cliente resuelva).

**Se evaluó cambiar de motor por completo, con evidencia real en cada caso, no solo teoría:**

6. **Evolution Go** (`evolution-foundation/evolution-go`, motor en Go con `whatsmeow` en vez de
   Baileys/Node.js) — se investigó como posible alternativa completa de motor. Descartado antes
   de migrar nada: [evolution-foundation/evolution-go#50](https://github.com/evolution-foundation/evolution-go/issues/50)
   reporta el **mismo error 463 exacto**, sin fix del mantenedor, causa idéntica (tokens
   `tctoken`/`cstoken` no persistidos). Confirmado además en el propio tracker de `whatsmeow`
   ([tulir/whatsmeow#1074](https://github.com/tulir/whatsmeow/issues/1074)) — el problema no es
   de Baileys específicamente, es de cómo WhatsApp trata a *cualquier* librería no oficial que
   hable el protocolo de WhatsApp Web directamente.
7. **OpenWA** (`rmyndharis/OpenWA`, gateway con dos motores seleccionables) — descartado también
   sin migrar nada. Motor Baileys: literalmente la misma librería que ya usamos, mismo bug,
   cero beneficio. Motor `whatsapp-web.js` (navegador headless real en vez de reimplementar el
   protocolo): su propio historial de issues
   ([wwebjs/whatsapp-web.js#3250](https://github.com/wwebjs/whatsapp-web.js/issues/3250),
   [#1909](https://github.com/pedroslopez/whatsapp-web.js/issues/1909),
   [#1872](https://github.com/pedroslopez/whatsapp-web.js/issues/1872),
   [#532](https://github.com/pedroslopez/whatsapp-web.js/issues/532)) muestra el mismo problema
   de fondo (WhatsApp restringiendo el contacto con desconocidos) manifestándose **peor**: no un
   mensaje rechazado limpio (463), sino **el número completo bloqueado/bloqueado por WhatsApp**.
   Cambiar de motor no resuelve nada aquí — es la misma restricción de la plataforma de
   WhatsApp contra clientes no oficiales, no un defecto de una librería en particular.

**⚠️ Precaución activa, no solo nota histórica:** una fuente encontrada durante esta
investigación (documentación de seguridad de un proyecto de gateway de terceros) describe este
"reach-out time-lock" como una medida de *enforcement* de WhatsApp que **se levanta sola con el
tiempo**, y advierte explícitamente que **reintentar contra el mismo destinatario en bucle es
justo lo que escala el enforcement hacia un bloqueo permanente real de la cuenta**. Ya se le
mandaron bastantes intentos fallidos a los mismos 2-3 números durante todo este debugging.
**Decisión tomada: dejar de mandar mensajes de prueba a esos números por ahora** — no hay
confirmación de daño hecho, pero seguir insistiendo es justo lo que la evidencia dice que lo
empeora. Si se retoma la investigación, usar números frescos, no los ya usados.

**8. Prueba de "¿se levanta solo con el tiempo?" — falsada.** Más de 12 horas después del último
intento, sin cambiar nada, un cliente real volvió a escribir y la IA volvió a intentar
responder: **mismo error 463 exacto, idéntico**. Esto descarta la teoría de "es un enforcement
temporal que se levanta solo" — si fuera así, 12+ horas debería haber sido más que suficiente.
La naturaleza 100% reproducible, instantánea y ahora también persistente-en-el-tiempo del fallo
(nunca intermitente, nunca "a veces sí") apunta a algo más simple y más duro: **un hueco de
implementación en el código de Baileys/Evolution API que nunca envía el campo que WhatsApp
exige, en ningún intento, sin importar cuánto tiempo pase.** No es un castigo temporal de la
cuenta — es que el software nunca hace lo que hace falta.

**Esto también responde una pregunta razonable que surgió:** ¿ayudaría cambiar de número (SIM
nueva)? No, por el mismo motivo — el defecto vive en cómo el cliente (Baileys/Evolution API)
maneja el token de privacidad de *cualquier* mensaje entrante, no en la reputación de una cuenta
en particular. Cualquier número corriendo este mismo software fallaría igual en su primer
intento de responder a un contacto nuevo. Un número nuevo, además, sin historial y vinculado vía
un cliente no oficial, es si acaso un perfil *más* sospechoso para la detección de spam de
WhatsApp, no menos.

**9. Actualización 21 de agosto — sí hay un camino de ingeniería concreto, pero bloqueado por
otro bug distinto.** Un colega del equipo técnico externo señaló, con razón, que el fix real de
`tctoken`/Reachout Timelock en Baileys se agregó específicamente en `v7.0.0-rc.10` (mayo 2025),
y que nunca se había confirmado qué versión de Baileys viene empaquetada dentro de cada imagen
de Evolution API probada. Se verificó inspeccionando el `package.json` de Baileys dentro de cada
imagen (sin ejecutar ninguna insegura, solo lectura de archivos):

| Imagen | Baileys empaquetado | ¿Tiene el fix (rc.10+)? |
|---|---|---|
| `v2.3.6` | `7.0.0-rc.6` | ❌ |
| `v2.3.7` (la actual) | `7.0.0-rc.9` | ❌ — justo la anterior al fix |
| `2.4.0-rc2` | `7.0.0-rc.9` | ❌ — ni siquiera se actualizó en este bump |
| `latest` | `7.0.0-rc.9` | ❌ |
| `homolog` (oficial, pre-lanzamiento) | `7.0.0-rc13` | ✅ |

**Nunca se había probado una versión con el fix real** — las tres que sí se probaron nunca lo
tuvieron empaquetado. Se intentó `homolog` (con backup previo de BD y volumen): entra en bucle
de reinicio por un **bug de empaquetado distinto y no relacionado**, Prisma `7.8.0` sin
`datasource.url` configurado en el schema ni un `prisma.config.ts` — confirmado inspeccionando
el schema empaquetado directamente. No es algo resoluble solo con variables de entorno desde
afuera. Se revirtió a `v2.3.7` de inmediato, sesión intacta, sin pérdida de datos.

También se evaluó `deployfybr/evolution:latest` (sugerida por un tercero) — **no se ejecutó**:
publicador de Docker Hub sin repositorio fuente visible (`source: null`), 188 descargas, 0
estrellas, cuenta de menos de un mes. Riesgo real de cadena de suministro al correrla contra
credenciales reales de WhatsApp sin poder auditar qué contiene — no se justifica todavía.
Detalle completo, con logs, en `docs/ops/whatsapp_463_technical_report.md`.

**10. Actualización 21 de agosto (misma sesión) — se arregló el bug de Prisma, pero aparece un
segundo bloqueador, distinto y todavía sin resolver.** Se intentó parchar `homolog` en un
entorno completamente aislado (Postgres desechable en una red Docker separada, nunca contra la
instancia real que sirve la sesión de WhatsApp): montando un `prisma.config.ts` propio con
`datasource.url = env("DATABASE_CONNECTION_URI")` (la imagen ya trae `@prisma/config` y
`@prisma/adapter-pg` como dependencias — solo faltaba ese archivo), las migraciones corrieron sin
error y el proceso arrancó sirviendo en el puerto 8080.

Al primer intento de usar un endpoint real (`GET /instance/fetchInstances`), apareció un
bloqueador nuevo, no relacionado con Prisma ni con el 463: `HTTP 503 {"code":"LICENSE_REQUIRED"}`.
Confirmado contra la documentación oficial: desde Evolution API `2.4.0` en adelante (aplica tanto
a `homolog` como a `2.4.0-rc2`, ya descartado antes por el 463) exigen activar cada instancia
contra el servidor de licencias de Evolution Foundation — gratuito, pero requiere registrar un
email de operador y acepta telemetría periódica obligatoria (instance_id, versión, conteo de
mensajes enviados — su documentación afirma que no incluye contenido de mensajes ni números de
contacto). `v2.3.7` (< 2.4.0) no tiene esta exigencia, por eso nunca apareció antes.

**Todavía NO se ha confirmado si Baileys `rc13` resuelve el 463 en la práctica** — el muro de
licencia impidió llegar a probar el envío de un mensaje real. La instancia de producción
(`v2.3.7`) no se tocó en ningún momento; sigue con la sesión real intacta. Detalle completo,
con logs y las opciones propuestas, en `docs/ops/whatsapp_463_technical_report.md` (secciones 5c
y 7).

**11. Actualización 21 de agosto (continuación, misma sesión) — se pasó el muro de licencia, pero
un tercer bug en `homolog` impidió llegar a probar el 463.** Con autorización explícita, se
completó la activación de licencia contra el servidor real de Evolution Foundation
(`EVOLUTION_OPERATOR_EMAIL=keveenrodriguez@gmail.com`, entorno de prueba aislado, nunca contra la
instancia real): funcionó al primer intento, gratuita, sin necesitar el flujo manual de
navegador — `GET /instance/fetchInstances` pasó de `503 LICENSE_REQUIRED` a `200 []`.

Justo después, `POST /instance/create` con `integration: "WHATSAPP-BAILEYS"` falló de forma
100% reproducible (3 intentos, distintos payloads) con un error de foreign key
(`Setting_instanceId_fkey`) dentro del código ya compilado de `homolog` — confirmado en la base
de datos de prueba que la instancia nunca llega a crearse, ni parcialmente. Es un tercer bug de
release independiente de los otros dos (Prisma, licencia), y a diferencia de esos, **no es
parchable desde afuera** (vive en el bundle minificado, no en un archivo de config o variable de
entorno). Se detuvo el experimento ahí: nunca se generó un QR, nunca se conectó una sesión, nunca
se probó un mensaje real. Entorno de prueba desmontado por completo; la instancia de producción
(`v2.3.7`) nunca se tocó, sesión real intacta durante todo el proceso. Detalle completo (incluida
la tabla comparativa que se iba a usar para el 463, con `homolog` en blanco porque no se alcanzó
esa etapa) en `docs/ops/whatsapp_463_technical_report.md`, sección 5d.

**Conclusión final (revisada de nuevo, sigue sin resolverse):** de tres motores/librerías
completamente distintos investigados (Baileys, whatsmeow/Evolution Go, whatsapp-web.js/OpenWA),
los tres tienen alguna forma del mismo problema del lado de WhatsApp, y ya se confirmó que no se
resuelve con tiempo ni cambiaría con un número nuevo. El camino de ingeniería identificado
(Baileys ≥ `rc.10` vía `homolog`) ya superó dos de sus tres bloqueadores (Prisma, licencia), pero
el tercero (creación de instancia rota) sigue sin resolverse y no depende de nuestro código — es
un bug del propio release de `homolog`. **El 463 sigue sin confirmarse resuelto ni descartado**,
no porque el fix de Baileys no sirva, sino porque el canal que lo trae está roto en un punto
anterior. Próximos pasos posibles (ver reporte, sección 7): intentar un workaround al bug de FK,
escalarlo directamente al soporte de Evolution Foundation, o esperar una release más estable. Si
ninguna vía da una imagen `WHATSAPP-BAILEYS` funcional en un tiempo razonable, la alternativa de
fondo sigue siendo la API oficial de WhatsApp Business de Meta (de pago, requiere aprobación) —
una decisión de producto/costo mayor. Dado que WhatsApp es el canal que de verdad le importa al
piloto (no Telegram), esta decisión se retoma como prioridad en la próxima sesión, no se archiva.

**What does NOT exist yet:**

* Captura de `username` de Telegram (gap identificado en spec 007, decisión de producto pendiente)
* `MicrosoftOAuthProvider` (registrado en Future Evolution de spec 008, sin diseño)
* Revocación de JWT / lista negra (aceptado para MVP, ver spec 008 sección 4)
* Instrumentación de métricas del piloto (ver "Next Step" — se acuerdan antes de instrumentar)

---

# Next Step

**Cambio de rumbo (post spec 010, antes de arrancar cualquier piloto):** en vez de validar el
Advisor Workspace actual con Amza Empaques, se decidió completar más la plataforma primero —
rediseño de interfaz (panel de chat estilo WhatsApp Web), integración de WhatsApp vía Evolution
API, gobernanza de administradores, base de conocimiento, y almacenamiento de multimedia. El
piloto operativo (`docs/pilot/success_criteria_template.md`, ya completado con Amza) queda
pospuesto hasta que esta nueva tanda de specs esté implementada — no se descarta, se pospone
deliberadamente.

El rediseño de interfaz se validó primero como **mockup interactivo sin backend**
(`docs/design/amza_workspace_mockup/` — HTML/CSS/JS autocontenido, iterado varias veces con
retroalimentación directa) antes de comprometer nada a una spec o a código real de `frontend/`.

**Specs 011 a 017 ya están escritas** (Navigation Shell & Theming, Chat Panel Redesign, Contact
Enrichment & Follow-ups, Admin Governance & Access Control, Channel Provider Routing, WhatsApp
Integration, Admin Panel) — ver `specifications/MVP/011_Navigation_Shell_and_Theming.md` hasta
`specifications/MVP/017_Admin_Panel.md`. **El usuario ya pidió empezar a implementar** — se
procede en orden desde 011, una spec a la vez, validando antes de seguir (misma regla de siempre,
ahora aplicada de verdad en vez de solo en la fase de escritura). Al escribir 012 se dividió en
dos: el
rediseño visual del chat no necesita dominio nuevo (quedó en 012), pero etiquetas/notas/
favoritos/seguimientos/reasignación/búsqueda entre conversaciones sí (spec 013, ya escrita) —
mismo criterio que ya partió la propuesta original de spec 006 en su momento. **015 se renombró**
de "Contact Channel Tagging" a "Channel Provider Routing" al escribirla: la etiqueta de canal que
se planeó agregar ya existía (`Contact.channel_type` desde spec 002, ya usado por el chip de spec
012) — el prerrequisito real de WhatsApp era otro (ver nota más abajo). Orden vigente para el resto
de esta tanda (no implementar más de una a la vez, misma regla de siempre):

| Spec | Contenido |
|---|---|
| 011 Navigation Shell & Theming | Barra lateral, logo, tema claro/oscuro — el contenedor, sin tocar el chat |
| 012 Chat Panel Redesign | Burbujas estilo WhatsApp Web, nombre real del contacto, emojis, búsqueda dentro/por nombre — sin dominio nuevo |
| 013 Contact Enrichment & Follow-ups | `Contact.tags`/`notes`/`is_favorite`, entidad `FollowUp`, reasignación entre asesores, búsqueda de mensajes, "no leído" |
| 014 Admin Governance & Access Control | Un admin principal + administradores, reglas de quién puede agregar/eliminar a quién |
| 015 Channel Provider Routing | `ChannelProviderRegistry` — selecciona el `ChannelProvider` correcto por canal, prerrequisito real de 016 |
| 016 WhatsApp Integration (Evolution API) | `WhatsAppChannelProvider` con cola/worker anti-baneo (retrasos simulados, ritmo entre envíos), webhook, script de aprovisionamiento — sin UI de QR (spec 017) ni descarga de multimedia (Media Library) |
| 017 Admin Panel | `Agent.escalation_rules` nuevo, edición de prompt vía UI, conectar/desconectar WhatsApp (QR) usando `WhatsAppChannelProvider.health()`/nuevos métodos — Telegram sigue sin editable por UI, a propósito |
| 018 Knowledge Base | Subida de archivos (listas de precios, etc.) como insumo de contexto para la IA |
| 019 Media Library | Almacenamiento de multimedia entrante/saliente, con limpieza automática periódica |

Gap real encontrado al escribir spec 012, corregido ahí mismo (no era del alcance original de esta
spec, pero bloqueaba construirla): ninguna pantalla mostraba nunca el nombre del contacto —
`OpportunityResponse` nunca expuso `Contact.display_name`, aunque existe desde spec 002. Corregido
como "corrección de contrato" (mismo criterio que `assigned_advisor_id` en spec 009), sin tocar
`AssignToAdvisorUseCase`/`ReturnToAIUseCase`/`SendAdvisorReplyUseCase`.

Gap real encontrado al escribir spec 013: `InternalUserRepository.list_advisors_by_organization()`
ya existía desde spec 008, pero nunca se conectó a ningún endpoint — la reasignación entre asesores
necesitaba mostrar nombres reales, así que spec 013 solo agrega el endpoint que faltaba
(`GET /organizations/{slug}/advisors`), sin tocar el repositorio. También: reasignar de un asesor a
otro **ya funcionaba** en el backend desde spec 009 (`Opportunity.assign_to_advisor()` sobreescribe
sin comprobar el valor anterior) — spec 013 no agregó lógica de reasignación, solo el selector de
nombres que le faltaba al frontend.

Otro más al escribir spec 014: `app/security.py::require_role()` existe desde spec 008 pero
**nunca se conectó a ningún endpoint** — spec 014 es su primer uso real (protege
`/organizations/{slug}/users`). Antes de asumir que un permiso "no existe todavía", revisar si ya
hay una pieza construida y solo sin cablear — viene pasando seguido en esta tanda
(`Contact.display_name`, `list_advisors_by_organization`, `require_role`, y ahora el hallazgo de
spec 015 abajo).

Gap real encontrado al escribir spec 015 (de un sabor distinto a los anteriores — no es una
capacidad sin cablear, es código de un solo canal que hay que generalizar antes de que llegue el
segundo): `app/dependencies.py::get_channel_provider()` construye un único `ChannelProvider`
(siempre Telegram) y ese mismo objeto se inyecta tanto en `ReceiveIncomingMessageUseCase` como en
`SendAdvisorReplyUseCase`. En el momento en que existiera un `Contact` de WhatsApp, responderle
por `POST .../messages` habría intentado enviar por la API de Telegram, sin ningún error visible.
Spec 015 agrega `ChannelProviderRegistry` (selecciona el provider por `channel_type`) antes de que
spec 016 agregue el segundo provider — así esa spec no toca ninguno de los dos casos de uso.

Al escribir spec 016 se consultó la documentación real de Evolution API
(`docs.evolutionfoundation.com.br`) en vez de asumir endpoints de memoria — confirmó
`POST /message/sendText/{instance}`, `POST /webhook/set/{instance}`,
`GET /instance/connectionState/{instance}`, `POST /instance/create` (devuelve el QR en la misma
respuesta) y `POST /chat/markMessageAsRead/{instance}`. Dos puntos quedaron sin confirmar en la
documentación (anotados explícitamente en la spec, no asumidos): si el objeto `headers` al
registrar un webhook realmente se reenvía en cada llamada entrante (se diseñó con eso como
mecanismo principal de verificación y un plan B si no), y si existe un endpoint de presencia
("escribiendo...") para "Evolution API" específicamente o solo para el producto hermano
"Evolution Go".

**Hallazgo arquitectónico real al escribir spec 016**, no solo un gap de cableado: los retrasos
anti-baneo (hasta 30 segundos) no pueden vivir dentro de la transacción donde
`ChannelProvider.send()` se llama hoy (spec 006) — SQLite no tolera una transacción abierta ese
tiempo. Se resolvió con una cola en memoria + un único worker en segundo plano dentro de
`WhatsAppChannelProvider` (arrancado una vez en `app/lifecycle.py`, no `asyncio.create_task()` por
request — ese patrón se había descartado explícitamente en spec 006 por "sin cola ni supervisión";
aquí sí hay cola y un worker supervisado, es la pieza que le faltaba a ese razonamiento). Riesgo
aceptado: la cola es en memoria, un mensaje ya persistido pero no enviado se pierde si el proceso
se cae — mismo espíritu que "sin cola de reintentos" ya aceptado en Production Risks.

Recomendaciones dadas antes de escribir spec 016, ya resueltas concretamente ahí (dejo el resumen
por si hace falta el porqué sin releer la spec completa):
- **Gobernanza de administradores (spec 014, ya implementado en la spec):** un admin "principal"
  (el primer `InternalUser` con rol Administrator creado); cualquier admin puede agregar
  administradores o asesores; **solo** el admin principal puede eliminar/desactivar
  administradores; nadie puede eliminarse a sí mismo.
- **Ventana de 24h de WhatsApp:** terminó sin necesitar nada de spec 016 — es aritmética
  client-side sobre `sent_at` (ya disponible desde spec 012), se implementa cuando exista la UI
  que lo necesite, no antes.
- **Reconexión por QR:** spec 016 deja `WhatsAppChannelProvider.health()` (consulta el estado real
  de conexión) y un script de aprovisionamiento — la pantalla que muestre el QR cuando `health()`
  falle es spec 017, no 016.

No retomar el roadmap tecnológico especulativo previo (Memory Extraction, AI Task Framework,
Embedding Search, Background Jobs, Model Routing, Prompt Management genérico, Context
Optimization, `MicrosoftOAuthProvider` — "Future Evolution" de specs 006/008) hasta que esta nueva
tanda esté implementada y el piloto pospuesto dé evidencia real de qué más hace falta.

Política vigente desde spec 008: toda spec nueva debe incluir tests de lo que introduce; si
modifica comportamiento existente, actualiza los tests afectados (ver
`03_Engineering_Principles.md`).

**Siguiente acción: specs 011, 012, 013, 013b, 014, 015, 016 y 017 implementadas, validadas y
committed (eb6071e, 332708c, 7b59e54, 7d1a6a9, 3e8d86a, e1b1482, f5d77db, 5422047), más dos
tandas de refinamientos post-014 sobre el panel de administración y el chat (cc33ae7, 6ff94ae,
02c693d, 68c8b20, 2a866e9 — ver secciones "Admin panel y refinamientos de chat post-014" y
"Buscador general post-014, segunda ronda" arriba). **Antes de spec 018 (Knowledge Base):
retomar el error 463 de WhatsApp (tabla de Production Risks arriba) — crítico, no un riesgo
aceptado y cerrado, sin esto el canal real que le importa al piloto queda inservible. Plan:
esperar (el time-lock se levanta solo) y reintentar con números frescos, no los ya usados en el
debugging.**

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

🟢 Plataforma completa de punta a punta: dominio, persistencia, memoria conversacional, providers
reales (Telegram + OpenRouter, más WhatsApp vía Evolution API ya implementado y con tests propios
pero sin una instancia real todavía provisionada — ver spec 016), API protegida (Google OAuth +
JWT), y un frontend real (Advisor Workspace) donde un asesor humano puede tomar una conversación,
**responderle al cliente**, y devolverla a IA — validado manualmente con login real y Telegram
real, sin bugs conocidos. Siguiente: se pospuso el piloto operativo para completar más la
plataforma primero (UI rediseñada, WhatsApp, panel de administración, base de conocimiento,
multimedia) — specs 011 (Navigation Shell & Theming), 012 (Chat Panel Redesign), 013 (Contact
Enrichment & Follow-ups), 013b (Design System Alignment, spec correctiva que portó la
paleta/tipografía/layout reales del mockup — ver esa sección para el porqué), 014 (Admin
Governance & Access Control), 015 (Channel Provider Routing), 016 (WhatsApp Integration) y 017
(Admin Panel) ya implementadas, validadas y committed, más dos tandas de refinamientos post-014
sobre administración y chat (edición de usuarios, notas de sistema en el hilo, conteo real de no
leídos, vista previa del último mensaje, buscador con navegación entre coincidencias, apertura
automática de un único resultado de búsqueda, botón de limpiar que vuelve a la conversación de
antes). **🔴 Bloqueador crítico activo, no cerrado:** las respuestas automáticas de WhatsApp a
contactos nuevos fallan con error 463 de WhatsApp (rate-limit "reach-out time-lock", confirmado
como limitación real de la plataforma tras investigar tres motores/librerías distintos —
Baileys, whatsmeow/Evolution Go, whatsapp-web.js/OpenWA — ver tabla de Production Risks para el
detalle completo). Sin resolver esto, WhatsApp (el canal que de verdad le importa al piloto) no
sirve para su caso de uso real. Se retoma en la próxima sesión antes de spec 018 (Knowledge
Base). Ver sección "Next Step" arriba para el orden completo de la nueva tanda de specs.
