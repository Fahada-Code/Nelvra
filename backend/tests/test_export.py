from datetime import UTC, datetime

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from api.schemas.events import LLMEventCreate
from api.schemas.projects import ProjectCreate
from api.services.event_service import EventService
from api.services.export_service import ExportService
from api.services.project_service import ProjectService


def _event() -> LLMEventCreate:
    return LLMEventCreate(
        timestamp=datetime.now(UTC),
        model="gpt-4o",
        provider="openai",
        messages=[{"role": "user", "content": "hi"}],
        response_text="hello",
        finish_reason="stop",
        prompt_tokens=10,
        completion_tokens=5,
        total_tokens=15,
        cost_usd=0.0002,
        latency_ms=300,
        environment="production",
    )


@pytest.mark.asyncio
async def test_export_empty_project_has_header_only(db: AsyncSession):
    project = await ProjectService.create(db, ProjectCreate(name="Export Empty"))
    csv_bytes = await ExportService.export_events_csv(db, project.id)
    text = csv_bytes.decode("utf-8")
    lines = [line for line in text.splitlines() if line]
    assert lines[0].startswith("id,timestamp,model,provider")
    assert len(lines) == 1


@pytest.mark.asyncio
async def test_export_includes_events(db: AsyncSession):
    project = await ProjectService.create(db, ProjectCreate(name="Export Data"))
    for _ in range(3):
        await EventService.create(db, project.id, _event())

    csv_bytes = await ExportService.export_events_csv(db, project.id)
    lines = [line for line in csv_bytes.decode("utf-8").splitlines() if line]
    assert len(lines) == 4  # header + 3 events
    assert "gpt-4o" in lines[1]
