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
| 006 Provider Implementations + API Layer | ❌ spec no escrito aún |

**Siguiente acción:** confirmar con el usuario el alcance exacto de spec 006, luego escribirlo e implementarlo.

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
