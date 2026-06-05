from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from ..exceptions import NelvraException
from ..models.subscription import PLAN_LIMITS, Subscription


class BillingService:
    @staticmethod
    async def get_or_create(db: AsyncSession, user_id: str) -> Subscription:
        result = await db.execute(
            select(Subscription).where(Subscription.user_id == user_id, Subscription.deleted_at.is_(None))
        )
        sub = result.scalar_one_or_none()
        if sub is None:
            sub = Subscription(user_id=user_id)
            db.add(sub)
            await db.flush()
            await db.refresh(sub)
        return sub

    @staticmethod
    async def check_event_limit(db: AsyncSession, user_id: str) -> None:
        """Raises 402 if the user has exceeded their monthly event quota."""
        sub = await BillingService.get_or_create(db, user_id)
        now_key = datetime.now(timezone.utc).strftime("%Y-%m")
        if sub.events_month_key != now_key:
            sub.events_this_month = 0
            sub.events_month_key = now_key

        limit = PLAN_LIMITS[sub.plan]["events_per_month"]
        if sub.events_this_month >= limit:
            raise NelvraException(
                message=f"Monthly event limit reached ({limit:,} events on the {sub.plan} plan). Upgrade to continue.",
                code="EVENT_LIMIT_EXCEEDED",
                status_code=402,
            )
        sub.events_this_month += 1

    @staticmethod
    async def create_checkout_session(
        user_id: str, plan: str, success_url: str, cancel_url: str
    ) -> str:
        from api.config import settings
        import stripe

        if not settings.stripe_secret_key:
            raise NelvraException("Stripe not configured", "STRIPE_NOT_CONFIGURED", 503)

        stripe.api_key = settings.stripe_secret_key
        price_id = settings.stripe_price_pro if plan == "pro" else settings.stripe_price_team

        session = stripe.checkout.Session.create(
            mode="subscription",
            line_items=[{"price": price_id, "quantity": 1}],
            success_url=success_url,
            cancel_url=cancel_url,
            metadata={"user_id": user_id, "plan": plan},
        )
        return session.url

    @staticmethod
    async def create_portal_session(db: AsyncSession, user_id: str, return_url: str) -> str:
        from api.config import settings
        import stripe

        if not settings.stripe_secret_key:
            raise NelvraException("Stripe not configured", "STRIPE_NOT_CONFIGURED", 503)

        sub = await BillingService.get_or_create(db, user_id)
        if not sub.stripe_customer_id:
            raise NelvraException("No billing account found", "NO_BILLING_ACCOUNT", 400)

        stripe.api_key = settings.stripe_secret_key
        session = stripe.billing_portal.Session.create(
            customer=sub.stripe_customer_id,
            return_url=return_url,
        )
        return session.url

    @staticmethod
    async def handle_webhook(db: AsyncSession, payload: bytes, sig_header: str) -> None:
        from api.config import settings
        import stripe

        try:
            event = stripe.Webhook.construct_event(payload, sig_header, settings.stripe_webhook_secret)
        except stripe.error.SignatureVerificationError:
            raise NelvraException("Invalid webhook signature", "INVALID_WEBHOOK_SIGNATURE", 400)

        if event["type"] == "checkout.session.completed":
            session = event["data"]["object"]
            user_id = session["metadata"]["user_id"]
            plan = session["metadata"]["plan"]
            customer_id = session["customer"]
            subscription_id = session["subscription"]

            result = await db.execute(
                select(Subscription).where(Subscription.user_id == user_id)
            )
            sub = result.scalar_one_or_none()
            if sub is None:
                sub = Subscription(user_id=user_id)
                db.add(sub)

            sub.plan = plan
            sub.status = "active"
            sub.stripe_customer_id = customer_id
            sub.stripe_subscription_id = subscription_id
            await db.flush()

        elif event["type"] == "customer.subscription.deleted":
            subscription_id = event["data"]["object"]["id"]
            result = await db.execute(
                select(Subscription).where(Subscription.stripe_subscription_id == subscription_id)
            )
            sub = result.scalar_one_or_none()
            if sub:
                sub.plan = "free"
                sub.status = "canceled"
                sub.stripe_subscription_id = None
                await db.flush()
