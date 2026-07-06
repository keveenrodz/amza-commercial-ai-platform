from __future__ import annotations

from core.interfaces.providers import ConversationContext
from core.interfaces.repositories import UnitOfWork
from core.value_objects.identifiers import ConversationId


class ConversationContextAssembler:
    def __init__(self, working_memory_size: int) -> None:
        self._working_memory_size = working_memory_size

    async def assemble(
        self,
        conversation_id: ConversationId,
        uow: UnitOfWork,
    ) -> ConversationContext:
        latest_summary = await uow.conversation_summaries.get_latest(conversation_id)
        recent_messages = await uow.messages.list_by_conversation(
            conversation_id,
            limit=self._working_memory_size,
        )
        return ConversationContext(
            summary=latest_summary.summary if latest_summary else None,
            recent_messages=recent_messages,
        )
