"""
Alert Dispatcher — Celery task.

Runs every minute. Evaluates all enabled threshold alerts against recent data
and fires notifications when thresholds are breached.
"""
import asyncio
import logging
from datetime import datetime, timedelta, timezone

from workers.celery_app import app

logger = logging.getLogger(__name__)

_NOTIFICATION_COOLDOWN_MINUTES = 30


@app.task(name="workers.alert_dispatcher.check_all_alerts")
def check_all_alerts() -> None:
    asyncio.run(_run())


async def _run() -> None:
    from api.database import AsyncSessionLocal
    from api.models.alert import Alert
    from sqlalchemy import select

    async with AsyncSessionLocal() as db:
        result = await db.execute(
            select(Alert).where(Alert.enabled == True, Alert.deleted_at.is_(None))
        )
        for alert in result.scalars():
            await _evaluate(db, alert)
        await db.commit()


async def _evaluate(db, alert) -> None:
    value = await _compute_metric(db, alert)
    if value is None:
        return

    breached = _check_threshold(value, alert.operator, alert.threshold)
    now = datetime.now(timezone.utc)

    if breached:
        alert.consecutive_breaches += 1
        cooldown_passed = (
            alert.last_triggered_at is None
            or (now - alert.last_triggered_at).total_seconds() > _NOTIFICATION_COOLDOWN_MINUTES * 60
        )
        if cooldown_passed:
            alert.last_triggered_at = now
            await _create_incident(db, alert, value)
            await AlertNotifier.send(
                alert,
                f"Alert '{alert.name}' triggered",
                f"{alert.metric} = {value:.4f} (threshold: {alert.operator} {alert.threshold})",
            )
    else:
        alert.consecutive_breaches = 0


def _check_threshold(value: float, operator: str, threshold: float) -> bool:
    ops = {"gt": value > threshold, "lt": value < threshold, "gte": value >= threshold, "lte": value <= threshold}
    return ops.get(operator, False)


async def _compute_metric(db, alert) -> float | None:
    from api.models.llm_event import LLMEvent
    from sqlalchemy import cast, func, select
    from sqlalchemy.dialects.postgresql import TIMESTAMP as PG_TS

    since = datetime.now(timezone.utc) - timedelta(minutes=alert.window_minutes)

    def _ts(col):
        return cast(col, PG_TS(timezone=True))

    filters = (
        LLMEvent.project_id == alert.project_id,
        _ts(LLMEvent.timestamp) >= since,
        LLMEvent.deleted_at.is_(None),
    )

    if alert.metric == "cost_usd":
        r = await db.execute(select(func.coalesce(func.sum(LLMEvent.cost_usd), 0)).where(*filters))
        return float(r.scalar())

    if alert.metric == "error_rate":
        r = await db.execute(
            select(func.count(), func.count().filter(
                LLMEvent.finish_reason.in_(["error", "content_filter", "canceled"])
            )).where(*filters)
        )
        total, errors = r.one()
        return (errors / total) if total > 0 else 0.0

    if alert.metric == "latency_p95":
        r = await db.execute(
            select(func.percentile_cont(0.95).within_group(LLMEvent.latency_ms)).where(*filters)
        )
        val = r.scalar()
        return float(val) if val is not None else None

    if alert.metric == "request_count":
        r = await db.execute(select(func.count()).where(*filters))
        return float(r.scalar())

    return None


async def _create_incident(db, alert, value: float) -> None:
    from api.models.alert import AlertIncident
    incident = AlertIncident(
        alert_id=alert.id,
        project_id=alert.project_id,
        triggered_value=value,
        notification_sent=True,
    )
    db.add(incident)


class AlertNotifier:
    """Handles Slack and email notification dispatch."""

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
        from api.config import settings
        if not settings.smtp_username:
            return
        try:
            import aiosmtplib
            from email.mime.text import MIMEText

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
