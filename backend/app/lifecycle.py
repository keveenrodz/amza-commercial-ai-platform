import structlog
from fastapi import FastAPI

from app.dependencies import get_channel_provider_registry
from core.enums.channel import ChannelType
from infrastructure.channels.whatsapp import WhatsAppChannelProvider

logger = structlog.get_logger()


def register_lifecycle_events(app: FastAPI) -> None:
    @app.on_event("startup")
    async def on_startup() -> None:
        # Arranca el worker en segundo plano del único ChannelProvider que lo necesita --
        # iterar el registro y comprobar el tipo evita que ChannelProvider (el Protocol) tenga
        # que declarar start()/stop() para Telegram, que no los necesita. Ver spec 016 sección 6.
        registry = get_channel_provider_registry()
        whatsapp_provider = registry.get(ChannelType.WHATSAPP)
        if isinstance(whatsapp_provider, WhatsAppChannelProvider):
            whatsapp_provider.start()
        logger.info("application.started")

    @app.on_event("shutdown")
    async def on_shutdown() -> None:
        registry = get_channel_provider_registry()
        whatsapp_provider = registry.get(ChannelType.WHATSAPP)
        if isinstance(whatsapp_provider, WhatsAppChannelProvider):
            await whatsapp_provider.stop()
        logger.info("application.stopped")
