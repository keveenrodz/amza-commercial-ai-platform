# 009 Advisor Workspace

## Propósito

Primera interfaz de usuario real de la plataforma. No es un CRM, no tiene reportes, no tiene
administración — es exactamente el flujo que ya existe en el backend (specs 006-008), expuesto a
un asesor humano:

```
Login con Google → Mis oportunidades → Abrir conversación → Tomar / Devolver a IA
```

El objetivo no es construir un frontend grande. Es que un asesor pueda trabajar, y que el
proyecto obtenga la primera señal real de si esta experiencia ayuda a vender más — la pregunta
que hoy importa más que cualquier mejora técnica al motor de IA.

**Explícitamente fuera de alcance** (no es una lista de "todavía no", es una decisión de
alcance): gestión de usuarios (sigue siendo `create_user.py`), reportes/analytics,
configuración de agentes u organizaciones, notificaciones en tiempo real.

---

## Principio arquitectónico

> El navegador se comunica exclusivamente con Next.js. Next.js es el único consumidor HTTP del
> backend. Next.js actúa como Backend-for-Frontend (BFF) — hoy solo hace proxy puro, pero el
> límite queda establecido desde ahora, no como consecuencia de evitar configurar CORS.

Esto sigue siendo válido incluso si algún día frontend y backend terminan en dominios distintos,
o si `Next.js` empieza a hacer cache, agregación de varias llamadas, o SSR — nada de eso rompe el
principio, porque el navegador nunca necesitó saber dónde vive realmente FastAPI.

---

## 1. Next.js como BFF — proxy puro

`frontend/next.config.ts`:

```typescript
import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  async rewrites() {
    return [
      { source: "/api/:path*", destination: `${process.env.BACKEND_URL}/:path*` },
    ];
  },
};

export default nextConfig;
```

El navegador solo conoce rutas relativas (`fetch("/api/organizations/...")`, `<a
href="/api/auth/google/login">`). Next.js reenvía server-side a FastAPI. La cookie `HttpOnly` que
fija `/auth/google/callback` (spec 008) viaja transparente en ambas direcciones — para el
navegador todo es el mismo origen, así que nunca hace falta `CORSMiddleware`,
`allow_credentials`, ni discutir `SameSite=None`.

**Corrección a Spec 007 — `.env.example`:** `NEXT_PUBLIC_API_URL` deja de tener sentido — exponía
la URL del backend al bundle del navegador, que ya no necesita conocerla. Se reemplaza por
`BACKEND_URL` (sin prefijo `NEXT_PUBLIC_`, nunca llega al navegador, solo lo lee el servidor de
Next.js al construir la tabla de rewrites).

```bash
# antes
NEXT_PUBLIC_API_URL=http://localhost:8000
# ahora
BACKEND_URL=http://localhost:8000
```

En producción, si Next.js y FastAPI comparten dominio detrás de un reverse proxy, `BACKEND_URL`
apunta a la dirección interna del backend (ej. `http://backend:8000` en Docker Compose) — el
navegador sigue sin verla nunca.

---

## 2. Corrección a Spec 007 — `OpportunityResponse.assigned_advisor_id`

No es una feature nueva del frontend — es un DTO incompleto. El frontend necesita responder "¿es
mía / está libre / la tiene otro asesor?", y sin este campo no puede.

`app/api/dto/opportunity.py`:

```python
class OpportunityResponse(BaseModel):
    id: str
    contact_id: str
    agent_id: str
    assigned_advisor_id: str | None
    attention_mode: str
    status: str
    channel_type: str
    started_at: datetime
    last_activity_at: datetime
    closed_at: datetime | None

    @classmethod
    def from_domain(cls, opportunity: Opportunity) -> OpportunityResponse:
        return cls(
            id=str(opportunity.id),
            contact_id=str(opportunity.contact_id),
            agent_id=str(opportunity.agent_id),
            assigned_advisor_id=(
                str(opportunity.assigned_advisor_id)
                if opportunity.assigned_advisor_id
                else None
            ),
            attention_mode=opportunity.attention_mode.value,
            status=opportunity.status.value,
            channel_type=opportunity.channel_type.value,
            started_at=opportunity.started_at,
            last_activity_at=opportunity.last_activity_at,
            closed_at=opportunity.closed_at,
        )
```

---

## 3. Corrección a Spec 008 — `CurrentUserResponse.organization_slug`

El frontend nunca debería resolver un UUID a un slug — eso es una fuga del dominio hacia la capa
de presentación. Si `/organizations/{slug}/opportunities` espera un slug, `/auth/me` debe
entregarlo directo.

Se resuelve **solo dentro del endpoint `/auth/me`**, no dentro de `get_current_user()` — esa
dependencia la usan también `/organizations/*`, que no necesita el slug (ya lo tiene de la URL).
Agregarle una consulta extra a `get_current_user()` penalizaría cada request protegido por algo
que solo un endpoint necesita.

`app/api/dto/auth.py`:

```python
class CurrentUserResponse(BaseModel):
    id: str
    organization_id: str
    organization_slug: str
    full_name: str
    email: str
    role: str
    status: str

    @classmethod
    def from_domain(cls, user: InternalUser, organization_slug: str) -> CurrentUserResponse:
        return cls(
            id=str(user.id),
            organization_id=str(user.organization_id),
            organization_slug=organization_slug,
            full_name=user.full_name,
            email=user.email,
            role=user.role.value,
            status=user.status.value,
        )
```

`app/api/routers/auth.py` — `get_me()` ahora resuelve la organización antes de construir la
respuesta:

```python
@router.get("/me")
async def get_me(user: InternalUser = Depends(get_current_user)) -> CurrentUserResponse:
    async with SQLAlchemyUnitOfWork(AsyncSessionFactory) as uow:
        organization = await uow.organizations.get_by_id(user.organization_id)
    assert organization is not None  # invariante: no existe InternalUser sin Organization válida
    return CurrentUserResponse.from_domain(user, organization.slug)
```

---

## 4. Nuevo — `POST /auth/logout`

Omisión del flujo original: un workspace real necesita cerrar sesión. Borra la cookie, no hay
estado de servidor que limpiar (el JWT sigue siendo stateless).

```python
@router.post("/logout")
async def logout() -> Response:
    response = Response(status_code=200)
    response.delete_cookie("access_token")
    return response
```

---

## 5. Páginas del Advisor Workspace

Client Components + `@tanstack/react-query` (ya es dependencia del scaffold). Nada de Server
Components haciendo data-fetching hacia el backend en este spec — el `fetch()` de un Server
Component es una llamada saliente del propio servidor de Next.js, no pasa por la tabla de
`rewrites()` (esa solo aplica a requests que le llegan al servidor desde el navegador). Mantenerlo
todo client-side evita esa complejidad para un workspace que debe seguir siendo pequeño.

**Regla sin excepciones: React Query es la única fuente de datos del cliente.** Ningún componente
hace `useEffect(() => { fetch(...) }, [])` directo — todo acceso HTTP pasa por `useQuery()` o
`useMutation()`. No es una preferencia de estilo: mantiene una sola estrategia de caché, errores,
reintentos e invalidación en todo el workspace, en vez de que cada componente reinvente la suya.

**El frontend nunca construye URLs del backend.** Siempre `fetch("/api/...")`, con literal `/api`
al inicio. Nunca `fetch(process.env.BACKEND_URL + ...)` ni nada equivalente — `BACKEND_URL` es una
variable server-only que Next.js lee para construir la tabla de `rewrites()` (sección 1); ningún
componente cliente debería referenciarla ni saber que existe. Si algún componente la necesitara,
es una señal de que algo está mal diseñado, no una excepción válida.

**No almacenar estado derivado.** `myOpportunities`, `unassignedOpportunities`, etc. nunca son
`useState` — son un `.filter()` sobre el resultado de `useQuery()`, calculado en cada render. Ya
quedó documentado que `assigned_advisor_id` es suficiente para derivar cualquier vista; guardarlo
en estado aparte solo crea una copia que puede desincronizarse del dato real.

| Ruta | Contenido |
|---|---|
| `/login` | Un botón: `<a href="/api/auth/google/login">Iniciar sesión con Google</a>` |
| `/opportunities` | Lista de oportunidades de la organización (`GET /api/organizations/{slug}/opportunities`), con tres pestañas, todas derivadas client-side (`.filter()`, nunca estado propio) de la misma respuesta: **Sin asignar** (`assigned_advisor_id == null`), **Mías** (`== currentUser.id`), **Todas** (sin filtro — útil para un Administrator, y para pruebas) |
| `/opportunities/[id]` | Historial de conversación (`GET .../history`) + botón **Tomar** (`POST .../assign-advisor` con `advisor_id = currentUser.id`) o **Devolver a IA** (`POST .../return-to-ai`), según el estado actual |

Gating de autenticación: cada página protegida llama `GET /api/auth/me` al montar (vía
`useQuery`); si responde 401, redirige a `/login`. Sin middleware de Next.js en este spec — es una
decisión de simplicidad consistente con "workspace pequeño", no una limitación técnica; se
revisita si el parpadeo de redirect molesta en uso real.

`organization_slug` para las llamadas a `/opportunities` viene de `/auth/me` (sección 3) — el
frontend nunca lo pide en otro lado ni lo construye.

---

## 6. Tests

Política vigente desde spec 008: este spec incluye pruebas de lo que introduce.

- Backend: extender `tests/test_security_and_identity.py` (o un archivo nuevo) para
  `assigned_advisor_id`/`organization_slug` en las respuestas, y para `/auth/logout`.
- Frontend: al menos un test de Playwright (`frontend/tests/e2e/`, ya configurado en el
  scaffold) cubriendo el flujo completo con el backend real de pruebas: login (con el
  `AuthProvider` fake, no Google real) → ver oportunidad sin asignar → tomarla → aparece en
  "Mías" → devolver a IA.

---

## Production Risks (agregar a `PROJECT_STATE.md`, no a este spec)

| Riesgo | Estado |
|---|---|
| SQLite (contención de escritura) | Aceptado para MVP — con frontend, Telegram y asesor escriben potencialmente sobre las mismas oportunidades |
| `_pending_states` en memoria sin expiración activa (spec 008) | Aceptado para MVP |
| Secretos en `.env` sin rotación ni vault | Aceptado para MVP — adecuado solo para despliegues de una sola máquina |
| Sin cola de reintentos para fallos de infraestructura | Aceptado para MVP |
| Sin revocación explícita de JWT | Mitigado — `get_current_user()` valida contra BD en cada request |
| Protección CSRF pendiente | Mitigación parcial — cookies `HttpOnly` + `SameSite=Lax` |

No son pendientes a resolver ahora — son decisiones conscientes que conviene tener visibles antes
de preparar un despliegue más robusto.

---

## Próximo paso

**"Pilot Validation" (Operational Validation) — no es una spec técnica, no se numera como
spec 010.** No se está construyendo software, se está validando una hipótesis de negocio: que
alguien de Amza Empaques use el Advisor Workspace durante unos días reales, antes de retomar
cualquier ítem del roadmap tecnológico (Knowledge Base, Embeddings, Memory Extraction, Prompt
Management, Background Jobs — todo registrado en "Future Evolution" de specs 006/008).

**Antes de empezar el piloto, definir qué significa éxito** — no instrumentarlo todavía, solo
acordarlo, para que el resultado sea comparable y no termine siendo únicamente "se sintió bien".
Candidatos a discutir con Amza Empaques:

- Tiempo promedio para tomar una conversación desde que queda sin asignar
- Porcentaje de conversaciones devueltas a la IA (¿el asesor las toma y las regresa rápido, o se
  queda con ellas?)
- Número de incidencias reportadas durante el piloto
- Satisfacción del asesor, aunque sea cualitativa (una conversación corta al final del piloto)

La retroalimentación de este piloto probablemente cambie el roadmap tecnológico más de lo que
cualquier decisión de diseño podría anticipar hoy — es exactamente la razón para no adelantarlo.

**Nota aparte, no bloqueante:** con arquitectura, seguridad, tests, e integración real ya
funcionando, vale la pena escribir ADRs cortos para las decisiones que ya demostraron ser valiosas
y dejaron de ser "de una spec específica" — candidatas: BFF, `ConversationSummary` como entidad
propia, `AIProvider.generate()` vs `complete()`, OAuth sin auto-provisioning, JWT validado contra
BD, proxy de Next.js. Cinco o seis, no todas las decisiones tomadas — se propone como tarea
separada, después de este spec.
