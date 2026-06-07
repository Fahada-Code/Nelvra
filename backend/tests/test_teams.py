import uuid

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from api.models.team_member import TeamMember
from api.models.user import User
from api.schemas.api_keys import ApiKeyCreate
from api.schemas.projects import ProjectCreate
from api.services.api_key_service import ApiKeyService
from api.services.project_service import ProjectService


async def _project_key(db: AsyncSession) -> tuple[str, str]:
    project = await ProjectService.create(db, ProjectCreate(name="Team Test"))
    _, key = await ApiKeyService.create(db, project.id, ApiKeyCreate(name="test"))
    return project.id, key


async def _make_user(db: AsyncSession, login: str) -> User:
    user = User(github_id=str(uuid.uuid4()), github_login=login, name=login.title())
    db.add(user)
    await db.flush()
    await db.refresh(user)
    return user


def _auth(key: str) -> dict:
    return {"Authorization": f"Bearer {key}"}


@pytest.mark.asyncio
async def test_invite_member(client: AsyncClient, db: AsyncSession):
    project_id, key = await _project_key(db)
    await _make_user(db, "alice")

    resp = await client.post(
        f"/v1/teams/{project_id}/members",
        json={"github_login": "alice", "role": "member"},
        headers=_auth(key),
    )
    assert resp.status_code == 201
    data = resp.json()
    assert data["github_login"] == "alice"
    assert data["role"] == "member"


@pytest.mark.asyncio
async def test_invite_unknown_user(client: AsyncClient, db: AsyncSession):
    project_id, key = await _project_key(db)
    resp = await client.post(
        f"/v1/teams/{project_id}/members",
        json={"github_login": "ghost"},
        headers=_auth(key),
    )
    assert resp.status_code == 404
    assert resp.json()["error"]["code"] == "USER_NOT_FOUND"


@pytest.mark.asyncio
async def test_invite_duplicate_member(client: AsyncClient, db: AsyncSession):
    project_id, key = await _project_key(db)
    await _make_user(db, "bob")

    first = await client.post(
        f"/v1/teams/{project_id}/members", json={"github_login": "bob"}, headers=_auth(key)
    )
    assert first.status_code == 201

    second = await client.post(
        f"/v1/teams/{project_id}/members", json={"github_login": "bob"}, headers=_auth(key)
    )
    assert second.status_code == 409
    assert second.json()["error"]["code"] == "ALREADY_MEMBER"


@pytest.mark.asyncio
async def test_update_member_role(client: AsyncClient, db: AsyncSession):
    project_id, key = await _project_key(db)
    await _make_user(db, "carol")
    invited = await client.post(
        f"/v1/teams/{project_id}/members", json={"github_login": "carol"}, headers=_auth(key)
    )
    member_id = invited.json()["id"]

    resp = await client.put(
        f"/v1/teams/{project_id}/members/{member_id}",
        json={"role": "admin"},
        headers=_auth(key),
    )
    assert resp.status_code == 200
    assert resp.json()["role"] == "admin"


@pytest.mark.asyncio
async def test_cannot_change_owner_role(client: AsyncClient, db: AsyncSession):
    project_id, key = await _project_key(db)
    owner = await _make_user(db, "owner_user")
    tm = TeamMember(project_id=project_id, user_id=owner.id, role="owner")
    db.add(tm)
    await db.flush()
    await db.refresh(tm)

    resp = await client.put(
        f"/v1/teams/{project_id}/members/{tm.id}",
        json={"role": "member"},
        headers=_auth(key),
    )
    assert resp.status_code == 403
    assert resp.json()["error"]["code"] == "CANNOT_CHANGE_OWNER"


@pytest.mark.asyncio
async def test_cannot_remove_owner(client: AsyncClient, db: AsyncSession):
    project_id, key = await _project_key(db)
    owner = await _make_user(db, "owner_user2")
    tm = TeamMember(project_id=project_id, user_id=owner.id, role="owner")
    db.add(tm)
    await db.flush()
    await db.refresh(tm)

    resp = await client.delete(f"/v1/teams/{project_id}/members/{tm.id}", headers=_auth(key))
    assert resp.status_code == 403
    assert resp.json()["error"]["code"] == "CANNOT_REMOVE_OWNER"


@pytest.mark.asyncio
async def test_remove_member(client: AsyncClient, db: AsyncSession):
    project_id, key = await _project_key(db)
    await _make_user(db, "dave")
    invited = await client.post(
        f"/v1/teams/{project_id}/members", json={"github_login": "dave"}, headers=_auth(key)
    )
    member_id = invited.json()["id"]

    resp = await client.delete(f"/v1/teams/{project_id}/members/{member_id}", headers=_auth(key))
    assert resp.status_code == 204

    members = await client.get(f"/v1/teams/{project_id}/members", headers=_auth(key))
    assert all(m["id"] != member_id for m in members.json())
