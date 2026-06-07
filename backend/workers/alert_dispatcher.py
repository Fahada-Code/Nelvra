"""
Alert Dispatcher — Celery task.

Runs every minute. Evaluates all enabled threshold alerts against recent data
and fires notifications when thresholds are breached.
"""

import asyncio
import logging
from datetime import UTC, datetime, timedelta

from workers.celery_app import app

logger = logging.getLogger(__name__)

_NOTIFICATION_COOLDOWN_MINUTES = 30


@app.task(name="workers.alert_dispatcher.check_all_alerts")
def check_all_alerts() -> None:
    asyncio.run(_run())


async def _run() -> None:
    from sqlalchemy import select

    from api.database import AsyncSessionLocal
    from api.models.alert import Alert

    async with AsyncSessionLocal() as db:
        result = await db.execute(
            select(Alert).where(Alert.enabled.is_(True), Alert.deleted_at.is_(None))
        )
        for alert in result.scalars():
            await _evaluate(db, alert)
        await db.commit()


async def _evaluate(db, alert) -> None:
    from api.services.alert_service import AlertNotifier

    value = await _compute_metric(db, alert)
    if value is None:
        return

    breached = _check_threshold(value, alert.operator, alert.threshold)
    now = datetime.now(UTC)

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
    ops = {
        "gt": value > threshold,
        "lt": value < threshold,
        "gte": value >= threshold,
        "lte": value <= threshold,
    }
    return ops.get(operator, False)


async def _compute_metric(db, alert) -> float | None:
    from sqlalchemy import func, select

    from api.models.llm_event import LLMEvent

    since = datetime.now(UTC) - timedelta(minutes=alert.window_minutes)

    filters = (
        LLMEvent.project_id == alert.project_id,
        LLMEvent.timestamp >= since,
        LLMEvent.deleted_at.is_(None),
    )

    if alert.metric == "cost_usd":
        r = await db.execute(select(func.coalesce(func.sum(LLMEvent.cost_usd), 0)).where(*filters))
        return float(r.scalar())

    if alert.metric == "error_rate":
        r = await db.execute(
            select(
                func.count(),
                func.count().filter(
                    LLMEvent.finish_reason.in_(["error", "content_filter", "canceled"])
                ),
            ).where(*filters)
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
