from fastapi import APIRouter, Depends, Header, Request
from sqlalchemy.ext.asyncio import AsyncSession

from ..database import get_db
from ..dependencies import get_current_project_id
from ..exceptions import NelvraException
from ..models.subscription import PLAN_LIMITS
from ..schemas.billing import (
    CheckoutRequest,
    CheckoutResponse,
    PortalResponse,
    SubscriptionResponse,
    UsageResponse,
)
from ..services.billing_service import BillingService

router = APIRouter(prefix="/billing", tags=["billing"])


@router.get("/subscription", response_model=SubscriptionResponse)
async def get_subscription(
    project_id: str = Depends(get_current_project_id),
    db: AsyncSession = Depends(get_db),
) -> SubscriptionResponse:
    from sqlalchemy import select

    from ..models.project import Project

    # Resolve user_id from project
    result = await db.execute(select(Project).where(Project.id == project_id))
    project = result.scalar_one_or_none()
    if not project or not project.owner_user_id:
        raise NelvraException("Project owner not found", "OWNER_NOT_FOUND", 404)

    sub = await BillingService.get_or_create(db, project.owner_user_id)
    limits = PLAN_LIMITS[sub.plan]
    return SubscriptionResponse(
        plan=sub.plan,
        status=sub.status,
        current_period_end=sub.current_period_end,
        cancel_at_period_end=sub.cancel_at_period_end,
        events_this_month=sub.events_this_month,
        events_limit=limits["events_per_month"],
        retention_days=limits["retention_days"],
    )


@router.get("/usage", response_model=UsageResponse)
async def get_usage(
    project_id: str = Depends(get_current_project_id),
    db: AsyncSession = Depends(get_db),
) -> UsageResponse:
    from sqlalchemy import select

    from ..models.project import Project

    result = await db.execute(select(Project).where(Project.id == project_id))
    project = result.scalar_one_or_none()
    if not project or not project.owner_user_id:
        raise NelvraException("Project owner not found", "OWNER_NOT_FOUND", 404)

    sub = await BillingService.get_or_create(db, project.owner_user_id)
    limit = PLAN_LIMITS[sub.plan]["events_per_month"]
    return UsageResponse(
        events_this_month=sub.events_this_month,
        events_limit=limit,
        pct_used=round(sub.events_this_month / limit * 100, 1),
        plan=sub.plan,
    )


@router.post("/checkout", response_model=CheckoutResponse)
async def create_checkout(
    data: CheckoutRequest,
    project_id: str = Depends(get_current_project_id),
    db: AsyncSession = Depends(get_db),
) -> CheckoutResponse:
    from sqlalchemy import select

    from ..models.project import Project

    result = await db.execute(select(Project).where(Project.id == project_id))
    project = result.scalar_one_or_none()
    if not project or not project.owner_user_id:
        raise NelvraException("Project owner not found", "OWNER_NOT_FOUND", 404)

    url = await BillingService.create_checkout_session(
        project.owner_user_id, data.plan, data.success_url, data.cancel_url
    )
    return CheckoutResponse(checkout_url=url)


@router.post("/portal", response_model=PortalResponse)
async def create_portal(
    return_url: str,
    project_id: str = Depends(get_current_project_id),
    db: AsyncSession = Depends(get_db),
) -> PortalResponse:
    from sqlalchemy import select

    from ..models.project import Project

    result = await db.execute(select(Project).where(Project.id == project_id))
    project = result.scalar_one_or_none()
    if not project or not project.owner_user_id:
        raise NelvraException("Project owner not found", "OWNER_NOT_FOUND", 404)

    url = await BillingService.create_portal_session(db, project.owner_user_id, return_url)
    return PortalResponse(portal_url=url)


@router.post("/webhook", status_code=200)
async def stripe_webhook(
    request: Request,
    db: AsyncSession = Depends(get_db),
    stripe_signature: str | None = Header(default=None, alias="stripe-signature"),
) -> dict:
    payload = await request.body()
    if not stripe_signature:
        raise NelvraException("Missing Stripe-Signature header", "MISSING_SIGNATURE", 400)
    await BillingService.handle_webhook(db, payload, stripe_signature)
    return {"received": True}
