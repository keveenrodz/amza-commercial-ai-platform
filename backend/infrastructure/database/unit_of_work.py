from __future__ import annotations

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from core.interfaces.repositories import (
    AgentRepository,
    ContactNoteRepository,
    ContactRepository,
    ConversationRepository,
    ConversationSummaryRepository,
    FollowUpRepository,
    InternalUserRepository,
    MessageRepository,
    OpportunityRepository,
    OrganizationRepository,
)
from modules.agents.repositories.agent import SQLAlchemyAgentRepository
from modules.configuration.repositories.organization import SQLAlchemyOrganizationRepository
from modules.memory.repositories.conversation_summary import (
    SQLAlchemyConversationSummaryRepository,
)
from modules.opportunities.repositories.contact import SQLAlchemyContactRepository
from modules.opportunities.repositories.contact_note import SQLAlchemyContactNoteRepository
from modules.opportunities.repositories.conversation import SQLAlchemyConversationRepository
from modules.opportunities.repositories.follow_up import SQLAlchemyFollowUpRepository
from modules.opportunities.repositories.message import SQLAlchemyMessageRepository
from modules.opportunities.repositories.opportunity import SQLAlchemyOpportunityRepository
from modules.users.repositories.internal_user import SQLAlchemyInternalUserRepository


class SQLAlchemyUnitOfWork:
    opportunities: OpportunityRepository
    conversations: ConversationRepository
    messages: MessageRepository
    conversation_summaries: ConversationSummaryRepository
    contacts: ContactRepository
    contact_notes: ContactNoteRepository
    follow_ups: FollowUpRepository
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
        self.conversation_summaries = SQLAlchemyConversationSummaryRepository(self._session)
        self.contacts = SQLAlchemyContactRepository(self._session)
        self.contact_notes = SQLAlchemyContactNoteRepository(self._session)
        self.follow_ups = SQLAlchemyFollowUpRepository(self._session)
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
