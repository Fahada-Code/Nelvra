from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from ..database import get_db
from ..dependencies import get_current_project_id
from ..schemas.teams import TeamMemberInvite, TeamMemberResponse, TeamMemberUpdate
from ..services.team_service import TeamService

router = APIRouter(prefix="/teams", tags=["teams"])


@router.get("/{project_id}/members", response_model=list[TeamMemberResponse])
async def list_members(
    project_id: str,
    _auth_project_id: str = Depends(get_current_project_id),
    db: AsyncSession = Depends(get_db),
) -> list[TeamMemberResponse]:
    return await TeamService.list_members(db, project_id)


@router.post("/{project_id}/members", response_model=TeamMemberResponse, status_code=201)
async def invite_member(
    project_id: str,
    data: TeamMemberInvite,
    auth_project_id: str = Depends(get_current_project_id),
    db: AsyncSession = Depends(get_db),
) -> TeamMemberResponse:
    from sqlalchemy import select

    from ..models.project import Project

    result = await db.execute(select(Project).where(Project.id == project_id))
    project = result.scalar_one_or_none()
    inviter_id = project.owner_user_id if project else None
    return await TeamService.invite(db, project_id, inviter_id or "", data)


@router.put("/{project_id}/members/{member_id}", response_model=TeamMemberResponse)
async def update_member_role(
    project_id: str,
    member_id: str,
    data: TeamMemberUpdate,
    _auth_project_id: str = Depends(get_current_project_id),
    db: AsyncSession = Depends(get_db),
) -> TeamMemberResponse:
    return await TeamService.update_role(db, project_id, member_id, data)


@router.delete("/{project_id}/members/{member_id}", status_code=204)
async def remove_member(
    project_id: str,
    member_id: str,
    _auth_project_id: str = Depends(get_current_project_id),
    db: AsyncSession = Depends(get_db),
) -> None:
    await TeamService.remove(db, project_id, member_id)
