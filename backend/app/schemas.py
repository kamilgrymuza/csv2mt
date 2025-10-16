from pydantic import BaseModel, EmailStr
from datetime import datetime
from typing import Optional
from .models import SubscriptionStatus


class UserBase(BaseModel):
    email: EmailStr
    first_name: Optional[str] = None
    last_name: Optional[str] = None


class UserCreate(UserBase):
    clerk_id: str


class UserUpdate(UserBase):
    pass


class User(UserBase):
    id: int
    clerk_id: str
    is_active: bool
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class HealthCheck(BaseModel):
    status: str
    timestamp: datetime


# Subscription Schemas
class SubscriptionBase(BaseModel):
    stripe_customer_id: Optional[str] = None
    stripe_subscription_id: Optional[str] = None
    status: Optional[SubscriptionStatus] = None


class SubscriptionCreate(SubscriptionBase):
    user_id: int


class Subscription(SubscriptionBase):
    id: int
    user_id: int
    stripe_price_id: Optional[str] = None
    current_period_start: Optional[datetime] = None
    current_period_end: Optional[datetime] = None
    cancel_at_period_end: bool = False
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class SubscriptionStatusResponse(BaseModel):
    """Response for user subscription status check"""
    has_active_subscription: bool
    status: Optional[SubscriptionStatus] = None
    conversions_used: int
    conversions_limit: Optional[int] = None
    can_convert: bool
    cancel_at_period_end: Optional[bool] = None
    current_period_end: Optional[datetime] = None


class CheckoutSessionRequest(BaseModel):
    """Request to create a Stripe Checkout Session"""
    price_id: Optional[str] = None  # Optional, falls back to config


class CheckoutSessionResponse(BaseModel):
    """Response containing Stripe Checkout Session URL"""
    session_id: str
    url: str


# Conversion Usage Schemas
class ConversionUsageCreate(BaseModel):
    user_id: int
    file_name: Optional[str] = None
    bank_name: Optional[str] = None
    input_tokens: Optional[int] = None
    output_tokens: Optional[int] = None


class ConversionUsage(ConversionUsageCreate):
    id: int
    conversion_date: datetime

    class Config:
        from_attributes = True