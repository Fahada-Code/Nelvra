"""
Drift Detector — Celery tasks.

Runs hourly. For each tracked prompt:
1. Computes avg quality score for the last 24 hours vs the 7-day baseline.
2. If current < baseline × 0.85 (>15% degradation): flags the prompt as degrading.
3. Calls Claude API to generate a plain-English explanation.
4. Also refreshes cached analytics (avg tokens, cost, latency) on all prompts.
"""

import asyncio
import logging
from datetime import UTC, datetime, timedelta

from workers.celery_app import app

logger = logging.getLogger(__name__)

_DRIFT_THRESHOLD = 0.85  # flag if 24h avg < 7d avg × this factor
_MIN_EVENTS_24H = 5  # require at least this many events for 24h window
_MIN_EVENTS_7D = 20  # require at least this many events for baseline


@app.task(name="workers.drift_detector.detect_all_drift")
def detect_all_drift() -> None:
    asyncio.run(_detect_all())


@app.task(name="workers.drift_detector.refresh_all_prompt_stats")
def refresh_all_prompt_stats() -> None:
    asyncio.run(_refresh_all_stats())


async def _detect_all() -> None:
    from sqlalchemy import select

    from api.database import AsyncSessionLocal
    from api.models.prompt import Prompt

    async with AsyncSessionLocal() as db:
        result = await db.execute(select(Prompt).where(Prompt.deleted_at.is_(None)))
        prompts = result.scalars().all()
        for prompt in prompts:
            await _check_drift(db, prompt)
        await db.commit()


async def _check_drift(db, prompt) -> None:
    from sqlalchemy import func, select

    from api.config import settings
    from api.models.llm_event import LLMEvent

    now = datetime.now(UTC)
    since_24h = now - timedelta(hours=24)
    since_7d = now - timedelta(days=7)

    base = (
        LLMEvent.prompt_id == prompt.id,
        LLMEvent.deleted_at.is_(None),
        LLMEvent.quality_score.is_not(None),
    )

    r24 = await db.execute(
        select(func.avg(LLMEvent.quality_score), func.count()).where(
            *base, LLMEvent.timestamp >= since_24h
        )
    )
    avg_24h, count_24h = r24.one()

    r7d = await db.execute(
        select(func.avg(LLMEvent.quality_score), func.count()).where(
            *base, LLMEvent.timestamp >= since_7d
        )
    )
    avg_7d, count_7d = r7d.one()

    if count_24h < _MIN_EVENTS_24H or count_7d < _MIN_EVENTS_7D:
        return  # not enough data

    avg_24h = float(avg_24h)
    avg_7d = float(avg_7d)

    if avg_24h < avg_7d * _DRIFT_THRESHOLD:
        drop_pct = round((1 - avg_24h / avg_7d) * 100, 1)
        explanation = await _explain_drift(
            prompt, avg_24h, avg_7d, drop_pct, settings.anthropic_api_key
        )
        prompt.quality_trend = "degrading"
        prompt.drift_detected_at = now
        prompt.drift_explanation = explanation

        # Fire drift alert notification
        _notify_drift.delay(str(prompt.id), drop_pct, explanation or "")
    elif avg_24h > avg_7d * (2 - _DRIFT_THRESHOLD):
        prompt.quality_trend = "improving"
        prompt.drift_detected_at = None
        prompt.drift_explanation = None
    else:
        prompt.quality_trend = "stable"


def _fallback_explanation(drop_pct: float, avg_7d: float, avg_24h: float) -> str:
    return (
        f"Quality dropped {drop_pct}% in the last 24 hours "
        f"(from {avg_7d:.2f} to {avg_24h:.2f})."
    )


async def _explain_drift(
    prompt, avg_24h: float, avg_7d: float, drop_pct: float, api_key: str
) -> str | None:
    if not api_key:
        return _fallback_explanation(drop_pct, avg_7d, avg_24h)

    import anthropic

    client = anthropic.AsyncAnthropic(api_key=api_key)
    try:
        msg = await client.messages.create(
            model="claude-haiku-4-5-20251001",
            max_tokens=150,
            messages=[
                {
                    "role": "user",
                    "content": (
                        f"An AI prompt called '{prompt.name}' has degraded in quality by "
                        f"{drop_pct}% over the last 24 hours (quality score dropped from "
                        f"{avg_7d:.2f} to {avg_24h:.2f} out of 1.0). Write one plain-English "
                        f"sentence explaining what this likely means for the application, and "
                        f"one sentence suggesting what to check. Be specific and actionable. "
                        f"No preamble."
                    ),
                }
            ],
        )
        return msg.content[0].text.strip()
    except Exception:
        return _fallback_explanation(drop_pct, avg_7d, avg_24h)


@app.task(name="workers.drift_detector.notify_drift")
def _notify_drift(prompt_id: str, drop_pct: float, explanation: str) -> None:
    asyncio.run(_send_drift_notification(prompt_id, drop_pct, explanation))


async def _send_drift_notification(prompt_id: str, drop_pct: float, explanation: str) -> None:
    from sqlalchemy import select

    from api.database import AsyncSessionLocal
    from api.models.alert import Alert
    from api.models.prompt import Prompt
    from api.services.alert_service import AlertNotifier

    async with AsyncSessionLocal() as db:
        prompt_result = await db.execute(select(Prompt).where(Prompt.id == prompt_id))
        prompt = prompt_result.scalar_one_or_none()
        if prompt is None:
            return

        alerts_result = await db.execute(
            select(Alert).where(
                Alert.project_id == prompt.project_id,
                Alert.metric == "quality_drift",
                Alert.enabled.is_(True),
                Alert.deleted_at.is_(None),
            )
        )
        for alert in alerts_result.scalars():
            await AlertNotifier.send(
                alert,
                f"Prompt '{prompt.name}' quality dropped {drop_pct}%",
                explanation,
            )
        await db.commit()


async def _refresh_all_stats() -> None:
    from sqlalchemy import func, select

    from api.database import AsyncSessionLocal
    from api.models.llm_event import LLMEvent
    from api.models.prompt import Prompt

    async with AsyncSessionLocal() as db:
        result = await db.execute(select(Prompt).where(Prompt.deleted_at.is_(None)))
        prompts = result.scalars().all()

        for prompt in prompts:
            stats = await db.execute(
                select(
                    func.count().label("count"),
                    func.avg(LLMEvent.total_tokens).label("avg_tokens"),
                    func.avg(LLMEvent.cost_usd).label("avg_cost"),
                    func.avg(LLMEvent.latency_ms).label("avg_latency"),
                    func.avg(LLMEvent.quality_score).label("avg_quality"),
                ).where(
                    LLMEvent.prompt_id == prompt.id,
                    LLMEvent.deleted_at.is_(None),
                )
            )
            row = stats.one()
            if row.count:
                prompt.request_count = row.count
                prompt.avg_tokens = int(row.avg_tokens) if row.avg_tokens else None
                prompt.avg_cost_usd = float(row.avg_cost) if row.avg_cost else None
                prompt.avg_latency_ms = int(row.avg_latency) if row.avg_latency else None
                prompt.avg_quality_score = float(row.avg_quality) if row.avg_quality else None

        await db.commit()
