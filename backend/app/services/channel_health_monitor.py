from __future__ import annotations

import asyncio

import structlog

from app.services.channel_provider_registry import ChannelProviderRegistry
from core.enums.channel import ChannelType
from infrastructure.channels.telegram import TelegramChannelProvider

logger = structlog.get_logger()


class ChannelHealthMonitor:
    """Revisa la salud real de cada canal registrado una sola vez por intervalo, en un worker
    en segundo plano -- sin importar cuántas pestañas del frontend estén consultando el
    resultado. `health()` de cada provider hace llamadas HTTP reales (OpenRouter, Evolution
    API, Telegram), así que si el frontend consultara eso directo cada 60s desde cada asesor
    conectado, el tráfico externo se multiplicaría por el número de pestañas abiertas. Este
    monitor lo evita: siempre es una sola revisión por intervalo, y el resto son lecturas de un
    dict en memoria (`status`), sin llamadas externas.
    """

    _CHECK_INTERVAL_SECONDS = 60.0

    def __init__(self, channel_provider_registry: ChannelProviderRegistry) -> None:
        self._registry = channel_provider_registry
        self._task: asyncio.Task[None] | None = None
        self._status: dict[str, bool] = {}

    def start(self) -> None:
        """Llamado una vez en app/lifecycle.py -- no por request."""
        self._task = asyncio.create_task(self._run())

    async def stop(self) -> None:
        if self._task is not None:
            self._task.cancel()

    @property
    def status(self) -> dict[str, bool]:
        return dict(self._status)

    async def _run(self) -> None:
        while True:
            await self._check_once()
            await asyncio.sleep(self._CHECK_INTERVAL_SECONDS)

    async def _check_once(self) -> None:
        new_status: dict[str, bool] = {}
        for channel_type, provider in self._registry.all().items():
            try:
                healthy = await provider.health()
                # Para Telegram, health() solo confirma que el token del bot es válido -- no
                # que el webhook esté funcionando de verdad. El caso real que se busca detectar
                # (URL pública rotó, ej. ngrok, y nadie volvió a registrar el webhook) solo se ve
                # consultando getWebhookInfo.
                if channel_type == ChannelType.TELEGRAM and isinstance(
                    provider, TelegramChannelProvider
                ):
                    healthy = healthy and await provider.webhook_health()
            except Exception:
                logger.warning(
                    "channel_health_monitor.check_failed", channel=channel_type.value
                )
                healthy = False
            new_status[channel_type.value] = healthy
        self._status = new_status
