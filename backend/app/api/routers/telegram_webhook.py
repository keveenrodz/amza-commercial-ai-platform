from __future__ import annotations

from typing import Any

import structlog
from fastapi import APIRouter, Depends, Response
from pydantic import ValidationError

from app.api.dto.telegram import TelegramUpdate
from app.dependencies import get_receive_incoming_message_use_case
from app.security import verify_telegram_secret
from app.use_cases.receive_incoming_message import (
    IncomingMessageInput,
    ReceiveIncomingMessageUseCase,
)
from core.enums.channel import ChannelType
from core.enums.message import MessageContentType

router = APIRouter(prefix="/webhooks/telegram", tags=["telegram"])
logger = structlog.get_logger()


@router.post("/{organization_slug}", dependencies=[Depends(verify_telegram_secret)])
async def receive_telegram_update(
    organization_slug: str,
    payload: dict[str, Any],
    use_case: ReceiveIncomingMessageUseCase = Depends(get_receive_incoming_message_use_case),
) -> Response:
    try:
        update = TelegramUpdate.model_validate(payload)
    except ValidationError:
        logger.warning("telegram.webhook.malformed_payload", organization_slug=organization_slug)
        return Response(status_code=200)

    if update.message is None:
        # edited_message, callback_query, channel_post, etc. — no soportado en el MVP. Se ignora
        # en silencio, nunca se rechaza (ver spec 007 sección 8).
        return Response(status_code=200)

    message = update.message
    if message.text is None:
        # foto, sticker, ubicación sin texto — no soportado en el MVP, mismo criterio de arriba.
        return Response(status_code=200)

    try:
        await use_case.execute(
            IncomingMessageInput(
                organization_slug=organization_slug,
                channel_type=ChannelType.TELEGRAM,
                external_contact_id=str(message.chat.id),
                contact_display_name=message.from_user.first_name,
                content=message.text,
                content_type=MessageContentType.TEXT,
                provider_message_id=str(message.message_id),
            )
        )
    except Exception:
        # Deliberadamente amplio, y solo aquí — ver justificación completa en spec 007 sección 6.
        # No delegamos la decisión de reintentar a Telegram: sus reintentos son ciegos y pueden
        # duplicar respuestas al cliente o resúmenes generados. El webhook se considera recibido
        # una vez validado el secreto; cualquier fallo posterior se registra para diagnóstico.
        logger.exception(
            "telegram.webhook.processing_failed",
            organization_slug=organization_slug,
        )

    return Response(status_code=200)
