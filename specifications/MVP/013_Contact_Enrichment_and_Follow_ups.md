# 013 Contact Enrichment & Follow-ups

## Propósito

Tercer paso del rediseño (ver specs 011, 012, y `PROJECT_STATE.md` sección "Next Step"). Cierra
todo lo que el mockup validó y que spec 012 dejó fuera **a propósito** porque necesitaba dominio
nuevo: etiquetas, notas y favoritos por contacto, seguimientos programados, reasignación entre
asesores, bandera de "no leído", y búsqueda que además de nombre de contacto (spec 012) también
busque contenido de mensajes.

A diferencia de 011/012 (solo frontend), este spec sí agrega entidades, tablas y endpoints nuevos
— es la spec de dominio de esta tanda, equivalente en tamaño a specs 006/008 del MVP original.

**Explícitamente fuera de alcance:**

- Notas generadas automáticamente por la IA (el modelo de datos las admite — ver sección 3 — pero
  nada en este spec las genera; hoy solo un asesor humano escribe notas).
- Restringir quién puede reasignar una conversación (hoy cualquier usuario autenticado puede — ver
  sección 6, nota sobre por qué esto no es una laguna de este spec). Reglas de permisos más finas
  quedan para spec 014 (Admin Governance).
- Notificaciones o recordatorios push cuando un seguimiento vence — este spec solo permite
  programarlo, verlo, filtrarlo y resolverlo; avisar proactivamente es una evolución futura.

---

## 1. Migración — `0004_add_contact_enrichment_and_follow_ups`

```python
def upgrade() -> None:
    op.add_column(
        "contacts",
        sa.Column("tags", sa.JSON(), nullable=False, server_default="[]"),
    )
    op.add_column(
        "contacts",
        sa.Column("is_favorite", sa.Boolean(), nullable=False, server_default=sa.false()),
    )
    op.add_column(
        "opportunities",
        sa.Column("has_unread_messages", sa.Boolean(), nullable=False, server_default=sa.false()),
    )

    op.create_table(
        "contact_notes",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column("contact_id", sa.Uuid(), sa.ForeignKey("contacts.id"), nullable=False),
        sa.Column("author_id", sa.Uuid(), sa.ForeignKey("internal_users.id"), nullable=False),
        sa.Column("content", sa.Text(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_contact_notes_contact_id", "contact_notes", ["contact_id"])

    op.create_table(
        "follow_ups",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column("opportunity_id", sa.Uuid(), sa.ForeignKey("opportunities.id"), nullable=False),
        sa.Column("due_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("reason", sa.Text(), nullable=False),
        sa.Column("created_by", sa.Uuid(), sa.ForeignKey("internal_users.id"), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("resolved_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.create_index("ix_follow_ups_opportunity_id", "follow_ups", ["opportunity_id"])
```

`tags` como columna `JSON` (no una tabla de etiquetas propia) — mismo patrón ya usado en
`MessageModel.extra_metadata` (spec 003). Al tamaño de este proyecto, filtrar en Python sobre la
lista ya cargada es más simple que mantener una tabla de relación N:M, y se revisita solo si el
volumen real de contactos lo justifica — mismo criterio de "no abstraer sin una segunda
implementación o un límite real de infraestructura" (`03_Engineering_Principles.md`).

---

## 2. `Contact` — etiquetas y favorito

`core/entities/contact.py` — dos campos nuevos, al final (mismo lugar que `phone_number`/`email`,
para no romper construcción posicional existente):

```python
tags: list[str] = field(default_factory=list)
is_favorite: bool = False
```

Sin métodos nuevos en la entidad — agregar/quitar una etiqueta es mutar la lista directamente
desde el caso de uso, no hay invariante que proteger (una etiqueta repetida simplemente no se
vuelve a agregar; ver sección siguiente).

`app/use_cases/add_contact_tag.py` / `remove_contact_tag.py` / `toggle_contact_favorite.py` —
mismo patrón de siempre (cargar, mutar, `save()`, `commit()`):

```python
class AddContactTagUseCase:
    def __init__(self, session_factory: async_sessionmaker[AsyncSession]) -> None:
        self._session_factory = session_factory

    async def execute(self, contact_id: ContactId, tag: str) -> Contact:
        async with SQLAlchemyUnitOfWork(self._session_factory) as uow:
            contact = await uow.contacts.get_by_id(contact_id)
            if contact is None:
                raise ContactNotFoundError(contact_id)
            if tag not in contact.tags:
                contact.tags.append(tag)
                await uow.contacts.save(contact)
                await uow.commit()
        return contact
```

`RemoveContactTagUseCase` es el mismo caso de uso con `contact.tags.remove(tag)` dentro de un
`if tag in contact.tags`. `ToggleContactFavoriteUseCase` invierte `contact.is_favorite`.

Endpoints nuevos, router nuevo `app/api/routers/contacts.py` (protegido igual que
`opportunities.py`):

| Método y ruta | Acción |
|---|---|
| `POST /organizations/{slug}/contacts/{id}/tags` (body `{tag: str}`) | agrega una etiqueta |
| `DELETE /organizations/{slug}/contacts/{id}/tags/{tag}` | quita una etiqueta |
| `POST /organizations/{slug}/contacts/{id}/favorite` | invierte `is_favorite` |
| `GET /organizations/{slug}/contacts/{id}/notes` | lista notas (sección 3) |
| `POST /organizations/{slug}/contacts/{id}/notes` (body `{advisor_id, content}`) | agrega una nota |

`ContactSummaryResponse` (`app/api/dto/contact.py`, nuevo archivo — separa DTOs de contacto de los
de oportunidad a medida que crecen) gana los dos campos:

```python
class ContactSummaryResponse(BaseModel):
    display_name: str
    phone_number: str | None
    tags: list[str]
    is_favorite: bool

    @classmethod
    def from_domain(cls, contact: Contact) -> ContactSummaryResponse:
        return cls(
            display_name=contact.display_name,
            phone_number=contact.phone_number,
            tags=contact.tags,
            is_favorite=contact.is_favorite,
        )
```

Ya viaja dentro de `OpenOpportunityResponse`/`ConversationHistoryResponse` (spec 012) — ningún
endpoint nuevo hace falta solo para *ver* las etiquetas/favorito en la lista o el detalle.

---

## 3. Notas de contacto — `ContactNote`

Entidad nueva (append-only, mismo espíritu que `ConversationSummary` de spec 006 — nunca se edita
ni se borra una nota, solo se agregan nuevas):

`core/entities/contact_note.py`:

```python
@dataclass(frozen=True)
class ContactNote:
    id: ContactNoteId
    contact_id: ContactId
    author_id: InternalUserId
    content: str
    created_at: datetime
```

Siempre autoría humana en este spec — `author_id` es obligatorio, no `str | None` con un caso
especial para IA. El campo se llama `author_id`, no `advisor_id`, deliberadamente: si algún día una
nota la genera la IA, el tipo no debería mentir sobre quién la escribió — pero esa es una decisión
de un spec futuro, no algo que este introduzca a medias.

`core/interfaces/repositories.py` — `ContactNoteRepository` nuevo (Protocol justificado: es un
puerto real hacia infraestructura de persistencia, mismo criterio que el resto de repositorios):

```python
class ContactNoteRepository(Protocol):
    async def list_by_contact(self, contact_id: ContactId) -> list[ContactNote]: ...
    async def save(self, note: ContactNote) -> None: ...
```

`save()` siempre inserta (`session.add()`, nunca `merge()`) — mismo motivo que
`ConversationSummaryRepository`: append-only, no hay fila que actualizar.

`app/use_cases/add_contact_note.py` / `list_contact_notes.py` — el segundo resuelve también el
nombre de cada autor (los asesores no tienen forma de recordar UUIDs), con `get_by_id()` en un
loop — aceptable a esta escala (un contacto tiene pocas notas, cada una con pocos autores
distintos); no se agrega un `list_by_ids()` a `InternalUserRepository` solo para esto, a diferencia
de `ContactRepository.list_by_ids()` en spec 012, que sí lo necesitaba para no repetir la consulta
por cada oportunidad de una lista potencialmente larga.

`ContactNoteResponse` (`app/api/dto/contact.py`):

```python
class ContactNoteResponse(BaseModel):
    id: str
    author_name: str
    content: str
    created_at: datetime
```

---

## 4. Seguimientos — `FollowUp`

`core/entities/follow_up.py` — a diferencia de `ContactNote`, sí muta (se resuelve):

```python
@dataclass
class FollowUp:
    id: FollowUpId
    opportunity_id: OpportunityId
    due_at: datetime
    reason: str
    created_by: InternalUserId
    created_at: datetime
    resolved_at: datetime | None = None

    @property
    def is_resolved(self) -> bool:
        return self.resolved_at is not None

    def resolve(self) -> None:
        self.resolved_at = datetime.now(tz=UTC)
```

**Ligado a `Opportunity`, no a `Contact`** — decisión explícita: un seguimiento necesita responder
"¿a quién está asignado?", y esa respuesta vive en `Opportunity.assigned_advisor_id`, no en
`Contact` (que no tiene ningún concepto de asignación). Etiquetas/notas/favorito sí describen al
cliente en general (por eso van en `Contact`); un seguimiento describe una acción pendiente sobre
un caso concreto que alguien está atendiendo.

**Regla de negocio: un solo seguimiento activo (sin resolver) por oportunidad.** Coincide con la
UI ya validada en el mockup (el panel muestra "Programar seguimiento" *o* la tarjeta del pendiente,
nunca ambos). Nueva excepción:

```python
class FollowUpAlreadyScheduledError(DomainError):
    def __init__(self, opportunity_id: OpportunityId) -> None:
        super().__init__(f"Opportunity {opportunity_id} already has an active follow-up")
```

`core/interfaces/repositories.py` — `FollowUpRepository`:

```python
class FollowUpRepository(Protocol):
    async def get_active_by_opportunity(
        self,
        opportunity_id: OpportunityId,
    ) -> FollowUp | None: ...

    async def list_active_by_opportunity_ids(
        self,
        opportunity_ids: list[OpportunityId],
    ) -> list[FollowUp]: ...

    async def save(self, follow_up: FollowUp) -> None: ...
```

`list_active_by_opportunity_ids` evita N+1 al construir la lista de oportunidades (sección 7) —
mismo motivo que `ContactRepository.list_by_ids` en spec 012. `save()` usa `merge()` (a diferencia
de `ContactNoteRepository`) porque un `FollowUp` sí se actualiza in-place al resolverse.

`app/use_cases/schedule_follow_up.py`:

```python
class ScheduleFollowUpUseCase:
    def __init__(self, session_factory: async_sessionmaker[AsyncSession]) -> None:
        self._session_factory = session_factory

    async def execute(
        self,
        opportunity_id: OpportunityId,
        advisor_id: InternalUserId,
        due_at: datetime,
        reason: str,
    ) -> FollowUp:
        async with SQLAlchemyUnitOfWork(self._session_factory) as uow:
            opportunity = await uow.opportunities.get_by_id(opportunity_id)
            if opportunity is None:
                raise OpportunityNotFoundError(opportunity_id)

            existing = await uow.follow_ups.get_active_by_opportunity(opportunity_id)
            if existing is not None:
                raise FollowUpAlreadyScheduledError(opportunity_id)

            follow_up = FollowUp(
                id=FollowUpId.generate(),
                opportunity_id=opportunity_id,
                due_at=due_at,
                reason=reason,
                created_by=advisor_id,
                created_at=datetime.now(tz=UTC),
            )
            await uow.follow_ups.save(follow_up)
            await uow.commit()
        return follow_up
```

`app/use_cases/resolve_follow_up.py` — carga el seguimiento activo de una oportunidad (404 propio,
`FollowUpNotFoundError`, si no hay ninguno), llama `.resolve()`, guarda.

`FollowUpResponse` (`app/api/dto/follow_up.py`, nuevo):

```python
class FollowUpResponse(BaseModel):
    id: str
    due_at: datetime
    reason: str

    @classmethod
    def from_domain(cls, follow_up: FollowUp) -> FollowUpResponse:
        return cls(id=str(follow_up.id), due_at=follow_up.due_at, reason=follow_up.reason)
```

Solo se serializan seguimientos **activos** — un `FollowUp` resuelto simplemente deja de aparecer
(`OpenOpportunityResponse.follow_up`/`ConversationHistoryResponse.follow_up` vuelven a `None`), no
hace falta un campo `resolved_at` en la respuesta para este spec. "Vencido" (mostrado en el mockup
con otro color) se calcula en el frontend comparando `due_at` contra la hora actual — no es un
estado que la base de datos necesite guardar.

Endpoints, mismo router `opportunities.py`:

| Método y ruta | Body | Acción |
|---|---|---|
| `POST /organizations/{slug}/opportunities/{id}/follow-up` | `{advisor_id, due_at, reason}` | programa (422 si ya hay uno activo) |
| `POST /organizations/{slug}/opportunities/{id}/follow-up/resolve` | — | marca como resuelto (404 si no hay uno activo) |

---

## 5. "No leído" — `Opportunity.has_unread_messages`

`core/entities/opportunity.py` — un campo y dos métodos, mismo estilo que
`assign_to_advisor()`/`return_to_ai()`:

```python
has_unread_messages: bool = False  # nuevo campo del dataclass

def mark_unread(self) -> None:
    self.has_unread_messages = True

def mark_read(self) -> None:
    self.has_unread_messages = False
```

**Automático en dos puntos, manual en un tercero:**

1. `app/use_cases/receive_incoming_message.py` (spec 006) — después de guardar el mensaje entrante
   del cliente: `opportunity.mark_unread()` antes de `save()`. Se marca sin importar si
   `attention_mode` es `AI` o `HUMAN` — la bandera indica actividad nueva sin revisar, no
   "necesita intervención humana" (eso ya lo indica `attention_mode` por su cuenta).
2. `app/use_cases/get_conversation_history.py` — al final de `execute()`, si
   `opportunity.has_unread_messages` es `True`, se llama `mark_read()` y se guarda **en la misma
   transacción de lectura**. Es una excepción deliberada a "los casos de uso de lectura no
   escriben": abrir la conversación *es* la señal de "ya lo vi", igual que en cualquier cliente de
   chat — el efecto secundario es mínimo (un `UPDATE` de una columna) y evita necesitar un
   endpoint separado solo para esto.
3. Manual — nuevo `app/use_cases/set_opportunity_unread.py`, para el botón "Marcar como no
   leída"/"Marcar como leída" del menú de tres puntos (ya validado en el mockup): recibe
   `unread: bool` explícito en vez de invertir, para que marcar-como-leída y marcar-como-no-leída
   sean la misma llamada con distinto valor, no dos endpoints.

```python
class SetOpportunityUnreadUseCase:
    async def execute(self, opportunity_id: OpportunityId, unread: bool) -> Opportunity:
        async with SQLAlchemyUnitOfWork(self._session_factory) as uow:
            opportunity = await uow.opportunities.get_by_id(opportunity_id)
            if opportunity is None:
                raise OpportunityNotFoundError(opportunity_id)
            opportunity.mark_unread() if unread else opportunity.mark_read()
            await uow.opportunities.save(opportunity)
            await uow.commit()
        return opportunity
```

Endpoint: `POST /organizations/{slug}/opportunities/{id}/unread` con body `{"unread": true|false}`.

`has_unread_messages` se agrega directamente a `OpportunityResponse` (a diferencia de
`contact`/`follow_up`, que van en los DTOs contenedores) — es un campo propio de `Opportunity`, sin
consulta adicional, así que no hay ningún motivo para no incluirlo siempre:

```python
class OpportunityResponse(BaseModel):
    # ...campos existentes...
    has_unread_messages: bool
```

---

## 6. Reasignación entre asesores

**No hace falta un endpoint nuevo.** `AssignToAdvisorUseCase` (spec 009) ya asigna
`assigned_advisor_id` sin comprobar si la oportunidad ya estaba asignada a otro asesor —
`Opportunity.assign_to_advisor()` simplemente sobreescribe. Reasignar es llamar
`POST .../assign-advisor` con un `advisor_id` distinto — funciona hoy, sin cambios de backend.

Lo que faltaba, y sí es nuevo: el frontend nunca tuvo cómo obtener **nombres** de otros asesores
para poblar el selector de "Reasignar a" (mismo gap que spec 012 dejó anotado al no poder mostrar
"Asignada a Andrea T." en la pestaña Todas). El repositorio ya tenía el método
(`InternalUserRepository.list_advisors_by_organization`, desde spec 008) — **nunca se conectó a
un endpoint.**

`app/use_cases/list_advisors.py`:

```python
class ListAdvisorsUseCase:
    def __init__(self, session_factory: async_sessionmaker[AsyncSession]) -> None:
        self._session_factory = session_factory

    async def execute(self, organization_slug: str) -> list[InternalUser]:
        async with SQLAlchemyUnitOfWork(self._session_factory) as uow:
            organization = await uow.organizations.get_by_slug(organization_slug)
            if organization is None:
                raise OrganizationSlugNotFoundError(organization_slug)
            return await uow.internal_users.list_advisors_by_organization(organization.id)
```

Solo devuelve rol `Advisor` (no `Administrator`) — así estaba filtrado el método desde que se
escribió en spec 008; se respeta ese filtro existente en vez de cambiarlo de paso.

`app/api/dto/advisor.py` (nuevo): `AdvisorSummaryResponse{id: str, full_name: str}`. Endpoint:
`GET /organizations/{slug}/advisors`.

**Por qué "cualquiera puede reasignar" no es una laguna de este spec:** hoy ningún endpoint de
`opportunities.py` distingue roles (comentario ya existente en ese router: "Advisor y
Administrator pueden hacer las cuatro cosas por igual"). Restringir reasignación a ciertos roles
sería inventar una regla de permisos que ninguna otra acción de este router tiene — spec 014
(Admin Governance) es donde corresponde decidir reglas de permisos, no aquí, por consistencia con
el resto del router.

---

## 7. Listas y detalle — `follow_up` en `OpenOpportunity`/`ConversationHistory`

`app/use_cases/list_open_opportunities.py` — `OpenOpportunity` gana un campo, resuelto en batch:

```python
@dataclass(frozen=True)
class OpenOpportunity:
    opportunity: Opportunity
    contact: Contact
    follow_up: FollowUp | None
```

Dentro de `execute()`, después de resolver `contacts_by_id` (spec 012):

```python
follow_ups_by_opportunity = {
    f.opportunity_id: f
    for f in await uow.follow_ups.list_active_by_opportunity_ids([o.id for o in opportunities])
}
...
follow_up=follow_ups_by_opportunity.get(o.id)
```

`app/use_cases/get_conversation_history.py` — `ConversationHistory` gana el mismo campo,
resuelto con `get_active_by_opportunity()` (una sola oportunidad, no hace falta la versión batch).

`OpenOpportunityResponse`/`ConversationHistoryResponse` (`app/api/dto/opportunity.py`) agregan
`follow_up: FollowUpResponse | None`.

---

## 8. Búsqueda — nombre de contacto (spec 012) + contenido de mensajes

`OpportunityRepository.search_open_by_organization` (nuevo método, mismo archivo que
`list_open_by_organization`):

```python
async def search_open_by_organization(
    self,
    organization_id: OrganizationId,
    query: str,
) -> list[Opportunity]:
    pattern = f"%{query}%"
    result = await self._session.execute(
        select(OpportunityModel)
        .join(ContactModel, ContactModel.id == OpportunityModel.contact_id)
        .outerjoin(ConversationModel, ConversationModel.opportunity_id == OpportunityModel.id)
        .outerjoin(MessageModel, MessageModel.conversation_id == ConversationModel.id)
        .where(
            OpportunityModel.organization_id == organization_id.value,
            ~OpportunityModel.status.in_(_TERMINAL_STATUSES),
            sa.or_(
                ContactModel.display_name.ilike(pattern),
                ContactModel.phone_number.ilike(pattern),
                MessageModel.content.ilike(pattern),
            ),
        )
        .distinct()
        .order_by(OpportunityModel.last_activity_at.desc())
    )
    return [_to_entity(model) for model in result.scalars().all()]
```

**Limitación aceptada, no un bug:** `ILIKE` sobre SQLite es case-insensitive solo para ASCII — una
búsqueda de "café" no encontrará "Café" con mayúscula acentuada. Suficiente para MVP; resolver
colación acentuada correctamente necesitaría FTS5 o normalizar a la escritura, que no se justifica
todavía a este volumen de datos.

`app/use_cases/search_opportunities.py` — mismo patrón que `ListOpenOpportunitiesUseCase`
(resuelve `Contact`/`FollowUp` en batch para las oportunidades que matchean), devuelve
`list[OpenOpportunity]`. Endpoint: `GET /organizations/{slug}/opportunities/search?q=...` →
`list[OpenOpportunityResponse]` (mismo shape que el listado, así el frontend reutiliza el mismo
renderizado de fila).

---

## 9. Frontend

Con etiquetas/notas/favorito/seguimiento/no-leído/reasignación ya disponibles del backend, esta
sección conecta lo que el mockup (`docs/design/amza_workspace_mockup/`) ya validó — la mayoría del
código React porta directamente esa lógica, ya probada visualmente.

**Barra de herramientas de la lista** (spec 012 la dejó pendiente a propósito): ícono de orden
cíclico (por defecto → recientes → no leídos → seguimiento → por defecto) y un menú de filtros de
tres puntos — "Asignado a" solo visible en la pestaña Todas, "No leídos", "Seguimiento pendiente",
y etiquetas (multi-selección, coincide cualquier etiqueta marcada) — mismo diseño y misma
corrección de bugs ya resueltas en el mockup (cerrar en fase de captura, nunca duplicar el menú al
re-renderizar — ver memoria de decisiones técnicas si se reintroduce el patrón a mano en vez de
portar el código ya corregido).

**Panel de información del cliente** (`frontend/components/contact-panel.tsx`, nuevo): se abre al
hacer clic en el avatar dentro del encabezado del chat. Muestra info básica (`contact.phone_number`,
etc.), etiquetas con `+ Etiqueta` (`useAddContactTag`/`useRemoveContactTag`), notas
(`useContactNotes` + `useAddContactNote`), y el bloque de seguimiento (`useScheduleFollowUp`/
`useResolveFollowUp`) con el **selector real de fecha y hora** (calendario flotante → hora AM/PM)
ya construido y corregido en el mockup — portar ese componente, no rehacerlo.

**Favorito**: estrella no-clicable en la fila de la lista (visual, evita anidar un botón dentro del
`<button>` de la fila — mismo motivo que en el mockup), botón real en el encabezado del chat y en
el panel de cliente (`useToggleFavorite`).

**Reasignación**: botón "Reasignar" junto a "Devolver a IA" cuando `attention_mode === "human"`,
con un menú poblado por `useAdvisors()` (nuevo hook, `GET /api/organizations/.../advisors`),
llamando al mismo `useAssignToAdvisor()` que ya existe (spec 009) con el `advisor_id` elegido.

**No leído**: badge con el número en la lista (`opportunity.has_unread_messages` es booleano, no
un contador real — el badge siempre muestra un punto/indicador, no una cifra, a diferencia del
mockup que usaba un número de ejemplo); opción "Marcar como no leída"/"leída" en el menú de tres
puntos del encabezado del chat (`useSetUnread`).

**Búsqueda**: `frontend/hooks/use-search-opportunities.ts` nuevo, reemplaza el filtro puramente
client-side de spec 012 cuando el usuario escribe una consulta no vacía — llama al endpoint de la
sección 8 (`GET .../opportunities/search`) en vez de filtrar solo por nombre en memoria.

---

## 10. Tests

Política vigente desde spec 008: este spec incluye pruebas de lo que introduce, y actualiza las
que su cambio de comportamiento rompe (spec 012's e2e ya necesitará adaptarse al nuevo shape de
`OpportunityResponse`/`OpenOpportunityResponse` con `has_unread_messages`/`follow_up`).

- Backend (`tests/test_contact_enrichment.py`, nuevo):
  1. Agregar/quitar una etiqueta es idempotente (agregar dos veces la misma no duplica; quitar una
     que no existe no lanza error).
  2. Alternar favorito invierte el valor cada vez.
  3. Agregar una nota y listarlas devuelve el nombre del autor correcto, en orden cronológico.
  4. Programar un seguimiento con uno ya activo → 422 (`FollowUpAlreadyScheduledError`).
  5. Resolver un seguimiento sin ninguno activo → 404.
  6. Resolver un seguimiento activo y volver a listar oportunidades → ya no aparece en
     `follow_up`.
  7. `ReceiveIncomingMessageUseCase` marca `has_unread_messages=True` en un mensaje entrante nuevo.
  8. `GetConversationHistoryUseCase` marca `has_unread_messages=False` tras leer una conversación
     que estaba marcada como no leída.
  9. `POST .../assign-advisor` reasigna correctamente de un asesor a otro (no solo de IA a un
     asesor) — regresión explícita, ya que hoy nadie prueba ese camino.
  10. `GET .../advisors` devuelve solo asesores activos con rol Advisor, ordenados por nombre.
  11. `GET .../opportunities/search?q=...` encuentra una oportunidad tanto por nombre de contacto
      como por contenido de un mensaje, sin distinguir mayúsculas/minúsculas (ASCII).
- Frontend (`frontend/tests/e2e/advisor-workspace.spec.ts`, extender): abrir el panel de cliente,
  agregar una etiqueta y una nota, programarlo un seguimiento con el selector de fecha/hora,
  marcarlo resuelto, reasignar una conversación a otro asesor, marcar/desmarcar como no leída, y
  buscar por una palabra que solo existe dentro de un mensaje (no en el nombre del contacto).

---

## Próximo paso

Spec 014 — **Admin Governance & Access Control**: modelo de administrador principal +
administradores (agregar/eliminar usuarios, solo el principal puede eliminar administradores,
nadie se elimina a sí mismo — recomendación ya registrada en `PROJECT_STATE.md`), y las primeras
reglas de permisos reales sobre estos routers (hoy deliberadamente sin distinción de rol, ver
sección 6).
