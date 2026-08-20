"""
Cubre spec 017 (Admin Panel):

1. PUT .../agent actualiza system_prompt/escalation_rules/model; GET .../agent devuelve los
   valores guardados.
2. Un Advisor autenticado llama cualquier endpoint de /agent o /whatsapp/* -> 403 (require_role,
   mismo patrón que spec 014).
3. Regresión sobre OpenRouterAIProvider.generate(): con escalation_rules no vacío, el mensaje de
   sistema enviado a OpenRouter incluye ambos bloques, en el orden documentado en la sección 1
   (prompt principal, reglas de escalamiento, resumen).
4. GET .../whatsapp/status refleja WhatsAppChannelProvider.health().
5. POST .../whatsapp/connect devuelve el base64 que responde el fake de Evolution API;
   POST .../whatsapp/disconnect -> 204 y llama DELETE /instance/logout/... exactamente una vez.
"""

from __future__ import annotations

import json
import uuid
from datetime import UTC, datetime

import httpx
from httpx import AsyncClient
from sqlalchemy import select

from app.dependencies import get_channel_provider_registry
from app.services.channel_provider_registry import ChannelProviderRegistry
from core.entities.message import Message
from core.enums.channel import ChannelType
from core.enums.message import MessageContentType, MessageRole
from core.value_objects.identifiers import AgentId, ConversationId, MessageId
from infrastructure.ai.openrouter import OpenRouterAIProvider
from infrastructure.channels.whatsapp import WhatsAppChannelProvider
from infrastructure.database.session import AsyncSessionFactory
from modules.agents.models.agent import AgentModel
from modules.configuration.models.organization import OrganizationModel
from scripts.create_user import create_user
from tests.test_security_and_identity import _ORG_SLUG, _login, _seed_organization

_AGENT_URL = f"/organizations/{_ORG_SLUG}/agent"
_WHATSAPP_URL = f"/organizations/{_ORG_SLUG}/whatsapp"


async def _seed_agent() -> uuid.UUID:
    async with AsyncSessionFactory() as session:
        org = (
            await session.execute(
                select(OrganizationModel).where(OrganizationModel.slug == _ORG_SLUG)
            )
        ).scalar_one()
        now = datetime.now(tz=UTC)
        agent_id = uuid.uuid4()
        session.add(
            AgentModel(
                id=agent_id,
                organization_id=org.id,
                name="Test Agent",
                system_prompt="Eres un asistente comercial.",
                model="openai/gpt-4.1-nano",
                status="active",
                created_at=now,
                updated_at=now,
            )
        )
        await session.commit()
    return agent_id


def _make_whatsapp_provider(handler: httpx.MockTransport) -> WhatsAppChannelProvider:
    provider = WhatsAppChannelProvider(
        base_url="https://evolution.test", api_key="test-key", instance_name="test-instance"
    )
    provider._client = httpx.AsyncClient(  # noqa: SLF001
        base_url="https://evolution.test", transport=handler
    )
    return provider


async def test_get_and_update_agent(client: AsyncClient) -> None:
    await _seed_organization()
    await _seed_agent()
    await create_user(_ORG_SLUG, "admin@gmail.com", "Admin Principal", "administrator")
    await _login(client, "admin@gmail.com")

    update_response = await client.put(
        _AGENT_URL,
        json={
            "system_prompt": "Eres un asistente de ventas de empaques.",
            "escalation_rules": "Deriva a un humano si el cliente pide crédito.",
            "model": "openai/gpt-4.1-mini",
        },
    )
    assert update_response.status_code == 200, update_response.text
    body = update_response.json()
    assert body["system_prompt"] == "Eres un asistente de ventas de empaques."
    assert body["escalation_rules"] == "Deriva a un humano si el cliente pide crédito."
    assert body["model"] == "openai/gpt-4.1-mini"

    get_response = await client.get(_AGENT_URL)
    assert get_response.status_code == 200
    assert get_response.json() == body


async def test_advisor_gets_403_on_agent_and_whatsapp_endpoints(client: AsyncClient) -> None:
    await _seed_organization()
    await _seed_agent()
    await create_user(_ORG_SLUG, "asesor@gmail.com", "Un Asesor", "advisor")
    await _login(client, "asesor@gmail.com")

    assert (await client.get(_AGENT_URL)).status_code == 403
    assert (
        await client.put(
            _AGENT_URL,
            json={"system_prompt": "x", "escalation_rules": "", "model": "openai/gpt-4.1-nano"},
        )
    ).status_code == 403
    assert (await client.get(f"{_WHATSAPP_URL}/status")).status_code == 403
    assert (await client.post(f"{_WHATSAPP_URL}/connect")).status_code == 403
    assert (await client.post(f"{_WHATSAPP_URL}/disconnect")).status_code == 403


async def test_generate_includes_escalation_rules_and_summary_in_order() -> None:
    await _seed_organization()
    agent_id = await _seed_agent()

    async with AsyncSessionFactory() as session:
        model = (
            await session.execute(select(AgentModel).where(AgentModel.id == agent_id))
        ).scalar_one()
        model.escalation_rules = "Deriva a un humano si el cliente pide crédito."
        await session.commit()

    captured_payload: dict = {}

    def handler(request: httpx.Request) -> httpx.Response:
        nonlocal captured_payload
        captured_payload = json.loads(request.content)
        return httpx.Response(200, json={"choices": [{"message": {"content": "ok"}}]})

    provider = OpenRouterAIProvider(
        session_factory=AsyncSessionFactory,
        api_key="test-key",
        base_url="https://openrouter.test",
    )
    provider._client = httpx.AsyncClient(  # noqa: SLF001
        base_url="https://openrouter.test", transport=httpx.MockTransport(handler)
    )

    from core.interfaces.providers import ConversationContext

    context = ConversationContext(
        summary="El cliente busca vasos desechables.",
        recent_messages=[
            Message(
                id=MessageId.generate(),
                conversation_id=ConversationId.generate(),
                sender_role=MessageRole.USER,
                content_type=MessageContentType.TEXT,
                content="Hola",
                channel_type=ChannelType.TELEGRAM,
                sent_at=datetime.now(tz=UTC),
            ),
        ],
    )

    await provider.generate(context, AgentId(value=agent_id))

    system_content = captured_payload["messages"][0]["content"]
    assert system_content.index("Eres un asistente comercial.") < system_content.index(
        "Cuándo derivar a un humano:"
    )
    assert system_content.index("Cuándo derivar a un humano:") < system_content.index(
        "Resumen de la conversación:"
    )
    assert "Deriva a un humano si el cliente pide crédito." in system_content
    assert "El cliente busca vasos desechables." in system_content


async def test_whatsapp_status_reflects_provider_health(client: AsyncClient) -> None:
    from app.main import app

    await _seed_organization()
    await create_user(_ORG_SLUG, "admin@gmail.com", "Admin Principal", "administrator")
    await _login(client, "admin@gmail.com")

    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(200, json={"instance": {"state": "open"}})

    provider = _make_whatsapp_provider(httpx.MockTransport(handler))
    app.dependency_overrides[get_channel_provider_registry] = lambda: ChannelProviderRegistry(
        {ChannelType.WHATSAPP: provider}
    )

    response = await client.get(f"{_WHATSAPP_URL}/status")
    assert response.status_code == 200
    assert response.json() == {"connected": True}


async def test_whatsapp_connect_returns_qrcode_base64(client: AsyncClient) -> None:
    from app.main import app

    await _seed_organization()
    await create_user(_ORG_SLUG, "admin@gmail.com", "Admin Principal", "administrator")
    await _login(client, "admin@gmail.com")

    # Evolution API real devuelve el data URI completo, no solo el payload -- regresión: sin
    # quitarle el prefijo aquí, el frontend construye su propio "data:image/png;base64,..." y
    # termina duplicándolo (data URI inválido, icono de imagen rota en el navegador).
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(200, json={"base64": "data:image/png;base64,iVBORfake=="})

    provider = _make_whatsapp_provider(httpx.MockTransport(handler))
    app.dependency_overrides[get_channel_provider_registry] = lambda: ChannelProviderRegistry(
        {ChannelType.WHATSAPP: provider}
    )

    response = await client.post(f"{_WHATSAPP_URL}/connect")
    assert response.status_code == 200
    assert response.json() == {"qrcode_base64": "iVBORfake=="}


async def test_whatsapp_disconnect_calls_logout_exactly_once(client: AsyncClient) -> None:
    from app.main import app

    await _seed_organization()
    await create_user(_ORG_SLUG, "admin@gmail.com", "Admin Principal", "administrator")
    await _login(client, "admin@gmail.com")

    calls: list[str] = []

    def handler(request: httpx.Request) -> httpx.Response:
        calls.append(str(request.url))
        return httpx.Response(200, json={})

    provider = _make_whatsapp_provider(httpx.MockTransport(handler))
    app.dependency_overrides[get_channel_provider_registry] = lambda: ChannelProviderRegistry(
        {ChannelType.WHATSAPP: provider}
    )

    response = await client.post(f"{_WHATSAPP_URL}/disconnect")
    assert response.status_code == 204
    assert len(calls) == 1
    assert "/instance/logout/test-instance" in calls[0]
