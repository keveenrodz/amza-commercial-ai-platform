from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime

from core.enums.channel import ChannelType
from core.enums.user import ContactStatus
from core.value_objects.identifiers import ContactId, OrganizationId


@dataclass
class Contact:
    id: ContactId
    organization_id: OrganizationId
    channel_type: ChannelType
    external_id: str
    display_name: str
    status: ContactStatus
    created_at: datetime
    updated_at: datetime
    phone_number: str | None = None
    email: str | None = None
