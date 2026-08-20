"""
Cubre spec 016 (WhatsApp Integration) sección 4: POST /webhooks/whatsapp/{organization_slug}.
Mismo patrón que se hubiera usado para telegram_webhook.py (spec 007) -- nunca invoca al
ChannelProviderRegistry ni al backend real de Evolution API, solo confirma el contrato del
router: qué invoca al caso de uso y con qué datos, qué se ignora en silencio, y la verificación
del secreto.
"""

from __future__ import annotations

from httpx import AsyncClient

from app.dependencies import get_receive_incoming_message_use_case
from app.use_cases.receive_incoming_message import IncomingMessageInput
from core.enums.channel import ChannelType
from core.enums.message import MessageContentType


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


async def test_invalid_secret_returns_401(client: AsyncClient) -> None:
    response = await client.post(
        "/webhooks/whatsapp/test-org",
        json=_valid_payload(),
        headers={"X-Webhook-Secret": "wrong-secret"},
    )

    assert response.status_code == 401
