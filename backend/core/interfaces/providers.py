from __future__ import annotations

from typing import Protocol

from core.entities.message import Message
from core.entities.opportunity import Opportunity
from core.value_objects.identifiers import AgentId


class ChannelProvider(Protocol):
    async def send(self, message: Message, opportunity: Opportunity) -> None: ...

    async def health(self) -> bool: ...


class AIProvider(Protocol):
    async def generate(self, messages: list[Message], agent_id: AgentId) -> str: ...

    async def health(self) -> bool: ...
