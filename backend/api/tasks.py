"""
Thin wrappers that dispatch background Celery tasks.
Using a separate module avoids circular imports between api/ and workers/.
All functions are safe to call even when Celery is not running — they log and skip.
"""
import logging

logger = logging.getLogger(__name__)


def evaluate_quality_async(event_id: str) -> None:
    try:
        from workers.quality_evaluator import evaluate_quality
        evaluate_quality.delay(event_id)
    except Exception:
        logger.debug("Celery unavailable — quality evaluation skipped for event %s", event_id)


def optimize_prompt_async(prompt_id: str) -> None:
    try:
        from workers.prompt_optimizer import optimize_prompt
        optimize_prompt.delay(prompt_id)
    except Exception:
        logger.debug("Celery unavailable — prompt optimization skipped for prompt %s", prompt_id)
