"""
Quality Evaluator — Celery task.

Scores each LLM event using Claude as a judge (LLM-as-judge pattern).
Called asynchronously after every event is ingested.

Requires ANTHROPIC_API_KEY. If not set, silently skips scoring.
"""
import asyncio
import json
import logging

from workers.celery_app import app

logger = logging.getLogger(__name__)

SCORING_PROMPT = """\
You are an impartial evaluator assessing the quality of an AI assistant response.

<conversation>
{conversation}
</conversation>

<response>
{response}
</response>

Score this response on a scale from 0.0 to 1.0 based on:
- Relevance: Does it address what was asked?
- Accuracy: Is the information correct and precise?
- Completeness: Is the answer sufficiently thorough?
- Clarity: Is it well-written and easy to understand?

Return ONLY a JSON object with no other text:
{{"score": 0.X, "flags": ["flag1"]}}

Valid flags: "off_topic", "incomplete", "unclear", "potentially_incorrect", "refusal"
If none apply, return an empty flags list."""


@app.task(name="workers.quality_evaluator.evaluate_quality", bind=True, max_retries=2)
def evaluate_quality(self, event_id: str) -> None:
    try:
        asyncio.run(_run(event_id))
    except Exception as exc:
        logger.warning("Quality evaluation failed for event %s: %s", event_id, type(exc).__name__)
        raise self.retry(exc=exc, countdown=60)


async def _run(event_id: str) -> None:
    from api.config import settings
    if not settings.anthropic_api_key or not settings.quality_scoring_enabled:
        return

    from api.database import AsyncSessionLocal
    from api.models.llm_event import LLMEvent
    from sqlalchemy import select

    async with AsyncSessionLocal() as db:
        result = await db.execute(
            select(LLMEvent).where(LLMEvent.id == event_id, LLMEvent.deleted_at.is_(None))
        )
        event = result.scalar_one_or_none()
        if event is None or event.quality_score is not None:
            return

        conversation_text = _format_conversation(event.messages, event.system_prompt)
        score, flags = await _score(
            settings.anthropic_api_key,
            conversation_text,
            event.response_text,
            event.model,
        )
        if score is not None:
            event.quality_score = score
            event.quality_flags = flags
            await db.commit()


def _format_conversation(messages: list, system_prompt: str | None) -> str:
    parts = []
    if system_prompt:
        parts.append(f"[System]: {system_prompt[:500]}")
    for msg in (messages or [])[-5:]:  # last 5 messages for context
        role = msg.get("role", "user")
        content = msg.get("content", "")
        if isinstance(content, list):
            content = " ".join(b.get("text", "") for b in content if isinstance(b, dict))
        parts.append(f"[{role.capitalize()}]: {str(content)[:500]}")
    return "\n".join(parts)


async def _score(api_key: str, conversation: str, response: str, model: str) -> tuple[float | None, list[str]]:
    import anthropic

    client = anthropic.AsyncAnthropic(api_key=api_key)
    try:
        msg = await client.messages.create(
            model="claude-haiku-4-5-20251001",
            max_tokens=100,
            messages=[{
                "role": "user",
                "content": SCORING_PROMPT.format(
                    conversation=conversation[:1000],
                    response=response[:1000],
                ),
            }],
        )
        raw = msg.content[0].text.strip()
        data = json.loads(raw)
        score = float(data.get("score", 0))
        score = max(0.0, min(1.0, score))
        flags = [str(f) for f in data.get("flags", [])]
        return score, flags
    except Exception as exc:
        logger.debug("Scoring API call failed for model %s: %s", model, exc)
        return None, []
