import stripe
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.api.deps import get_db, get_current_user
from app.core.config import settings
from app.models.user import User
from app.models.subscription import Plan, Subscription, SubscriptionStatus
from fastapi import Request
from datetime import datetime

router = APIRouter()

stripe.api_key = settings.STRIPE_SECRET_KEY

@router.post("/create-checkout-session")
def create_checkout_session(
    plan_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Create a new Stripe Checkout Session for a user to subscribe to a plan.
    """
    plan = db.query(Plan).filter(Plan.id == plan_id).first()
    if not plan:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Plan not found")

    try:
        # For a new subscription, we don't have a customer ID yet.
        # Stripe can create one for us.
        checkout_session = stripe.checkout.Session.create(
            line_items=[
                {
                    'price': plan.stripe_price_id,
                    'quantity': 1,
                },
            ],
            mode='subscription',
            success_url=f"http://localhost:3000/dashboard?success=true", # Placeholder URL
            cancel_url=f"http://localhost:3000/dashboard?canceled=true", # Placeholder URL
            # Pass our internal user ID to Stripe's metadata
            # so we know who subscribed when we get the webhook event.
            metadata={
                "user_id": current_user.id
            }
        )
        return {"sessionId": checkout_session.id}
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e),
        )

@router.post("/stripe-webhook")
async def stripe_webhook(request: Request, db: Session = Depends(get_db)):
    payload = await request.body()
    sig_header = request.headers.get('stripe-signature')
    event = None

    try:
        event = stripe.Webhook.construct_event(
            payload, sig_header, settings.STRIPE_WEBHOOK_SECRET
        )
    except ValueError as e:
        # Invalid payload
        raise HTTPException(status_code=400, detail=str(e))
    except stripe.error.SignatureVerificationError as e:
        # Invalid signature
        raise HTTPException(status_code=400, detail=str(e))

    # Handle the event
    if event['type'] == 'checkout.session.completed':
        session = event['data']['object']
        user_id = session.get('metadata', {}).get('user_id')
        stripe_subscription_id = session.get('subscription')

        if not user_id or not stripe_subscription_id:
            raise HTTPException(status_code=400, detail="Missing metadata in webhook event.")

        # Retrieve subscription details from Stripe to get plan and period end
        stripe_sub = stripe.Subscription.retrieve(stripe_subscription_id)
        plan_id = db.query(Plan.id).filter(Plan.stripe_price_id == stripe_sub.items.data[0].price.id).scalar()

        # Create a new subscription record in our DB
        new_subscription = Subscription(
            user_id=int(user_id),
            plan_id=plan_id,
            stripe_subscription_id=stripe_subscription_id,
            status=stripe_sub.status,
            current_period_end=datetime.fromtimestamp(stripe_sub.current_period_end)
        )
        db.add(new_subscription)
        db.commit()

    return {"status": "success"}