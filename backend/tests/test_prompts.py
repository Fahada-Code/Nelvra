import pytest
from httpx import AsyncClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from api.models.prompt import Prompt
from api.schemas.api_keys import ApiKeyCreate
from api.schemas.projects import ProjectCreate
from api.services.api_key_service import ApiKeyService
from api.services.project_service import ProjectService


async def _project_key(db: AsyncSession) -> tuple[str, str]:
    project = await ProjectService.create(db, ProjectCreate(name="Prompt Test"))
    _, key = await ApiKeyService.create(db, project.id, ApiKeyCreate(name="test"))
    return project.id, key


def _auth(key: str) -> dict:
    return {"Authorization": f"Bearer {key}"}


@pytest.mark.asyncio
async def test_create_prompt(client: AsyncClient, db: AsyncSession):
    _, key = await _project_key(db)
    resp = await client.post(
        "/v1/prompts",
        json={"name": "Support Reply", "content": "You are a support agent. {question}"},
        headers=_auth(key),
    )
    assert resp.status_code == 201
    data = resp.json()
    assert data["name"] == "Support Reply"
    assert data["version"] == 1
    assert data["quality_trend"] == "stable"


@pytest.mark.asyncio
async def test_create_prompt_records_initial_version(client: AsyncClient, db: AsyncSession):
    _, key = await _project_key(db)
    create = await client.post(
        "/v1/prompts", json={"name": "P", "content": "v1 content"}, headers=_auth(key)
    )
    prompt_id = create.json()["id"]

    resp = await client.get(f"/v1/prompts/{prompt_id}/versions", headers=_auth(key))
    assert resp.status_code == 200
    versions = resp.json()
    assert len(versions) == 1
    assert versions[0]["version"] == 1


@pytest.mark.asyncio
async def test_create_prompt_validation(client: AsyncClient, db: AsyncSession):
    _, key = await _project_key(db)
    resp = await client.post("/v1/prompts", json={"name": "", "content": "x"}, headers=_auth(key))
    assert resp.status_code == 422


@pytest.mark.asyncio
async def test_get_nonexistent_prompt(client: AsyncClient, db: AsyncSession):
    _, key = await _project_key(db)
    resp = await client.get("/v1/prompts/00000000-0000-0000-0000-000000000000", headers=_auth(key))
    assert resp.status_code == 404
    assert resp.json()["error"]["code"] == "PROMPT_NOT_FOUND"


@pytest.mark.asyncio
async def test_update_name_does_not_bump_version(client: AsyncClient, db: AsyncSession):
    _, key = await _project_key(db)
    create = await client.post(
        "/v1/prompts", json={"name": "Old", "content": "same"}, headers=_auth(key)
    )
    prompt_id = create.json()["id"]

    resp = await client.put(f"/v1/prompts/{prompt_id}", json={"name": "New"}, headers=_auth(key))
    assert resp.status_code == 200
    assert resp.json()["name"] == "New"
    assert resp.json()["version"] == 1


@pytest.mark.asyncio
async def test_update_content_bumps_version_and_resets_drift(client: AsyncClient, db: AsyncSession):
    _, key = await _project_key(db)
    create = await client.post(
        "/v1/prompts", json={"name": "P", "content": "original"}, headers=_auth(key)
    )
    prompt_id = create.json()["id"]

    resp = await client.put(
        f"/v1/prompts/{prompt_id}",
        json={"content": "rewritten", "change_note": "tweaked wording"},
        headers=_auth(key),
    )
    assert resp.status_code == 200
    body = resp.json()
    assert body["version"] == 2
    assert body["quality_trend"] == "stable"
    assert body["optimization_status"] == "none"

    versions = (await client.get(f"/v1/prompts/{prompt_id}/versions", headers=_auth(key))).json()
    assert len(versions) == 2


@pytest.mark.asyncio
async def test_delete_prompt(client: AsyncClient, db: AsyncSession):
    _, key = await _project_key(db)
    create = await client.post(
        "/v1/prompts", json={"name": "Doomed", "content": "x"}, headers=_auth(key)
    )
    prompt_id = create.json()["id"]

    delete = await client.delete(f"/v1/prompts/{prompt_id}", headers=_auth(key))
    assert delete.status_code == 204

    get = await client.get(f"/v1/prompts/{prompt_id}", headers=_auth(key))
    assert get.status_code == 404


@pytest.mark.asyncio
async def test_deploy_without_optimization_fails(client: AsyncClient, db: AsyncSession):
    _, key = await _project_key(db)
    create = await client.post(
        "/v1/prompts", json={"name": "P", "content": "x"}, headers=_auth(key)
    )
    prompt_id = create.json()["id"]

    resp = await client.post(
        f"/v1/prompts/{prompt_id}/deploy", json={"confirm": True}, headers=_auth(key)
    )
    assert resp.status_code == 400
    assert resp.json()["error"]["code"] == "NO_OPTIMIZATION"


@pytest.mark.asyncio
async def test_deploy_requires_confirmation(client: AsyncClient, db: AsyncSession):
    _, key = await _project_key(db)
    create = await client.post(
        "/v1/prompts", json={"name": "P", "content": "x"}, headers=_auth(key)
    )
    prompt_id = create.json()["id"]

    resp = await client.post(
        f"/v1/prompts/{prompt_id}/deploy", json={"confirm": False}, headers=_auth(key)
    )
    assert resp.status_code == 400
    assert resp.json()["error"]["code"] == "CONFIRMATION_REQUIRED"


@pytest.mark.asyncio
async def test_deploy_optimization_success(client: AsyncClient, db: AsyncSession):
    _, key = await _project_key(db)
    create = await client.post(
        "/v1/prompts", json={"name": "P", "content": "long original prompt"}, headers=_auth(key)
    )
    prompt_id = create.json()["id"]

    # Simulate the optimizer worker having produced a suggestion.
    prompt = (await db.execute(select(Prompt).where(Prompt.id == prompt_id))).scalar_one()
    prompt.optimized_version = "short prompt"
    prompt.optimization_status = "suggested"
    prompt.optimization_savings = 30.0
    await db.flush()

    resp = await client.post(
        f"/v1/prompts/{prompt_id}/deploy", json={"confirm": True}, headers=_auth(key)
    )
    assert resp.status_code == 200
    body = resp.json()
    assert body["content"] == "short prompt"
    assert body["version"] == 2
    assert body["optimization_status"] == "deployed"
    assert body["optimized_version"] is None


@pytest.mark.asyncio
async def test_prompts_are_project_scoped(client: AsyncClient, db: AsyncSession):
    _, key_a = await _project_key(db)
    _, key_b = await _project_key(db)

    create = await client.post(
        "/v1/prompts", json={"name": "Secret", "content": "x"}, headers=_auth(key_a)
    )
    prompt_id = create.json()["id"]

    resp = await client.get(f"/v1/prompts/{prompt_id}", headers=_auth(key_b))
    assert resp.status_code == 404
