import csv
import io
from datetime import UTC, datetime, timedelta

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from ..models.llm_event import LLMEvent


class ExportService:
    @staticmethod
    async def export_events_csv(
        db: AsyncSession,
        project_id: str,
        days: int = 30,
    ) -> bytes:
        since = datetime.now(UTC) - timedelta(days=days)

        result = await db.execute(
            select(LLMEvent)
            .where(
                LLMEvent.project_id == project_id,
                LLMEvent.timestamp >= since,
                LLMEvent.deleted_at.is_(None),
            )
            .order_by(LLMEvent.timestamp.desc())
            .limit(100_000)
        )
        events = result.scalars().all()

        output = io.StringIO()
        writer = csv.writer(output)
        writer.writerow(
            [
                "id",
                "timestamp",
                "model",
                "provider",
                "prompt_id",
                "finish_reason",
                "prompt_tokens",
                "completion_tokens",
                "total_tokens",
                "cost_usd",
                "latency_ms",
                "environment",
                "feature",
                "user_id",
                "session_id",
                "quality_score",
                "tags",
            ]
        )
        for e in events:
            writer.writerow(
                [
                    e.id,
                    e.timestamp.isoformat(),
                    e.model,
                    e.provider,
                    e.prompt_id or "",
                    e.finish_reason,
                    e.prompt_tokens,
                    e.completion_tokens,
                    e.total_tokens,
                    float(e.cost_usd) if e.cost_usd else "",
                    e.latency_ms,
                    e.environment,
                    e.feature or "",
                    e.user_id or "",
                    e.session_id or "",
                    e.quality_score if e.quality_score is not None else "",
                    ",".join(e.tags or []),
                ]
            )
        return output.getvalue().encode("utf-8")
