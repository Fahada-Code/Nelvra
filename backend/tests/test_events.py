from datetime import UTC, datetime

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from api.schemas.api_keys import ApiKeyCreate
from api.schemas.projects import ProjectCreate
from api.services.api_key_service import ApiKeyService
from api.services.project_service import ProjectService


def _valid_event_payload() -> dict:
    return {
        "timestamp": datetime.now(UTC).isoformat(),
        "model": "gpt-4o",
        "provider": "openai",
        "messages": [{"role": "user", "content": "Hello"}],
        "response_text": "Hi there!",
        "finish_reason": "stop",
        "prompt_tokens": 10,
        "completion_tokens": 5,
        "total_tokens": 15,
        "cost_usd": 0.00005,
        "latency_ms": 450,
        "environment": "production",
    }


async def _create_project_with_key(db: AsyncSession, client: AsyncClient) -> tuple[str, str]:
    """Helper: create project and API key, return (project_id, api_key)."""
    project = await ProjectService.create(db, ProjectCreate(name="Event Test Project"))
    _, plaintext = await ApiKeyService.create(db, project.id, ApiKeyCreate(name="test"))
    return project.id, plaintext


@pytest.mark.asyncio
async def test_ingest_event_success(client: AsyncClient, db: AsyncSession):
    project_id, key = await _create_project_with_key(db, client)

    resp = await client.post(
        "/v1/events",
        json=_valid_event_payload(),
        headers={"Authorization": f"Bearer {key}"},
    )
    assert resp.status_code == 201
    data = resp.json()
    assert data["project_id"] == project_id
    assert data["model"] == "gpt-4o"
    assert data["provider"] == "openai"
    assert "id" in data


@pytest.mark.asyncio
async def test_ingest_event_unauthorized(client: AsyncClient):
    resp = await client.post("/v1/events", json=_valid_event_payload())
    assert resp.status_code == 403


@pytest.mark.asyncio
async def test_ingest_event_invalid_api_key(client: AsyncClient):
    resp = await client.post(
        "/v1/events",
        json=_valid_event_payload(),
        headers={"Authorization": "Bearer nvl_live_" + "0" * 32},
    )
    assert resp.status_code == 401
    assert resp.json()["error"]["code"] == "INVALID_API_KEY"


@pytest.mark.asyncio
async def test_ingest_event_invalid_provider(client: AsyncClient, db: AsyncSession):
    _, key = await _create_project_with_key(db, client)

    payload = _valid_event_payload()
    payload["provider"] = "cohere"  # not supported

    resp = await client.post(
        "/v1/events",
        json=payload,
        headers={"Authorization": f"Bearer {key}"},
    )
    assert resp.status_code == 422


@pytest.mark.asyncio
async def test_ingest_event_invalid_environment(client: AsyncClient, db: AsyncSession):
    _, key = await _create_project_with_key(db, client)

    payload = _valid_event_payload()
    payload["environment"] = "local"  # not a valid enum value

    resp = await client.post(
        "/v1/events",
        json=payload,
        headers={"Authorization": f"Bearer {key}"},
    )
    assert resp.status_code == 422


@pytest.mark.asyncio
async def test_ingest_event_negative_tokens(client: AsyncClient, db: AsyncSession):
    _, key = await _create_project_with_key(db, client)

    payload = _valid_event_payload()
    payload["prompt_tokens"] = -1

    resp = await client.post(
        "/v1/events",
        json=payload,
        headers={"Authorization": f"Bearer {key}"},
    )
    assert resp.status_code == 422


@pytest.mark.asyncio
async def test_ingest_batch_events(client: AsyncClient, db: AsyncSession):
    project_id, key = await _create_project_with_key(db, client)

    batch = {"events": [_valid_event_payload() for _ in range(5)]}
    resp = await client.post(
        "/v1/events/batch",
        json=batch,
        headers={"Authorization": f"Bearer {key}"},
    )
    assert resp.status_code == 201
    data = resp.json()
    assert data["created"] == 5
    assert len(data["ids"]) == 5


@pytest.mark.asyncio
async def test_ingest_batch_too_large(client: AsyncClient, db: AsyncSession):
    _, key = await _create_project_with_key(db, client)

    batch = {"events": [_valid_event_payload() for _ in range(101)]}
    resp = await client.post(
        "/v1/events/batch",
        json=batch,
        headers={"Authorization": f"Bearer {key}"},
    )
    assert resp.status_code == 422


@pytest.mark.asyncio
async def test_ingest_event_anthropic_provider(client: AsyncClient, db: AsyncSession):
    _, key = await _create_project_with_key(db, client)

    payload = _valid_event_payload()
    payload["provider"] = "anthropic"
    payload["model"] = "claude-3-5-sonnet-20241022"
    payload["system_prompt"] = "You are a helpful assistant."

    resp = await client.post(
        "/v1/events",
        json=payload,
        headers={"Authorization": f"Bearer {key}"},
    )
    assert resp.status_code == 201


@pytest.mark.asyncio
async def test_ingest_event_with_optional_fields(client: AsyncClient, db: AsyncSession):
    _, key = await _create_project_with_key(db, client)

    payload = _valid_event_payload()
    payload.update(
        {
            "user_id": "user_123",
            "session_id": "sess_abc",
            "feature": "chat",
            "tags": ["production", "v2"],
            "custom_metadata": {"ab_test": "variant_b"},
        }
    )

    resp = await client.post(
        "/v1/events",
        json=payload,
        headers={"Authorization": f"Bearer {key}"},
    )
    assert resp.status_code == 201
    data = resp.json()
    assert data["user_id"] == "user_123"
    assert data["feature"] == "chat"


@pytest.mark.asyncio
async def test_health_endpoint(client: AsyncClient):
    resp = await client.get("/health")
    assert resp.status_code == 200
    assert resp.json()["status"] == "ok"
