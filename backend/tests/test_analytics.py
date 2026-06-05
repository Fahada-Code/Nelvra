from datetime import datetime, timezone

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from api.schemas.projects import ProjectCreate
from api.schemas.api_keys import ApiKeyCreate
from api.services.project_service import ProjectService
from api.services.api_key_service import ApiKeyService
from api.services.event_service import EventService
from api.schemas.events import LLMEventCreate


async def _setup(db: AsyncSession) -> tuple[str, str]:
    """Creates a project, API key, and returns (project_id, api_key)."""
    project = await ProjectService.create(db, ProjectCreate(name="Analytics Test"))
    _, key = await ApiKeyService.create(db, project.id, ApiKeyCreate(name="test"))
    return project.id, key


def _event_data(model: str = "gpt-4o", provider: str = "openai") -> LLMEventCreate:
    return LLMEventCreate(
        timestamp=datetime.now(timezone.utc),
        model=model,
        provider=provider,
        messages=[{"role": "user", "content": "hello"}],
        response_text="hi",
        finish_reason="stop",
        prompt_tokens=10,
        completion_tokens=5,
        total_tokens=15,
        cost_usd=0.0001,
        latency_ms=300,
        environment="production",
    )


@pytest.mark.asyncio
async def test_overview_empty(client: AsyncClient, db: AsyncSession):
    project_id, key = await _setup(db)
    resp = await client.get(
        "/v1/analytics/overview",
        headers={"Authorization": f"Bearer {key}"},
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["total_requests"] == 0
    assert data["total_cost_usd"] == 0
    assert data["hourly_requests"] == []


@pytest.mark.asyncio
async def test_overview_with_events(client: AsyncClient, db: AsyncSession):
    project_id, key = await _setup(db)

    # Ingest 5 events
    for _ in range(5):
        await EventService.create(db, project_id, _event_data())

    resp = await client.get(
        "/v1/analytics/overview",
        headers={"Authorization": f"Bearer {key}"},
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["total_requests"] == 5
    assert data["requests_by_model"].get("gpt-4o") == 5
    assert data["requests_by_provider"].get("openai") == 5


@pytest.mark.asyncio
async def test_overview_multiple_models(client: AsyncClient, db: AsyncSession):
    project_id, key = await _setup(db)

    await EventService.create(db, project_id, _event_data("gpt-4o", "openai"))
    await EventService.create(db, project_id, _event_data("claude-3-5-sonnet-20241022", "anthropic"))

    resp = await client.get(
        "/v1/analytics/overview",
        headers={"Authorization": f"Bearer {key}"},
    )
    data = resp.json()
    assert data["total_requests"] == 2
    assert "gpt-4o" in data["requests_by_model"]
    assert "claude-3-5-sonnet-20241022" in data["requests_by_model"]


@pytest.mark.asyncio
async def test_list_requests(client: AsyncClient, db: AsyncSession):
    project_id, key = await _setup(db)

    for _ in range(3):
        await EventService.create(db, project_id, _event_data())

    resp = await client.get(
        "/v1/analytics/requests",
        headers={"Authorization": f"Bearer {key}"},
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["total"] == 3
    assert len(data["items"]) == 3


@pytest.mark.asyncio
async def test_list_requests_filter_by_provider(client: AsyncClient, db: AsyncSession):
    project_id, key = await _setup(db)

    await EventService.create(db, project_id, _event_data("gpt-4o", "openai"))
    await EventService.create(db, project_id, _event_data("claude-3-5-sonnet-20241022", "anthropic"))

    resp = await client.get(
        "/v1/analytics/requests?provider=openai",
        headers={"Authorization": f"Bearer {key}"},
    )
    data = resp.json()
    assert data["total"] == 1
    assert data["items"][0]["provider"] == "openai"


@pytest.mark.asyncio
async def test_get_event_detail(client: AsyncClient, db: AsyncSession):
    project_id, key = await _setup(db)
    event = await EventService.create(db, project_id, _event_data())

    resp = await client.get(
        f"/v1/analytics/requests/{event.id}",
        headers={"Authorization": f"Bearer {key}"},
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["id"] == event.id
    assert "messages" in data
    assert "response_text" in data


@pytest.mark.asyncio
async def test_event_detail_not_found(client: AsyncClient, db: AsyncSession):
    project_id, key = await _setup(db)

    resp = await client.get(
        "/v1/analytics/requests/00000000-0000-0000-0000-000000000000",
        headers={"Authorization": f"Bearer {key}"},
    )
    assert resp.status_code == 404
    assert resp.json()["error"]["code"] == "EVENT_NOT_FOUND"


@pytest.mark.asyncio
async def test_cannot_access_other_project_events(client: AsyncClient, db: AsyncSession):
    """Events from project A must not be visible via project B's API key."""
    project_a_id, key_a = await _setup(db)
    project_b_id, key_b = await _setup(db)

    event = await EventService.create(db, project_a_id, _event_data())

    resp = await client.get(
        f"/v1/analytics/requests/{event.id}",
        headers={"Authorization": f"Bearer {key_b}"},
    )
    assert resp.status_code == 404
