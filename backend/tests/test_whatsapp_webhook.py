"""
Cubre spec 016 (WhatsApp Integration) sección 4: POST /webhooks/whatsapp/{organization_slug}.
Mismo patrón que se hubiera usado para telegram_webhook.py (spec 007) -- nunca invoca al
ChannelProviderRegistry ni al backend real de Evolution API, solo confirma el contrato del
router: qué invoca al caso de uso y con qué datos, qué se ignora en silencio, y la verificación
del secreto.
"""

from __future__ import annotations

import httpx
from httpx import AsyncClient

from app.dependencies import get_channel_provider_registry, get_receive_incoming_message_use_case
from app.services.channel_provider_registry import ChannelProviderRegistry
from app.use_cases.receive_incoming_message import IncomingMessageInput
from core.enums.channel import ChannelType
from core.enums.message import MessageContentType
from infrastructure.channels.whatsapp import WhatsAppChannelProvider


class _SpyUseCase:
    def __init__(self) -> None:
        self.calls: list[IncomingMessageInput] = []

    async def execute(self, input: IncomingMessageInput) -> None:  # noqa: A002
        self.calls.append(input)


def _valid_payload(**overrides: object) -> dict:
    # "messages.upsert" (minúsculas, con punto) -- confirmado contra un payload real de
    # Evolution API en vivo, no el "MESSAGES_UPSERT" tentativo original de spec 016.
    payload = {
        "event": "messages.upsert",
        "data": {
            "key": {
                "remoteJid": "573001234567@s.whatsapp.net",
                "id": "ABC123",
                "fromMe": False,
            },
            "message": {"conversation": "Hola, busco vasos"},
            "pushName": "Cliente Prueba",
            "messageTimestamp": 1700000000,
        },
    }
    payload.update(overrides)
    return payload


async def test_valid_text_payload_invokes_the_use_case_with_whatsapp_channel(
    client: AsyncClient,
) -> None:
    from app.main import app

    spy = _SpyUseCase()
    app.dependency_overrides[get_receive_incoming_message_use_case] = lambda: spy

    response = await client.post(
        "/webhooks/whatsapp/test-org",
        json=_valid_payload(),
        headers={"X-Webhook-Secret": "test-whatsapp-secret"},
    )

    assert response.status_code == 200
    assert len(spy.calls) == 1
    call = spy.calls[0]
    assert call.organization_slug == "test-org"
    assert call.channel_type == ChannelType.WHATSAPP
    assert call.external_contact_id == "573001234567@s.whatsapp.net"
    assert call.contact_display_name == "Cliente Prueba"
    assert call.content == "Hola, busco vasos"
    assert call.content_type == MessageContentType.TEXT
    assert call.provider_message_id == "ABC123"


async def test_lid_message_resolves_to_the_phone_number_jid(client: AsyncClient) -> None:
    """Regresión de un bug real en producción: el mismo cliente (+573217227941) quedó como dos
    Contact distintos porque un mensaje llegó como remoteJid="...@lid" y otro como
    "...@s.whatsapp.net". Con remoteJidAlt presente, el JID de número real debe ganar siempre."""
    from app.main import app

    spy = _SpyUseCase()
    app.dependency_overrides[get_receive_incoming_message_use_case] = lambda: spy

    payload = _valid_payload()
    payload["data"]["key"]["remoteJid"] = "122891949609121@lid"
    payload["data"]["key"]["remoteJidAlt"] = "573217227941@s.whatsapp.net"

    response = await client.post(
        "/webhooks/whatsapp/test-org",
        json=payload,
        headers={"X-Webhook-Secret": "test-whatsapp-secret"},
    )

    assert response.status_code == 200
    assert spy.calls[0].external_contact_id == "573217227941@s.whatsapp.net"


async def test_lid_message_without_alt_falls_back_to_the_lid_itself(
    client: AsyncClient,
) -> None:
    """Sin remoteJidAlt no hay nada que resolver -- se usa el LID tal cual llegó, no se inventa
    un número."""
    from app.main import app

    spy = _SpyUseCase()
    app.dependency_overrides[get_receive_incoming_message_use_case] = lambda: spy

    payload = _valid_payload()
    payload["data"]["key"]["remoteJid"] = "122891949609121@lid"

    response = await client.post(
        "/webhooks/whatsapp/test-org",
        json=payload,
        headers={"X-Webhook-Secret": "test-whatsapp-secret"},
    )

    assert response.status_code == 200
    assert spy.calls[0].external_contact_id == "122891949609121@lid"


async def test_from_me_is_ignored_without_invoking_the_use_case(client: AsyncClient) -> None:
    from app.main import app

    spy = _SpyUseCase()
    app.dependency_overrides[get_receive_incoming_message_use_case] = lambda: spy

    payload = _valid_payload()
    payload["data"]["key"]["fromMe"] = True

    response = await client.post(
        "/webhooks/whatsapp/test-org",
        json=payload,
        headers={"X-Webhook-Secret": "test-whatsapp-secret"},
    )

    assert response.status_code == 200
    assert spy.calls == []


async def test_an_event_other_than_messages_upsert_is_ignored(client: AsyncClient) -> None:
    from app.main import app

    spy = _SpyUseCase()
    app.dependency_overrides[get_receive_incoming_message_use_case] = lambda: spy

    payload = _valid_payload(event="CONNECTION_UPDATE")

    response = await client.post(
        "/webhooks/whatsapp/test-org",
        json=payload,
        headers={"X-Webhook-Secret": "test-whatsapp-secret"},
    )

    assert response.status_code == 200
    assert spy.calls == []


async def test_malformed_payload_returns_200_without_raising(client: AsyncClient) -> None:
    from app.main import app

    spy = _SpyUseCase()
    app.dependency_overrides[get_receive_incoming_message_use_case] = lambda: spy

    response = await client.post(
        "/webhooks/whatsapp/test-org",
        json={"not": "a valid payload"},
        headers={"X-Webhook-Secret": "test-whatsapp-secret"},
    )

    assert response.status_code == 200
    assert spy.calls == []


async def test_valid_message_marks_as_read_and_sends_composing_presence(
    client: AsyncClient,
) -> None:
    from app.main import app

    spy = _SpyUseCase()
    app.dependency_overrides[get_receive_incoming_message_use_case] = lambda: spy

    calls: list[str] = []

    def handler(request: httpx.Request) -> httpx.Response:
        calls.append(str(request.url))
        return httpx.Response(201, json={})

    provider = WhatsAppChannelProvider(
        base_url="https://evolution.test", api_key="test-key", instance_name="test-instance"
    )
    provider._client = httpx.AsyncClient(  # noqa: SLF001
        base_url="https://evolution.test", transport=httpx.MockTransport(handler)
    )
    app.dependency_overrides[get_channel_provider_registry] = lambda: ChannelProviderRegistry(
        {ChannelType.WHATSAPP: provider}
    )

    response = await client.post(
        "/webhooks/whatsapp/test-org",
        json=_valid_payload(),
        headers={"X-Webhook-Secret": "test-whatsapp-secret"},
    )

    assert response.status_code == 200
    assert len(spy.calls) == 1
    assert any("markMessageAsRead" in url for url in calls)
    assert any("sendPresence" in url for url in calls)


async def test_read_receipt_failure_does_not_block_the_use_case(client: AsyncClient) -> None:
    from app.main import app

    spy = _SpyUseCase()
    app.dependency_overrides[get_receive_incoming_message_use_case] = lambda: spy

    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(500, json={"error": "boom"})

    provider = WhatsAppChannelProvider(
        base_url="https://evolution.test", api_key="test-key", instance_name="test-instance"
    )
    provider._client = httpx.AsyncClient(  # noqa: SLF001
        base_url="https://evolution.test", transport=httpx.MockTransport(handler)
    )
    app.dependency_overrides[get_channel_provider_registry] = lambda: ChannelProviderRegistry(
        {ChannelType.WHATSAPP: provider}
    )

    response = await client.post(
        "/webhooks/whatsapp/test-org",
        json=_valid_payload(),
        headers={"X-Webhook-Secret": "test-whatsapp-secret"},
    )

    assert response.status_code == 200
    assert len(spy.calls) == 1


async def test_invalid_secret_returns_401(client: AsyncClient) -> None:
    response = await client.post(
        "/webhooks/whatsapp/test-org",
        json=_valid_payload(),
        headers={"X-Webhook-Secret": "wrong-secret"},
    )

    assert response.status_code == 401
