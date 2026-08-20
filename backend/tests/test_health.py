"""
Cubre spec 015 (Channel Provider Routing) sección 4: GET /health/ready se generaliza para iterar
todos los canales registrados en vez de reportar una clave "telegram" fija -- esta prueba es la
regresión explícita de que, con un solo canal registrado (el caso de hoy), el shape de la
respuesta no cambió.

Ambas dependencias (AIProvider, ChannelProviderRegistry) se sobreescriben con fakes -- los
providers reales hacen llamadas de red (a OpenRouter/Telegram), que no deben ejecutarse en tests.
"""

from __future__ import annotations

from httpx import AsyncClient

from app.dependencies import get_ai_provider, get_channel_provider_registry
from app.services.channel_provider_registry import ChannelProviderRegistry
from core.entities.contact import Contact
from core.entities.message import Message
from core.enums.channel import ChannelType
from core.interfaces.providers import CompletionRequest, ConversationContext


class _FakeAIProvider:
    def __init__(self, *, healthy: bool) -> None:
        self._healthy = healthy

    async def generate(self, context: ConversationContext, agent_id: object) -> str:
        raise NotImplementedError

    async def complete(self, request: CompletionRequest) -> str:
        raise NotImplementedError

    async def health(self) -> bool:
        return self._healthy


class _FakeChannelProvider:
    def __init__(self, *, healthy: bool) -> None:
        self._healthy = healthy

    async def send(self, message: Message, contact: Contact) -> None:
        return None

    async def health(self) -> bool:
        return self._healthy


async def test_ready_reports_database_openrouter_and_every_registered_channel(
    client: AsyncClient,
) -> None:
    from app.main import app

    app.dependency_overrides[get_ai_provider] = lambda: _FakeAIProvider(healthy=True)
    app.dependency_overrides[get_channel_provider_registry] = lambda: ChannelProviderRegistry(
        {ChannelType.TELEGRAM: _FakeChannelProvider(healthy=True)}
    )

    response = await client.get("/health/ready")

    assert response.status_code == 200
    assert response.json() == {"database": True, "openrouter": True, "telegram": True}


async def test_ready_returns_503_when_any_registered_channel_is_unhealthy(
    client: AsyncClient,
) -> None:
    from app.main import app

    app.dependency_overrides[get_ai_provider] = lambda: _FakeAIProvider(healthy=True)
    app.dependency_overrides[get_channel_provider_registry] = lambda: ChannelProviderRegistry(
        {ChannelType.TELEGRAM: _FakeChannelProvider(healthy=False)}
    )

    response = await client.get("/health/ready")

    assert response.status_code == 503
    assert response.json() == {"database": True, "openrouter": True, "telegram": False}
