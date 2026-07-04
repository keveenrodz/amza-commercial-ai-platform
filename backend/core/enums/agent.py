from __future__ import annotations

from enum import Enum


class AgentStatus(Enum):
    ACTIVE = "active"
    PAUSED = "paused"
    DISABLED = "disabled"
    MAINTENANCE = "maintenance"
