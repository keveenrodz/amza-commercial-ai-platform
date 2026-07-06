from __future__ import annotations

from datetime import UTC, datetime

from core.entities.conversation_summary import ConversationSummary
from core.interfaces.providers import AIProvider, CompletionRequest
from core.interfaces.repositories import UnitOfWork
from core.value_objects.identifiers import ConversationId, ConversationSummaryId

# Placeholder — no es un contrato definitivo. Este prompt cambiará varias veces antes de
# estabilizarse; cuando eso empiece a doler, ver spec 014 (Prompt Management) en Future Evolution.
_SUMMARY_SYSTEM_PROMPT = (
    "Resume la siguiente conversación comercial en 3-5 frases. Conserva intención de compra, "
    "objeciones, acuerdos y cualquier dato que un asesor humano necesite para continuarla."
)


class ConversationSummarizationService:
    """Sabe cómo generar un resumen. Nunca decide si debe generarse uno — esa decisión es
    siempre del caller (ver spec 006, sección 8)."""

    def __init__(self, ai_provider: AIProvider, summarization_model: str) -> None:
        self._ai_provider = ai_provider
        self._summarization_model = summarization_model

    async def execute(self, conversation_id: ConversationId, uow: UnitOfWork) -> None:
        previous = await uow.conversation_summaries.get_latest(conversation_id)
        since = previous.up_to_sent_at if previous else None

        new_messages = await uow.messages.list_since(conversation_id, after=since)
        if not new_messages:
            return

        transcript = "\n".join(f"{m.sender_role.value}: {m.content}" for m in new_messages)
        user_prompt = (
            f"Resumen anterior:\n{previous.summary}\n\n---\n\nNuevos mensajes:\n{transcript}"
            if previous
            else transcript
        )

        summary_text = await self._ai_provider.complete(
            CompletionRequest(
                model=self._summarization_model,
                system_prompt=_SUMMARY_SYSTEM_PROMPT,
                user_prompt=user_prompt,
                temperature=0.0,
            )
        )

        await uow.conversation_summaries.save(
            ConversationSummary(
                id=ConversationSummaryId.generate(),
                conversation_id=conversation_id,
                summary=summary_text,
                up_to_sent_at=new_messages[-1].sent_at,
                version=(previous.version + 1) if previous else 1,
                created_at=datetime.now(tz=UTC),
            )
        )
