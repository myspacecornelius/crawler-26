"""
Billing endpoints: Stripe checkout, webhook, portal, and credit history.
"""

from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Request, Query
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from ..database import get_db
from ..models import User, CreditTransaction
from ..schemas import (
    CheckoutRequest, CheckoutResponse, BillingHistory,
    BillingHistoryItem, PortalResponse,
)
from ..auth import get_current_user_id
from ..billing import (
    create_checkout_session, create_portal_session, handle_webhook,
    PLANS, CREDIT_PACKS,
)

router = APIRouter(prefix="/billing", tags=["billing"])


@router.post("/checkout", response_model=CheckoutResponse)
async def checkout(
    body: CheckoutRequest,
    user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    """Create a Stripe Checkout Session for plan upgrade or credit pack purchase."""
    result = await db.execute(select(User).where(User.id == UUID(user_id)))
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    if not body.plan and not body.credit_pack:
        raise HTTPException(status_code=400, detail="Must specify plan or credit_pack")

    try:
        url = await create_checkout_session(user, db, plan=body.plan, credit_pack=body.credit_pack)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    return CheckoutResponse(checkout_url=url)


@router.post("/webhook")
async def stripe_webhook(request: Request, db: AsyncSession = Depends(get_db)):
    """Handle Stripe webhook events. Must receive raw body for signature verification."""
    payload = await request.body()
    sig_header = request.headers.get("stripe-signature", "")

    try:
        result = await handle_webhook(payload, sig_header, db)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    return result


@router.get("/portal", response_model=PortalResponse)
async def billing_portal(
    user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    """Get a Stripe Billing Portal URL for managing subscriptions."""
    result = await db.execute(select(User).where(User.id == UUID(user_id)))
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    try:
        url = await create_portal_session(user, db)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Could not create portal session: {e}")

    return PortalResponse(portal_url=url)


@router.get("/history", response_model=BillingHistory)
async def billing_history(
    page: int = Query(1, ge=1),
    per_page: int = Query(20, ge=1, le=100),
    user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    """Get credit transaction history for the current user."""
    uid = UUID(user_id)

    # Count
    count_q = select(func.count()).where(CreditTransaction.user_id == uid)
    total = (await db.execute(count_q)).scalar()

    # Fetch
    query = (
        select(CreditTransaction)
        .where(CreditTransaction.user_id == uid)
        .order_by(CreditTransaction.created_at.desc())
        .offset((page - 1) * per_page)
        .limit(per_page)
    )
    result = await db.execute(query)
    transactions = result.scalars().all()

    return BillingHistory(
        transactions=[BillingHistoryItem.model_validate(t) for t in transactions],
        total=total,
    )


@router.get("/plans")
async def list_plans():
    """List available plans and credit packs with pricing."""
    plans = []
    for slug, info in PLANS.items():
        plans.append({
            "slug": slug,
            "name": info["name"],
            "price_cents": info["price_cents"],
            "credits_monthly": info["credits_monthly"],
        })

    packs = []
    for slug, info in CREDIT_PACKS.items():
        packs.append({
            "slug": slug,
            "name": info["name"],
            "credits": info["credits"],
            "price_cents": info["price_cents"],
        })

    return {"plans": plans, "credit_packs": packs}
