from __future__ import annotations

from core.enums.channel import ChannelType
from core.exceptions.domain import UnsupportedChannelError
from core.interfaces.providers import ChannelProvider


class ChannelProviderRegistry:
    def __init__(self, providers: dict[ChannelType, ChannelProvider]) -> None:
        self._providers = providers

    def get(self, channel_type: ChannelType) -> ChannelProvider:
        provider = self._providers.get(channel_type)
        if provider is None:
            raise UnsupportedChannelError(channel_type)
        return provider

    def all(self) -> dict[ChannelType, ChannelProvider]:
        return dict(self._providers)
