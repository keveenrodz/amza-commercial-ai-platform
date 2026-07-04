from sqlalchemy.ext.asyncio import AsyncEngine, create_async_engine

from app.config import settings


def build_engine() -> AsyncEngine:
    url = settings.database_url.replace("sqlite:///", "sqlite+aiosqlite:///", 1)
    return create_async_engine(url, echo=settings.debug)
