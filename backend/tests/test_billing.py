import uuid
from datetime import UTC, datetime

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from api.exceptions import NelvraException
from api.models.subscription import PLAN_LIMITS
from api.models.user import User
from api.services.billing_service import BillingService


async def _make_user(db: AsyncSession) -> User:
    user = User(github_id=str(uuid.uuid4()), github_login=f"u{uuid.uuid4().hex[:8]}")
    db.add(user)
    await db.flush()
    await db.refresh(user)
    return user


@pytest.mark.asyncio
async def test_get_or_create_is_idempotent(db: AsyncSession):
    user = await _make_user(db)
    first = await BillingService.get_or_create(db, user.id)
    second = await BillingService.get_or_create(db, user.id)
    assert first.id == second.id
    assert first.plan == "free"


@pytest.mark.asyncio
async def test_check_event_limit_increments(db: AsyncSession):
    user = await _make_user(db)
    await BillingService.check_event_limit(db, user.id)
    sub = await BillingService.get_or_create(db, user.id)
    assert sub.events_this_month == 1
    assert sub.events_month_key == datetime.now(UTC).strftime("%Y-%m")


@pytest.mark.asyncio
async def test_check_event_limit_raises_at_cap(db: AsyncSession):
    user = await _make_user(db)
    sub = await BillingService.get_or_create(db, user.id)
    sub.events_this_month = PLAN_LIMITS["free"]["events_per_month"]
    sub.events_month_key = datetime.now(UTC).strftime("%Y-%m")
    await db.flush()

    with pytest.raises(NelvraException) as exc:
        await BillingService.check_event_limit(db, user.id)
    assert exc.value.code == "EVENT_LIMIT_EXCEEDED"
    assert exc.value.status_code == 402


@pytest.mark.asyncio
async def test_monthly_counter_resets_on_new_month(db: AsyncSession):
    user = await _make_user(db)
    sub = await BillingService.get_or_create(db, user.id)
    sub.events_this_month = 999
    sub.events_month_key = "2020-01"  # stale month
    await db.flush()

    await BillingService.check_event_limit(db, user.id)
    refreshed = await BillingService.get_or_create(db, user.id)
    assert refreshed.events_month_key == datetime.now(UTC).strftime("%Y-%m")
    assert refreshed.events_this_month == 1
