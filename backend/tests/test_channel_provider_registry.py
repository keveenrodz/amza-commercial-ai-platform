"""
Cubre spec 015 (Channel Provider Routing): ChannelProviderRegistry resuelve el ChannelProvider
correcto por canal en vez de asumir que solo existe uno (prerrequisito de spec 016, que agrega un
segundo canal real).
"""

from __future__ import annotations

import pytest

from app.services.channel_provider_registry import ChannelProviderRegistry
from core.entities.contact import Contact
from core.entities.message import Message
from core.enums.channel import ChannelType
from core.exceptions.domain import UnsupportedChannelError


class _FakeChannelProvider:
    async def send(
        self, message: Message, contact: Contact, *, is_first_reply: bool = False
    ) -> None:
        return None

    async def health(self) -> bool:
        return True


def test_get_returns_the_registered_provider_for_that_channel() -> None:
    provider = _FakeChannelProvider()
    registry = ChannelProviderRegistry({ChannelType.TELEGRAM: provider})

    assert registry.get(ChannelType.TELEGRAM) is provider


def test_get_raises_for_an_unregistered_channel() -> None:
    registry = ChannelProviderRegistry({ChannelType.TELEGRAM: _FakeChannelProvider()})

    with pytest.raises(UnsupportedChannelError):
        registry.get(ChannelType.WHATSAPP)


def test_all_returns_a_copy_not_the_internal_dict() -> None:
    provider = _FakeChannelProvider()
    registry = ChannelProviderRegistry({ChannelType.TELEGRAM: provider})

    snapshot = registry.all()
    snapshot[ChannelType.WHATSAPP] = _FakeChannelProvider()

    with pytest.raises(UnsupportedChannelError):
        registry.get(ChannelType.WHATSAPP)
