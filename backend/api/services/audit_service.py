from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from ..models.audit_log import AuditLog


class AuditService:
    @staticmethod
    async def log(
        db: AsyncSession,
        action: str,
        resource_type: str,
        resource_id: str | None = None,
        project_id: str | None = None,
        user_id: str | None = None,
        details: dict | None = None,
        ip_address: str | None = None,
    ) -> None:
        entry = AuditLog(
            project_id=project_id,
            user_id=user_id,
            action=action,
            resource_type=resource_type,
            resource_id=resource_id,
            details=details or {},
            ip_address=ip_address,
        )
        db.add(entry)

    @staticmethod
    async def list_for_project(
        db: AsyncSession, project_id: str, limit: int = 100
    ) -> list[AuditLog]:
        result = await db.execute(
            select(AuditLog)
            .where(AuditLog.project_id == project_id)
            .order_by(AuditLog.created_at.desc())
            .limit(limit)
        )
        return list(result.scalars())
