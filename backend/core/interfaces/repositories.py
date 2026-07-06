from __future__ import annotations

from datetime import datetime
from typing import Protocol

from core.entities.agent import Agent
from core.entities.contact import Contact
from core.entities.conversation import Conversation
from core.entities.conversation_summary import ConversationSummary
from core.entities.internal_user import InternalUser
from core.entities.message import Message
from core.entities.opportunity import Opportunity
from core.entities.organization import Organization
from core.enums.channel import ChannelType
from core.value_objects.identifiers import (
    AgentId,
    ContactId,
    ConversationId,
    InternalUserId,
    MessageId,
    OpportunityId,
    OrganizationId,
)


class OpportunityRepository(Protocol):
    async def get_by_id(self, id: OpportunityId) -> Opportunity | None: ...

    async def get_active_by_contact(
        self,
        contact_id: ContactId,
        channel_type: ChannelType,
    ) -> Opportunity | None: ...

    async def save(self, opportunity: Opportunity) -> None: ...

    async def list_open_by_organization(
        self,
        organization_id: OrganizationId,
    ) -> list[Opportunity]: ...


class ConversationRepository(Protocol):
    async def get_by_id(self, id: ConversationId) -> Conversation | None: ...

    async def get_by_opportunity(
        self,
        opportunity_id: OpportunityId,
    ) -> Conversation | None: ...

    async def save(self, conversation: Conversation) -> None: ...


class MessageRepository(Protocol):
    async def get_by_id(self, id: MessageId) -> Message | None: ...

    async def list_by_conversation(
        self,
        conversation_id: ConversationId,
        limit: int,
    ) -> list[Message]: ...

    async def list_since(
        self,
        conversation_id: ConversationId,
        after: datetime | None,
    ) -> list[Message]:
        """after es exclusivo: sent_at > after, nunca >= (evita re-resumir el mensaje de corte)."""
        ...

    async def count_since(
        self,
        conversation_id: ConversationId,
        after: datetime | None,
    ) -> int:
        """after es exclusivo, mismo criterio que list_since."""
        ...

    async def save(self, message: Message) -> None: ...


class ConversationSummaryRepository(Protocol):
    async def get_latest(
        self,
        conversation_id: ConversationId,
    ) -> ConversationSummary | None: ...

    async def save(self, summary: ConversationSummary) -> None: ...


class ContactRepository(Protocol):
    async def get_by_id(self, id: ContactId) -> Contact | None: ...

    async def get_by_external_id(
        self,
        external_id: str,
        channel_type: ChannelType,
        organization_id: OrganizationId,
    ) -> Contact | None: ...

    async def save(self, contact: Contact) -> None: ...


class AgentRepository(Protocol):
    async def get_by_id(self, id: AgentId) -> Agent | None: ...

    async def get_default_by_organization(
        self,
        organization_id: OrganizationId,
    ) -> Agent | None: ...

    async def save(self, agent: Agent) -> None: ...


class OrganizationRepository(Protocol):
    async def get_by_id(self, id: OrganizationId) -> Organization | None: ...

    async def get_by_slug(self, slug: str) -> Organization | None: ...


class InternalUserRepository(Protocol):
    async def get_by_id(self, id: InternalUserId) -> InternalUser | None: ...

    async def list_advisors_by_organization(
        self,
        organization_id: OrganizationId,
    ) -> list[InternalUser]: ...


class UnitOfWork(Protocol):
    opportunities: OpportunityRepository
    conversations: ConversationRepository
    messages: MessageRepository
    conversation_summaries: ConversationSummaryRepository
    contacts: ContactRepository
    agents: AgentRepository
    organizations: OrganizationRepository
    internal_users: InternalUserRepository

    async def commit(self) -> None: ...

    async def rollback(self) -> None: ...

    async def __aenter__(self) -> UnitOfWork: ...

    async def __aexit__(
        self,
        exc_type: type[BaseException] | None,
        exc_val: BaseException | None,
        exc_tb: object,
    ) -> None: ...
