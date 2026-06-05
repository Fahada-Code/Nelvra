from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from ..database import get_db
from ..dependencies import get_current_project_id
from ..exceptions import NelvraException
from ..schemas.prompts import (
    DeployOptimizationRequest,
    PromptCreate,
    PromptResponse,
    PromptUpdate,
    PromptVersionResponse,
)
from ..services.prompt_service import PromptService
from ..tasks import optimize_prompt_async

router = APIRouter(prefix="/prompts", tags=["prompts"])


@router.get("", response_model=list[PromptResponse])
async def list_prompts(
    project_id: str = Depends(get_current_project_id),
    db: AsyncSession = Depends(get_db),
) -> list[PromptResponse]:
    prompts = await PromptService.list_for_project(db, project_id)
    return [PromptResponse.model_validate(p) for p in prompts]


@router.post("", response_model=PromptResponse, status_code=201)
async def create_prompt(
    data: PromptCreate,
    project_id: str = Depends(get_current_project_id),
    db: AsyncSession = Depends(get_db),
) -> PromptResponse:
    prompt = await PromptService.create(db, project_id, data)
    return PromptResponse.model_validate(prompt)


@router.get("/{prompt_id}", response_model=PromptResponse)
async def get_prompt(
    prompt_id: str,
    project_id: str = Depends(get_current_project_id),
    db: AsyncSession = Depends(get_db),
) -> PromptResponse:
    prompt = await PromptService.get(db, project_id, prompt_id)
    return PromptResponse.model_validate(prompt)


@router.put("/{prompt_id}", response_model=PromptResponse)
async def update_prompt(
    prompt_id: str,
    data: PromptUpdate,
    project_id: str = Depends(get_current_project_id),
    db: AsyncSession = Depends(get_db),
) -> PromptResponse:
    prompt = await PromptService.update(db, project_id, prompt_id, data)
    return PromptResponse.model_validate(prompt)


@router.delete("/{prompt_id}", status_code=204)
async def delete_prompt(
    prompt_id: str,
    project_id: str = Depends(get_current_project_id),
    db: AsyncSession = Depends(get_db),
) -> None:
    await PromptService.delete(db, project_id, prompt_id)


@router.get("/{prompt_id}/versions", response_model=list[PromptVersionResponse])
async def list_versions(
    prompt_id: str,
    project_id: str = Depends(get_current_project_id),
    db: AsyncSession = Depends(get_db),
) -> list[PromptVersionResponse]:
    await PromptService.get(db, project_id, prompt_id)  # ownership check
    versions = await PromptService.get_versions(db, prompt_id)
    return [PromptVersionResponse.model_validate(v) for v in versions]


@router.get("/{prompt_id}/drift", response_model=PromptResponse)
async def get_drift_status(
    prompt_id: str,
    project_id: str = Depends(get_current_project_id),
    db: AsyncSession = Depends(get_db),
) -> PromptResponse:
    prompt = await PromptService.get(db, project_id, prompt_id)
    return PromptResponse.model_validate(prompt)


@router.post("/{prompt_id}/optimize", response_model=PromptResponse)
async def request_optimization(
    prompt_id: str,
    project_id: str = Depends(get_current_project_id),
    db: AsyncSession = Depends(get_db),
) -> PromptResponse:
    prompt = await PromptService.get(db, project_id, prompt_id)
    optimize_prompt_async(prompt_id)
    return PromptResponse.model_validate(prompt)


@router.post("/{prompt_id}/deploy", response_model=PromptResponse)
async def deploy_optimization(
    prompt_id: str,
    data: DeployOptimizationRequest,
    project_id: str = Depends(get_current_project_id),
    db: AsyncSession = Depends(get_db),
) -> PromptResponse:
    if not data.confirm:
        raise NelvraException("confirm must be true to deploy", "CONFIRMATION_REQUIRED", 400)
    prompt = await PromptService.deploy_optimization(db, project_id, prompt_id)
    return PromptResponse.model_validate(prompt)
