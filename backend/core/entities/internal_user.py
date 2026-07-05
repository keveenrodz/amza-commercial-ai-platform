from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime

from core.enums.user import InternalUserRole, InternalUserStatus
from core.value_objects.identifiers import InternalUserId, OrganizationId


@dataclass
class InternalUser:
    id: InternalUserId
    organization_id: OrganizationId
    full_name: str
    email: str
    role: InternalUserRole
    status: InternalUserStatus
    created_at: datetime
    updated_at: datetime
