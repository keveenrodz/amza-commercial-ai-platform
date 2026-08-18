# 012 Chat Panel Redesign

## Propósito

Segundo paso del rediseño de interfaz (ver spec 011 y `PROJECT_STATE.md`, sección "Next Step").
Rediseña la lista de conversaciones y el hilo de mensajes con el estilo validado en el mockup
(`docs/design/amza_workspace_mockup/`) — visualmente cercano a WhatsApp Web — dentro del
`WorkspaceShell` que ya construyó spec 011.

**Decisión de alcance, tomada explícitamente antes de escribir este spec:** el mockup mezclaba dos
cosas de tamaño e infraestructura muy distinta. Este spec cubre solo la que **no necesita
conceptos de dominio nuevos** — rediseño visual, agrupar mensajes por día, distinguir
cliente/IA/asesor, selector de emojis, búsqueda dentro de una conversación ya cargada, búsqueda de
contactos por nombre en la lista. Todo lo que sí requiere entidades o endpoints nuevos —
etiquetas, notas, favoritos, seguimientos programados, reasignación entre asesores, búsqueda de
contenido de mensajes entre conversaciones, bandera de "no leído" — queda en spec 013 (**Contact
Enrichment & Follow-ups**), a propósito, para no mezclar una spec de UI con una de dominio.

**Explícitamente fuera de alcance:**

- Adjuntar y enviar archivos nuevos desde el composer (necesita almacenamiento real — spec de
  Media Library, más adelante en la tanda). Este spec sí mejora cómo se **muestran** mensajes que
  ya llegan con `content_type` distinto de texto (imagen/video/documento/audio, ya soportado por
  Telegram hoy sin visor especial) — mostrarlos bien no requiere backend nuevo, enviarlos sí.
- Etiquetas, notas, favoritos, seguimientos, reasignación, no leído, orden/filtro de la lista más
  allá de las tres pestañas — spec 013 (esos campos todavía no existen).
- Atribución de autor específico cuando escribe un asesor (`Message` no guarda **qué** asesor
  escribió un mensaje, solo que el rol fue `advisor` — ver sección 4). No es un gap de este spec,
  es una limitación real del dominio hoy; queda anotada como candidata a futuro, no resuelta aquí.
- Cualquier cambio a `AssignToAdvisorUseCase`, `ReturnToAIUseCase` o `SendAdvisorReplyUseCase` —
  su lógica de negocio no cambia, solo su presentación.

---

## Alcance — un gap real bloqueaba el rediseño: el frontend nunca supo el nombre del contacto

Antes de tocar cualquier componente visual, una revisión del código actual encontró que **ninguna
pantalla muestra hoy el nombre del contacto** — ni la lista (`o.status` / `o.attention_mode`, spec
007) ni el detalle (`Oportunidad {opportunity.id.slice(0, 8)}`, spec 010). `Contact.display_name`
existe en el dominio desde spec 002, pero `OpportunityResponse` nunca lo expuso. Sin esto, un
panel de chat "estilo WhatsApp Web" no se puede construir — WhatsApp Web *es*, ante todo, una lista
de nombres de contacto. La sección 1 corrige esto: es una **corrección de contrato**, mismo
criterio que spec 009 usó para `assigned_advisor_id`/`organization_slug` — no una feature nueva,
un DTO incompleto.

Deliberadamente **no** se agrega un preview del último mensaje en la lista (`last_message_preview`)
— sí ayudaría a la sensación de WhatsApp Web, pero a diferencia del nombre del contacto no es
bloqueante (la lista sigue siendo útil sin él), y agregarlo implica resolver el último mensaje de
cada oportunidad en el listado — más costo de by fila del que esta corrección puntual justifica.
Candidato para spec 013 si hace falta.

---

## 1. Corrección de contrato — el contacto real en `OpportunityResponse`/`ConversationHistoryResponse`

### 1.1 `ContactRepository.list_by_ids` — nuevo método

`core/interfaces/repositories.py`:

```python
class ContactRepository(Protocol):
    async def get_by_id(self, id: ContactId) -> Contact | None: ...

    async def list_by_ids(self, ids: list[ContactId]) -> list[Contact]: ...

    async def get_by_external_id(
        self,
        external_id: str,
        channel_type: ChannelType,
        organization_id: OrganizationId,
    ) -> Contact | None: ...

    async def save(self, contact: Contact) -> None: ...
```

`modules/opportunities/repositories/contact.py`:

```python
async def list_by_ids(self, ids: list[ContactId]) -> list[Contact]:
    if not ids:
        return []
    result = await self._session.execute(
        select(ContactModel).where(ContactModel.id.in_([i.value for i in ids]))
    )
    return [_to_entity(model) for model in result.scalars()]
```

Sin este método, listar N oportunidades resolvería N contactos con N consultas separadas
(`get_by_id` en un loop) — una sola consulta `IN (...)` evita el N+1 al construir la lista de
conversaciones (sección 3).

### 1.2 `ListOpenOpportunitiesUseCase` — resuelve el contacto de cada oportunidad

`app/use_cases/list_open_opportunities.py`:

```python
from __future__ import annotations

from dataclasses import dataclass

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from core.entities.contact import Contact
from core.entities.opportunity import Opportunity
from core.exceptions.domain import OrganizationSlugNotFoundError
from infrastructure.database.unit_of_work import SQLAlchemyUnitOfWork


@dataclass(frozen=True)
class OpenOpportunity:
    opportunity: Opportunity
    contact: Contact


class ListOpenOpportunitiesUseCase:
    def __init__(self, session_factory: async_sessionmaker[AsyncSession]) -> None:
        self._session_factory = session_factory

    async def execute(self, organization_slug: str) -> list[OpenOpportunity]:
        async with SQLAlchemyUnitOfWork(self._session_factory) as uow:
            organization = await uow.organizations.get_by_slug(organization_slug)
            if organization is None:
                raise OrganizationSlugNotFoundError(organization_slug)

            opportunities = await uow.opportunities.list_open_by_organization(organization.id)

            contacts_by_id = {
                c.id: c
                for c in await uow.contacts.list_by_ids([o.contact_id for o in opportunities])
            }

            return [
                OpenOpportunity(opportunity=o, contact=contacts_by_id[o.contact_id])
                for o in opportunities
            ]
```

`contacts_by_id[o.contact_id]` sin `.get()` es intencional: todo `Opportunity` persistido tiene un
`contact_id` válido (invariante de base de datos, `FOREIGN KEY` desde spec 003) — un `KeyError`
aquí significaría datos corruptos, no un caso de negocio a manejar con una respuesta 404.

### 1.3 `GetConversationHistoryUseCase` — el `Contact` viaja junto al historial

`app/use_cases/get_conversation_history.py` — `ConversationHistory` gana un campo:

```python
@dataclass(frozen=True)
class ConversationHistory:
    opportunity: Opportunity
    conversation: Conversation | None
    contact: Contact
    messages: list[Message]
```

Dentro de `execute()`, después de resolver `opportunity`:

```python
contact = await uow.contacts.get_by_id(opportunity.contact_id)
if contact is None:
    raise ContactNotFoundError(opportunity.contact_id)
```

(mismo patrón que ya usa `SendAdvisorReplyUseCase` desde spec 010 — el chequeo existe porque el
tipo de `get_by_id` es `Contact | None`, no porque se espere que falle en la práctica).

### 1.4 DTOs — `ContactSummaryResponse`, nuevo `OpenOpportunityResponse`, `ConversationHistoryResponse` extendido

`app/api/dto/opportunity.py` — `OpportunityResponse` **no cambia** (lo siguen devolviendo tal cual
`assign-advisor`/`return-to-ai`/`messages`, que nunca necesitaron el nombre del contacto y cuyo
body de respuesta el frontend ya ignora — cero riesgo de romper esos tres endpoints):

```python
class ContactSummaryResponse(BaseModel):
    display_name: str
    phone_number: str | None

    @classmethod
    def from_domain(cls, contact: Contact) -> ContactSummaryResponse:
        return cls(display_name=contact.display_name, phone_number=contact.phone_number)


class OpenOpportunityResponse(BaseModel):
    opportunity: OpportunityResponse
    contact: ContactSummaryResponse

    @classmethod
    def from_domain(cls, item: OpenOpportunity) -> OpenOpportunityResponse:
        return cls(
            opportunity=OpportunityResponse.from_domain(item.opportunity),
            contact=ContactSummaryResponse.from_domain(item.contact),
        )


class ConversationHistoryResponse(BaseModel):
    opportunity: OpportunityResponse
    contact: ContactSummaryResponse
    messages: list[MessageResponse]

    @classmethod
    def from_domain(cls, history: ConversationHistory) -> ConversationHistoryResponse:
        return cls(
            opportunity=OpportunityResponse.from_domain(history.opportunity),
            contact=ContactSummaryResponse.from_domain(history.contact),
            messages=[MessageResponse.from_domain(m) for m in history.messages],
        )
```

`app/api/routers/opportunities.py` — un solo endpoint cambia de tipo de retorno:

```python
@router.get("")
async def list_open_opportunities(
    organization_slug: str,
    use_case: ListOpenOpportunitiesUseCase = Depends(get_list_open_opportunities_use_case),
) -> list[OpenOpportunityResponse]:
    items = await use_case.execute(organization_slug)
    return [OpenOpportunityResponse.from_domain(item) for item in items]
```

`get_conversation_history`, `assign_to_advisor`, `return_to_ai`, `send_advisor_reply` **no cambian
una sola línea** — sus casos de uso y firmas siguen igual; `ConversationHistoryResponse` ya arma el
`contact` a partir del `ConversationHistory` extendido en la sección 1.3.

---

## 2. Frontend — tipos y hooks

`frontend/types/api.ts`:

```typescript
export interface ContactSummary {
  display_name: string;
  phone_number: string | null;
}

export interface OpenOpportunity {
  opportunity: Opportunity;
  contact: ContactSummary;
}

export interface ConversationHistory {
  opportunity: Opportunity;
  contact: ContactSummary;
  messages: Message[];
}
```

`frontend/hooks/use-opportunities.ts` — un solo cambio de tipo:

```typescript
export function useOpportunities(organizationSlug: string | undefined) {
  return useQuery<OpenOpportunity[]>({
    queryKey: ["opportunities", organizationSlug],
    queryFn: () =>
      apiFetch<OpenOpportunity[]>(`/api/organizations/${organizationSlug}/opportunities`),
    enabled: organizationSlug !== undefined,
  });
}
```

`useConversationHistory` no cambia — sigue tipado por `ConversationHistory`, que ya trae `contact`.

---

## 3. `app/(workspace)/opportunities/page.tsx` — lista estilo WhatsApp Web

Reemplaza la lista de una línea por filas con avatar (iniciales de `contact.display_name`), nombre
real, chip de canal (ícono Telegram/WhatsApp según `opportunity.channel_type` — `ChannelType.WHATSAPP`
ya existe en el dominio desde spec 002, aunque el provider real llega en una spec futura de esta
tanda; el chip ya queda listo para ese día), y un chip de estado:

| Estado | Chip |
|---|---|
| `attention_mode === "ai"` | `IA` |
| `assigned_advisor_id === currentUser.id` | `Mía` |
| `assigned_advisor_id` es otro asesor (solo visible en la pestaña **Todas**) | `Asignada` |

No se muestra el nombre del *otro* asesor — no hay endpoint para listar `InternalUser` desde el
frontend todavía (candidato natural para spec de gobernanza de administradores).

Pestañas: se renombra **Sin asignar → IA** (mismo criterio que ya se aplicó al mockup — el estado
no es "abandonado", es "la IA lo está atendiendo"). El valor interno del tipo también se renombra
para que el código quede consistente con lo que muestra:

```typescript
type Tab = "ai" | "mine" | "all";
```

**Búsqueda por nombre de contacto** — client-side, sobre los datos ya cargados por
`useOpportunities` (sin endpoint nuevo; buscar además por contenido de mensajes entre
conversaciones queda para spec 013, que sí trae un endpoint de búsqueda):

```tsx
const [query, setQuery] = useState("");

const filtered = (opportunities ?? [])
  .filter((item) => {
    if (tab === "ai") return item.opportunity.attention_mode === "ai";
    if (tab === "mine") return item.opportunity.assigned_advisor_id === currentUser.id;
    return true;
  })
  .filter((item) =>
    query.trim() === ""
      ? true
      : item.contact.display_name.toLowerCase().includes(query.trim().toLowerCase()),
  );
```

Cada fila enlaza a `/opportunities/${item.opportunity.id}` (sin cambios en la URL de destino).

---

## 4. `app/(workspace)/opportunities/[id]/page.tsx` — encabezado e hilo

**Encabezado**: reemplaza `Oportunidad {id.slice(0, 8)}` por `contact.display_name`, con el chip de
canal y el mismo chip de estado de la sección 3 junto al nombre.

**Burbujas** (`frontend/components/chat-bubble.tsx`, nuevo): cliente a la izquierda, IA/asesor a la
derecha — la posición ya existía desde spec 010, lo nuevo es distinguir visualmente **quién**
generó el turno del lado derecho:

```tsx
function bubbleLabel(role: Message["sender_role"]): string | null {
  if (role === "assistant") return "IA";
  if (role === "advisor") return "Asesor"; // sin nombre específico -- ver "Fuera de alcance"
  return null;
}
```

Hoy ambos roles se veían idénticos (gap señalado explícitamente en spec 010, nunca cerrado) — este
spec lo cierra a nivel visual, sin tocar el dominio.

Mensajes con `content_type !== "text"` (imagen/video/documento/audio — ya soportados por
`MessageContentType` desde spec 002, y ya pueden llegar hoy vía Telegram) se muestran como una
tarjeta compacta con ícono según tipo en vez de intentar renderizar `content` como texto plano —
sin visor real todavía (eso es Media Library), solo una representación honesta de que ahí hay un
adjunto:

```tsx
{message.content_type !== "text" ? (
  <FileCard type={message.content_type} />
) : (
  <p>{message.content}</p>
)}
```

**Separadores de día**: agrupar `messages` por la fecha de `sent_at` (cálculo puramente de
presentación, sin cambios de datos) e insertar un separador tipo "Hoy" / "Ayer" / fecha completa
entre grupos.

**Búsqueda dentro de la conversación**: botón de lupa en el encabezado que abre un campo de texto;
filtra sobre `messages` ya cargado por `useConversationHistory` (nada nuevo del servidor),
resaltando coincidencias con `<mark>` — mismo comportamiento ya validado en el mockup
(`docs/design/amza_workspace_mockup/template.html`, función `highlightText`/`renderThreadMessages`),
portado a React en vez de manipulación directa del DOM.

---

## 5. Composer — `frontend/components/message-composer.tsx`

Reemplaza el `<input>` de una línea (spec 010) por un `<textarea>` que crece con el contenido, con
un botón de emoji a la izquierda. Sigue enviando por el mismo `useSendMessage()` sin cambios — un
emoji es simplemente parte del `content: string` que ya viaja hoy, no requiere nada nuevo del
backend.

`frontend/components/emoji-picker.tsx` (nuevo) — mismo comportamiento ya validado en el mockup:
buscador por palabra clave, fila de "Frecuentes" (top 3 por uso, persistido en `localStorage` bajo
`amza-emoji-freq`, con `👍`/`✅`/`🙏` como default antes de tener historial), inserción en la
posición del cursor. Es la misma lógica de `docs/design/amza_workspace_mockup/template.html`
(`EMOJI_DATA`, `getFrequentEmojis`, `insertAtCursor`) portada a un componente de React — no hace
falta rediseñarla, ya fue validada.

Adjuntar archivos **no** se agrega en este spec (ver "Fuera de alcance").

---

## 6. Tests

Política vigente desde spec 008: este spec incluye pruebas de lo que introduce, y actualiza las que
su cambio de comportamiento rompe.

- Backend (`tests/test_opportunity_contact_summary.py`, nuevo, o junto a la suite existente de
  oportunidades):
  1. `ContactRepository.list_by_ids` — lista vacía de ids no consulta la base de datos y devuelve
     `[]`; una lista de ids existentes devuelve los `Contact` correspondientes.
  2. `GET /organizations/{slug}/opportunities` — cada elemento incluye `contact.display_name`
     correcto para su `opportunity.contact_id`.
  3. `GET .../opportunities/{id}/history` — la respuesta incluye `contact` con el `display_name`
     correcto.
  4. Regresión: `POST .../assign-advisor`, `POST .../return-to-ai`, `POST .../messages` siguen
     devolviendo exactamente el mismo shape que antes de este spec (nadie rompió esos tres
     endpoints al tocar `OpportunityResponse` — deberían quedar sin cambios, este test lo hace
     explícito).
- Frontend (`frontend/tests/e2e/advisor-workspace.spec.ts`, existente) — **debe actualizarse**: los
  fixtures mockeados de `/api/organizations/.../opportunities` y `.../history` necesitan el nuevo
  shape (`{ opportunity, contact }` en vez de la oportunidad plana) para que la página compile
  contra datos realistas; agregar aserciones sobre el nombre del contacto en la lista y en el
  encabezado del detalle (ya no debería aparecer ningún UUID visible en pantalla).
- Nuevo test e2e: escribir en el buscador de la lista un nombre parcial de contacto, confirmar que
  filtra a los resultados esperados dentro de la pestaña activa.
- Nuevo test e2e: abrir una conversación, buscar una palabra presente en un mensaje anterior,
  confirmar que aparece resaltada.
- Nuevo test e2e (o de componente): el selector de emojis muestra los mismos tres emojis por
  defecto (`👍`, `✅`, `🙏`) antes de cualquier uso, y promueve un emoji a "Frecuentes" tras usarlo
  varias veces.

---

## Próximo paso

Spec 013 — **Contact Enrichment & Follow-ups**: etiquetas, notas, favoritos, seguimientos
programados (fecha/hora + motivo, con calendario flotante como el validado en el mockup),
reasignación entre asesores, bandera de "no leído", y el endpoint de búsqueda que extienda la
búsqueda por nombre de esta spec a también buscar contenido de mensajes. Necesita nuevas entidades
de dominio (`Contact` gana `tags`/`notes`/`is_favorite`; nueva entidad `FollowUp`) y su propia
migración — por eso quedó separada de esta spec desde el principio.

No avanzar a spec 014 (gobernanza de administradores) hasta que 013 esté implementada y validada.
