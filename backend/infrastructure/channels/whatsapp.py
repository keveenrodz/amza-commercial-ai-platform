from __future__ import annotations

import asyncio
import random
import time
from dataclasses import dataclass
from typing import Any

import httpx
import structlog

from core.entities.contact import Contact
from core.entities.message import Message
from core.enums.message import MessageRole

logger = structlog.get_logger()


@dataclass(frozen=True)
class _QueuedSend:
    message: Message
    contact: Contact
    typing_delay_seconds: float


@dataclass(frozen=True)
class WhatsAppConnectionInfo:
    connected: bool
    phone_number: str | None


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

            # Un solo envío fallido (Evolution API caído, número inválido, un 400 transitorio)
            # no puede matar el worker para siempre -- sin este try/except, una excepción aquí
            # se escapa del `while True` y el worker muere en silencio: todo lo que se encole
            # después nunca se procesa hasta reiniciar el proceso. Confirmado en vivo (bug
            # real, no hipotético): un 400 de Evolution API dejó el worker muerto.
            try:
                await self._send_now(item.message, item.contact)
            except Exception:
                logger.exception(
                    "whatsapp.send_failed",
                    contact_external_id=item.contact.external_id,
                )
            finally:
                self._last_sent_at = time.monotonic()

    async def _send_now(self, message: Message, contact: Contact) -> None:
        response = await self._client.post(
            f"/message/sendText/{self._instance_name}",
            json={
                "number": contact.external_id,
                # "text" en la raíz del body, no anidado bajo "textMessage" -- ese anidado
                # (tentativo, tomado de una versión más vieja de la documentación al escribir
                # spec 016) le hace fallar 400 "instance requires property \"text\"" contra la
                # v2.3.7 real. Confirmado contra la instancia real.
                "text": message.content,
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

    # Administración de la instancia (spec 017), no mensajería -- deliberadamente fuera del
    # ChannelProvider Protocol, igual que start()/stop() (spec 016): TelegramChannelProvider no
    # necesita ninguno de los dos, así que no tiene sentido forzarlos en la interfaz genérica.

    async def get_connection_info(self) -> WhatsAppConnectionInfo:
        # /instance/connectionState (usado por health()) solo da el estado -- /fetchInstances
        # da estado y número en la misma llamada (ownerJid), así que la pantalla de admin usa
        # esta en vez de duplicar la lógica de health() más una segunda llamada aparte.
        response = await self._client.get(
            "/instance/fetchInstances", params={"instanceName": self._instance_name}
        )
        response.raise_for_status()
        instances = response.json()
        if not instances:
            return WhatsAppConnectionInfo(connected=False, phone_number=None)

        instance = instances[0]
        connected = instance.get("connectionStatus") == "open"
        owner_jid = instance.get("ownerJid")
        phone_number = owner_jid.split("@")[0] if owner_jid else None
        return WhatsAppConnectionInfo(connected=connected, phone_number=phone_number)

    async def get_qr_code(self) -> str:
        response = await self._client.get(f"/instance/connect/{self._instance_name}")
        response.raise_for_status()
        # Evolution API devuelve el data URI completo ("data:image/png;base64,...."), no solo el
        # payload -- confirmado contra una instancia real, no documentado con claridad. Se le
        # quita el prefijo aquí porque el nombre del campo (qrcode_base64 en el DTO) y el
        # frontend (que construye su propio data URI) asumen que es solo el payload.
        base64_value = str(response.json()["base64"])
        return base64_value.removeprefix("data:image/png;base64,")

    async def disconnect(self) -> None:
        response = await self._client.delete(f"/instance/logout/{self._instance_name}")
        response.raise_for_status()
