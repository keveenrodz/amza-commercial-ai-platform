from __future__ import annotations

from fastapi import APIRouter, Depends

from app.api.dto.advisor import AdvisorSummaryResponse
from app.dependencies import get_list_advisors_use_case
from app.security import get_current_user
from app.use_cases.list_advisors import ListAdvisorsUseCase

router = APIRouter(
    prefix="/organizations/{organization_slug}/advisors",
    tags=["advisors"],
    dependencies=[Depends(get_current_user)],
)


@router.get("")
async def list_advisors(
    organization_slug: str,
    use_case: ListAdvisorsUseCase = Depends(get_list_advisors_use_case),
) -> list[AdvisorSummaryResponse]:
    advisors = await use_case.execute(organization_slug)
    return [AdvisorSummaryResponse.from_domain(a) for a in advisors]
