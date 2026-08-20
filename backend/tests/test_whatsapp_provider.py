"""
Cubre spec 016 (WhatsApp Integration) sección 3: WhatsAppChannelProvider.send() nunca bloquea --
encola y el ritmo anti-baneo real (retraso simulado + separación mínima entre envíos) ocurre en
el worker en segundo plano.
"""

from __future__ import annotations

import asyncio
import time
from datetime import UTC, datetime

import httpx

from core.entities.contact import Contact
from core.entities.message import Message
from core.enums.channel import ChannelType
from core.enums.message import MessageContentType, MessageRole
from core.enums.user import ContactStatus
from core.value_objects.identifiers import ContactId, ConversationId, MessageId, OrganizationId
from infrastructure.channels.whatsapp import WhatsAppChannelProvider


def _make_provider() -> WhatsAppChannelProvider:
    return WhatsAppChannelProvider(
        base_url="https://evolution.test", api_key="test-key", instance_name="test-instance"
    )


def _make_message(role: MessageRole, content: str = "hola") -> Message:
    return Message(
        id=MessageId.generate(),
        conversation_id=ConversationId.generate(),
        sender_role=role,
        content_type=MessageContentType.TEXT,
        content=content,
        channel_type=ChannelType.WHATSAPP,
        sent_at=datetime.now(tz=UTC),
    )


def _make_contact() -> Contact:
    now = datetime.now(tz=UTC)
    return Contact(
        id=ContactId.generate(),
        organization_id=OrganizationId.generate(),
        channel_type=ChannelType.WHATSAPP,
        external_id="573015092386",
        display_name="Cliente",
        status=ContactStatus.ACTIVE,
        created_at=now,
        updated_at=now,
    )


async def test_send_ai_first_reply_queues_a_fixed_30_second_delay() -> None:
    provider = _make_provider()

    await provider.send(_make_message(MessageRole.ASSISTANT), _make_contact(), is_first_reply=True)

    item = await provider._queue.get()  # noqa: SLF001
    assert item.typing_delay_seconds == 30.0


async def test_send_ai_followup_queues_a_random_delay_between_2_and_15() -> None:
    provider = _make_provider()

    await provider.send(_make_message(MessageRole.ASSISTANT), _make_contact(), is_first_reply=False)

    item = await provider._queue.get()  # noqa: SLF001
    assert 2.0 <= item.typing_delay_seconds <= 15.0


async def test_send_advisor_queues_zero_delay_regardless_of_is_first_reply() -> None:
    provider = _make_provider()

    await provider.send(_make_message(MessageRole.ADVISOR), _make_contact(), is_first_reply=True)

    item = await provider._queue.get()  # noqa: SLF001
    assert item.typing_delay_seconds == 0.0


async def test_worker_waits_the_minimum_gap_between_two_consecutive_sends() -> None:
    provider = _make_provider()
    # Rango de gap encogido a milisegundos -- mismo mecanismo, sin esperar segundos reales en
    # el test (parchar time.monotonic/asyncio.sleep globalmente es más riesgoso que esto: son
    # módulos compartidos por todo el proceso, incluido el propio scheduler de asyncio).
    provider._MIN_GAP_RANGE = (0.05, 0.05)  # noqa: SLF001

    sent_at: list[float] = []

    async def fake_send_now(message: Message, contact: Contact) -> None:
        sent_at.append(time.monotonic())

    provider._send_now = fake_send_now  # type: ignore[method-assign]  # noqa: SLF001

    contact = _make_contact()
    # ADVISOR -- typing_delay_seconds queda en 0, así el único delay en juego es el gap mínimo.
    await provider.send(_make_message(MessageRole.ADVISOR, "uno"), contact)
    await provider.send(_make_message(MessageRole.ADVISOR, "dos"), contact)

    worker = asyncio.create_task(provider._run_worker())  # noqa: SLF001
    await asyncio.sleep(0.3)
    worker.cancel()

    assert len(sent_at) == 2
    assert sent_at[1] - sent_at[0] >= 0.04


async def test_health_is_true_only_when_state_is_open() -> None:
    provider = _make_provider()

    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(200, json={"instance": {"state": "open"}})

    provider._client = httpx.AsyncClient(  # noqa: SLF001
        base_url="https://evolution.test", transport=httpx.MockTransport(handler)
    )

    assert await provider.health() is True


async def test_health_is_false_when_state_is_not_open() -> None:
    provider = _make_provider()

    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(200, json={"instance": {"state": "connecting"}})

    provider._client = httpx.AsyncClient(  # noqa: SLF001
        base_url="https://evolution.test", transport=httpx.MockTransport(handler)
    )

    assert await provider.health() is False


async def test_health_is_false_when_the_http_call_fails() -> None:
    provider = _make_provider()

    def handler(request: httpx.Request) -> httpx.Response:
        raise httpx.ConnectError("connection refused")

    provider._client = httpx.AsyncClient(  # noqa: SLF001
        base_url="https://evolution.test", transport=httpx.MockTransport(handler)
    )

    assert await provider.health() is False
