from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from ..exceptions import NelvraException
from ..models.alert import Alert, AlertIncident
from ..schemas.alerts import AlertCreate, AlertUpdate


class AlertService:
    @staticmethod
    async def create(db: AsyncSession, project_id: str, data: AlertCreate) -> Alert:
        alert = Alert(
            project_id=project_id,
            name=data.name,
            metric=data.metric,
            operator=data.operator,
            threshold=data.threshold,
            window_minutes=data.window_minutes,
            notify_slack=data.notify_slack,
            slack_webhook_url=data.slack_webhook_url,
            notify_email=data.notify_email,
            email_address=data.email_address,
        )
        db.add(alert)
        await db.flush()
        await db.refresh(alert)
        return alert

    @staticmethod
    async def list_for_project(db: AsyncSession, project_id: str) -> list[Alert]:
        result = await db.execute(
            select(Alert)
            .where(Alert.project_id == project_id, Alert.deleted_at.is_(None))
            .order_by(Alert.created_at.desc())
        )
        return list(result.scalars())

    @staticmethod
    async def get(db: AsyncSession, project_id: str, alert_id: str) -> Alert:
        result = await db.execute(
            select(Alert).where(Alert.id == alert_id, Alert.project_id == project_id, Alert.deleted_at.is_(None))
        )
        alert = result.scalar_one_or_none()
        if not alert:
            raise NelvraException("Alert not found", "ALERT_NOT_FOUND", 404)
        return alert

    @staticmethod
    async def update(db: AsyncSession, project_id: str, alert_id: str, data: AlertUpdate) -> Alert:
        alert = await AlertService.get(db, project_id, alert_id)
        for field, value in data.model_dump(exclude_none=True).items():
            setattr(alert, field, value)
        await db.flush()
        await db.refresh(alert)
        return alert

    @staticmethod
    async def delete(db: AsyncSession, project_id: str, alert_id: str) -> None:
        from datetime import datetime, timezone
        alert = await AlertService.get(db, project_id, alert_id)
        alert.deleted_at = datetime.now(timezone.utc)
        await db.flush()

    @staticmethod
    async def list_incidents(
        db: AsyncSession, project_id: str, limit: int = 50
    ) -> list[AlertIncident]:
        result = await db.execute(
            select(AlertIncident)
            .where(AlertIncident.project_id == project_id)
            .order_by(AlertIncident.created_at.desc())
            .limit(limit)
        )
        return list(result.scalars())
