"""
Stripe Service Module - Reusable subscription management

This module handles all Stripe-related operations including:
- Customer creation
- Subscription creation and management
- Checkout session creation
- Webhook event processing

To reuse in other projects:
1. Copy this file to your new project
2. Ensure you have Subscription and User models
3. Update settings to include Stripe config
4. Add stripe to requirements.txt
"""

import stripe
from stripe import StripeError
from datetime import datetime
from typing import Optional, Dict, Any
from sqlalchemy.orm import Session

from ..config import settings
from ..models import User, Subscription, SubscriptionStatus

# Initialize Stripe
stripe.api_key = settings.stripe_secret_key


class StripeService:
    """Service class for Stripe operations"""

    @staticmethod
    def create_customer(user: User) -> str:
        """
        Create a Stripe customer for a user

        Args:
            user: User model instance

        Returns:
            Stripe customer ID
        """
        customer = stripe.Customer.create(
            email=user.email,
            name=f"{user.first_name or ''} {user.last_name or ''}".strip(),
            metadata={
                "user_id": user.id,
                "clerk_id": user.clerk_id
            }
        )
        return customer.id

    @staticmethod
    def create_checkout_session(
        db: Session,
        user: User,
        price_id: Optional[str] = None,
        success_url: Optional[str] = None,
        cancel_url: Optional[str] = None
    ) -> Dict[str, str]:
        """
        Create a Stripe Checkout Session for subscription

        Args:
            db: Database session
            user: User model instance
            price_id: Stripe price ID (defaults to settings.stripe_price_id)
            success_url: URL to redirect after success
            cancel_url: URL to redirect after cancellation

        Returns:
            Dict with session_id and url
        """
        # Get or create subscription record
        subscription = db.query(Subscription).filter(
            Subscription.user_id == user.id
        ).first()

        if not subscription:
            subscription = Subscription(user_id=user.id)
            db.add(subscription)

        # Get or create Stripe customer
        if not subscription.stripe_customer_id:
            customer_id = StripeService.create_customer(user)
            subscription.stripe_customer_id = customer_id
            db.commit()
        else:
            customer_id = subscription.stripe_customer_id

        # Use provided price_id or default from settings
        price_id = price_id or settings.stripe_price_id

        # Set default URLs
        success_url = success_url or f"{settings.frontend_url}/subscription?success=true"
        cancel_url = cancel_url or f"{settings.frontend_url}/subscription?canceled=true"

        # Check if customer already has any active subscriptions in Stripe
        # This prevents race conditions where multiple checkout sessions are opened
        existing_subs = stripe.Subscription.list(
            customer=customer_id,
            status='active',
            limit=1
        )

        if existing_subs.data:
            # Customer already has an active subscription in Stripe
            raise StripeError(
                message="Customer already has an active subscription",
                code="subscription_already_exists"
            )

        # Create checkout session
        session = stripe.checkout.Session.create(
            customer=customer_id,
            payment_method_types=["card"],
            line_items=[{
                "price": price_id,
                "quantity": 1,
            }],
            mode="subscription",
            success_url=success_url,
            cancel_url=cancel_url,
            metadata={
                "user_id": user.id,
            },
            # Prevent duplicate subscriptions by using customer's email as idempotency key base
            subscription_data={
                "metadata": {
                    "user_id": user.id,
                }
            }
        )

        return {
            "session_id": session.id,
            "url": session.url
        }

    @staticmethod
    def create_portal_session(
        customer_id: str,
        return_url: Optional[str] = None
    ) -> str:
        """
        Create a Stripe Customer Portal session for managing subscription

        Args:
            customer_id: Stripe customer ID
            return_url: URL to return to after portal

        Returns:
            Portal session URL
        """
        return_url = return_url or f"{settings.frontend_url}/subscription"

        session = stripe.billing_portal.Session.create(
            customer=customer_id,
            return_url=return_url,
        )
        return session.url

    @staticmethod
    def sync_subscription_from_stripe(db: Session, subscription: Subscription) -> bool:
        """
        Sync subscription details from Stripe API (useful for missing period dates)

        Args:
            db: Database session
            subscription: Local subscription object

        Returns:
            True if successful
        """
        try:
            if not subscription.stripe_subscription_id:
                return False

            # Fetch subscription from Stripe
            stripe_sub = stripe.Subscription.retrieve(subscription.stripe_subscription_id)

            # Update period dates if they exist in Stripe
            if stripe_sub.get("current_period_start"):
                subscription.current_period_start = datetime.fromtimestamp(
                    stripe_sub["current_period_start"],
                    tz=datetime.now().astimezone().tzinfo
                ).replace(tzinfo=None)

            if stripe_sub.get("current_period_end"):
                subscription.current_period_end = datetime.fromtimestamp(
                    stripe_sub["current_period_end"],
                    tz=datetime.now().astimezone().tzinfo
                ).replace(tzinfo=None)

            # Update status
            if stripe_sub.get("status"):
                status_map = {
                    "active": SubscriptionStatus.ACTIVE,
                    "canceled": SubscriptionStatus.CANCELED,
                    "incomplete": SubscriptionStatus.INCOMPLETE,
                    "incomplete_expired": SubscriptionStatus.INCOMPLETE_EXPIRED,
                    "past_due": SubscriptionStatus.PAST_DUE,
                    "trialing": SubscriptionStatus.TRIALING,
                    "unpaid": SubscriptionStatus.UNPAID,
                }
                subscription.status = status_map.get(stripe_sub["status"])

            subscription.cancel_at_period_end = stripe_sub.get("cancel_at_period_end", False)

            db.commit()
            return True
        except StripeError:
            return False

    @staticmethod
    def cancel_subscription(subscription_id: str) -> bool:
        """
        Cancel a Stripe subscription

        Args:
            subscription_id: Stripe subscription ID

        Returns:
            True if successful
        """
        try:
            stripe.Subscription.modify(
                subscription_id,
                cancel_at_period_end=True
            )
            return True
        except StripeError:
            return False

    @staticmethod
    def reactivate_subscription(subscription_id: str) -> bool:
        """
        Reactivate a canceled subscription (before period end)

        Args:
            subscription_id: Stripe subscription ID

        Returns:
            True if successful
        """
        try:
            stripe.Subscription.modify(
                subscription_id,
                cancel_at_period_end=False
            )
            return True
        except StripeError:
            return False

    @staticmethod
    def handle_webhook_event(db: Session, event: Dict[str, Any]) -> bool:
        """
        Process Stripe webhook events

        Args:
            db: Database session
            event: Stripe event object

        Returns:
            True if event was handled successfully
        """
        event_type = event["type"]
        data = event["data"]["object"]

        if event_type == "customer.subscription.created":
            return StripeService._handle_subscription_created(db, data)

        elif event_type == "customer.subscription.updated":
            return StripeService._handle_subscription_updated(db, data)

        elif event_type == "customer.subscription.deleted":
            return StripeService._handle_subscription_deleted(db, data)

        elif event_type == "invoice.paid":
            return StripeService._handle_invoice_paid(db, data)

        elif event_type == "invoice.payment_failed":
            return StripeService._handle_payment_failed(db, data)

        return True  # Unhandled events are considered successful

    @staticmethod
    def _handle_subscription_created(db: Session, subscription_data: Dict) -> bool:
        """Handle subscription.created webhook"""
        customer_id = subscription_data.get("customer")
        subscription_id = subscription_data.get("id")

        if not customer_id or not subscription_id:
            return False

        # Find existing subscription record by customer_id
        subscription = db.query(Subscription).filter(
            Subscription.stripe_customer_id == customer_id
        ).first()

        if subscription:
            # If there's already an active subscription with a different subscription_id,
            # cancel the old one in Stripe before updating to the new one
            if (subscription.stripe_subscription_id and
                subscription.stripe_subscription_id != subscription_id and
                subscription.status == SubscriptionStatus.ACTIVE):
                try:
                    # Cancel the old subscription in Stripe immediately
                    stripe.Subscription.delete(subscription.stripe_subscription_id)
                except StripeError as e:
                    # Log but don't fail - the old subscription might already be canceled
                    print(f"[WEBHOOK] Error canceling old subscription {subscription.stripe_subscription_id}: {str(e)}")

            # Update existing subscription
            subscription.stripe_subscription_id = subscription_id
            subscription.stripe_price_id = subscription_data["items"]["data"][0]["price"]["id"]
            subscription.status = SubscriptionStatus(subscription_data.get("status", "active"))

            # Handle timestamps safely
            if subscription_data.get("current_period_start"):
                subscription.current_period_start = datetime.fromtimestamp(subscription_data["current_period_start"])
            if subscription_data.get("current_period_end"):
                subscription.current_period_end = datetime.fromtimestamp(subscription_data["current_period_end"])

            # Check both cancel_at_period_end flag and cancel_at timestamp
            cancel_at_period_end_flag = subscription_data.get("cancel_at_period_end", False)
            cancel_at_timestamp = subscription_data.get("cancel_at")
            subscription.cancel_at_period_end = cancel_at_period_end_flag or (cancel_at_timestamp is not None)

            db.commit()
            return True

        return False

    @staticmethod
    def _handle_subscription_updated(db: Session, subscription_data: Dict) -> bool:
        """Handle subscription.updated webhook"""
        subscription_id = subscription_data.get("id")

        if not subscription_id:
            print(f"[WEBHOOK DEBUG] No subscription_id found in data")
            return False

        # Print ALL fields to debug
        print(f"[WEBHOOK DEBUG] Full subscription_data keys: {list(subscription_data.keys())}")
        print(f"[WEBHOOK DEBUG] cancel_at_period_end: {subscription_data.get('cancel_at_period_end')}")
        print(f"[WEBHOOK DEBUG] cancel_at: {subscription_data.get('cancel_at')}")
        print(f"[WEBHOOK DEBUG] canceled_at: {subscription_data.get('canceled_at')}")
        print(f"[WEBHOOK DEBUG] cancellation_details: {subscription_data.get('cancellation_details')}")

        subscription = db.query(Subscription).filter(
            Subscription.stripe_subscription_id == subscription_id
        ).first()

        if subscription:
            # Stripe uses EITHER cancel_at_period_end OR cancel_at timestamp
            # If cancel_at exists (timestamp), subscription is scheduled to cancel
            cancel_at_period_end_flag = subscription_data.get("cancel_at_period_end", False)
            cancel_at_timestamp = subscription_data.get("cancel_at")

            # Subscription is scheduled to cancel if EITHER field indicates it
            is_canceling = cancel_at_period_end_flag or (cancel_at_timestamp is not None)

            status = subscription_data.get("status", "active")

            print(f"[WEBHOOK DEBUG] Subscription {subscription_id}")
            print(f"[WEBHOOK DEBUG] - cancel_at_period_end flag: {cancel_at_period_end_flag}")
            print(f"[WEBHOOK DEBUG] - cancel_at timestamp: {cancel_at_timestamp}")
            print(f"[WEBHOOK DEBUG] - CALCULATED is_canceling: {is_canceling}")
            print(f"[WEBHOOK DEBUG] - status: {status}")

            subscription.status = SubscriptionStatus(status)

            # Handle timestamps safely
            if subscription_data.get("current_period_start"):
                subscription.current_period_start = datetime.fromtimestamp(subscription_data["current_period_start"])
            if subscription_data.get("current_period_end"):
                subscription.current_period_end = datetime.fromtimestamp(subscription_data["current_period_end"])

            # Set cancel_at_period_end based on either flag OR cancel_at timestamp
            subscription.cancel_at_period_end = is_canceling
            db.commit()

            print(f"[WEBHOOK DEBUG] After commit - cancel_at_period_end: {subscription.cancel_at_period_end}")
            return True

        print(f"[WEBHOOK DEBUG] No subscription found in DB with stripe_subscription_id: {subscription_id}")
        return False

    @staticmethod
    def _handle_subscription_deleted(db: Session, subscription_data: Dict) -> bool:
        """Handle subscription.deleted webhook"""
        subscription_id = subscription_data["id"]

        subscription = db.query(Subscription).filter(
            Subscription.stripe_subscription_id == subscription_id
        ).first()

        if subscription:
            subscription.status = SubscriptionStatus.CANCELED
            db.commit()
            return True

        return False

    @staticmethod
    def _handle_invoice_paid(db: Session, invoice_data: Dict) -> bool:
        """Handle invoice.paid webhook"""
        customer_id = invoice_data["customer"]
        subscription_id = invoice_data.get("subscription")

        if subscription_id:
            subscription = db.query(Subscription).filter(
                Subscription.stripe_subscription_id == subscription_id
            ).first()

            if subscription and subscription.status != SubscriptionStatus.ACTIVE:
                subscription.status = SubscriptionStatus.ACTIVE
                db.commit()
                return True

        return True

    @staticmethod
    def _handle_payment_failed(db: Session, invoice_data: Dict) -> bool:
        """Handle invoice.payment_failed webhook"""
        subscription_id = invoice_data.get("subscription")

        if subscription_id:
            subscription = db.query(Subscription).filter(
                Subscription.stripe_subscription_id == subscription_id
            ).first()

            if subscription:
                subscription.status = SubscriptionStatus.PAST_DUE
                db.commit()
                return True

        return True
