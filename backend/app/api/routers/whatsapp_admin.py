from __future__ import annotations

from fastapi import APIRouter, Depends, Response

from app.api.dto.whatsapp import WhatsAppStatusResponse
from app.dependencies import get_channel_provider_registry
from app.security import require_role
from app.services.channel_provider_registry import ChannelProviderRegistry
from core.enums.channel import ChannelType
from core.enums.user import InternalUserRole
from core.exceptions.domain import UnsupportedChannelError
from infrastructure.channels.whatsapp import WhatsAppChannelProvider

router = APIRouter(
    prefix="/organizations/{organization_slug}/whatsapp",
    tags=["whatsapp-admin"],
    dependencies=[Depends(require_role(InternalUserRole.ADMINISTRATOR))],
)


def _get_whatsapp_provider(registry: ChannelProviderRegistry) -> WhatsAppChannelProvider:
    provider = registry.get(ChannelType.WHATSAPP)
    if not isinstance(provider, WhatsAppChannelProvider):
        # Solo puede pasar si algún día se registra otro tipo de ChannelProvider bajo
        # ChannelType.WHATSAPP -- bug de configuración de despliegue, no una respuesta esperada
        # del usuario, mismo criterio que UnsupportedChannelError (spec 015).
        raise UnsupportedChannelError(ChannelType.WHATSAPP)
    return provider


@router.get("/status")
async def get_whatsapp_status(
    organization_slug: str,
    registry: ChannelProviderRegistry = Depends(get_channel_provider_registry),
) -> WhatsAppStatusResponse:
    provider = _get_whatsapp_provider(registry)
    info = await provider.get_connection_info()
    return WhatsAppStatusResponse.from_domain(info)


@router.post("/connect")
async def connect_whatsapp(
    organization_slug: str,
    registry: ChannelProviderRegistry = Depends(get_channel_provider_registry),
) -> dict[str, str]:
    provider = _get_whatsapp_provider(registry)
    qrcode_base64 = await provider.get_qr_code()
    return {"qrcode_base64": qrcode_base64}


@router.post("/disconnect", status_code=204)
async def disconnect_whatsapp(
    organization_slug: str,
    registry: ChannelProviderRegistry = Depends(get_channel_provider_registry),
) -> Response:
    provider = _get_whatsapp_provider(registry)
    await provider.disconnect()
    return Response(status_code=204)
