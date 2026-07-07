"""
Shared pytest fixtures.

Primera infraestructura de tests del proyecto (spec 008). Usa un archivo SQLite temporal propio
-- nunca la BD de desarrollo -- creado y destruido en cada sesión de tests.

Las variables de entorno se fijan ANTES de cualquier import de app/core/infrastructure, porque
Settings() y AsyncSessionFactory se construyen una sola vez, al importarse por primera vez.
"""

from __future__ import annotations

import os
from collections.abc import AsyncIterator
from pathlib import Path

_TEST_DB_PATH = Path(__file__).resolve().parent / "test.db"
if _TEST_DB_PATH.exists():
    _TEST_DB_PATH.unlink()

os.environ["DATABASE_URL"] = f"sqlite:///{_TEST_DB_PATH}"
os.environ["JWT_SECRET"] = "test-secret-key-not-for-production-use"
os.environ["JWT_TTL_HOURS"] = "24"
os.environ["GOOGLE_CLIENT_ID"] = "test-client-id"
os.environ["GOOGLE_CLIENT_SECRET"] = "test-client-secret"
os.environ["GOOGLE_REDIRECT_URI"] = "http://testserver/auth/google/callback"
os.environ["DEBUG"] = "true"  # Secure=False en la cookie, httpx no manda cookies Secure en test

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient

from infrastructure.database.base import Base
from infrastructure.database.session import _engine

# Importados para que Base.metadata conozca todas las tablas antes de create_all -- mismo
# patrón que migrations/env.py.
from modules.agents.models.agent import AgentModel  # noqa: F401
from modules.configuration.models.organization import OrganizationModel  # noqa: F401
from modules.memory.models.conversation_summary import ConversationSummaryModel  # noqa: F401
from modules.opportunities.models.contact import ContactModel  # noqa: F401
from modules.opportunities.models.conversation import ConversationModel  # noqa: F401
from modules.opportunities.models.message import MessageModel  # noqa: F401
from modules.opportunities.models.opportunity import OpportunityModel  # noqa: F401
from modules.users.models.internal_user import InternalUserModel  # noqa: F401


@pytest.fixture(scope="session")
def anyio_backend() -> str:
    return "asyncio"


@pytest_asyncio.fixture(autouse=True)
async def _reset_schema() -> AsyncIterator[None]:
    async with _engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
        await conn.run_sync(Base.metadata.create_all)
    yield


@pytest_asyncio.fixture
async def client() -> AsyncIterator[AsyncClient]:
    from app.main import app

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://testserver") as ac:
        yield ac
