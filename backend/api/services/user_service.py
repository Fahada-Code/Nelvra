from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from ..models.project import Project
from ..models.user import User
from ..schemas.api_keys import ApiKeyCreate
from ..schemas.auth import GitHubRegisterRequest
from ..schemas.projects import ProjectCreate
from .api_key_service import ApiKeyService
from .project_service import ProjectService


class UserService:
    """Handles GitHub-authenticated user registration and project bootstrapping."""

    @staticmethod
    async def register_or_login(
        db: AsyncSession, data: GitHubRegisterRequest
    ) -> tuple[User, Project, str | None]:
        """
        Returns (user, default_project, plaintext_api_key).
        On first login: creates user + project + API key, returns plaintext key.
        On subsequent logins: returns existing user + project, plaintext_api_key=None.
        The caller is responsible for telling the user they need to create a new key
        if they've lost their original one.
        """
        result = await db.execute(
            select(User).where(User.github_id == data.github_id, User.deleted_at.is_(None))
        )
        user = result.scalar_one_or_none()

        if user is None:
            user = User(
                github_id=data.github_id,
                github_login=data.github_login,
                email=data.email,
                name=data.name,
                avatar_url=data.avatar_url,
            )
            db.add(user)
            await db.flush()
            await db.refresh(user)

            # Create a default project for new users
            project = await ProjectService.create(
                db,
                ProjectCreate(name=f"{data.github_login}'s Project"),
            )
            # Link project to owner
            project.owner_user_id = user.id
            await db.flush()

            # Auto-generate first API key
            _, plaintext_key = await ApiKeyService.create(
                db, project.id, ApiKeyCreate(name="Default Key")
            )
            return user, project, plaintext_key

        # Update profile fields on subsequent logins
        user.github_login = data.github_login
        if data.email:
            user.email = data.email
        if data.name:
            user.name = data.name
        if data.avatar_url:
            user.avatar_url = data.avatar_url
        await db.flush()

        # Return the user's first active project
        proj_result = await db.execute(
            select(Project)
            .where(Project.owner_user_id == user.id, Project.deleted_at.is_(None))
            .order_by(Project.created_at.asc())
            .limit(1)
        )
        project = proj_result.scalar_one_or_none()

        if project is None:
            project = await ProjectService.create(
                db, ProjectCreate(name=f"{data.github_login}'s Project")
            )
            project.owner_user_id = user.id
            await db.flush()

        return user, project, None

    @staticmethod
    async def list_projects(db: AsyncSession, user_id: str) -> list[Project]:
        result = await db.execute(
            select(Project)
            .where(Project.owner_user_id == user_id, Project.deleted_at.is_(None))
            .order_by(Project.created_at.asc())
        )
        return list(result.scalars().all())
