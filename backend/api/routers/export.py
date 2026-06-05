from fastapi import APIRouter, Depends, Query
from fastapi.responses import Response
from sqlalchemy.ext.asyncio import AsyncSession

from ..database import get_db
from ..dependencies import get_current_project_id
from ..services.export_service import ExportService

router = APIRouter(prefix="/export", tags=["export"])


@router.get("/events.csv")
async def export_events_csv(
    days: int = Query(default=30, ge=1, le=90, description="Number of days to export"),
    project_id: str = Depends(get_current_project_id),
    db: AsyncSession = Depends(get_db),
) -> Response:
    data = await ExportService.export_events_csv(db, project_id, days)
    return Response(
        content=data,
        media_type="text/csv",
        headers={"Content-Disposition": f"attachment; filename=nelvra-events-{days}d.csv"},
    )
