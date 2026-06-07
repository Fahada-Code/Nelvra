import hashlib
import secrets
from datetime import UTC, datetime

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from ..exceptions import NelvraException
from ..models.api_key import ApiKey
from ..schemas.api_keys import ApiKeyCreate


def _generate_raw_key() -> str:
    return secrets.token_hex(16)  # 32 hex chars


def _build_full_key(raw: str) -> str:
    return f"nvl_live_{raw}"


def _hash_key(full_key: str) -> str:
    return hashlib.sha256(full_key.encode()).hexdigest()


def _extract_prefix(full_key: str) -> str | None:
    if not full_key.startswith("nvl_live_"):
        return None
    return full_key[9:17]  # 8 chars — enough for indexed lookup


class ApiKeyService:
    """Business logic for API key lifecycle."""

    @staticmethod
    async def create(db: AsyncSession, project_id: str, data: ApiKeyCreate) -> tuple[ApiKey, str]:
        """Returns the ApiKey model and the plaintext key (shown only once)."""
        raw = _generate_raw_key()
        full_key = _build_full_key(raw)
        prefix = raw[:8]
        key_hash = _hash_key(full_key)

        api_key = ApiKey(
            project_id=project_id,
            name=data.name,
            key_hash=key_hash,
            key_prefix=prefix,
        )
        db.add(api_key)
        await db.flush()
        await db.refresh(api_key)
        return api_key, full_key

    @staticmethod
    async def validate(db: AsyncSession, full_key: str) -> str | None:
        """Returns project_id if the key is valid, None otherwise."""
        prefix = _extract_prefix(full_key)
        if prefix is None:
            return None

        key_hash = _hash_key(full_key)

        result = await db.execute(
            select(ApiKey).where(
                ApiKey.key_prefix == prefix,
                ApiKey.key_hash == key_hash,
                ApiKey.deleted_at.is_(None),
            )
        )
        api_key = result.scalar_one_or_none()
        if api_key is None:
            return None

        # Fire-and-forget last_used_at update — best effort, non-critical
        await db.execute(
            update(ApiKey).where(ApiKey.id == api_key.id).values(last_used_at=datetime.now(UTC))
        )

        return api_key.project_id

    @staticmethod
    async def list_for_project(db: AsyncSession, project_id: str) -> list[ApiKey]:
        result = await db.execute(
            select(ApiKey)
            .where(ApiKey.project_id == project_id, ApiKey.deleted_at.is_(None))
            .order_by(ApiKey.created_at.desc())
        )
        return list(result.scalars().all())

    @staticmethod
    async def revoke(db: AsyncSession, project_id: str, key_id: str) -> None:
        result = await db.execute(
            select(ApiKey).where(
                ApiKey.id == key_id,
                ApiKey.project_id == project_id,
                ApiKey.deleted_at.is_(None),
            )
        )
        api_key = result.scalar_one_or_none()
        if api_key is None:
            raise NelvraException(
                message="API key not found",
                code="API_KEY_NOT_FOUND",
                status_code=404,
            )
        api_key.deleted_at = datetime.now(UTC)
        await db.flush()
