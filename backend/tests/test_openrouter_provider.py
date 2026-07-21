"""
Regresión de spec 010: generate() no puede seguir usando sender_role.value directo como rol de
la API de OpenRouter una vez existe MessageRole.ADVISOR -- ver infrastructure/ai/openrouter.py.
Un mensaje de asesor humano dentro de la ventana de "recientes" debe viajar como "assistant",
nunca como "advisor" (rol que OpenRouter/OpenAI no reconoce).
"""

from __future__ import annotations

import json
import uuid
from datetime import UTC, datetime
from typing import Any

import httpx

from core.entities.message import Message
from core.enums.channel import ChannelType
from core.enums.message import MessageContentType, MessageRole
from core.interfaces.providers import ConversationContext
from core.value_objects.identifiers import AgentId, ConversationId, MessageId
from infrastructure.ai.openrouter import OpenRouterAIProvider
from infrastructure.database.session import AsyncSessionFactory
from modules.agents.models.agent import AgentModel


async def _seed_agent() -> uuid.UUID:
    async with AsyncSessionFactory() as session:
        now = datetime.now(tz=UTC)
        agent_id = uuid.uuid4()
        session.add(
            AgentModel(
                id=agent_id,
                organization_id=uuid.uuid4(),
                name="Test Agent",
                system_prompt="You are a helpful assistant.",
                model="openai/gpt-4.1-nano",
                status="active",
                created_at=now,
                updated_at=now,
            )
        )
        await session.commit()
        return agent_id


async def test_advisor_messages_are_sent_as_assistant_role() -> None:
    agent_id = await _seed_agent()
    captured_payload: dict[str, Any] = {}

    def handler(request: httpx.Request) -> httpx.Response:
        nonlocal captured_payload
        captured_payload = json.loads(request.content)
        return httpx.Response(200, json={"choices": [{"message": {"content": "ok"}}]})

    provider = OpenRouterAIProvider(
        session_factory=AsyncSessionFactory,
        api_key="test-key",
        base_url="https://openrouter.test",
    )
    provider._client = httpx.AsyncClient(  # noqa: SLF001
        base_url="https://openrouter.test",
        transport=httpx.MockTransport(handler),
    )

    conversation_id = ConversationId.generate()
    now = datetime.now(tz=UTC)
    context = ConversationContext(
        summary=None,
        recent_messages=[
            Message(
                id=MessageId.generate(),
                conversation_id=conversation_id,
                sender_role=MessageRole.USER,
                content_type=MessageContentType.TEXT,
                content="Busco cajas de arroz",
                channel_type=ChannelType.TELEGRAM,
                sent_at=now,
            ),
            Message(
                id=MessageId.generate(),
                conversation_id=conversation_id,
                sender_role=MessageRole.ADVISOR,
                content_type=MessageContentType.TEXT,
                content="Claro, ¿cuántas unidades necesitas?",
                channel_type=ChannelType.TELEGRAM,
                sent_at=now,
            ),
        ],
    )

    await provider.generate(context, AgentId(value=agent_id))

    roles = [m["role"] for m in captured_payload["messages"]]
    assert roles == ["system", "user", "assistant"]
