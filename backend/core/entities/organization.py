from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime

from core.enums.user import OrganizationStatus
from core.value_objects.identifiers import OrganizationId


@dataclass
class Organization:
    id: OrganizationId
    name: str
    slug: str
    timezone: str
    language: str
    status: OrganizationStatus
    created_at: datetime
    updated_at: datetime
