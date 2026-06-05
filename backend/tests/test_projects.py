import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_create_project(client: AsyncClient):
    resp = await client.post("/v1/projects", json={"name": "My AI App"})
    assert resp.status_code == 201
    data = resp.json()
    assert data["name"] == "My AI App"
    assert "id" in data
    assert "created_at" in data


@pytest.mark.asyncio
async def test_create_project_with_description(client: AsyncClient):
    resp = await client.post(
        "/v1/projects",
        json={"name": "My AI App", "description": "Production LLM app"},
    )
    assert resp.status_code == 201
    assert resp.json()["description"] == "Production LLM app"


@pytest.mark.asyncio
async def test_create_project_name_required(client: AsyncClient):
    resp = await client.post("/v1/projects", json={"description": "no name"})
    assert resp.status_code == 422


@pytest.mark.asyncio
async def test_create_project_name_too_long(client: AsyncClient):
    resp = await client.post("/v1/projects", json={"name": "x" * 256})
    assert resp.status_code == 422


@pytest.mark.asyncio
async def test_get_project(client: AsyncClient):
    create_resp = await client.post("/v1/projects", json={"name": "Get Me"})
    project_id = create_resp.json()["id"]

    get_resp = await client.get(f"/v1/projects/{project_id}")
    assert get_resp.status_code == 200
    assert get_resp.json()["id"] == project_id


@pytest.mark.asyncio
async def test_get_nonexistent_project(client: AsyncClient):
    resp = await client.get("/v1/projects/00000000-0000-0000-0000-000000000000")
    assert resp.status_code == 404
    assert resp.json()["error"]["code"] == "PROJECT_NOT_FOUND"


@pytest.mark.asyncio
async def test_list_projects(client: AsyncClient):
    await client.post("/v1/projects", json={"name": "Project Alpha"})
    await client.post("/v1/projects", json={"name": "Project Beta"})

    resp = await client.get("/v1/projects")
    assert resp.status_code == 200
    assert len(resp.json()) >= 2


@pytest.mark.asyncio
async def test_update_project(client: AsyncClient):
    create_resp = await client.post("/v1/projects", json={"name": "Original"})
    project_id = create_resp.json()["id"]

    update_resp = await client.put(
        f"/v1/projects/{project_id}", json={"name": "Updated"}
    )
    assert update_resp.status_code == 200
    assert update_resp.json()["name"] == "Updated"
