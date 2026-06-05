"""
Prompt Optimizer — Celery task.

Generates an optimized version of an underperforming prompt using Claude.
Triggered manually (via API) or automatically when a prompt's quality score
drops below the optimization threshold.
"""
import asyncio
import logging

from workers.celery_app import app

logger = logging.getLogger(__name__)

_OPTIMIZATION_PROMPT = """\
You are an expert prompt engineer. The following AI prompt is underperforming.

<prompt_name>{name}</prompt_name>

<current_prompt>
{content}
</current_prompt>

<performance_data>
- Average quality score: {quality_score}/1.0
- Average token count: {avg_tokens} tokens per call
- Estimated monthly cost at current volume: ${monthly_cost:.2f}
- Request count (last 30 days): {request_count}
</performance_data>

Rewrite this prompt to:
1. Achieve the same task with fewer tokens (target 20-40% reduction)
2. Reduce ambiguity and improve response consistency
3. Increase quality score

CRITICAL: Return ONLY the rewritten prompt text. No explanations, no preamble, no markdown fences.
The output will be deployed directly as the new prompt."""


@app.task(name="workers.prompt_optimizer.optimize_prompt", bind=True, max_retries=1)
def optimize_prompt(self, prompt_id: str) -> None:
    try:
        asyncio.run(_run(prompt_id))
    except Exception as exc:
        logger.warning("Prompt optimization failed for %s: %s", prompt_id, exc)
        raise self.retry(exc=exc, countdown=120)


async def _run(prompt_id: str) -> None:
    from api.config import settings
    if not settings.anthropic_api_key:
        logger.warning("ANTHROPIC_API_KEY not set — prompt optimization skipped")
        return

    from api.database import AsyncSessionLocal
    from api.models.prompt import Prompt
    from sqlalchemy import select

    async with AsyncSessionLocal() as db:
        result = await db.execute(select(Prompt).where(Prompt.id == prompt_id, Prompt.deleted_at.is_(None)))
        prompt = result.scalar_one_or_none()
        if prompt is None:
            return

        prompt.optimization_status = "testing"
        await db.flush()

        optimized = await _generate_optimized(settings.anthropic_api_key, prompt)
        if optimized is None:
            prompt.optimization_status = "none"
            await db.commit()
            return

        savings = _estimate_savings(prompt.content, optimized, prompt.avg_tokens or 0)

        prompt.optimized_version = optimized
        prompt.optimization_status = "suggested"
        prompt.optimization_savings = savings
        await db.commit()
        logger.info("Optimization suggested for prompt %s (est. %.1f%% token reduction)", prompt_id, savings)


async def _generate_optimized(api_key: str, prompt) -> str | None:
    import anthropic

    monthly_cost = (
        (prompt.avg_cost_usd or 0) * (prompt.request_count or 0) * 30
    )

    client = anthropic.AsyncAnthropic(api_key=api_key)
    try:
        msg = await client.messages.create(
            model="claude-sonnet-4-6",
            max_tokens=2000,
            messages=[{
                "role": "user",
                "content": _OPTIMIZATION_PROMPT.format(
                    name=prompt.name,
                    content=prompt.content,
                    quality_score=f"{prompt.avg_quality_score:.2f}" if prompt.avg_quality_score else "unknown",
                    avg_tokens=prompt.avg_tokens or "unknown",
                    monthly_cost=monthly_cost,
                    request_count=prompt.request_count,
                ),
            }],
        )
        return msg.content[0].text.strip()
    except Exception as exc:
        logger.warning("Optimization API call failed: %s", exc)
        return None


def _estimate_savings(original: str, optimized: str, avg_tokens: int) -> float:
    """Rough token savings estimate based on character length ratio."""
    if not original or not optimized or avg_tokens == 0:
        return 0.0
    ratio = len(optimized) / max(len(original), 1)
    prompt_token_fraction = 0.4  # assume prompt is ~40% of total tokens
    savings_pct = (1 - ratio) * prompt_token_fraction * 100
    return round(max(0.0, min(savings_pct, 80.0)), 1)
