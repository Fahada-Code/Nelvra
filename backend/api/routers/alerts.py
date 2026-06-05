from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from ..database import get_db
from ..dependencies import get_current_project_id
from ..schemas.alerts import AlertCreate, AlertIncidentResponse, AlertResponse, AlertUpdate
from ..services.alert_service import AlertService

router = APIRouter(prefix="/alerts", tags=["alerts"])


@router.get("", response_model=list[AlertResponse])
async def list_alerts(
    project_id: str = Depends(get_current_project_id),
    db: AsyncSession = Depends(get_db),
) -> list[AlertResponse]:
    alerts = await AlertService.list_for_project(db, project_id)
    return [AlertResponse.model_validate(a) for a in alerts]


@router.post("", response_model=AlertResponse, status_code=201)
async def create_alert(
    data: AlertCreate,
    project_id: str = Depends(get_current_project_id),
    db: AsyncSession = Depends(get_db),
) -> AlertResponse:
    alert = await AlertService.create(db, project_id, data)
    return AlertResponse.model_validate(alert)


@router.get("/incidents", response_model=list[AlertIncidentResponse])
async def list_incidents(
    limit: int = Query(default=50, ge=1, le=200),
    project_id: str = Depends(get_current_project_id),
    db: AsyncSession = Depends(get_db),
) -> list[AlertIncidentResponse]:
    incidents = await AlertService.list_incidents(db, project_id, limit)
    return [AlertIncidentResponse.model_validate(i) for i in incidents]


@router.put("/{alert_id}", response_model=AlertResponse)
async def update_alert(
    alert_id: str,
    data: AlertUpdate,
    project_id: str = Depends(get_current_project_id),
    db: AsyncSession = Depends(get_db),
) -> AlertResponse:
    alert = await AlertService.update(db, project_id, alert_id, data)
    return AlertResponse.model_validate(alert)


@router.delete("/{alert_id}", status_code=204)
async def delete_alert(
    alert_id: str,
    project_id: str = Depends(get_current_project_id),
    db: AsyncSession = Depends(get_db),
) -> None:
    await AlertService.delete(db, project_id, alert_id)
