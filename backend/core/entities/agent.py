from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime

from core.enums.agent import AgentStatus
from core.value_objects.identifiers import AgentId, OrganizationId


@dataclass
class Agent:
    id: AgentId
    organization_id: OrganizationId
    name: str
    description: str
    status: AgentStatus
    created_at: datetime
    updated_at: datetime
