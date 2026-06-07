from datetime import UTC, datetime

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from ..exceptions import NelvraException
from ..models.prompt import Prompt, PromptVersion
from ..schemas.prompts import PromptCreate, PromptUpdate


class PromptService:
    @staticmethod
    async def create(db: AsyncSession, project_id: str, data: PromptCreate) -> Prompt:
        prompt = Prompt(
            project_id=project_id,
            name=data.name,
            content=data.content,
            variables=data.variables,
        )
        db.add(prompt)
        await db.flush()
        # Create initial version record
        v = PromptVersion(
            prompt_id=prompt.id, version=1, content=data.content, change_note="Initial version"
        )
        db.add(v)
        await db.flush()
        await db.refresh(prompt)
        return prompt

    @staticmethod
    async def list_for_project(db: AsyncSession, project_id: str) -> list[Prompt]:
        result = await db.execute(
            select(Prompt)
            .where(Prompt.project_id == project_id, Prompt.deleted_at.is_(None))
            .order_by(Prompt.created_at.desc())
        )
        return list(result.scalars())

    @staticmethod
    async def get(db: AsyncSession, project_id: str, prompt_id: str) -> Prompt:
        result = await db.execute(
            select(Prompt).where(
                Prompt.id == prompt_id, Prompt.project_id == project_id, Prompt.deleted_at.is_(None)
            )
        )
        prompt = result.scalar_one_or_none()
        if not prompt:
            raise NelvraException("Prompt not found", "PROMPT_NOT_FOUND", 404)
        return prompt

    @staticmethod
    async def update(
        db: AsyncSession, project_id: str, prompt_id: str, data: PromptUpdate
    ) -> Prompt:
        prompt = await PromptService.get(db, project_id, prompt_id)
        content_changed = data.content is not None and data.content != prompt.content

        if data.name is not None:
            prompt.name = data.name
        if data.content is not None:
            prompt.content = data.content
        if data.variables is not None:
            prompt.variables = data.variables

        if content_changed:
            prompt.version += 1
            v = PromptVersion(
                prompt_id=prompt.id,
                version=prompt.version,
                content=prompt.content,
                change_note=data.change_note,
            )
            db.add(v)
            # Reset drift/optimization state on content change
            prompt.drift_detected_at = None
            prompt.drift_explanation = None
            prompt.quality_trend = "stable"
            prompt.optimization_status = "none"
            prompt.optimized_version = None
            prompt.optimization_savings = None

        await db.flush()
        await db.refresh(prompt)
        return prompt

    @staticmethod
    async def delete(db: AsyncSession, project_id: str, prompt_id: str) -> None:
        prompt = await PromptService.get(db, project_id, prompt_id)
        prompt.deleted_at = datetime.now(UTC)
        await db.flush()

    @staticmethod
    async def get_versions(db: AsyncSession, prompt_id: str) -> list[PromptVersion]:
        result = await db.execute(
            select(PromptVersion)
            .where(PromptVersion.prompt_id == prompt_id)
            .order_by(PromptVersion.version.desc())
        )
        return list(result.scalars())

    @staticmethod
    async def deploy_optimization(db: AsyncSession, project_id: str, prompt_id: str) -> Prompt:
        """Replaces current content with the optimized version and resets optimization state."""
        prompt = await PromptService.get(db, project_id, prompt_id)
        if not prompt.optimized_version:
            raise NelvraException("No optimized version available", "NO_OPTIMIZATION", 400)

        prompt.content = prompt.optimized_version
        prompt.version += 1
        prompt.optimization_status = "deployed"
        prompt.optimized_version = None

        savings = prompt.optimization_savings or 0
        v = PromptVersion(
            prompt_id=prompt.id,
            version=prompt.version,
            content=prompt.content,
            change_note=f"Deployed optimized version (est. {savings:.1f}% token reduction)",
        )
        db.add(v)
        await db.flush()
        await db.refresh(prompt)
        return prompt
