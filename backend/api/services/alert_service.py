import logging
from datetime import UTC

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from ..exceptions import NelvraException
from ..models.alert import Alert, AlertIncident
from ..schemas.alerts import AlertCreate, AlertUpdate

logger = logging.getLogger(__name__)


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
            select(Alert).where(
                Alert.id == alert_id, Alert.project_id == project_id, Alert.deleted_at.is_(None)
            )
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
        from datetime import datetime

        alert = await AlertService.get(db, project_id, alert_id)
        alert.deleted_at = datetime.now(UTC)
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


class AlertNotifier:
    """Dispatches alert notifications to Slack and email.

    Shared by the alert dispatcher (threshold breaches) and the drift detector
    (quality degradation). Failures are logged, never raised — a notification
    outage must not block alert evaluation.
    """

    @staticmethod
    async def send(alert, title: str, body: str) -> None:
        if alert.notify_slack and alert.slack_webhook_url:
            await AlertNotifier._send_slack(alert.slack_webhook_url, title, body)
        if alert.notify_email and alert.email_address:
            await AlertNotifier._send_email(alert.email_address, title, body)

    @staticmethod
    async def _send_slack(webhook_url: str, title: str, body: str) -> None:
        import httpx

        payload = {
            "text": f"🚨 *{title}*\n{body}",
            "username": "Nelvra Alerts",
            "icon_emoji": ":warning:",
        }
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                resp = await client.post(webhook_url, json=payload)
                resp.raise_for_status()
        except Exception as exc:
            logger.warning("Slack notification failed: %s", exc)

    @staticmethod
    async def _send_email(to_address: str, title: str, body: str) -> None:
        from ..config import settings

        if not settings.smtp_username:
            return
        try:
            from email.mime.text import MIMEText

            import aiosmtplib

            msg = MIMEText(f"{body}\n\n— Nelvra Alerts\nhttps://app.nelvra.io")
            msg["Subject"] = f"[Nelvra] {title}"
            msg["From"] = settings.smtp_from
            msg["To"] = to_address

            await aiosmtplib.send(
                msg,
                hostname=settings.smtp_host,
                port=settings.smtp_port,
                username=settings.smtp_username,
                password=settings.smtp_password,
                start_tls=True,
            )
        except Exception as exc:
            logger.warning("Email notification failed: %s", exc)
