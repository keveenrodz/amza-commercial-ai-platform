from __future__ import annotations

from enum import Enum


class InternalUserRole(Enum):
    ADVISOR = "advisor"
    ADMINISTRATOR = "administrator"


class InternalUserStatus(Enum):
    ACTIVE = "active"
    INACTIVE = "inactive"


class OrganizationStatus(Enum):
    ACTIVE = "active"
    SUSPENDED = "suspended"


class ContactStatus(Enum):
    ACTIVE = "active"
    CUSTOMER = "customer"
    BLOCKED = "blocked"
