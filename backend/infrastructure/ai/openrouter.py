from __future__ import annotations

from typing import Any

import httpx
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from core.enums.message import MessageRole
from core.exceptions.domain import AgentNotFoundError
from core.interfaces.providers import CompletionRequest, ConversationContext
from core.value_objects.identifiers import AgentId
from modules.agents.repositories.agent import SQLAlchemyAgentRepository

# La API de OpenRouter/OpenAI solo reconoce "system"/"user"/"assistant". MessageRole tiene un
# cuarto valor, ADVISOR (spec 010) -- desde el punto de vista del modelo, el turno de un asesor
# humano es funcionalmente el turno del "assistant" (todo lo que no es el cliente).
_TO_OPENAI_ROLE = {
    MessageRole.USER: "user",
    MessageRole.ASSISTANT: "assistant",
    MessageRole.ADVISOR: "assistant",
    MessageRole.SYSTEM: "system",
}


class OpenRouterAIProvider:
    """Implementa AIProvider (core/interfaces/providers.py).

    generate() resuelve agent_id -> Agent vía AgentRepository — fricción conocida y aceptada
    para spec 006, ver "ADR pendiente de evaluación durante implementación" en el spec. complete()
    no toca ningún repositorio: recibe todo lo que necesita en el CompletionRequest.
    """

    def __init__(
        self,
        session_factory: async_sessionmaker[AsyncSession],
        api_key: str,
        base_url: str,
    ) -> None:
        self._session_factory = session_factory
        self._client = httpx.AsyncClient(
            base_url=base_url,
            headers={"Authorization": f"Bearer {api_key}"},
        )

    async def generate(self, context: ConversationContext, agent_id: AgentId) -> str:
        async with self._session_factory() as session:
            agent = await SQLAlchemyAgentRepository(session).get_by_id(agent_id)
        if agent is None:
            raise AgentNotFoundError(agent_id)

        system_content = agent.system_prompt
        if context.summary:
            system_content = (
                f"{agent.system_prompt}\n\n---\nResumen de la conversación:\n{context.summary}"
            )

        messages: list[dict[str, str]] = [{"role": "system", "content": system_content}]
        messages.extend(
            {"role": _TO_OPENAI_ROLE[m.sender_role], "content": m.content}
            for m in context.recent_messages
        )

        response = await self._client.post(
            "/chat/completions",
            json={"model": agent.model, "messages": messages},
        )
        response.raise_for_status()
        data: dict[str, Any] = response.json()
        return str(data["choices"][0]["message"]["content"])

    async def complete(self, request: CompletionRequest) -> str:
        payload: dict[str, Any] = {
            "model": request.model,
            "messages": [
                {"role": "system", "content": request.system_prompt},
                {"role": "user", "content": request.user_prompt},
            ],
            "temperature": request.temperature,
        }
        if request.max_tokens is not None:
            payload["max_tokens"] = request.max_tokens

        response = await self._client.post(
            "/chat/completions",
            json=payload,
            timeout=request.timeout,
        )
        response.raise_for_status()
        data: dict[str, Any] = response.json()
        return str(data["choices"][0]["message"]["content"])

    async def health(self) -> bool:
        try:
            response = await self._client.get("/models")
        except httpx.HTTPError:
            return False
        return response.status_code == httpx.codes.OK
