"""
Shared pytest fixtures.

Test fixtures and configuration will be added here as the project grows.
"""

import pytest


@pytest.fixture(scope="session")
def anyio_backend() -> str:
    return "asyncio"
