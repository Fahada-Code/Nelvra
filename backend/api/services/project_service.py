from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from ..exceptions import NelvraException
from ..models.project import Project
from ..schemas.projects import ProjectCreate, ProjectUpdate


class ProjectService:
    """Business logic for project management."""

    @staticmethod
    async def create(db: AsyncSession, data: ProjectCreate) -> Project:
        project = Project(name=data.name, description=data.description)
        db.add(project)
        await db.flush()
        await db.refresh(project)
        return project

    @staticmethod
    async def get_by_id(db: AsyncSession, project_id: str) -> Project:
        result = await db.execute(
            select(Project).where(Project.id == project_id, Project.deleted_at.is_(None))
        )
        project = result.scalar_one_or_none()
        if project is None:
            raise NelvraException(
                message="Project not found",
                code="PROJECT_NOT_FOUND",
                status_code=404,
            )
        return project

    @staticmethod
    async def list_all(db: AsyncSession) -> list[Project]:
        result = await db.execute(
            select(Project).where(Project.deleted_at.is_(None)).order_by(Project.created_at.desc())
        )
        return list(result.scalars().all())

    @staticmethod
    async def update(db: AsyncSession, project_id: str, data: ProjectUpdate) -> Project:
        project = await ProjectService.get_by_id(db, project_id)
        if data.name is not None:
            project.name = data.name
        if data.description is not None:
            project.description = data.description
        await db.flush()
        await db.refresh(project)
        return project
