# 005 Application Services

## Propósito

Implementar los casos de uso que orquestan el flujo de negocio: coordinan entidades de dominio,
repositorios y providers para ejecutar las operaciones principales de la plataforma.

---

## 1. Correcciones a Spec 004 — Message Repository

### 1.1 `modules/opportunities/repositories/message.py` — orden de `list_by_conversation`

La implementación actual usa `ORDER BY sent_at ASC LIMIT ?`, que retorna los **primeros** N
mensajes (los más antiguos). Para el contexto de AI necesitamos los **últimos** N mensajes
en orden cronológico.

**Corrección:** cambiar a `ORDER BY sent_at DESC LIMIT ?` y revertir el resultado. El método
sigue retornando mensajes en orden cronológico (ASC) para cualquier caller, pero ahora
carga los más recientes cuando la conversación tiene más de `limit` mensajes.

```python
async def list_by_conversation(
    self,
    conversation_id: ConversationId,
    limit: int,
) -> list[Message]:
    result = await self._session.execute(
        select(MessageModel)
        .where(MessageModel.conversation_id == conversation_id.value)
        .order_by(MessageModel.sent_at.desc())
        .limit(limit)
    )
    return [_to_entity(m) for m in reversed(result.scalars().all())]
```

---

## 2. Correcciones a Spec 002 — Excepciones de Dominio

Agregar dos excepciones a `core/exceptions/domain.py`:

```python
class OrganizationSlugNotFoundError(DomainError):
    def __init__(self, slug: str) -> None:
        super().__init__(f"Organization with slug {slug!r} not found")
        self.slug = slug


class InternalUserNotFoundError(DomainError):
    def __init__(self, user_id: InternalUserId) -> None:
        super().__init__(f"InternalUser {user_id} not found")
        self.user_id = user_id


class NoActiveAgentError(DomainError):
    def __init__(self, organization_id: OrganizationId) -> None:
        super().__init__(f"No active agent found for organization {organization_id}")
        self.organization_id = organization_id
```

`OrganizationSlugNotFoundError` — se usa cuando se busca la organización por slug al recibir
un mensaje entrante y no existe.

`InternalUserNotFoundError` — se usa cuando se asigna un asesor por ID y no existe.

`NoActiveAgentError` — se usa cuando se crea una oportunidad nueva y la organización no tiene
ningún agente activo.

Las tres deben importarse en el `__init__` de `core/exceptions/` si lo hay, o simplemente se
importan directamente desde `core.exceptions.domain`.

---

## 3. Manejo de errores HTTP — `app/exceptions.py`

Agregar handlers para las excepciones de dominio. Los casos de uso no atrapan errores — los
dejan subir. La capa FastAPI los convierte a HTTP.

```python
from core.exceptions.domain import (
    DomainError,
    InternalUserNotFoundError,
    InvalidStatusTransitionError,
    NoActiveAgentError,
    OpportunityAlreadyClosedError,
    OpportunityNotFoundError,
    OrganizationNotFoundError,
    OrganizationSlugNotFoundError,
)

_NOT_FOUND_ERRORS = (
    OpportunityNotFoundError,
    OrganizationNotFoundError,
    OrganizationSlugNotFoundError,
    InternalUserNotFoundError,
    NoActiveAgentError,
)

_UNPROCESSABLE_ERRORS = (
    InvalidStatusTransitionError,
    OpportunityAlreadyClosedError,
)


def register_exception_handlers(app: FastAPI) -> None:
    @app.exception_handler(Exception)
    async def unhandled_exception_handler(...) -> JSONResponse:
        ...  # already exists

    @app.exception_handler(DomainError)
    async def domain_error_handler(request: Request, exc: DomainError) -> JSONResponse:
        if isinstance(exc, _NOT_FOUND_ERRORS):
            return JSONResponse(status_code=404, content={"detail": str(exc)})
        if isinstance(exc, _UNPROCESSABLE_ERRORS):
            return JSONResponse(status_code=422, content={"detail": str(exc)})
        logger.warning("domain.error.unhandled", error=str(exc))
        return JSONResponse(status_code=400, content={"detail": str(exc)})
```

---

## 4. Application Services

### Estructura de archivos

```
app/
  use_cases/
    __init__.py
    receive_incoming_message.py    → ReceiveIncomingMessageUseCase
    assign_to_advisor.py           → AssignToAdvisorUseCase
    return_to_ai.py                → ReturnToAIUseCase
    get_conversation_history.py    → GetConversationHistoryUseCase
```

### Patrón común

Cada caso de uso:
- Recibe sus dependencias por constructor (session_factory, providers)
- Expone un método `async def execute(...)` con los parámetros del caso de uso
- Crea un `SQLAlchemyUnitOfWork` por ejecución — la transacción dura lo que dura el `execute`
- Propaga excepciones de dominio sin atraparlas (las maneja `app/exceptions.py`)

---

### 4.1 `app/use_cases/receive_incoming_message.py`

#### Input

```python
@dataclass(frozen=True)
class IncomingMessageInput:
    organization_slug: str
    channel_type: ChannelType
    external_contact_id: str
    contact_display_name: str
    content: str
    content_type: MessageContentType
    provider_message_id: str | None = None
```

#### Flujo completo

```
1. Cargar organización por slug           → OrganizationSlugNotFoundError si no existe
2. Find-or-create Contact                 → crea con ContactStatus.ACTIVE si no existe
3. Find-or-create Opportunity activa      → crea con status=NEW, attention_mode=AI si no existe
   └─ Si crea: cargar agente default      → NoActiveAgentError si la org no tiene agente activo
4. Find-or-create Conversation            → crea con started_at=now, ended_at=None si no existe
5. Guardar mensaje entrante (MessageRole.USER)
6. opportunity.record_activity()
7. Guardar opportunity actualizada
8. Si attention_mode == AI:
   └─ _build_context() → últimos 50 mensajes
   └─ AIProvider.generate(context, opportunity.agent_id) → response_text
   └─ Crear y guardar mensaje de respuesta (MessageRole.ASSISTANT)
   └─ ChannelProvider.send(response_message, opportunity)
   Nota: send() ocurre antes del commit. Limitación aceptada en MVP; el outbox pattern
   se evaluará cuando se discuta idempotencia en spec 006.
9. Si attention_mode == HUMAN:
   El mensaje entrante ya está guardado (paso 5). El asesor responde desde el dashboard
   de la plataforma o directamente desde su app nativa (Telegram/WhatsApp). Las respuestas
   via app nativa no pasan por la plataforma y no se almacenan — esa trazabilidad es
   opcional y queda fuera del MVP.
10. commit()
11. Retornar opportunity
```

#### `_build_context` — extension point para spec 006

```python
_AI_CONTEXT_MESSAGES = 50

async def _build_context(
    self,
    conversation: Conversation,
    uow: SQLAlchemyUnitOfWork,
) -> list[Message]:
    """
    Retorna los mensajes de contexto para AIProvider.generate().

    SPEC 006 — Resumen por inactividad:
    Cuando last_activity_at lleva más de 2 horas sin actividad, este método deberá:
    - Llamar AIProvider.summarize(all_messages, agent_id) → str  (nuevo método en el Protocol)
    - Guardar el resumen como Message(sender_role=SYSTEM) en DB para trazabilidad
    - Retornar [summary_message] + últimos 50 mensajes no-SYSTEM
    El diseño exacto (costo de llamadas, cuándo resumir vs. truncar) se decide en spec 006
    junto con la implementación de AIProvider.
    """
    return await uow.messages.list_by_conversation(
        conversation.id,
        limit=_AI_CONTEXT_MESSAGES,
    )
```

#### Código completo

```python
from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from core.entities.contact import Contact
from core.entities.conversation import Conversation
from core.entities.message import Message
from core.entities.opportunity import Opportunity
from core.enums.channel import ChannelType
from core.enums.message import MessageContentType, MessageRole
from core.enums.opportunity import AttentionMode, OpportunityStatus
from core.enums.user import ContactStatus
from core.exceptions.domain import (
    NoActiveAgentError,
    OrganizationSlugNotFoundError,
)
from core.interfaces.providers import AIProvider, ChannelProvider
from core.value_objects.identifiers import (
    ContactId,
    ConversationId,
    MessageId,
    OpportunityId,
)
from infrastructure.database.unit_of_work import SQLAlchemyUnitOfWork

_AI_CONTEXT_MESSAGES = 50


@dataclass(frozen=True)
class IncomingMessageInput:
    organization_slug: str
    channel_type: ChannelType
    external_contact_id: str
    contact_display_name: str
    content: str
    content_type: MessageContentType
    provider_message_id: str | None = None


class ReceiveIncomingMessageUseCase:
    def __init__(
        self,
        session_factory: async_sessionmaker[AsyncSession],
        ai_provider: AIProvider,
        channel_provider: ChannelProvider,
    ) -> None:
        self._session_factory = session_factory
        self._ai_provider = ai_provider
        self._channel_provider = channel_provider

    async def execute(self, input: IncomingMessageInput) -> Opportunity:
        async with SQLAlchemyUnitOfWork(self._session_factory) as uow:
            organization = await uow.organizations.get_by_slug(input.organization_slug)
            if organization is None:
                raise OrganizationSlugNotFoundError(input.organization_slug)

            contact = await uow.contacts.get_by_external_id(
                input.external_contact_id,
                input.channel_type,
                organization.id,
            )
            if contact is None:
                now = datetime.now(tz=UTC)
                contact = Contact(
                    id=ContactId.generate(),
                    organization_id=organization.id,
                    channel_type=input.channel_type,
                    external_id=input.external_contact_id,
                    display_name=input.contact_display_name,
                    status=ContactStatus.ACTIVE,
                    created_at=now,
                    updated_at=now,
                )
                await uow.contacts.save(contact)

            opportunity = await uow.opportunities.get_active_by_contact(
                contact.id,
                input.channel_type,
            )
            if opportunity is None:
                agent = await uow.agents.get_default_by_organization(organization.id)
                if agent is None:
                    raise NoActiveAgentError(organization.id)
                now = datetime.now(tz=UTC)
                opportunity = Opportunity(
                    id=OpportunityId.generate(),
                    organization_id=organization.id,
                    contact_id=contact.id,
                    agent_id=agent.id,
                    attention_mode=AttentionMode.AI,
                    assigned_advisor_id=None,
                    status=OpportunityStatus.NEW,
                    channel_type=input.channel_type,
                    started_at=now,
                    last_activity_at=now,
                    closed_at=None,
                )
                await uow.opportunities.save(opportunity)

            conversation = await uow.conversations.get_by_opportunity(opportunity.id)
            if conversation is None:
                conversation = Conversation(
                    id=ConversationId.generate(),
                    opportunity_id=opportunity.id,
                    started_at=datetime.now(tz=UTC),
                    ended_at=None,
                )
                await uow.conversations.save(conversation)

            incoming_message = Message(
                id=MessageId.generate(),
                conversation_id=conversation.id,
                sender_role=MessageRole.USER,
                content_type=input.content_type,
                content=input.content,
                channel_type=input.channel_type,
                sent_at=datetime.now(tz=UTC),
                provider_message_id=input.provider_message_id,
            )
            await uow.messages.save(incoming_message)

            opportunity.record_activity()
            await uow.opportunities.save(opportunity)

            if opportunity.attention_mode == AttentionMode.AI:
                context = await self._build_context(conversation, uow)
                response_text = await self._ai_provider.generate(context, opportunity.agent_id)

                response_message = Message(
                    id=MessageId.generate(),
                    conversation_id=conversation.id,
                    sender_role=MessageRole.ASSISTANT,
                    content_type=MessageContentType.TEXT,
                    content=response_text,
                    channel_type=input.channel_type,
                    sent_at=datetime.now(tz=UTC),
                )
                await uow.messages.save(response_message)
                await self._channel_provider.send(response_message, opportunity)

            await uow.commit()
            return opportunity

    async def _build_context(
        self,
        conversation: Conversation,
        uow: SQLAlchemyUnitOfWork,
    ) -> list[Message]:
        """
        Retorna los mensajes de contexto para AIProvider.generate().

        SPEC 006 — Resumen por inactividad:
        Cuando last_activity_at lleva más de 2 horas sin actividad, este método deberá:
        - Llamar AIProvider.summarize(all_messages, agent_id) → str
        - Guardar el resumen como Message(sender_role=SYSTEM) en DB para trazabilidad
        - Retornar [summary_message] + últimos 50 mensajes no-SYSTEM
        El diseño exacto (costos, cuándo resumir vs. truncar) se decide en spec 006
        junto con la implementación de AIProvider.
        """
        return await uow.messages.list_by_conversation(
            conversation.id,
            limit=_AI_CONTEXT_MESSAGES,
        )
```

---

### 4.2 `app/use_cases/assign_to_advisor.py`

```python
from __future__ import annotations

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from core.entities.opportunity import Opportunity
from core.enums.opportunity import OpportunityStatus
from core.exceptions.domain import (
    InternalUserNotFoundError,
    InvalidStatusTransitionError,
    OpportunityNotFoundError,
)
from core.value_objects.identifiers import InternalUserId, OpportunityId
from infrastructure.database.unit_of_work import SQLAlchemyUnitOfWork


class AssignToAdvisorUseCase:
    def __init__(self, session_factory: async_sessionmaker[AsyncSession]) -> None:
        self._session_factory = session_factory

    async def execute(
        self,
        opportunity_id: OpportunityId,
        advisor_id: InternalUserId,
    ) -> Opportunity:
        async with SQLAlchemyUnitOfWork(self._session_factory) as uow:
            opportunity = await uow.opportunities.get_by_id(opportunity_id)
            if opportunity is None:
                raise OpportunityNotFoundError(opportunity_id)

            advisor = await uow.internal_users.get_by_id(advisor_id)
            if advisor is None:
                raise InternalUserNotFoundError(advisor_id)

            opportunity.assign_to_advisor(advisor_id)

            try:
                opportunity.transition_to(OpportunityStatus.WAITING_FOR_ADVISOR)
            except InvalidStatusTransitionError:
                # El estado actual no permite WAITING_FOR_ADVISOR (ej. QUOTATION_PENDING).
                # La asignación ocurre de todas formas; el estado no cambia.
                pass

            opportunity.record_activity()
            await uow.opportunities.save(opportunity)
            await uow.commit()
            return opportunity
```

---

### 4.3 `app/use_cases/return_to_ai.py`

```python
from __future__ import annotations

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from core.entities.opportunity import Opportunity
from core.enums.opportunity import OpportunityStatus
from core.exceptions.domain import (
    InvalidStatusTransitionError,
    OpportunityNotFoundError,
)
from core.value_objects.identifiers import OpportunityId
from infrastructure.database.unit_of_work import SQLAlchemyUnitOfWork


class ReturnToAIUseCase:
    def __init__(self, session_factory: async_sessionmaker[AsyncSession]) -> None:
        self._session_factory = session_factory

    async def execute(self, opportunity_id: OpportunityId) -> Opportunity:
        async with SQLAlchemyUnitOfWork(self._session_factory) as uow:
            opportunity = await uow.opportunities.get_by_id(opportunity_id)
            if opportunity is None:
                raise OpportunityNotFoundError(opportunity_id)

            opportunity.return_to_ai()

            try:
                opportunity.transition_to(OpportunityStatus.QUALIFIED)
            except InvalidStatusTransitionError:
                # El estado actual no permite QUALIFIED desde aquí (ej. QUOTATION_SENT).
                # El modo AI se restaura de todas formas; el estado no cambia.
                pass

            opportunity.record_activity()
            await uow.opportunities.save(opportunity)
            await uow.commit()
            return opportunity
```

---

### 4.4 `app/use_cases/get_conversation_history.py`

#### Output

```python
@dataclass(frozen=True)
class ConversationHistory:
    opportunity: Opportunity
    conversation: Conversation | None
    messages: list[Message]
```

#### Código completo

```python
from __future__ import annotations

from dataclasses import dataclass

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from core.entities.conversation import Conversation
from core.entities.message import Message
from core.entities.opportunity import Opportunity
from core.exceptions.domain import OpportunityNotFoundError
from core.value_objects.identifiers import OpportunityId
from infrastructure.database.unit_of_work import SQLAlchemyUnitOfWork

_DEFAULT_MESSAGE_LIMIT = 50


@dataclass(frozen=True)
class ConversationHistory:
    opportunity: Opportunity
    conversation: Conversation | None
    messages: list[Message]


class GetConversationHistoryUseCase:
    def __init__(self, session_factory: async_sessionmaker[AsyncSession]) -> None:
        self._session_factory = session_factory

    async def execute(
        self,
        opportunity_id: OpportunityId,
        message_limit: int = _DEFAULT_MESSAGE_LIMIT,
    ) -> ConversationHistory:
        async with SQLAlchemyUnitOfWork(self._session_factory) as uow:
            opportunity = await uow.opportunities.get_by_id(opportunity_id)
            if opportunity is None:
                raise OpportunityNotFoundError(opportunity_id)

            conversation = await uow.conversations.get_by_opportunity(opportunity_id)

            messages: list[Message] = []
            if conversation is not None:
                messages = await uow.messages.list_by_conversation(
                    conversation.id,
                    limit=message_limit,
                )

            return ConversationHistory(
                opportunity=opportunity,
                conversation=conversation,
                messages=messages,
            )
```

---

## 5. Proceso de Implementación

```
1. Corregir list_by_conversation en modules/opportunities/repositories/message.py
2. Agregar 3 excepciones a core/exceptions/domain.py
3. Actualizar app/exceptions.py con los domain error handlers
4. Crear app/use_cases/__init__.py
5. Crear los 4 archivos de casos de uso
6. Validar: ruff check . && mypy app core infrastructure modules
7. Commit
```

---

## 6. Validación

```bash
ruff check .
mypy app core infrastructure modules
```

MyPy verificará que `ReceiveIncomingMessageUseCase` satisface sus dependencias tipadas:
- `AIProvider` y `ChannelProvider` son Protocols — cualquier implementación es válida
- `SQLAlchemyUnitOfWork` satisface `UnitOfWork` Protocol estructuralmente

No hay migración en este spec — no se modifica el schema de base de datos.
