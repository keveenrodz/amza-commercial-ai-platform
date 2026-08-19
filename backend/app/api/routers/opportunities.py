from __future__ import annotations

from fastapi import APIRouter, Depends

from app.api.dto.follow_up import FollowUpResponse, ScheduleFollowUpRequest
from app.api.dto.opportunity import (
    AssignAdvisorRequest,
    ConversationHistoryResponse,
    MessageResponse,
    OpenOpportunityResponse,
    OpportunityResponse,
    SendMessageRequest,
    SetUnreadRequest,
)
from app.dependencies import (
    get_assign_to_advisor_use_case,
    get_get_conversation_history_use_case,
    get_list_open_opportunities_use_case,
    get_resolve_follow_up_use_case,
    get_return_to_ai_use_case,
    get_schedule_follow_up_use_case,
    get_search_opportunities_use_case,
    get_send_advisor_reply_use_case,
    get_set_opportunity_unread_use_case,
)
from app.security import get_current_user
from app.use_cases.assign_to_advisor import AssignToAdvisorUseCase
from app.use_cases.get_conversation_history import GetConversationHistoryUseCase
from app.use_cases.list_open_opportunities import ListOpenOpportunitiesUseCase
from app.use_cases.resolve_follow_up import ResolveFollowUpUseCase
from app.use_cases.return_to_ai import ReturnToAIUseCase
from app.use_cases.schedule_follow_up import ScheduleFollowUpUseCase
from app.use_cases.search_opportunities import SearchOpportunitiesUseCase
from app.use_cases.send_advisor_reply import SendAdvisorReplyUseCase
from app.use_cases.set_opportunity_unread import SetOpportunityUnreadUseCase
from core.value_objects.identifiers import InternalUserId, OpportunityId

# Protegido a nivel de router, no endpoint por endpoint -- todos los endpoints requieren la misma
# sesión válida (spec 008 sección 8/3: hoy Advisor y Administrator pueden hacer todas las
# acciones por igual, no hay ninguna restricción de rol real todavía -- ver require_role() en
# app/security.py para cuando exista un endpoint que sí la necesite).
router = APIRouter(
    prefix="/organizations/{organization_slug}/opportunities",
    tags=["opportunities"],
    dependencies=[Depends(get_current_user)],
)


@router.get("")
async def list_open_opportunities(
    organization_slug: str,
    use_case: ListOpenOpportunitiesUseCase = Depends(get_list_open_opportunities_use_case),
) -> list[OpenOpportunityResponse]:
    items = await use_case.execute(organization_slug)
    return [OpenOpportunityResponse.from_domain(item) for item in items]


@router.get("/search")
async def search_opportunities(
    organization_slug: str,
    q: str,
    use_case: SearchOpportunitiesUseCase = Depends(get_search_opportunities_use_case),
) -> list[OpenOpportunityResponse]:
    items = await use_case.execute(organization_slug, q)
    return [OpenOpportunityResponse.from_domain(item) for item in items]


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


@router.post("/{opportunity_id}/messages")
async def send_advisor_reply(
    organization_slug: str,  # ignorado intencionalmente, ver nota de alcance en spec 007
    opportunity_id: str,
    body: SendMessageRequest,
    use_case: SendAdvisorReplyUseCase = Depends(get_send_advisor_reply_use_case),
) -> MessageResponse:
    message = await use_case.execute(
        OpportunityId.from_string(opportunity_id),
        InternalUserId.from_string(body.advisor_id),
        body.content,
    )
    return MessageResponse.from_domain(message)


@router.post("/{opportunity_id}/unread")
async def set_opportunity_unread(
    organization_slug: str,
    opportunity_id: str,
    body: SetUnreadRequest,
    use_case: SetOpportunityUnreadUseCase = Depends(get_set_opportunity_unread_use_case),
) -> OpportunityResponse:
    opportunity = await use_case.execute(OpportunityId.from_string(opportunity_id), body.unread)
    return OpportunityResponse.from_domain(opportunity)


@router.post("/{opportunity_id}/follow-up")
async def schedule_follow_up(
    organization_slug: str,
    opportunity_id: str,
    body: ScheduleFollowUpRequest,
    use_case: ScheduleFollowUpUseCase = Depends(get_schedule_follow_up_use_case),
) -> FollowUpResponse:
    follow_up = await use_case.execute(
        OpportunityId.from_string(opportunity_id),
        InternalUserId.from_string(body.advisor_id),
        body.due_at,
        body.reason,
    )
    return FollowUpResponse.from_domain(follow_up)


@router.post("/{opportunity_id}/follow-up/resolve")
async def resolve_follow_up(
    organization_slug: str,
    opportunity_id: str,
    use_case: ResolveFollowUpUseCase = Depends(get_resolve_follow_up_use_case),
) -> FollowUpResponse:
    follow_up = await use_case.execute(OpportunityId.from_string(opportunity_id))
    return FollowUpResponse.from_domain(follow_up)
