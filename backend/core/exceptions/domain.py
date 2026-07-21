from __future__ import annotations

from core.enums.opportunity import OpportunityStatus
from core.value_objects.identifiers import (
    AgentId,
    ContactId,
    InternalUserId,
    OpportunityId,
    OrganizationId,
)


class DomainError(Exception):
    pass


class OpportunityNotFoundError(DomainError):
    def __init__(self, opportunity_id: OpportunityId) -> None:
        super().__init__(f"Opportunity {opportunity_id} not found")
        self.opportunity_id = opportunity_id


class OpportunityAlreadyClosedError(DomainError):
    def __init__(self, opportunity_id: OpportunityId) -> None:
        super().__init__(f"Opportunity {opportunity_id} is already closed")
        self.opportunity_id = opportunity_id


class InvalidStatusTransitionError(DomainError):
    def __init__(
        self,
        current_status: OpportunityStatus,
        attempted_status: OpportunityStatus,
    ) -> None:
        super().__init__(
            f"Cannot transition from {current_status.value!r} to {attempted_status.value!r}"
        )
        self.current_status = current_status
        self.attempted_status = attempted_status


class ContactNotFoundError(DomainError):
    def __init__(self, contact_id: ContactId) -> None:
        super().__init__(f"Contact {contact_id} not found")
        self.contact_id = contact_id


class AgentNotFoundError(DomainError):
    def __init__(self, agent_id: AgentId) -> None:
        super().__init__(f"Agent {agent_id} not found")
        self.agent_id = agent_id


class OrganizationNotFoundError(DomainError):
    def __init__(self, organization_id: OrganizationId) -> None:
        super().__init__(f"Organization {organization_id} not found")
        self.organization_id = organization_id


class OrganizationSlugNotFoundError(DomainError):
    def __init__(self, slug: str) -> None:
        super().__init__(f"Organization with slug {slug!r} not found")
        self.slug = slug


class InternalUserNotFoundError(DomainError):
    def __init__(self, user_id: InternalUserId) -> None:
        super().__init__(f"InternalUser {user_id} not found")
        self.user_id = user_id


class NoActiveAgentError(DomainError):
    def __init__(self, organization_id: OrganizationId) -> None:
        super().__init__(f"No active agent found for organization {organization_id}")
        self.organization_id = organization_id


class OpportunityNotAssignedToAdvisorError(DomainError):
    """Un solo chequeo (assigned_advisor_id != advisor_id) cubre dos casos: la oportunidad sigue
    en modo AI (assigned_advisor_id es None, nunca igual a un advisor_id real), o está asignada a
    otro asesor. Opportunity.assign_to_advisor()/return_to_ai() siempre fijan/limpian
    attention_mode y assigned_advisor_id juntos, así que este único campo basta."""

    def __init__(self, opportunity_id: OpportunityId, advisor_id: InternalUserId) -> None:
        super().__init__(f"Opportunity {opportunity_id} is not assigned to advisor {advisor_id}")
        self.opportunity_id = opportunity_id
        self.advisor_id = advisor_id


class AccessDeniedError(DomainError):
    """Alguien probó con éxito ser dueño de un email vía OAuth, pero no existe ningún
    InternalUser activo para ese email. Distinto de InternalUserNotFoundError -- ese es un lookup
    por ID dentro de un flujo ya autenticado; este es el resultado de un intento de login."""

    def __init__(self, email: str) -> None:
        super().__init__(f"No active InternalUser found for email {email!r}")
        self.email = email
