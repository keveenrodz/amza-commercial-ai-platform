from __future__ import annotations

from fastapi import APIRouter, Depends

from app.api.dto.agent import AgentResponse, UpdateAgentRequest
from app.dependencies import get_get_agent_use_case, get_update_agent_use_case
from app.security import require_role
from app.use_cases.get_agent import GetAgentUseCase
from app.use_cases.update_agent import UpdateAgentUseCase
from core.enums.user import InternalUserRole

router = APIRouter(
    prefix="/organizations/{organization_slug}/agent",
    tags=["agent"],
    dependencies=[Depends(require_role(InternalUserRole.ADMINISTRATOR))],
)


@router.get("")
async def get_agent(
    organization_slug: str,
    use_case: GetAgentUseCase = Depends(get_get_agent_use_case),
) -> AgentResponse:
    agent = await use_case.execute(organization_slug)
    return AgentResponse.from_domain(agent)


@router.put("")
async def update_agent(
    organization_slug: str,
    body: UpdateAgentRequest,
    use_case: UpdateAgentUseCase = Depends(get_update_agent_use_case),
) -> AgentResponse:
    agent = await use_case.execute(
        organization_slug, body.system_prompt, body.escalation_rules, body.model
    )
    return AgentResponse.from_domain(agent)
