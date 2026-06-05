from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from ..database import get_db
from ..dependencies import get_current_project_id
from ..exceptions import NelvraException
from ..schemas.analytics import OverviewResponse, RequestsListResponse
from ..schemas.events import LLMEventDetailResponse
from ..services.analytics_service import AnalyticsService

router = APIRouter(prefix="/analytics", tags=["analytics"])


@router.get("/overview", response_model=OverviewResponse)
async def get_overview(
    period_hours: int = Query(default=24, ge=1, le=720),
    project_id: str = Depends(get_current_project_id),
    db: AsyncSession = Depends(get_db),
) -> OverviewResponse:
    return await AnalyticsService.get_overview(db, project_id, period_hours)


@router.get("/requests", response_model=RequestsListResponse)
async def list_requests(
    page: int = Query(default=1, ge=1),
    per_page: int = Query(default=50, ge=1, le=200),
    model: str | None = Query(default=None),
    provider: str | None = Query(default=None),
    environment: str | None = Query(default=None),
    feature: str | None = Query(default=None),
    project_id: str = Depends(get_current_project_id),
    db: AsyncSession = Depends(get_db),
) -> RequestsListResponse:
    return await AnalyticsService.list_requests(
        db, project_id, page, per_page, model, provider, environment, feature
    )


@router.get("/requests/{event_id}", response_model=LLMEventDetailResponse)
async def get_request_detail(
    event_id: str,
    project_id: str = Depends(get_current_project_id),
    db: AsyncSession = Depends(get_db),
) -> LLMEventDetailResponse:
    event = await AnalyticsService.get_event_detail(db, project_id, event_id)
    if event is None:
        raise NelvraException(
            message="Event not found",
            code="EVENT_NOT_FOUND",
            status_code=404,
        )
    return LLMEventDetailResponse.model_validate(event)
