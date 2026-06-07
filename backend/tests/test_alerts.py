import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from api.schemas.api_keys import ApiKeyCreate
from api.schemas.projects import ProjectCreate
from api.services.api_key_service import ApiKeyService
from api.services.project_service import ProjectService


async def _project_key(db: AsyncSession) -> tuple[str, str]:
    project = await ProjectService.create(db, ProjectCreate(name="Alert Test"))
    _, key = await ApiKeyService.create(db, project.id, ApiKeyCreate(name="test"))
    return project.id, key


def _auth(key: str) -> dict:
    return {"Authorization": f"Bearer {key}"}


def _cost_alert() -> dict:
    return {"name": "Cost spike", "metric": "cost_usd", "operator": "gt", "threshold": 10.0}


@pytest.mark.asyncio
async def test_create_alert(client: AsyncClient, db: AsyncSession):
    _, key = await _project_key(db)
    resp = await client.post("/v1/alerts", json=_cost_alert(), headers=_auth(key))
    assert resp.status_code == 201
    data = resp.json()
    assert data["metric"] == "cost_usd"
    assert data["enabled"] is True
    assert data["window_minutes"] == 60


@pytest.mark.asyncio
async def test_create_alert_invalid_metric(client: AsyncClient, db: AsyncSession):
    _, key = await _project_key(db)
    payload = _cost_alert()
    payload["metric"] = "made_up"
    resp = await client.post("/v1/alerts", json=payload, headers=_auth(key))
    assert resp.status_code == 422


@pytest.mark.asyncio
async def test_create_alert_slack_requires_webhook(client: AsyncClient, db: AsyncSession):
    _, key = await _project_key(db)
    payload = _cost_alert()
    payload["notify_slack"] = True  # but no slack_webhook_url
    resp = await client.post("/v1/alerts", json=payload, headers=_auth(key))
    assert resp.status_code == 422


@pytest.mark.asyncio
async def test_list_alerts(client: AsyncClient, db: AsyncSession):
    _, key = await _project_key(db)
    await client.post("/v1/alerts", json=_cost_alert(), headers=_auth(key))
    resp = await client.get("/v1/alerts", headers=_auth(key))
    assert resp.status_code == 200
    assert len(resp.json()) == 1


@pytest.mark.asyncio
async def test_update_alert(client: AsyncClient, db: AsyncSession):
    _, key = await _project_key(db)
    created = await client.post("/v1/alerts", json=_cost_alert(), headers=_auth(key))
    alert_id = created.json()["id"]

    resp = await client.put(
        f"/v1/alerts/{alert_id}",
        json={"threshold": 99.0, "enabled": False},
        headers=_auth(key),
    )
    assert resp.status_code == 200
    body = resp.json()
    assert body["threshold"] == 99.0
    assert body["enabled"] is False


@pytest.mark.asyncio
async def test_update_nonexistent_alert(client: AsyncClient, db: AsyncSession):
    _, key = await _project_key(db)
    resp = await client.put(
        "/v1/alerts/00000000-0000-0000-0000-000000000000",
        json={"threshold": 1.0},
        headers=_auth(key),
    )
    assert resp.status_code == 404
    assert resp.json()["error"]["code"] == "ALERT_NOT_FOUND"


@pytest.mark.asyncio
async def test_delete_alert(client: AsyncClient, db: AsyncSession):
    _, key = await _project_key(db)
    created = await client.post("/v1/alerts", json=_cost_alert(), headers=_auth(key))
    alert_id = created.json()["id"]

    delete = await client.delete(f"/v1/alerts/{alert_id}", headers=_auth(key))
    assert delete.status_code == 204

    remaining = await client.get("/v1/alerts", headers=_auth(key))
    assert remaining.json() == []


@pytest.mark.asyncio
async def test_list_incidents_empty(client: AsyncClient, db: AsyncSession):
    _, key = await _project_key(db)
    resp = await client.get("/v1/alerts/incidents", headers=_auth(key))
    assert resp.status_code == 200
    assert resp.json() == []


@pytest.mark.asyncio
async def test_alerts_are_project_scoped(client: AsyncClient, db: AsyncSession):
    _, key_a = await _project_key(db)
    _, key_b = await _project_key(db)
    await client.post("/v1/alerts", json=_cost_alert(), headers=_auth(key_a))

    resp = await client.get("/v1/alerts", headers=_auth(key_b))
    assert resp.json() == []
