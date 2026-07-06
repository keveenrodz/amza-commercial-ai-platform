from __future__ import annotations

from typing import Any

import httpx

from core.entities.contact import Contact
from core.entities.message import Message


class TelegramChannelProvider:
    """Implementa ChannelProvider (core/interfaces/providers.py).

    send() recibe el Contact directo -- no consulta ningún repositorio. Antes resolvía
    opportunity.contact_id vía ContactRepository con una sesión propia, pero eso rompía cuando
    el Contact se creaba en la misma transacción del use case: una sesión separada no puede ver
    una fila que la otra transacción todavía no confirmó (ContactNotFoundError, rollback
    completo, ningún mensaje llega). Confirmado con una prueba real de punta a punta — resuelve
    el ADR de spec 006 para este provider en el sentido de "sí complica el código en la
    práctica". El provider queda completamente stateless.
    """

    def __init__(self, bot_token: str) -> None:
        self._client = httpx.AsyncClient(base_url=f"https://api.telegram.org/bot{bot_token}")

    async def send(self, message: Message, contact: Contact) -> None:
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
