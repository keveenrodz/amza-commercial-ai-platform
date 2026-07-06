from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime

import structlog
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from app.services.conversation_context_assembler import ConversationContextAssembler
from app.services.conversation_summarization_service import ConversationSummarizationService
from core.entities.contact import Contact
from core.entities.conversation import Conversation
from core.entities.message import Message
from core.entities.opportunity import Opportunity
from core.enums.channel import ChannelType
from core.enums.message import MessageContentType, MessageRole
from core.enums.opportunity import AttentionMode, OpportunityStatus
from core.enums.user import ContactStatus
from core.exceptions.domain import NoActiveAgentError, OrganizationSlugNotFoundError
from core.interfaces.providers import AIProvider, ChannelProvider
from core.value_objects.identifiers import (
    ContactId,
    ConversationId,
    MessageId,
    OpportunityId,
)
from infrastructure.database.unit_of_work import SQLAlchemyUnitOfWork

logger = structlog.get_logger()


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
        context_assembler: ConversationContextAssembler,
        summarization_service: ConversationSummarizationService,
        summary_trigger_messages: int,
    ) -> None:
        self._session_factory = session_factory
        self._ai_provider = ai_provider
        self._channel_provider = channel_provider
        self._context_assembler = context_assembler
        self._summarization_service = summarization_service
        self._summary_trigger_messages = summary_trigger_messages

    async def execute(self, input: IncomingMessageInput) -> Opportunity:  # noqa: A002
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
                context = await self._context_assembler.assemble(conversation.id, uow)
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

        if opportunity.attention_mode == AttentionMode.AI:
            await self._maybe_summarize(conversation.id)

        return opportunity

    async def _maybe_summarize(self, conversation_id: ConversationId) -> None:
        # Segunda transacción, deliberadamente separada de la principal: el cliente ya recibió
        # su respuesta vía channel_provider.send() antes de llegar aquí, así que un fallo o la
        # latencia de este bloque no le afectan. Best-effort — si falla, se loguea y se
        # recalculará en el siguiente disparo. Sin asyncio.create_task(): sin cola de tareas ni
        # supervisión, una excepción ahí se tragaría en silencio.
        try:
            async with SQLAlchemyUnitOfWork(self._session_factory) as uow:
                previous = await uow.conversation_summaries.get_latest(conversation_id)
                since = previous.up_to_sent_at if previous else None
                count = await uow.messages.count_since(conversation_id, after=since)
                if count >= self._summary_trigger_messages:
                    await self._summarization_service.execute(conversation_id, uow)
                    await uow.commit()
        except Exception:
            logger.warning("summary.generation_failed", conversation_id=str(conversation_id))
