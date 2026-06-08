"""Payment and subscription endpoints — plans, checkout, webhooks."""
import uuid
from datetime import datetime, timedelta
from fastapi import APIRouter, Depends, HTTPException, Request, status
from pydantic import BaseModel as PydanticModel
from sqlalchemy.orm import Session

from app.database import get_db
from app.api.deps import get_current_user
from app.models.user import User
from app.models.payment import Subscription, Payment, PlanType, PaymentStatus, PLAN_DETAILS
from app.core.config import settings

router = APIRouter()


class CheckoutReq(PydanticModel):
    plan: PlanType


class PlanOut(PydanticModel):
    id: str
    name: str
    price: int
    films_limit: int
    features: list[str]


@router.get("/plans")
def list_plans():
    return [
        PlanOut(id=plan.value, name=info["name"], price=info["price"],
                films_limit=info["films_limit"], features=info["features"])
        for plan, info in PLAN_DETAILS.items()
    ]


@router.get("/subscription")
def get_subscription(db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    sub = db.query(Subscription).filter(Subscription.user_id == user.id).first()
    if not sub:
        return {
            "plan": "free", "films_limit": 5, "films_used": 0,
            "is_active": True, "stripe_configured": bool(getattr(settings, "STRIPE_SECRET_KEY", "")),
        }
    return {
        "plan": sub.plan.value, "films_limit": sub.films_limit,
        "films_used": sub.films_used, "is_active": sub.is_active,
        "current_period_end": sub.current_period_end.isoformat() if sub.current_period_end else None,
        "stripe_configured": bool(getattr(settings, "STRIPE_SECRET_KEY", "")),
    }


@router.post("/checkout")
def create_checkout(body: CheckoutReq, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    stripe_key = getattr(settings, "STRIPE_SECRET_KEY", "")
    if not stripe_key:
        sub = db.query(Subscription).filter(Subscription.user_id == user.id).first()
        plan_info = PLAN_DETAILS[body.plan]
        if not sub:
            sub = Subscription(
                id=str(uuid.uuid4()), user_id=user.id, plan=body.plan,
                films_limit=plan_info["films_limit"], films_used=0,
                current_period_start=datetime.utcnow(),
                current_period_end=datetime.utcnow() + timedelta(days=30),
            )
            db.add(sub)
        else:
            sub.plan = body.plan
            sub.films_limit = plan_info["films_limit"]
            sub.current_period_start = datetime.utcnow()
            sub.current_period_end = datetime.utcnow() + timedelta(days=30)
        db.commit()
        return {
            "message": f"Upgraded to {plan_info['name']} plan (Stripe not configured — demo mode)",
            "plan": body.plan.value,
            "demo_mode": True,
        }

    try:
        import stripe
        stripe.api_key = stripe_key
        plan_info = PLAN_DETAILS[body.plan]
        session = stripe.checkout.Session.create(
            payment_method_types=["card"],
            line_items=[{
                "price_data": {
                    "currency": "usd",
                    "product_data": {"name": f"AI Film Studio — {plan_info['name']}"},
                    "unit_amount": plan_info["price"],
                    "recurring": {"interval": "month"},
                },
                "quantity": 1,
            }],
            mode="subscription",
            success_url=f"{getattr(settings, 'FRONTEND_URL', 'http://localhost:3000')}/profile?payment=success",
            cancel_url=f"{getattr(settings, 'FRONTEND_URL', 'http://localhost:3000')}/profile?payment=cancelled",
            client_reference_id=user.id,
            metadata={"plan": body.plan.value},
        )
        return {"checkout_url": session.url, "session_id": session.id}
    except ImportError:
        raise HTTPException(status_code=503, detail="Stripe SDK not installed")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Stripe error: {str(e)}")


@router.post("/webhook")
async def stripe_webhook(request: Request, db: Session = Depends(get_db)):
    stripe_key = getattr(settings, "STRIPE_SECRET_KEY", "")
    webhook_secret = getattr(settings, "STRIPE_WEBHOOK_SECRET", "")
    if not stripe_key or not webhook_secret:
        raise HTTPException(status_code=503, detail="Stripe not configured")

    try:
        import stripe
        stripe.api_key = stripe_key
        payload = await request.body()
        sig = request.headers.get("stripe-signature", "")
        event = stripe.Webhook.construct_event(payload, sig, webhook_secret)

        if event["type"] == "checkout.session.completed":
            session = event["data"]["object"]
            user_id = session.get("client_reference_id")
            plan_str = session.get("metadata", {}).get("plan", "starter")
            plan = PlanType(plan_str)
            plan_info = PLAN_DETAILS[plan]

            sub = db.query(Subscription).filter(Subscription.user_id == user_id).first()
            if not sub:
                sub = Subscription(id=str(uuid.uuid4()), user_id=user_id)
                db.add(sub)
            sub.plan = plan
            sub.films_limit = plan_info["films_limit"]
            sub.stripe_customer_id = session.get("customer")
            sub.stripe_subscription_id = session.get("subscription")
            sub.current_period_start = datetime.utcnow()
            sub.current_period_end = datetime.utcnow() + timedelta(days=30)

            payment = Payment(
                id=str(uuid.uuid4()), user_id=user_id,
                stripe_payment_intent_id=session.get("payment_intent"),
                amount=session.get("amount_total", 0), currency="usd",
                status=PaymentStatus.succeeded,
                description=f"Subscription: {plan_info['name']}",
            )
            db.add(payment)
            db.commit()

        return {"status": "ok"}
    except ImportError:
        raise HTTPException(status_code=503, detail="Stripe SDK not installed")
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Webhook error: {str(e)}")


@router.get("/history")
def payment_history(db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    payments = db.query(Payment).filter(Payment.user_id == user.id).order_by(Payment.created_at.desc()).limit(20).all()
    return [
        {
            "id": p.id, "amount": p.amount, "currency": p.currency,
            "status": p.status.value, "description": p.description,
            "created_at": p.created_at.isoformat(),
        }
        for p in payments
    ]
