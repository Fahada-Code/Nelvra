from datetime import UTC, datetime, timedelta

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from ..models.llm_event import LLMEvent
from ..schemas.analytics import HourlyBucket, OverviewResponse, RequestsListResponse, RequestSummary

# finish_reason values that indicate something went wrong
_ERROR_FINISH_REASONS = frozenset({"error", "content_filter", "canceled"})


class AnalyticsService:
    """Read-only analytics queries scoped to a single project."""

    @staticmethod
    async def get_overview(
        db: AsyncSession, project_id: str, period_hours: int = 24
    ) -> OverviewResponse:
        since = datetime.now(UTC) - timedelta(hours=period_hours)

        base_filter = (
            LLMEvent.project_id == project_id,
            LLMEvent.timestamp >= since,
            LLMEvent.deleted_at.is_(None),
        )

        # Aggregate totals
        totals_result = await db.execute(
            select(
                func.count().label("total_requests"),
                func.coalesce(func.sum(LLMEvent.cost_usd), 0).label("total_cost_usd"),
                func.coalesce(func.avg(LLMEvent.latency_ms), 0).label("avg_latency_ms"),
                func.count()
                .filter(LLMEvent.finish_reason.in_(_ERROR_FINISH_REASONS))
                .label("error_count"),
            ).where(*base_filter)
        )
        totals = totals_result.one()
        total_requests = totals.total_requests or 0
        error_rate = (totals.error_count / total_requests) if total_requests > 0 else 0.0

        # Requests and cost by model
        model_result = await db.execute(
            select(
                LLMEvent.model,
                func.count().label("requests"),
                func.coalesce(func.sum(LLMEvent.cost_usd), 0).label("cost"),
            )
            .where(*base_filter)
            .group_by(LLMEvent.model)
        )
        requests_by_model: dict[str, int] = {}
        cost_by_model: dict[str, float] = {}
        for row in model_result:
            requests_by_model[row.model] = row.requests
            cost_by_model[row.model] = float(row.cost)

        # Requests by provider
        provider_result = await db.execute(
            select(LLMEvent.provider, func.count().label("requests"))
            .where(*base_filter)
            .group_by(LLMEvent.provider)
        )
        requests_by_provider = {row.provider: row.requests for row in provider_result}

        # Hourly bucketed requests (for sparklines / time-series charts)
        # Reuse one expression object so the "hour" bind parameter is identical in
        # SELECT, GROUP BY and ORDER BY — otherwise Postgres sees distinct params
        # and rejects the grouping.
        hour_bucket = func.date_trunc("hour", LLMEvent.timestamp)
        hourly_result = await db.execute(
            select(
                hour_bucket.label("hour"),
                func.count().label("requests"),
                func.coalesce(func.sum(LLMEvent.cost_usd), 0).label("cost_usd"),
            )
            .where(*base_filter)
            .group_by(hour_bucket)
            .order_by(hour_bucket)
        )
        hourly_buckets = [
            HourlyBucket(
                hour=row.hour.isoformat(),
                requests=row.requests,
                cost_usd=float(row.cost_usd),
            )
            for row in hourly_result
        ]

        return OverviewResponse(
            period_hours=period_hours,
            total_requests=total_requests,
            total_cost_usd=float(totals.total_cost_usd),
            avg_latency_ms=float(totals.avg_latency_ms),
            error_count=totals.error_count,
            error_rate=round(error_rate, 4),
            requests_by_model=requests_by_model,
            requests_by_provider=requests_by_provider,
            cost_by_model=cost_by_model,
            hourly_requests=hourly_buckets,
        )

    @staticmethod
    async def list_requests(
        db: AsyncSession,
        project_id: str,
        page: int = 1,
        per_page: int = 50,
        model: str | None = None,
        provider: str | None = None,
        environment: str | None = None,
        feature: str | None = None,
    ) -> RequestsListResponse:
        per_page = min(per_page, 200)
        offset = (page - 1) * per_page

        filters = [
            LLMEvent.project_id == project_id,
            LLMEvent.deleted_at.is_(None),
        ]
        if model:
            filters.append(LLMEvent.model == model)
        if provider:
            filters.append(LLMEvent.provider == provider)
        if environment:
            filters.append(LLMEvent.environment == environment)
        if feature:
            filters.append(LLMEvent.feature == feature)

        count_result = await db.execute(select(func.count()).where(*filters))
        total = count_result.scalar_one()

        items_result = await db.execute(
            select(LLMEvent)
            .where(*filters)
            .order_by(LLMEvent.timestamp.desc())
            .limit(per_page)
            .offset(offset)
        )
        items = [RequestSummary.model_validate(row) for row in items_result.scalars()]

        return RequestsListResponse(
            items=items,
            total=total,
            page=page,
            per_page=per_page,
        )

    @staticmethod
    async def get_event_detail(db: AsyncSession, project_id: str, event_id: str) -> LLMEvent | None:
        result = await db.execute(
            select(LLMEvent).where(
                LLMEvent.id == event_id,
                LLMEvent.project_id == project_id,
                LLMEvent.deleted_at.is_(None),
            )
        )
        return result.scalar_one_or_none()
