import logging

from fastapi import Depends
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.ext.asyncio import AsyncSession

from .config import settings
from .database import get_db
from .exceptions import NelvraException
from .redis_client import redis_client
from .services.api_key_service import ApiKeyService

logger = logging.getLogger(__name__)

security = HTTPBearer()


async def get_current_project_id(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: AsyncSession = Depends(get_db),
) -> str:
    """Validates the Bearer API key and returns the associated project_id."""
    project_id = await ApiKeyService.validate(db, credentials.credentials)
    if project_id is None:
        raise NelvraException(
            message="The provided API key is invalid or expired",
            code="INVALID_API_KEY",
            status_code=401,
        )
    return project_id


async def rate_limit_events(
    credentials: HTTPAuthorizationCredentials = Depends(security),
) -> None:
    """Enforces per-key rate limit on event ingestion endpoints."""
    # Use first 20 chars of the bearer token as the rate limit key.
    # This is not the full key, so it's safe to use as a Redis key.
    key_prefix = (
        credentials.credentials[:20]
        if len(credentials.credentials) >= 20
        else credentials.credentials
    )
    redis_key = f"rl:events:{key_prefix}"

    try:
        count = await redis_client.incr(redis_key)
        if count == 1:
            await redis_client.expire(redis_key, 60)
        if count > settings.events_rate_limit:
            raise NelvraException(
                message=(
                    f"Rate limit exceeded. Maximum {settings.events_rate_limit} "
                    f"events per minute."
                ),
                code="RATE_LIMIT_EXCEEDED",
                status_code=429,
            )
    except NelvraException:
        raise
    except Exception:
        # Redis failure should not block event ingestion
        logger.warning("Rate limit check failed — Redis unavailable")
