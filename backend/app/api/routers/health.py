from __future__ import annotations

from fastapi import APIRouter, Depends
from fastapi.responses import JSONResponse
from sqlalchemy import text

from app.dependencies import get_ai_provider, get_channel_provider_registry
from app.services.channel_provider_registry import ChannelProviderRegistry
from core.interfaces.providers import AIProvider
from infrastructure.database.session import AsyncSessionFactory

router = APIRouter(prefix="/health", tags=["health"])


@router.get("")
async def health() -> dict[str, str]:
    return {"status": "ok"}


@router.get("/ready")
async def readiness(
    ai_provider: AIProvider = Depends(get_ai_provider),
    channel_registry: ChannelProviderRegistry = Depends(get_channel_provider_registry),
) -> JSONResponse:
    checks: dict[str, bool] = {}

    try:
        async with AsyncSessionFactory() as session:
            await session.execute(text("SELECT 1"))
        checks["database"] = True
    except Exception:
        checks["database"] = False

    checks["openrouter"] = await ai_provider.health()
    for channel_type, provider in channel_registry.all().items():
        checks[channel_type.value] = await provider.health()

    status_code = 200 if all(checks.values()) else 503
    return JSONResponse(status_code=status_code, content=checks)
