"""
Reusable dependencies for FastAPI routes

These dependencies can be used across multiple projects to enforce
usage limits and subscription checks.
"""

from fastapi import Depends, HTTPException, status
from sqlalchemy.orm import Session

from .database import get_db
from .auth import verify_token
from .models import User
from . import crud


async def get_current_user_with_usage_check(
    current_user: User = Depends(verify_token),
    db: Session = Depends(get_db)
) -> User:
    """
    Dependency that checks if user can perform an action based on usage limits

    This should be used on endpoints that consume user quota (like conversions).
    Returns the current user if they can proceed, raises HTTP exception otherwise.

    Usage:
        @router.post("/some-action")
        async def some_action(user: User = Depends(get_current_user_with_usage_check)):
            # Your logic here
            pass
    """
    if not crud.user_can_convert(db, current_user.id):
        # Get usage stats for error message
        stats = crud.get_user_usage_stats(db, current_user.id)

        raise HTTPException(
            status_code=status.HTTP_402_PAYMENT_REQUIRED,
            detail={
                "message": "You have reached your free conversion limit. Please subscribe to continue.",
                "conversions_used": stats["conversions_used"],
                "conversions_limit": stats["conversions_limit"],
                "has_active_subscription": stats["has_active_subscription"]
            }
        )

    return current_user


async def get_current_user_subscription_required(
    current_user: User = Depends(verify_token),
    db: Session = Depends(get_db)
) -> User:
    """
    Dependency that requires an active subscription

    Use this for premium-only features that require a subscription
    regardless of usage count.

    Usage:
        @router.get("/premium-feature")
        async def premium_feature(user: User = Depends(get_current_user_subscription_required)):
            # Your premium logic here
            pass
    """
    if not crud.user_has_active_subscription(db, current_user.id):
        raise HTTPException(
            status_code=status.HTTP_402_PAYMENT_REQUIRED,
            detail="This feature requires an active subscription."
        )

    return current_user
