from __future__ import annotations

from typing import Any

import structlog
from fastapi import APIRouter, Depends, Response
from pydantic import ValidationError

from app.api.dto.whatsapp import WhatsAppWebhookEvent
from app.dependencies import get_channel_provider_registry, get_receive_incoming_message_use_case
from app.security import verify_whatsapp_secret
from app.services.channel_provider_registry import ChannelProviderRegistry
from app.use_cases.receive_incoming_message import (
    IncomingMessageInput,
    ReceiveIncomingMessageUseCase,
)
from core.enums.channel import ChannelType
from core.enums.message import MessageContentType
from infrastructure.channels.whatsapp import WhatsAppChannelProvider

router = APIRouter(prefix="/webhooks/whatsapp", tags=["whatsapp"])
logger = structlog.get_logger()


@router.post("/{organization_slug}", dependencies=[Depends(verify_whatsapp_secret)])
async def receive_whatsapp_event(
    organization_slug: str,
    payload: dict[str, Any],
    use_case: ReceiveIncomingMessageUseCase = Depends(get_receive_incoming_message_use_case),
    channel_registry: ChannelProviderRegistry = Depends(get_channel_provider_registry),
) -> Response:
    try:
        event = WhatsAppWebhookEvent.model_validate(payload)
    except ValidationError:
        logger.warning("whatsapp.webhook.malformed_payload", organization_slug=organization_slug)
        return Response(status_code=200)

    if event.event != "messages.upsert" or event.data.key.fromMe:
        # "messages.upsert" (minúsculas, con punto) confirmado contra un payload real -- spec
        # 016 lo modeló tentativamente como "MESSAGES_UPSERT" (mayúsculas, con guion bajo, el
        # nombre del evento en el array `events` al registrar el webhook) sin poder confirmarlo
        # contra la documentación; ese es el valor que de verdad manda Evolution API en el
        # payload entrante, y no coincidir aquí hacía que el mensaje se ignorara en silencio
        # (200 sin invocar el caso de uso, sin ningún error visible).
        # fromMe=True es un mensaje que salió de este mismo número (ej. enviado manualmente
        # desde el teléfono vinculado) -- no es un mensaje del cliente, se ignora en silencio.
        return Response(status_code=200)

    # Mitigación probada (no confirmada) contra el error 463 -- marcar el mensaje como leído y
    # mostrar "escribiendo..." antes de procesar la respuesta. Best-effort: si Evolution API
    # está caído o esto falla por cualquier motivo, el mensaje del cliente igual se procesa --
    # nunca debe ser esto lo que bloquee la conversación real.
    whatsapp_provider = channel_registry.get(ChannelType.WHATSAPP)
    if isinstance(whatsapp_provider, WhatsAppChannelProvider):
        try:
            await whatsapp_provider.mark_as_read(event.data.key.remoteJid, event.data.key.id)
            await whatsapp_provider.send_presence_composing(event.data.key.remoteJid)
        except Exception:
            logger.warning(
                "whatsapp.webhook.read_receipt_failed",
                organization_slug=organization_slug,
            )

    if event.data.message.conversation is None:
        # Multimedia (foto, audio, documento, ubicación) -- distinguir el tipo real necesita el
        # payload real de Evolution API (ver spec 016 sección 4); se guarda como placeholder de
        # imagen, mismo criterio que spec 012 ya decidió para adjuntos entrantes: mostrar el
        # tipo, no el contenido.
        content, content_type = "[multimedia]", MessageContentType.IMAGE
    else:
        content, content_type = event.data.message.conversation, MessageContentType.TEXT

    try:
        await use_case.execute(
            IncomingMessageInput(
                organization_slug=organization_slug,
                channel_type=ChannelType.WHATSAPP,
                external_contact_id=event.data.key.remoteJid,
                contact_display_name=event.data.pushName or event.data.key.remoteJid,
                content=content,
                content_type=content_type,
                provider_message_id=event.data.key.id,
            )
        )
    except Exception:
        # Mismo criterio que telegram_webhook.py (spec 007 sección 6): nunca delegar el
        # reintento a Evolution API, cualquier fallo posterior al secreto válido se registra
        # para diagnóstico y el webhook igual responde 200.
        logger.exception(
            "whatsapp.webhook.processing_failed",
            organization_slug=organization_slug,
        )

    return Response(status_code=200)
