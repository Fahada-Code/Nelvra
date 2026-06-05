from sqlalchemy.ext.asyncio import AsyncSession

from ..models.llm_event import LLMEvent
from ..schemas.events import LLMEventCreate


class EventService:
    """Business logic for LLM event ingestion."""

    @staticmethod
    async def create(
        db: AsyncSession, project_id: str, data: LLMEventCreate
    ) -> LLMEvent:
        event = LLMEvent(
            project_id=project_id,
            timestamp=data.timestamp.isoformat(),
            model=data.model,
            provider=data.provider,
            prompt_id=data.prompt_id,
            messages=data.messages,
            system_prompt=data.system_prompt,
            response_text=data.response_text,
            finish_reason=data.finish_reason,
            prompt_tokens=data.prompt_tokens,
            completion_tokens=data.completion_tokens,
            total_tokens=data.total_tokens,
            cost_usd=data.cost_usd,
            latency_ms=data.latency_ms,
            user_id=data.user_id,
            session_id=data.session_id,
            feature=data.feature,
            environment=data.environment,
            tags=data.tags,
            custom_metadata=data.custom_metadata,
        )
        db.add(event)
        await db.flush()
        await db.refresh(event)
        return event

    @staticmethod
    async def create_batch(
        db: AsyncSession, project_id: str, events_data: list[LLMEventCreate]
    ) -> list[LLMEvent]:
        events = [
            LLMEvent(
                project_id=project_id,
                timestamp=data.timestamp.isoformat(),
                model=data.model,
                provider=data.provider,
                prompt_id=data.prompt_id,
                messages=data.messages,
                system_prompt=data.system_prompt,
                response_text=data.response_text,
                finish_reason=data.finish_reason,
                prompt_tokens=data.prompt_tokens,
                completion_tokens=data.completion_tokens,
                total_tokens=data.total_tokens,
                cost_usd=data.cost_usd,
                latency_ms=data.latency_ms,
                user_id=data.user_id,
                session_id=data.session_id,
                feature=data.feature,
                environment=data.environment,
                tags=data.tags,
                custom_metadata=data.custom_metadata,
            )
            for data in events_data
        ]
        db.add_all(events)
        await db.flush()
        for event in events:
            await db.refresh(event)
        return events
