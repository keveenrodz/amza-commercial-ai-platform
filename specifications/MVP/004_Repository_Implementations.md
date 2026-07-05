# 004 Repository Implementations

## Propósito

Implementar los adaptadores SQLAlchemy que satisfacen los `Protocol` definidos en
`core/interfaces/repositories.py`, conectando la capa de dominio con la capa de persistencia.

Este spec también corrige 5 desajustes de campos descubiertos entre spec 002 (entidades) y
spec 003 (ORM models) al escribir los mappers.

---

## 1. Correcciones a Spec 002 — Entidades del Dominio

Las entidades del dominio son la fuente de verdad. Los ORM models deben reflejar las entidades,
no al revés.

### 1.1 `core/entities/agent.py`

`description: str` no tiene uso ni en el ORM ni en la lógica de negocio de un agente de IA.
Los campos reales de un agente son `system_prompt` (instrucciones que definen su comportamiento)
y `model` (el modelo de lenguaje que ejecuta esas instrucciones).

```python
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime

from core.enums.agent import AgentStatus
from core.value_objects.identifiers import AgentId, OrganizationId


@dataclass
class Agent:
    id: AgentId
    organization_id: OrganizationId
    name: str
    system_prompt: str
    model: str
    status: AgentStatus
    created_at: datetime
    updated_at: datetime
```

### 1.2 `core/entities/message.py`

Cuatro ajustes para alinear con el ORM y con el dominio real:

- `role` → `sender_role` (consistencia con el ORM)
- `created_at` → `sent_at` (los mensajes se envían; "created" es técnico, "sent" es de negocio)
- Agregar `channel_type: ChannelType` (los mensajes son canal-específicos; el formato de
  `content` varía por canal)
- `metadata` permanece en la entidad; el ORM lo almacena con atributo Python `extra_metadata`
  apuntando a la columna `metadata` (workaround al nombre reservado de SQLAlchemy)

```python
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any

from core.enums.channel import ChannelType
from core.enums.message import MessageContentType, MessageRole
from core.value_objects.identifiers import ConversationId, MessageId


@dataclass
class Message:
    id: MessageId
    conversation_id: ConversationId
    sender_role: MessageRole
    content_type: MessageContentType
    content: str
    channel_type: ChannelType
    sent_at: datetime
    provider_message_id: str | None = None
    metadata: dict[str, Any] = field(default_factory=dict)
```

### 1.3 `core/entities/conversation.py`

`created_at`/`updated_at` son nombres genéricos. Para una conversación, `started_at` y
`ended_at` expresan el ciclo de vida del negocio. El ORM ya los usa así; la entidad debe
coincidir. `ended_at` es `None` mientras la conversación está activa.

```python
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime

from core.value_objects.identifiers import ConversationId, OpportunityId


@dataclass
class Conversation:
    id: ConversationId
    opportunity_id: OpportunityId
    started_at: datetime
    ended_at: datetime | None
```

### 1.4 `core/entities/contact.py`

Agregar `phone_number` y `email` como campos opcionales. El ORM ya los tiene. Son datos de
contacto relevantes para el negocio (WhatsApp y email como canales futuros).

```python
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime

from core.enums.channel import ChannelType
from core.enums.user import ContactStatus
from core.value_objects.identifiers import ContactId, OrganizationId


@dataclass
class Contact:
    id: ContactId
    organization_id: OrganizationId
    channel_type: ChannelType
    external_id: str
    display_name: str
    status: ContactStatus
    created_at: datetime
    updated_at: datetime
    phone_number: str | None = None
    email: str | None = None
```

### 1.5 `core/entities/internal_user.py`

`name` → `full_name`. El ORM ya usa `full_name`. Es más explícito y evita ambigüedad con
nombre parcial.

```python
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime

from core.enums.user import InternalUserRole, InternalUserStatus
from core.value_objects.identifiers import InternalUserId, OrganizationId


@dataclass
class InternalUser:
    id: InternalUserId
    organization_id: OrganizationId
    full_name: str
    email: str
    role: InternalUserRole
    status: InternalUserStatus
    created_at: datetime
    updated_at: datetime
```

---

## 2. Correcciones a Spec 003 — ORM Models

### 2.1 `modules/opportunities/models/message.py`

Agregar `content_type` (tipo de contenido del mensaje) y `provider_message_id` (ID externo
asignado por Telegram/WhatsApp; necesario para evitar duplicados y correlacionar callbacks).

```python
from __future__ import annotations

import uuid
from datetime import datetime
from typing import Any

import sqlalchemy as sa
from sqlalchemy.orm import Mapped, mapped_column

from infrastructure.database.base import Base


class MessageModel(Base):
    __tablename__ = "messages"
    __table_args__ = (
        sa.Index("ix_messages_conversation_id", "conversation_id"),
        sa.Index("ix_messages_sent_at", "sent_at"),
    )

    id: Mapped[uuid.UUID] = mapped_column(sa.Uuid(native_uuid=False), primary_key=True)
    conversation_id: Mapped[uuid.UUID] = mapped_column(sa.Uuid(native_uuid=False), nullable=False)
    sender_role: Mapped[str] = mapped_column(sa.String(50), nullable=False)
    content_type: Mapped[str] = mapped_column(sa.String(50), nullable=False)
    content: Mapped[str] = mapped_column(sa.Text, nullable=False)
    channel_type: Mapped[str] = mapped_column(sa.String(50), nullable=False)
    sent_at: Mapped[datetime] = mapped_column(sa.DateTime(timezone=True), nullable=False)
    provider_message_id: Mapped[str | None] = mapped_column(sa.String(255), nullable=True)
    extra_metadata: Mapped[dict[str, Any] | None] = mapped_column(
        "metadata", sa.JSON, nullable=True
    )
```

### 2.2 `modules/opportunities/models/contact.py`

Agregar `status`. La entidad ya lo tiene (`ContactStatus`). Sin él no se puede persistir ni
recuperar el estado del contacto.

```python
from __future__ import annotations

import uuid
from datetime import datetime

import sqlalchemy as sa
from sqlalchemy.orm import Mapped, mapped_column

from infrastructure.database.base import Base


class ContactModel(Base):
    __tablename__ = "contacts"
    __table_args__ = (
        sa.UniqueConstraint(
            "external_id", "channel_type", "organization_id",
            name="uq_contacts_external_id_channel_org",
        ),
        sa.Index("ix_contacts_organization_id", "organization_id"),
    )

    id: Mapped[uuid.UUID] = mapped_column(sa.Uuid(native_uuid=False), primary_key=True)
    organization_id: Mapped[uuid.UUID] = mapped_column(sa.Uuid(native_uuid=False), nullable=False)
    external_id: Mapped[str] = mapped_column(sa.String(255), nullable=False)
    channel_type: Mapped[str] = mapped_column(sa.String(50), nullable=False)
    display_name: Mapped[str] = mapped_column(sa.String(255), nullable=False)
    status: Mapped[str] = mapped_column(sa.String(50), nullable=False)
    phone_number: Mapped[str | None] = mapped_column(sa.String(50), nullable=True)
    email: Mapped[str | None] = mapped_column(sa.String(255), nullable=True)
    created_at: Mapped[datetime] = mapped_column(sa.DateTime(timezone=True), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(sa.DateTime(timezone=True), nullable=False)
```

---

## 3. Migración — `migrations/versions/0002_fix_entity_model_alignment.py`

Agrega las 3 columnas faltantes. Los `server_default` son requeridos por SQLite: no permite
`ADD COLUMN NOT NULL` sin un valor por defecto para las filas existentes.

El `down_revision` debe apuntar al revision ID real de `0001_initial_schema.py` (que es
`da934eca16fd`).

```python
"""fix entity model alignment

Revision ID: 0002
Revises: da934eca16fd
Create Date: 2026-07-05
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0002"
down_revision: str | None = "da934eca16fd"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column(
        "messages",
        sa.Column("content_type", sa.String(50), nullable=False, server_default="text"),
    )
    op.add_column(
        "messages",
        sa.Column("provider_message_id", sa.String(255), nullable=True),
    )
    op.add_column(
        "contacts",
        sa.Column("status", sa.String(50), nullable=False, server_default="active"),
    )


def downgrade() -> None:
    # SQLite no soporta DROP COLUMN en versiones < 3.35.
    # En PostgreSQL se implementaría con op.drop_column().
    pass
```

---

## 4. Repository Implementations

### Estructura de archivos

```
modules/
  agents/repositories/
    __init__.py
    agent.py                       → SQLAlchemyAgentRepository
  configuration/repositories/
    __init__.py
    organization.py                → SQLAlchemyOrganizationRepository
  opportunities/repositories/
    __init__.py
    contact.py                     → SQLAlchemyContactRepository
    conversation.py                → SQLAlchemyConversationRepository
    message.py                     → SQLAlchemyMessageRepository
    opportunity.py                 → SQLAlchemyOpportunityRepository
  users/repositories/
    __init__.py
    internal_user.py               → SQLAlchemyInternalUserRepository
infrastructure/database/
  unit_of_work.py                  → SQLAlchemyUnitOfWork
```

### Patrón de mappers

Cada archivo de repositorio contiene dos funciones privadas a nivel de módulo:

- `_to_entity(model)` — ORM model → domain entity
- `_from_entity(entity)` — domain entity → ORM model (para `save()`)

Conversiones que realiza cada mapper:
- `model.id` (tipo `uuid.UUID`) → `XxxId(value=model.id)`
- `entity.id.value` (tipo `uuid.UUID`) → campo del ORM
- `model.status` (tipo `str`) → `XxxStatus(model.status)`
- `entity.status.value` (tipo `str`) → campo del ORM

### `save()` usa `session.merge()`

`merge()` hace INSERT-or-UPDATE por primary key: si el PK ya existe en el identity map o en
la base de datos, actualiza; si no, inserta. Retorna la instancia gestionada por la sesión.
Como `save()` retorna `None`, no usamos el valor de retorno.

### 4.1 `modules/opportunities/repositories/opportunity.py`

```python
from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from core.entities.opportunity import Opportunity
from core.enums.channel import ChannelType
from core.enums.opportunity import AttentionMode, OpportunityStatus
from core.value_objects.identifiers import (
    AgentId,
    ContactId,
    InternalUserId,
    OpportunityId,
    OrganizationId,
)
from modules.opportunities.models.opportunity import OpportunityModel

_TERMINAL_STATUSES = (
    OpportunityStatus.WON.value,
    OpportunityStatus.LOST.value,
    OpportunityStatus.CLOSED.value,
)


def _to_entity(model: OpportunityModel) -> Opportunity:
    return Opportunity(
        id=OpportunityId(value=model.id),
        organization_id=OrganizationId(value=model.organization_id),
        contact_id=ContactId(value=model.contact_id),
        agent_id=AgentId(value=model.agent_id),
        attention_mode=AttentionMode(model.attention_mode),
        assigned_advisor_id=(
            InternalUserId(value=model.assigned_advisor_id)
            if model.assigned_advisor_id
            else None
        ),
        status=OpportunityStatus(model.status),
        channel_type=ChannelType(model.channel_type),
        started_at=model.started_at,
        last_activity_at=model.last_activity_at,
        closed_at=model.closed_at,
    )


def _from_entity(entity: Opportunity) -> OpportunityModel:
    return OpportunityModel(
        id=entity.id.value,
        organization_id=entity.organization_id.value,
        contact_id=entity.contact_id.value,
        agent_id=entity.agent_id.value,
        assigned_advisor_id=(
            entity.assigned_advisor_id.value if entity.assigned_advisor_id else None
        ),
        attention_mode=entity.attention_mode.value,
        status=entity.status.value,
        channel_type=entity.channel_type.value,
        started_at=entity.started_at,
        last_activity_at=entity.last_activity_at,
        closed_at=entity.closed_at,
    )


class SQLAlchemyOpportunityRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def get_by_id(self, id: OpportunityId) -> Opportunity | None:
        result = await self._session.execute(
            select(OpportunityModel).where(OpportunityModel.id == id.value)
        )
        model = result.scalar_one_or_none()
        return _to_entity(model) if model else None

    async def get_active_by_contact(
        self,
        contact_id: ContactId,
        channel_type: ChannelType,
    ) -> Opportunity | None:
        result = await self._session.execute(
            select(OpportunityModel)
            .where(
                OpportunityModel.contact_id == contact_id.value,
                OpportunityModel.channel_type == channel_type.value,
                ~OpportunityModel.status.in_(_TERMINAL_STATUSES),
            )
            .order_by(OpportunityModel.started_at.desc())
            .limit(1)
        )
        model = result.scalar_one_or_none()
        return _to_entity(model) if model else None

    async def save(self, opportunity: Opportunity) -> None:
        await self._session.merge(_from_entity(opportunity))

    async def list_open_by_organization(
        self,
        organization_id: OrganizationId,
    ) -> list[Opportunity]:
        result = await self._session.execute(
            select(OpportunityModel)
            .where(
                OpportunityModel.organization_id == organization_id.value,
                ~OpportunityModel.status.in_(_TERMINAL_STATUSES),
            )
            .order_by(OpportunityModel.last_activity_at.desc())
        )
        return [_to_entity(m) for m in result.scalars().all()]
```

### 4.2 `modules/opportunities/repositories/contact.py`

```python
from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from core.entities.contact import Contact
from core.enums.channel import ChannelType
from core.enums.user import ContactStatus
from core.value_objects.identifiers import ContactId, OrganizationId
from modules.opportunities.models.contact import ContactModel


def _to_entity(model: ContactModel) -> Contact:
    return Contact(
        id=ContactId(value=model.id),
        organization_id=OrganizationId(value=model.organization_id),
        channel_type=ChannelType(model.channel_type),
        external_id=model.external_id,
        display_name=model.display_name,
        status=ContactStatus(model.status),
        created_at=model.created_at,
        updated_at=model.updated_at,
        phone_number=model.phone_number,
        email=model.email,
    )


def _from_entity(entity: Contact) -> ContactModel:
    return ContactModel(
        id=entity.id.value,
        organization_id=entity.organization_id.value,
        channel_type=entity.channel_type.value,
        external_id=entity.external_id,
        display_name=entity.display_name,
        status=entity.status.value,
        phone_number=entity.phone_number,
        email=entity.email,
        created_at=entity.created_at,
        updated_at=entity.updated_at,
    )


class SQLAlchemyContactRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def get_by_id(self, id: ContactId) -> Contact | None:
        result = await self._session.execute(
            select(ContactModel).where(ContactModel.id == id.value)
        )
        model = result.scalar_one_or_none()
        return _to_entity(model) if model else None

    async def get_by_external_id(
        self,
        external_id: str,
        channel_type: ChannelType,
        organization_id: OrganizationId,
    ) -> Contact | None:
        result = await self._session.execute(
            select(ContactModel).where(
                ContactModel.external_id == external_id,
                ContactModel.channel_type == channel_type.value,
                ContactModel.organization_id == organization_id.value,
            )
        )
        model = result.scalar_one_or_none()
        return _to_entity(model) if model else None

    async def save(self, contact: Contact) -> None:
        await self._session.merge(_from_entity(contact))
```

### 4.3 `modules/opportunities/repositories/conversation.py`

```python
from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from core.entities.conversation import Conversation
from core.value_objects.identifiers import ConversationId, OpportunityId
from modules.opportunities.models.conversation import ConversationModel


def _to_entity(model: ConversationModel) -> Conversation:
    return Conversation(
        id=ConversationId(value=model.id),
        opportunity_id=OpportunityId(value=model.opportunity_id),
        started_at=model.started_at,
        ended_at=model.ended_at,
    )


def _from_entity(entity: Conversation) -> ConversationModel:
    return ConversationModel(
        id=entity.id.value,
        opportunity_id=entity.opportunity_id.value,
        started_at=entity.started_at,
        ended_at=entity.ended_at,
    )


class SQLAlchemyConversationRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def get_by_id(self, id: ConversationId) -> Conversation | None:
        result = await self._session.execute(
            select(ConversationModel).where(ConversationModel.id == id.value)
        )
        model = result.scalar_one_or_none()
        return _to_entity(model) if model else None

    async def get_by_opportunity(
        self,
        opportunity_id: OpportunityId,
    ) -> Conversation | None:
        result = await self._session.execute(
            select(ConversationModel).where(
                ConversationModel.opportunity_id == opportunity_id.value
            )
        )
        model = result.scalar_one_or_none()
        return _to_entity(model) if model else None

    async def save(self, conversation: Conversation) -> None:
        await self._session.merge(_from_entity(conversation))
```

### 4.4 `modules/opportunities/repositories/message.py`

```python
from __future__ import annotations

from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from core.entities.message import Message
from core.enums.channel import ChannelType
from core.enums.message import MessageContentType, MessageRole
from core.value_objects.identifiers import ConversationId, MessageId
from modules.opportunities.models.message import MessageModel


def _to_entity(model: MessageModel) -> Message:
    return Message(
        id=MessageId(value=model.id),
        conversation_id=ConversationId(value=model.conversation_id),
        sender_role=MessageRole(model.sender_role),
        content_type=MessageContentType(model.content_type),
        content=model.content,
        channel_type=ChannelType(model.channel_type),
        sent_at=model.sent_at,
        provider_message_id=model.provider_message_id,
        metadata=model.extra_metadata if model.extra_metadata is not None else {},
    )


def _from_entity(entity: Message) -> MessageModel:
    return MessageModel(
        id=entity.id.value,
        conversation_id=entity.conversation_id.value,
        sender_role=entity.sender_role.value,
        content_type=entity.content_type.value,
        content=entity.content,
        channel_type=entity.channel_type.value,
        sent_at=entity.sent_at,
        provider_message_id=entity.provider_message_id,
        extra_metadata=entity.metadata if entity.metadata else None,
    )


class SQLAlchemyMessageRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def get_by_id(self, id: MessageId) -> Message | None:
        result = await self._session.execute(
            select(MessageModel).where(MessageModel.id == id.value)
        )
        model = result.scalar_one_or_none()
        return _to_entity(model) if model else None

    async def list_by_conversation(
        self,
        conversation_id: ConversationId,
        limit: int,
    ) -> list[Message]:
        result = await self._session.execute(
            select(MessageModel)
            .where(MessageModel.conversation_id == conversation_id.value)
            .order_by(MessageModel.sent_at.asc())
            .limit(limit)
        )
        return [_to_entity(m) for m in result.scalars().all()]

    async def save(self, message: Message) -> None:
        await self._session.merge(_from_entity(message))
```

### 4.5 `modules/configuration/repositories/organization.py`

`OrganizationRepository` no define `save()` — las organizaciones se gestionan fuera del
flujo de conversaciones en el MVP.

```python
from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from core.entities.organization import Organization
from core.enums.user import OrganizationStatus
from core.value_objects.identifiers import OrganizationId
from modules.configuration.models.organization import OrganizationModel


def _to_entity(model: OrganizationModel) -> Organization:
    return Organization(
        id=OrganizationId(value=model.id),
        name=model.name,
        slug=model.slug,
        timezone=model.timezone,
        language=model.language,
        status=OrganizationStatus(model.status),
        created_at=model.created_at,
        updated_at=model.updated_at,
    )


class SQLAlchemyOrganizationRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def get_by_id(self, id: OrganizationId) -> Organization | None:
        result = await self._session.execute(
            select(OrganizationModel).where(OrganizationModel.id == id.value)
        )
        model = result.scalar_one_or_none()
        return _to_entity(model) if model else None

    async def get_by_slug(self, slug: str) -> Organization | None:
        result = await self._session.execute(
            select(OrganizationModel).where(OrganizationModel.slug == slug)
        )
        model = result.scalar_one_or_none()
        return _to_entity(model) if model else None
```

### 4.6 `modules/users/repositories/internal_user.py`

`list_advisors_by_organization()` retorna solo asesores activos — los únicos que pueden
recibir asignaciones. Ordenados por `full_name ASC` para visualización consistente.

```python
from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from core.entities.internal_user import InternalUser
from core.enums.user import InternalUserRole, InternalUserStatus
from core.value_objects.identifiers import InternalUserId, OrganizationId
from modules.users.models.internal_user import InternalUserModel


def _to_entity(model: InternalUserModel) -> InternalUser:
    return InternalUser(
        id=InternalUserId(value=model.id),
        organization_id=OrganizationId(value=model.organization_id),
        full_name=model.full_name,
        email=model.email,
        role=InternalUserRole(model.role),
        status=InternalUserStatus(model.status),
        created_at=model.created_at,
        updated_at=model.updated_at,
    )


class SQLAlchemyInternalUserRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def get_by_id(self, id: InternalUserId) -> InternalUser | None:
        result = await self._session.execute(
            select(InternalUserModel).where(InternalUserModel.id == id.value)
        )
        model = result.scalar_one_or_none()
        return _to_entity(model) if model else None

    async def list_advisors_by_organization(
        self,
        organization_id: OrganizationId,
    ) -> list[InternalUser]:
        result = await self._session.execute(
            select(InternalUserModel)
            .where(
                InternalUserModel.organization_id == organization_id.value,
                InternalUserModel.role == InternalUserRole.ADVISOR.value,
                InternalUserModel.status == InternalUserStatus.ACTIVE.value,
            )
            .order_by(InternalUserModel.full_name.asc())
        )
        return [_to_entity(m) for m in result.scalars().all()]
```

### 4.7 `modules/agents/repositories/agent.py`

`get_default_by_organization()` retorna el primer agente activo de la organización ordenado
por `created_at ASC`. Convención para MVP: una organización tiene un agente activo principal.

```python
from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from core.entities.agent import Agent
from core.enums.agent import AgentStatus
from core.value_objects.identifiers import AgentId, OrganizationId
from modules.agents.models.agent import AgentModel


def _to_entity(model: AgentModel) -> Agent:
    return Agent(
        id=AgentId(value=model.id),
        organization_id=OrganizationId(value=model.organization_id),
        name=model.name,
        system_prompt=model.system_prompt,
        model=model.model,
        status=AgentStatus(model.status),
        created_at=model.created_at,
        updated_at=model.updated_at,
    )


def _from_entity(entity: Agent) -> AgentModel:
    return AgentModel(
        id=entity.id.value,
        organization_id=entity.organization_id.value,
        name=entity.name,
        system_prompt=entity.system_prompt,
        model=entity.model,
        status=entity.status.value,
        created_at=entity.created_at,
        updated_at=entity.updated_at,
    )


class SQLAlchemyAgentRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def get_by_id(self, id: AgentId) -> Agent | None:
        result = await self._session.execute(
            select(AgentModel).where(AgentModel.id == id.value)
        )
        model = result.scalar_one_or_none()
        return _to_entity(model) if model else None

    async def get_default_by_organization(
        self,
        organization_id: OrganizationId,
    ) -> Agent | None:
        result = await self._session.execute(
            select(AgentModel)
            .where(
                AgentModel.organization_id == organization_id.value,
                AgentModel.status == AgentStatus.ACTIVE.value,
            )
            .order_by(AgentModel.created_at.asc())
            .limit(1)
        )
        model = result.scalar_one_or_none()
        return _to_entity(model) if model else None

    async def save(self, agent: Agent) -> None:
        await self._session.merge(_from_entity(agent))
```

---

## 5. `infrastructure/database/unit_of_work.py`

`SQLAlchemyUnitOfWork` implementa el `UnitOfWork` Protocol. Crea la sesión al entrar al
context manager y la cierra al salir (siempre). Si ocurre una excepción, hace rollback antes
de cerrar.

Los atributos de repositorio se declaran con el tipo del Protocol (no la implementación)
para que MyPy verifique la compatibilidad estructural correctamente.

```python
from __future__ import annotations

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from core.interfaces.repositories import (
    AgentRepository,
    ContactRepository,
    ConversationRepository,
    InternalUserRepository,
    MessageRepository,
    OpportunityRepository,
    OrganizationRepository,
)
from modules.agents.repositories.agent import SQLAlchemyAgentRepository
from modules.configuration.repositories.organization import SQLAlchemyOrganizationRepository
from modules.opportunities.repositories.contact import SQLAlchemyContactRepository
from modules.opportunities.repositories.conversation import SQLAlchemyConversationRepository
from modules.opportunities.repositories.message import SQLAlchemyMessageRepository
from modules.opportunities.repositories.opportunity import SQLAlchemyOpportunityRepository
from modules.users.repositories.internal_user import SQLAlchemyInternalUserRepository


class SQLAlchemyUnitOfWork:
    opportunities: OpportunityRepository
    conversations: ConversationRepository
    messages: MessageRepository
    contacts: ContactRepository
    agents: AgentRepository
    organizations: OrganizationRepository
    internal_users: InternalUserRepository

    def __init__(self, session_factory: async_sessionmaker[AsyncSession]) -> None:
        self._session_factory = session_factory

    async def __aenter__(self) -> SQLAlchemyUnitOfWork:
        self._session: AsyncSession = self._session_factory()
        self.opportunities = SQLAlchemyOpportunityRepository(self._session)
        self.conversations = SQLAlchemyConversationRepository(self._session)
        self.messages = SQLAlchemyMessageRepository(self._session)
        self.contacts = SQLAlchemyContactRepository(self._session)
        self.agents = SQLAlchemyAgentRepository(self._session)
        self.organizations = SQLAlchemyOrganizationRepository(self._session)
        self.internal_users = SQLAlchemyInternalUserRepository(self._session)
        return self

    async def __aexit__(
        self,
        exc_type: type[BaseException] | None,
        exc_val: BaseException | None,
        exc_tb: object,
    ) -> None:
        if exc_type is not None:
            await self.rollback()
        await self._session.close()

    async def commit(self) -> None:
        await self._session.commit()

    async def rollback(self) -> None:
        await self._session.rollback()
```

---

## 6. Proceso de Implementación

```
1. Actualizar las 5 entidades en core/entities/
2. Actualizar los 2 ORM models en modules/*/models/
3. Crear migrations/versions/0002_fix_entity_model_alignment.py
4. Ejecutar: alembic upgrade head
5. Crear directorios modules/*/repositories/ con __init__.py
6. Crear los 7 archivos de repositorio
7. Crear infrastructure/database/unit_of_work.py
8. Validar: ruff check . && mypy app core infrastructure modules
9. Commit
```

---

## 7. Validación

```bash
ruff check .
mypy app core infrastructure modules
alembic upgrade head   # debe reportar "Running upgrade da934eca16fd -> 0002"
```

MyPy con `strict = true` verificará que cada repositorio satisface estructuralmente su
Protocol correspondiente y que `SQLAlchemyUnitOfWork` satisface `UnitOfWork`.
