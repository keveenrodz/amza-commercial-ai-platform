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
from core.exceptions.domain import NoActiveAgentError, OrganizationSlugNotFoundError
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
                context = await self._build_context(conversation, uow)
                response_text = await self._ai_provider.generate(
                    context, opportunity.agent_id
                )
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
        - Llamar AIProvider.summarize(all_messages, agent_id) -> str
        - Guardar el resumen como Message(sender_role=SYSTEM) en DB para trazabilidad
        - Retornar [summary_message] + últimos 50 mensajes no-SYSTEM
        El diseño exacto (costos, cuándo resumir vs. truncar) se decide en spec 006
        junto con la implementación de AIProvider.
        """
        return await uow.messages.list_by_conversation(
            conversation.id,
            limit=_AI_CONTEXT_MESSAGES,
        )
