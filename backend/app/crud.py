from sqlalchemy.orm import Session
from sqlalchemy import func, extract
from datetime import datetime, timezone
from typing import Optional
from . import models, schemas
from .config import settings


# User CRUD Operations
def get_user(db: Session, user_id: int):
    return db.query(models.User).filter(models.User.id == user_id).first()


def get_user_by_clerk_id(db: Session, clerk_id: str):
    return db.query(models.User).filter(models.User.clerk_id == clerk_id).first()


def get_user_by_email(db: Session, email: str):
    return db.query(models.User).filter(models.User.email == email).first()


def get_users(db: Session, skip: int = 0, limit: int = 100):
    return db.query(models.User).offset(skip).limit(limit).all()


def create_user(db: Session, user: schemas.UserCreate):
    db_user = models.User(
        clerk_id=user.clerk_id,
        email=user.email,
        first_name=user.first_name,
        last_name=user.last_name
    )
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user


def update_user(db: Session, user_id: int, user: schemas.UserUpdate):
    db_user = db.query(models.User).filter(models.User.id == user_id).first()
    if db_user:
        for key, value in user.dict(exclude_unset=True).items():
            setattr(db_user, key, value)
        db.commit()
        db.refresh(db_user)
    return db_user


def delete_user(db: Session, user_id: int):
    db_user = db.query(models.User).filter(models.User.id == user_id).first()
    if db_user:
        db.delete(db_user)
        db.commit()
    return db_user


# Subscription CRUD Operations
def get_subscription_by_user_id(db: Session, user_id: int) -> Optional[models.Subscription]:
    """Get subscription for a user"""
    return db.query(models.Subscription).filter(
        models.Subscription.user_id == user_id
    ).first()


def get_subscription_by_stripe_customer_id(db: Session, customer_id: str) -> Optional[models.Subscription]:
    """Get subscription by Stripe customer ID"""
    return db.query(models.Subscription).filter(
        models.Subscription.stripe_customer_id == customer_id
    ).first()


def create_subscription(db: Session, subscription: schemas.SubscriptionCreate) -> models.Subscription:
    """Create a new subscription"""
    db_subscription = models.Subscription(**subscription.dict())
    db.add(db_subscription)
    db.commit()
    db.refresh(db_subscription)
    return db_subscription


def user_has_active_subscription(db: Session, user_id: int) -> bool:
    """Check if user has an active subscription"""
    subscription = get_subscription_by_user_id(db, user_id)
    if not subscription:
        return False

    return subscription.status == models.SubscriptionStatus.ACTIVE


# Conversion Usage CRUD Operations
def create_conversion_usage(db: Session, usage: schemas.ConversionUsageCreate) -> models.ConversionUsage:
    """Record a conversion usage"""
    db_usage = models.ConversionUsage(**usage.dict())
    db.add(db_usage)
    db.commit()
    db.refresh(db_usage)
    return db_usage


def get_user_monthly_conversions(db: Session, user_id: int, subscription: Optional[models.Subscription] = None) -> int:
    """
    Get the number of conversions for the current period.

    For Premium users: Counts conversions within current billing period (current_period_start to current_period_end)
    For Free users: Counts conversions within current calendar month
    """
    # If user has active subscription with billing period dates, use those
    if subscription and subscription.status == models.SubscriptionStatus.ACTIVE and subscription.current_period_start and subscription.current_period_end:
        # Count conversions within current billing period
        count = db.query(func.count(models.ConversionUsage.id)).filter(
            models.ConversionUsage.user_id == user_id,
            models.ConversionUsage.conversion_date >= subscription.current_period_start,
            models.ConversionUsage.conversion_date < subscription.current_period_end
        ).scalar()
    else:
        # Free users: count conversions in current calendar month
        now = datetime.now(timezone.utc)
        current_month = now.month
        current_year = now.year

        count = db.query(func.count(models.ConversionUsage.id)).filter(
            models.ConversionUsage.user_id == user_id,
            extract('month', models.ConversionUsage.conversion_date) == current_month,
            extract('year', models.ConversionUsage.conversion_date) == current_year
        ).scalar()

    return count or 0


def user_can_convert(db: Session, user_id: int) -> bool:
    """
    Check if user can perform a conversion based on:
    1. Active subscription (100 per billing period)
    2. Free tier limit (5 per calendar month)
    """
    subscription = get_subscription_by_user_id(db, user_id)
    monthly_conversions = get_user_monthly_conversions(db, user_id, subscription)

    # Check if user has active subscription
    if user_has_active_subscription(db, user_id):
        # Premium users get 100 conversions per billing period
        return monthly_conversions < settings.premium_conversion_limit

    # Check free tier limit
    return monthly_conversions < settings.free_conversion_limit


def get_user_usage_stats(db: Session, user_id: int) -> dict:
    """Get user usage statistics"""
    from .services.stripe_service import StripeService

    subscription = get_subscription_by_user_id(db, user_id)
    has_subscription = user_has_active_subscription(db, user_id)

    # If subscription exists but missing period dates, sync from Stripe
    if subscription and subscription.status == models.SubscriptionStatus.ACTIVE:
        if not subscription.current_period_start or not subscription.current_period_end:
            # Try to sync from Stripe API
            StripeService.sync_subscription_from_stripe(db, subscription)
            # Refresh subscription object after sync
            db.refresh(subscription)

    conversions_used = get_user_monthly_conversions(db, user_id, subscription)

    # Set limit based on subscription status
    if has_subscription:
        conversions_limit = settings.premium_conversion_limit
        # Premium users: limit resets at end of billing period
        limit_reset_date = subscription.current_period_end if subscription else None
    else:
        conversions_limit = settings.free_conversion_limit
        # Free users: limit resets on 1st of next month
        now = datetime.now(timezone.utc)
        if now.month == 12:
            # December -> January next year
            limit_reset_date = datetime(now.year + 1, 1, 1, 0, 0, 0, tzinfo=timezone.utc)
        else:
            # Next month, same year
            limit_reset_date = datetime(now.year, now.month + 1, 1, 0, 0, 0, tzinfo=timezone.utc)

    return {
        "has_active_subscription": has_subscription,
        "status": subscription.status if subscription else None,
        "conversions_used": conversions_used,
        "conversions_limit": conversions_limit,
        "can_convert": user_can_convert(db, user_id),
        "cancel_at_period_end": subscription.cancel_at_period_end if subscription else None,
        "current_period_end": subscription.current_period_end if subscription else None,
        "limit_reset_date": limit_reset_date
    }