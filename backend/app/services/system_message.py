from __future__ import annotations

from datetime import UTC, datetime

from core.entities.message import Message
from core.entities.opportunity import Opportunity
from core.enums.message import MessageContentType, MessageRole
from core.interfaces.repositories import UnitOfWork
from core.value_objects.identifiers import MessageId

# Compartido por los casos de uso que cambian el estado de una oportunidad (reasignar, devolver a
# IA, programar/resolver un seguimiento) -- no es una abstracción nueva (Protocol/interfaz), solo
# una función para no repetir "buscar la conversación, construir el Message, guardarlo" cuatro
# veces (ver 03_Engineering_Principles.md sobre cuándo una abstracción se justifica).


async def record_system_message(uow: UnitOfWork, opportunity: Opportunity, content: str) -> None:
    conversation = await uow.conversations.get_by_opportunity(opportunity.id)
    if conversation is None:
        return
    message = Message(
        id=MessageId.generate(),
        conversation_id=conversation.id,
        sender_role=MessageRole.SYSTEM,
        content_type=MessageContentType.TEXT,
        content=content,
        channel_type=opportunity.channel_type,
        sent_at=datetime.now(tz=UTC),
    )
    await uow.messages.save(message)
