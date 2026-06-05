from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from ..exceptions import NelvraException
from ..models.team_member import TeamMember
from ..models.user import User
from ..schemas.teams import TeamMemberInvite, TeamMemberResponse, TeamMemberUpdate


class TeamService:
    @staticmethod
    async def list_members(db: AsyncSession, project_id: str) -> list[TeamMemberResponse]:
        result = await db.execute(
            select(TeamMember, User)
            .join(User, User.id == TeamMember.user_id)
            .where(TeamMember.project_id == project_id, TeamMember.deleted_at.is_(None))
            .order_by(TeamMember.created_at.asc())
        )
        members = []
        for tm, user in result:
            resp = TeamMemberResponse.model_validate(tm)
            resp.github_login = user.github_login
            resp.name = user.name
            resp.avatar_url = user.avatar_url
            members.append(resp)
        return members

    @staticmethod
    async def invite(db: AsyncSession, project_id: str, inviter_id: str, data: TeamMemberInvite) -> TeamMemberResponse:
        user_result = await db.execute(
            select(User).where(User.github_login == data.github_login, User.deleted_at.is_(None))
        )
        user = user_result.scalar_one_or_none()
        if user is None:
            raise NelvraException(
                f"User '{data.github_login}' not found. They must sign in to Nelvra first.",
                "USER_NOT_FOUND",
                404,
            )

        existing = await db.execute(
            select(TeamMember).where(
                TeamMember.project_id == project_id,
                TeamMember.user_id == user.id,
                TeamMember.deleted_at.is_(None),
            )
        )
        if existing.scalar_one_or_none():
            raise NelvraException("User is already a member", "ALREADY_MEMBER", 409)

        tm = TeamMember(
            project_id=project_id,
            user_id=user.id,
            role=data.role,
            invited_by=inviter_id,
            joined_at=datetime.now(timezone.utc),
        )
        db.add(tm)
        await db.flush()
        await db.refresh(tm)

        resp = TeamMemberResponse.model_validate(tm)
        resp.github_login = user.github_login
        resp.name = user.name
        resp.avatar_url = user.avatar_url
        return resp

    @staticmethod
    async def update_role(db: AsyncSession, project_id: str, member_id: str, data: TeamMemberUpdate) -> TeamMemberResponse:
        result = await db.execute(
            select(TeamMember, User)
            .join(User, User.id == TeamMember.user_id)
            .where(TeamMember.id == member_id, TeamMember.project_id == project_id, TeamMember.deleted_at.is_(None))
        )
        row = result.one_or_none()
        if not row:
            raise NelvraException("Team member not found", "MEMBER_NOT_FOUND", 404)
        tm, user = row
        if tm.role == "owner":
            raise NelvraException("Cannot change the owner's role", "CANNOT_CHANGE_OWNER", 403)
        tm.role = data.role
        await db.flush()
        resp = TeamMemberResponse.model_validate(tm)
        resp.github_login = user.github_login
        resp.name = user.name
        resp.avatar_url = user.avatar_url
        return resp

    @staticmethod
    async def remove(db: AsyncSession, project_id: str, member_id: str) -> None:
        result = await db.execute(
            select(TeamMember).where(
                TeamMember.id == member_id, TeamMember.project_id == project_id, TeamMember.deleted_at.is_(None)
            )
        )
        tm = result.scalar_one_or_none()
        if not tm:
            raise NelvraException("Team member not found", "MEMBER_NOT_FOUND", 404)
        if tm.role == "owner":
            raise NelvraException("Cannot remove the project owner", "CANNOT_REMOVE_OWNER", 403)
        tm.deleted_at = datetime.now(timezone.utc)
        await db.flush()
