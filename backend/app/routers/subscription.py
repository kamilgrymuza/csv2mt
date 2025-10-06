"""
Subscription API Router

Handles all subscription-related endpoints:
- Get subscription status
- Create checkout session
- Create portal session
- Handle Stripe webhooks

This router is designed to be reusable across projects.
"""

from fastapi import APIRouter, Depends, HTTPException, Request, Header
from sqlalchemy.orm import Session
import stripe
from stripe import StripeError
import logging

from ..database import get_db
from ..auth import verify_token
from ..models import User
from ..schemas import (
    SubscriptionStatusResponse,
    CheckoutSessionRequest,
    CheckoutSessionResponse
)
from ..services.stripe_service import StripeService
from .. import crud
from ..config import settings

router = APIRouter(prefix="/subscription", tags=["subscription"])
logger = logging.getLogger(__name__)


@router.get("/status", response_model=SubscriptionStatusResponse)
async def get_subscription_status(
    current_user: User = Depends(verify_token),
    db: Session = Depends(get_db)
):
    """
    Get current user's subscription status and usage statistics

    Returns:
        - has_active_subscription: Whether user has active subscription
        - status: Current subscription status (if exists)
        - conversions_used: Number of conversions this month
        - conversions_limit: Limit for free tier (null if subscribed)
        - can_convert: Whether user can perform another conversion
    """
    stats = crud.get_user_usage_stats(db, current_user.id)
    return SubscriptionStatusResponse(**stats)


@router.post("/create-checkout-session", response_model=CheckoutSessionResponse)
async def create_checkout_session(
    request: CheckoutSessionRequest,
    current_user: User = Depends(verify_token),
    db: Session = Depends(get_db)
):
    """
    Create a Stripe Checkout Session for subscription

    This redirects the user to Stripe's hosted checkout page.
    After successful payment, they'll be redirected back to your app.
    """
    try:
        # Check if user already has an active subscription
        if crud.user_has_active_subscription(db, current_user.id):
            raise HTTPException(
                status_code=400,
                detail="You already have an active subscription. Please cancel your existing subscription before creating a new one."
            )

        session_data = StripeService.create_checkout_session(
            db=db,
            user=current_user,
            price_id=request.price_id
        )

        return CheckoutSessionResponse(**session_data)

    except HTTPException:
        raise
    except StripeError as e:
        logger.error(f"Stripe error creating checkout session: {str(e)}")
        raise HTTPException(status_code=400, detail=f"Stripe error: {str(e)}")
    except Exception as e:
        logger.error(f"Error creating checkout session: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to create checkout session")


@router.post("/create-portal-session")
async def create_portal_session(
    current_user: User = Depends(verify_token),
    db: Session = Depends(get_db)
):
    """
    Create a Stripe Customer Portal session

    This allows users to manage their subscription (update payment method, cancel, etc.)
    """
    try:
        subscription = crud.get_subscription_by_user_id(db, current_user.id)

        if not subscription or not subscription.stripe_customer_id:
            raise HTTPException(
                status_code=404,
                detail="No subscription found. Please subscribe first."
            )

        portal_url = StripeService.create_portal_session(
            customer_id=subscription.stripe_customer_id
        )

        return {"url": portal_url}

    except HTTPException:
        raise
    except StripeError as e:
        logger.error(f"Stripe error creating portal session: {str(e)}")
        raise HTTPException(status_code=400, detail=f"Stripe error: {str(e)}")
    except Exception as e:
        logger.error(f"Error creating portal session: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to create portal session")


@router.post("/webhook")
async def stripe_webhook(
    request: Request,
    db: Session = Depends(get_db),
    stripe_signature: str = Header(None, alias="stripe-signature")
):
    """
    Handle Stripe webhook events

    This endpoint is called by Stripe when subscription events occur.
    It updates the local database to reflect the current subscription state.

    Important: This endpoint should be publicly accessible (no auth required)
    """
    try:
        payload = await request.body()

        # Verify webhook signature
        try:
            event = stripe.Webhook.construct_event(
                payload, stripe_signature, settings.stripe_webhook_secret
            )
        except ValueError:
            logger.error("Invalid webhook payload")
            raise HTTPException(status_code=400, detail="Invalid payload")
        except stripe.SignatureVerificationError:
            logger.error("Invalid webhook signature")
            raise HTTPException(status_code=400, detail="Invalid signature")

        # Handle the event
        logger.info(f"Received webhook event: {event['type']}")

        success = StripeService.handle_webhook_event(db, event)

        if not success:
            logger.warning(f"Webhook event {event['type']} was not fully processed")

        return {"status": "success"}

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error processing webhook: {str(e)}")
        raise HTTPException(status_code=500, detail="Webhook processing failed")
