from __future__ import annotations

import asyncio
import random
import time
from dataclasses import dataclass
from typing import Any

import httpx

from core.entities.contact import Contact
from core.entities.message import Message
from core.enums.message import MessageRole


@dataclass(frozen=True)
class _QueuedSend:
    message: Message
    contact: Contact
    typing_delay_seconds: float


class WhatsAppChannelProvider:
    """Implementa ChannelProvider (core/interfaces/providers.py), vía Evolution API.

    send() nunca bloquea dentro de la transacción que lo llama -- encola y retorna casi de
    inmediato. El ritmo anti-baneo real (esperar, "escribir", enviar, separación mínima entre
    envíos consecutivos) ocurre después, en un único worker en segundo plano arrancado una vez
    en el ciclo de vida de la aplicación (app/lifecycle.py), nunca por request -- ver spec 016
    sección 1 para la razón completa (SQLite con un solo escritor no tolera una transacción
    abierta 30+ segundos).
    """

    _MIN_GAP_RANGE = (2.0, 5.0)  # pausa aleatoria mínima entre cada envío consecutivo
    _FIRST_REPLY_DELAY = 30.0  # primer mensaje automático de una conversación
    _REPLY_DELAY_RANGE = (2.0, 15.0)  # respuestas automáticas siguientes

    def __init__(self, base_url: str, api_key: str, instance_name: str) -> None:
        self._client = httpx.AsyncClient(
            base_url=base_url,
            headers={"apikey": api_key},
        )
        self._instance_name = instance_name
        self._queue: asyncio.Queue[_QueuedSend] = asyncio.Queue()
        self._worker_task: asyncio.Task[None] | None = None
        self._last_sent_at: float = 0.0

    def start(self) -> None:
        """Llamado una vez en app/lifecycle.py -- no por request."""
        self._worker_task = asyncio.create_task(self._run_worker())

    async def stop(self) -> None:
        if self._worker_task is not None:
            self._worker_task.cancel()

    async def send(
        self, message: Message, contact: Contact, *, is_first_reply: bool = False
    ) -> None:
        delay = 0.0
        if message.sender_role == MessageRole.ASSISTANT:
            delay = (
                self._FIRST_REPLY_DELAY
                if is_first_reply
                else random.uniform(*self._REPLY_DELAY_RANGE)
            )
        await self._queue.put(_QueuedSend(message, contact, delay))

    async def _run_worker(self) -> None:
        while True:
            item = await self._queue.get()
            await asyncio.sleep(item.typing_delay_seconds)

            min_gap = random.uniform(*self._MIN_GAP_RANGE)
            elapsed = time.monotonic() - self._last_sent_at
            if elapsed < min_gap:
                await asyncio.sleep(min_gap - elapsed)

            await self._send_now(item.message, item.contact)
            self._last_sent_at = time.monotonic()

    async def _send_now(self, message: Message, contact: Contact) -> None:
        response = await self._client.post(
            f"/message/sendText/{self._instance_name}",
            json={
                "number": contact.external_id,
                "textMessage": {"text": message.content},
                # El ritmo ya lo controlamos nosotros (ver arriba) -- deliberadamente no se usa
                # el campo `delay` propio de Evolution API, ver spec 016 sección 3 para el
                # razonamiento completo (no está confirmado si ese delay bloquea la respuesta
                # HTTP, y el "escribiendo..." también necesita orquestarse desde este lado).
                "delay": 0,
            },
        )
        response.raise_for_status()

    async def health(self) -> bool:
        try:
            response = await self._client.get(f"/instance/connectionState/{self._instance_name}")
        except httpx.HTTPError:
            return False
        if response.status_code != httpx.codes.OK:
            return False
        data: dict[str, Any] = response.json()
        return bool(data.get("instance", {}).get("state") == "open")
