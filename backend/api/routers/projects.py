from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from ..database import get_db
from ..dependencies import get_current_project_id
from ..schemas.api_keys import ApiKeyCreate, ApiKeyCreatedResponse, ApiKeyResponse
from ..schemas.projects import ProjectCreate, ProjectResponse, ProjectUpdate
from ..services.api_key_service import ApiKeyService
from ..services.project_service import ProjectService

router = APIRouter(prefix="/projects", tags=["projects"])


@router.post("", response_model=ProjectResponse, status_code=201)
async def create_project(
    data: ProjectCreate,
    db: AsyncSession = Depends(get_db),
) -> ProjectResponse:
    project = await ProjectService.create(db, data)
    return ProjectResponse.model_validate(project)


@router.get("", response_model=list[ProjectResponse])
async def list_projects(
    db: AsyncSession = Depends(get_db),
) -> list[ProjectResponse]:
    projects = await ProjectService.list_all(db)
    return [ProjectResponse.model_validate(p) for p in projects]


@router.get("/{project_id}", response_model=ProjectResponse)
async def get_project(
    project_id: str,
    db: AsyncSession = Depends(get_db),
) -> ProjectResponse:
    project = await ProjectService.get_by_id(db, project_id)
    return ProjectResponse.model_validate(project)


@router.put("/{project_id}", response_model=ProjectResponse)
async def update_project(
    project_id: str,
    data: ProjectUpdate,
    db: AsyncSession = Depends(get_db),
) -> ProjectResponse:
    project = await ProjectService.update(db, project_id, data)
    return ProjectResponse.model_validate(project)


@router.post("/{project_id}/keys", response_model=ApiKeyCreatedResponse, status_code=201)
async def create_api_key(
    project_id: str,
    data: ApiKeyCreate,
    db: AsyncSession = Depends(get_db),
) -> ApiKeyCreatedResponse:
    # Verify project exists before creating a key for it
    await ProjectService.get_by_id(db, project_id)
    api_key, plaintext_key = await ApiKeyService.create(db, project_id, data)
    base = ApiKeyResponse.model_validate(api_key)
    return ApiKeyCreatedResponse(**base.model_dump(), key=plaintext_key)


@router.get("/{project_id}/keys", response_model=list[ApiKeyResponse])
async def list_api_keys(
    project_id: str,
    db: AsyncSession = Depends(get_db),
) -> list[ApiKeyResponse]:
    await ProjectService.get_by_id(db, project_id)
    keys = await ApiKeyService.list_for_project(db, project_id)
    return [ApiKeyResponse.model_validate(k) for k in keys]


@router.delete("/{project_id}/keys/{key_id}", status_code=204)
async def revoke_api_key(
    project_id: str,
    key_id: str,
    db: AsyncSession = Depends(get_db),
) -> None:
    await ApiKeyService.revoke(db, project_id, key_id)
