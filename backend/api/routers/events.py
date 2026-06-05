from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from ..database import get_db
from ..dependencies import get_current_project_id, rate_limit_events
from ..schemas.events import (
    LLMEventBatchCreate,
    LLMEventBatchResponse,
    LLMEventCreate,
    LLMEventResponse,
)
from ..services.event_service import EventService
from ..tasks import evaluate_quality_async

router = APIRouter(prefix="/events", tags=["events"])


@router.post(
    "",
    response_model=LLMEventResponse,
    status_code=201,
    dependencies=[Depends(rate_limit_events)],
)
async def ingest_event(
    data: LLMEventCreate,
    project_id: str = Depends(get_current_project_id),
    db: AsyncSession = Depends(get_db),
) -> LLMEventResponse:
    event = await EventService.create(db, project_id, data)
    evaluate_quality_async(event.id)
    return LLMEventResponse.model_validate(event)


@router.post(
    "/batch",
    response_model=LLMEventBatchResponse,
    status_code=201,
    dependencies=[Depends(rate_limit_events)],
)
async def ingest_events_batch(
    data: LLMEventBatchCreate,
    project_id: str = Depends(get_current_project_id),
    db: AsyncSession = Depends(get_db),
) -> LLMEventBatchResponse:
    events = await EventService.create_batch(db, project_id, data.events)
    for e in events:
        evaluate_quality_async(e.id)
    return LLMEventBatchResponse(created=len(events), ids=[e.id for e in events])
