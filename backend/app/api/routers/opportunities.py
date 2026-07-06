from __future__ import annotations

from fastapi import APIRouter, Depends

from app.api.dto.opportunity import (
    AssignAdvisorRequest,
    ConversationHistoryResponse,
    OpportunityResponse,
)
from app.dependencies import (
    get_assign_to_advisor_use_case,
    get_get_conversation_history_use_case,
    get_list_open_opportunities_use_case,
    get_return_to_ai_use_case,
)
from app.use_cases.assign_to_advisor import AssignToAdvisorUseCase
from app.use_cases.get_conversation_history import GetConversationHistoryUseCase
from app.use_cases.list_open_opportunities import ListOpenOpportunitiesUseCase
from app.use_cases.return_to_ai import ReturnToAIUseCase
from core.value_objects.identifiers import InternalUserId, OpportunityId

router = APIRouter(
    prefix="/organizations/{organization_slug}/opportunities", tags=["opportunities"]
)


@router.get("")
async def list_open_opportunities(
    organization_slug: str,
    use_case: ListOpenOpportunitiesUseCase = Depends(get_list_open_opportunities_use_case),
) -> list[OpportunityResponse]:
    opportunities = await use_case.execute(organization_slug)
    return [OpportunityResponse.from_domain(o) for o in opportunities]


@router.get("/{opportunity_id}/history")
async def get_conversation_history(
    organization_slug: str,  # ignorado intencionalmente, ver nota de alcance en spec 007
    opportunity_id: str,
    use_case: GetConversationHistoryUseCase = Depends(get_get_conversation_history_use_case),
) -> ConversationHistoryResponse:
    history = await use_case.execute(OpportunityId.from_string(opportunity_id))
    return ConversationHistoryResponse.from_domain(history)


@router.post("/{opportunity_id}/assign-advisor")
async def assign_to_advisor(
    organization_slug: str,  # ignorado intencionalmente, ver nota de alcance en spec 007
    opportunity_id: str,
    body: AssignAdvisorRequest,
    use_case: AssignToAdvisorUseCase = Depends(get_assign_to_advisor_use_case),
) -> OpportunityResponse:
    opportunity = await use_case.execute(
        OpportunityId.from_string(opportunity_id),
        InternalUserId.from_string(body.advisor_id),
    )
    return OpportunityResponse.from_domain(opportunity)


@router.post("/{opportunity_id}/return-to-ai")
async def return_to_ai(
    organization_slug: str,  # ignorado intencionalmente, ver nota de alcance en spec 007
    opportunity_id: str,
    use_case: ReturnToAIUseCase = Depends(get_return_to_ai_use_case),
) -> OpportunityResponse:
    opportunity = await use_case.execute(OpportunityId.from_string(opportunity_id))
    return OpportunityResponse.from_domain(opportunity)
