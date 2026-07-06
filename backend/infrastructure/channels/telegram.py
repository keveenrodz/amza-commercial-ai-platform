from __future__ import annotations

from typing import Any

import httpx
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from core.entities.message import Message
from core.entities.opportunity import Opportunity
from core.exceptions.domain import ContactNotFoundError
from modules.opportunities.repositories.contact import SQLAlchemyContactRepository


class TelegramChannelProvider:
    """Implementa ChannelProvider (core/interfaces/providers.py).

    send() recibe Message + Opportunity, pero el chat_id de Telegram vive en
    Contact.external_id — no en Opportunity. Misma fricción que AIProvider.generate() con
    agent_id: se resuelve internamente vía ContactRepository (ver ADR pendiente en spec 006,
    mismo criterio aplicado por consistencia).
    """

    def __init__(
        self,
        session_factory: async_sessionmaker[AsyncSession],
        bot_token: str,
    ) -> None:
        self._session_factory = session_factory
        self._client = httpx.AsyncClient(base_url=f"https://api.telegram.org/bot{bot_token}")

    async def send(self, message: Message, opportunity: Opportunity) -> None:
        async with self._session_factory() as session:
            contact = await SQLAlchemyContactRepository(session).get_by_id(opportunity.contact_id)
        if contact is None:
            raise ContactNotFoundError(opportunity.contact_id)

        response = await self._client.post(
            "/sendMessage",
            json={"chat_id": contact.external_id, "text": message.content},
        )
        response.raise_for_status()

    async def health(self) -> bool:
        try:
            response = await self._client.get("/getMe")
        except httpx.HTTPError:
            return False
        data: dict[str, Any] = response.json()
        return response.status_code == httpx.codes.OK and bool(data.get("ok"))
