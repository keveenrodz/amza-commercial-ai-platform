# IMPLEMENTATION ORDER

Este documento define el orden oficial de implementación del proyecto.

Ningún desarrollador (humano o IA) deberá implementar funcionalidades fuera de la tarea actual.

---

# Documentación obligatoria (leer una sola vez al iniciar el proyecto)

1. docs/product/00_Vision_and_Product_Principles.md
2. docs/product/01_Business_Validation.md
3. docs/engineering/02_Product_Glossary.md
4. docs/engineering/03_Engineering_Principles.md
5. docs/engineering/04_Architecture.md
6. docs/product/05_Roadmap.md
7. docs/product/06_Product_Specification.md

---

# Especificaciones del MVP (leer una por una)

Orden de implementación:

| Spec | Estado |
|---|---|
| 000 Technology Stack | ✅ spec — referencia, sin implementación |
| 001 Project Setup | ✅ spec + ✅ implementado + ✅ validado + ✅ committed |
| 002 Domain Model | ✅ spec + ✅ implementado + ✅ validado + ✅ committed |
| 003 Persistence Model | ✅ spec + ✅ implementado + ✅ validado + ✅ committed (aa2614b) |
| 004 Repository Implementations | ✅ spec + ✅ implementado + ✅ validado + ✅ committed (9cc20cf) |
| 005 Application Services | ✅ spec + ✅ implementado + ✅ validado + ✅ committed (ace5e30) |
| 006 Conversation Memory & Providers | ✅ spec + ✅ implementado + ✅ validado + ✅ committed |
| 007 API Layer | ✅ spec + ✅ implementado + ✅ validado + ✅ committed |
| 008 Security & Identity | ✅ spec + ✅ implementado + ✅ validado + ✅ committed |
| 009 Advisor Workspace | ✅ spec + ✅ implementado + ✅ validado + ✅ committed (4f7a183) |
| 010 Advisor Reply | ✅ spec + ✅ implementado + ✅ validado + ✅ committed (b181d1e) |
| 011 Navigation Shell & Theming | ✅ spec + ⬜ implementado + ⬜ validado + ⬜ committed |
| 012 Chat Panel Redesign | ✅ spec + ⬜ implementado + ⬜ validado + ⬜ committed |
| 013 Contact Enrichment & Follow-ups | ✅ spec + ⬜ implementado + ⬜ validado + ⬜ committed |
| 014 Admin Governance & Access Control | ✅ spec + ⬜ implementado + ⬜ validado + ⬜ committed |
| 015 Channel Provider Routing | ✅ spec + ⬜ implementado + ⬜ validado + ⬜ committed |
| 016 WhatsApp Integration (Evolution API) | ✅ spec + ⬜ implementado + ⬜ validado + ⬜ committed |
| 017 Admin Panel | ✅ spec + ⬜ implementado + ⬜ validado + ⬜ committed |

La propuesta original de spec 006 (más abajo, tachada) se dividió en la práctica: la memoria
conversacional y los providers quedaron en 006, la capa HTTP pasó a un spec 007 separado. Detalle
completo de cada spec en `PROJECT_STATE.md`, no aquí — este documento es el orden, no el estado.

**Cambio de rumbo tras las 10 specs del MVP:** en vez de arrancar el piloto operativo con Amza
Empaques directamente, se decidió completar más la plataforma primero (UI/UX rediseñada,
integración de WhatsApp vía Evolution API, panel de administración, base de conocimiento,
multimedia) — ver `PROJECT_STATE.md`, sección "Next Step", para el detalle completo y las razones.
El rediseño de interfaz se validó primero como mockup interactivo sin backend
(`docs/design/amza_workspace_mockup/`) antes de comprometerlo a una spec.

**Orden acordado para esta nueva tanda de specs** (011 en adelante, continúan la numeración del
MVP). Spec 012 se dividió en dos al escribirla: el rediseño visual del chat no necesita dominio
nuevo, pero etiquetas/notas/favoritos/seguimientos/reasignación/búsqueda sí — mismo criterio que ya
partió la propuesta original de spec 006 (ver más abajo). Orden vigente:

011 Navigation Shell & Theming → 012 Chat Panel Redesign → 013 Contact Enrichment & Follow-ups →
014 Admin Governance & Access Control → 015 Channel Provider Routing → 016 WhatsApp Integration
(Evolution API) → 017 Admin Panel (prompts, números, conexión WhatsApp) → 018 Knowledge Base
(subida de archivos) → 019 Media Library (almacenamiento e inbound media). No implementar más de
una a la vez, misma regla de siempre.

**Siguiente acción: specs 011-017 escritas. El usuario pidió empezar a implementar — se procede
en orden, empezando por 011, una a la vez, validando y ajustando antes de seguir con la
siguiente.**

<details>
<summary>Propuesta original de spec 006 (histórica, no lo que terminó pasando — ver arriba)</summary>

Propuesta para spec 006 (dos partes en un mismo spec o dos specs separados — confirmar):

**Parte A — Provider Implementations:**
- `infrastructure/channels/telegram.py` → `TelegramChannelProvider` (satisface `ChannelProvider` Protocol)
- `infrastructure/ai/openrouter.py` → `OpenRouterAIProvider` (satisface `AIProvider` Protocol)
- Incluye la discusión de `AIProvider.summarize()` y optimización de costos LLM (postergada desde spec 005)

**Parte B — API Layer:**
- `app/routers/telegram_webhook.py` → endpoint POST `/webhook/telegram`
- `app/routers/opportunities.py` → endpoints de gestión (asignar asesor, devolver a AI, historial)
- `app/dependencies.py` → wiring completo de inyección de dependencias
- Configuración de seguridad básica (token de webhook)

</details>

No avanzar hasta que la implementación haya sido validada.

---

# Regla

Nunca implementar más de una especificación al mismo tiempo.

Cada especificación deberá:

- implementarse;
- probarse;
- revisarse;
- aprobarse;

antes de continuar con la siguiente.

---

# Autoridad

En caso de conflicto entre documentos, el orden de prioridad será:

1. Vision
2. Product Glossary
3. Engineering Principles
4. Architecture
5. Product Specification
6. Specification actual
