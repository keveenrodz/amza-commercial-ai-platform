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

from app.dependencies import (
    get_ai_provider,
    get_channel_health_monitor,
    get_channel_provider_registry,
)
from app.services.channel_health_monitor import ChannelHealthMonitor
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

    async def send(
        self, message: Message, contact: Contact, *, is_first_reply: bool = False
    ) -> None:
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


async def test_status_reads_the_cached_monitor_result_without_calling_providers(
    client: AsyncClient,
) -> None:
    """A diferencia de /health/ready, este endpoint nunca debe tocar los providers reales --
    existe justamente para que el frontend lo consulte sin generar tráfico externo cada vez."""
    from app.main import app

    monitor = ChannelHealthMonitor(ChannelProviderRegistry({}))
    monitor._status = {"telegram": True, "whatsapp": False}  # noqa: SLF001

    app.dependency_overrides[get_channel_health_monitor] = lambda: monitor

    response = await client.get("/health/status")

    assert response.status_code == 200
    assert response.json() == {"telegram": True, "whatsapp": False}


async def test_status_defaults_to_empty_before_the_first_check_ran(client: AsyncClient) -> None:
    from app.main import app

    app.dependency_overrides[get_channel_health_monitor] = lambda: ChannelHealthMonitor(
        ChannelProviderRegistry({})
    )

    response = await client.get("/health/status")

    assert response.status_code == 200
    assert response.json() == {}


async def test_channel_health_monitor_checks_telegram_webhook_health_too() -> None:
    """Regresión: health() de Telegram solo confirma que el token es válido -- un webhook roto
    (ej. URL de ngrok vieja) no se detecta ahí, hace falta consultar webhook_health() aparte."""
    import httpx

    from infrastructure.channels.telegram import TelegramChannelProvider

    webhook_url = {"value": ""}  # mutable para cambiar la respuesta entre los dos chequeos

    def handler(request: httpx.Request) -> httpx.Response:
        if request.url.path.endswith("/getMe"):
            return httpx.Response(200, json={"ok": True})
        return httpx.Response(
            200,
            json={"ok": True, "result": {"url": webhook_url["value"], "last_error_date": None}},
        )

    provider = TelegramChannelProvider(bot_token="test-token")
    provider._client = httpx.AsyncClient(  # noqa: SLF001
        base_url="https://api.telegram.org/bottest-token",
        transport=httpx.MockTransport(handler),
    )

    monitor = ChannelHealthMonitor(ChannelProviderRegistry({ChannelType.TELEGRAM: provider}))

    await monitor._check_once()  # noqa: SLF001
    assert monitor.status == {"telegram": False}  # sin url registrada -> webhook roto

    webhook_url["value"] = "https://real-url.example.com/webhooks/telegram/amza-empaques"
    await monitor._check_once()  # noqa: SLF001
    assert monitor.status == {"telegram": True}
