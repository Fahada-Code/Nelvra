import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from api.schemas.api_keys import ApiKeyCreate
from api.services.api_key_service import ApiKeyService


@pytest.mark.asyncio
async def test_generate_api_key_format(db: AsyncSession):
    from api.schemas.projects import ProjectCreate
    from api.services.project_service import ProjectService

    project = await ProjectService.create(db, ProjectCreate(name="Format Test Project"))
    api_key, plaintext = await ApiKeyService.create(db, project.id, ApiKeyCreate(name="test key"))

    assert plaintext.startswith("nvl_live_")
    assert len(plaintext) == 9 + 32  # "nvl_live_" + 32 hex chars
    assert api_key.key_prefix == plaintext[9:17]


@pytest.mark.asyncio
async def test_validate_valid_key(db: AsyncSession):
    # Create a real project first
    from api.schemas.projects import ProjectCreate
    from api.services.project_service import ProjectService

    project = await ProjectService.create(db, ProjectCreate(name="Key Test Project"))

    api_key, plaintext = await ApiKeyService.create(db, project.id, ApiKeyCreate(name="test key"))

    project_id = await ApiKeyService.validate(db, plaintext)
    assert project_id == project.id


@pytest.mark.asyncio
async def test_validate_invalid_key(db: AsyncSession):
    result = await ApiKeyService.validate(db, "nvl_live_" + "0" * 32)
    assert result is None


@pytest.mark.asyncio
async def test_validate_malformed_key(db: AsyncSession):
    result = await ApiKeyService.validate(db, "not-a-valid-key")
    assert result is None


@pytest.mark.asyncio
async def test_revoked_key_is_invalid(db: AsyncSession):
    from api.schemas.projects import ProjectCreate
    from api.services.project_service import ProjectService

    project = await ProjectService.create(db, ProjectCreate(name="Revoke Test"))
    api_key, plaintext = await ApiKeyService.create(db, project.id, ApiKeyCreate(name="revoke me"))

    await ApiKeyService.revoke(db, project.id, api_key.id)

    result = await ApiKeyService.validate(db, plaintext)
    assert result is None


@pytest.mark.asyncio
async def test_create_api_key_via_endpoint(client: AsyncClient):
    create_resp = await client.post("/v1/projects", json={"name": "Key Endpoint Test"})
    project_id = create_resp.json()["id"]

    key_resp = await client.post(f"/v1/projects/{project_id}/keys", json={"name": "Production Key"})
    assert key_resp.status_code == 201
    data = key_resp.json()
    assert "key" in data
    assert data["key"].startswith("nvl_live_")
    assert "key_prefix" in data
    assert "key" not in [k for k in data if k != "key"]  # key only returned once


@pytest.mark.asyncio
async def test_list_api_keys(client: AsyncClient):
    create_resp = await client.post("/v1/projects", json={"name": "List Keys Test"})
    project_id = create_resp.json()["id"]

    await client.post(f"/v1/projects/{project_id}/keys", json={"name": "Key 1"})
    await client.post(f"/v1/projects/{project_id}/keys", json={"name": "Key 2"})

    list_resp = await client.get(f"/v1/projects/{project_id}/keys")
    assert list_resp.status_code == 200
    keys = list_resp.json()
    assert len(keys) == 2
    # Plaintext key is NOT returned in list
    for k in keys:
        assert "key" not in k


@pytest.mark.asyncio
async def test_revoke_api_key_via_endpoint(client: AsyncClient):
    create_resp = await client.post("/v1/projects", json={"name": "Revoke Endpoint Test"})
    project_id = create_resp.json()["id"]

    key_resp = await client.post(f"/v1/projects/{project_id}/keys", json={"name": "To Revoke"})
    key_id = key_resp.json()["id"]

    revoke_resp = await client.delete(f"/v1/projects/{project_id}/keys/{key_id}")
    assert revoke_resp.status_code == 204

    list_resp = await client.get(f"/v1/projects/{project_id}/keys")
    assert len(list_resp.json()) == 0
