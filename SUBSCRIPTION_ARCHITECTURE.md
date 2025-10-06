# Stripe Subscription Architecture

## Overview

This document describes the reusable Stripe subscription system integrated with Clerk authentication. This architecture implements:

- ✅ Usage limits (5 free conversions per month)
- ✅ Stripe subscription management ($4.99/month premium plan)
- ✅ Automatic webhook handling for subscription updates
- ✅ Frontend subscription UI with usage tracking
- ✅ Middleware-based access control

## Architecture Diagram

```
┌─────────────────────┐
│   User (Frontend)   │
└──────────┬──────────┘
           │
           │ 1. Makes conversion request
           ▼
┌─────────────────────────────────────┐
│  FastAPI Backend                    │
│  ┌───────────────────────────────┐ │
│  │ Dependencies Middleware       │ │
│  │ - get_current_user_with_usage │ │
│  │   _check()                    │ │
│  │ - Checks subscription status  │ │
│  │ - Checks usage limits         │ │
│  └──────────┬────────────────────┘ │
│             │                       │
│             ▼                       │
│  ┌───────────────────────────────┐ │
│  │ Conversion Router             │ │
│  │ - Tracks usage                │ │
│  │ - Returns converted file      │ │
│  └───────────────────────────────┘ │
└─────────────────────────────────────┘
           │
           │ 2. Usage tracked in DB
           ▼
┌─────────────────────────────────────┐
│  PostgreSQL Database                │
│  - users                            │
│  - subscriptions                    │
│  - conversion_usage                 │
└─────────────────────────────────────┘

┌─────────────────────────────────────┐
│  Stripe (External)                  │
│  ┌───────────────────────────────┐ │
│  │ Checkout Session              │ │
│  │ - Payment processing          │ │
│  └──────────┬────────────────────┘ │
│             │ Webhook events        │
│             ▼                       │
│  ┌───────────────────────────────┐ │
│  │ Webhook Handler               │ │
│  │ - subscription.created        │ │
│  │ - subscription.updated        │ │
│  │ - invoice.paid                │ │
│  └───────────────────────────────┘ │
└─────────────────────────────────────┘
```

## Database Models

### User Model
```python
class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    clerk_id = Column(String, unique=True, index=True, nullable=False)
    email = Column(String, unique=True, index=True, nullable=False)
    first_name = Column(String)
    last_name = Column(String)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Relationships
    subscription = relationship("Subscription", back_populates="user", uselist=False)
    conversions = relationship("ConversionUsage", back_populates="user")
```

### Subscription Model
```python
class Subscription(Base):
    __tablename__ = "subscriptions"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, unique=True)

    # Stripe identifiers
    stripe_customer_id = Column(String, unique=True, index=True, nullable=True)
    stripe_subscription_id = Column(String, unique=True, index=True, nullable=True)
    stripe_price_id = Column(String, nullable=True)

    # Subscription details
    status = Column(SQLEnum(SubscriptionStatus), default=None, nullable=True)
    current_period_start = Column(DateTime(timezone=True), nullable=True)
    current_period_end = Column(DateTime(timezone=True), nullable=True)
    cancel_at_period_end = Column(Boolean, default=False)
```

### ConversionUsage Model
```python
class ConversionUsage(Base):
    __tablename__ = "conversion_usage"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    file_name = Column(String, nullable=True)
    bank_name = Column(String, nullable=True)
    conversion_date = Column(DateTime(timezone=True), server_default=func.now(), index=True)
```

## Backend Components

### 1. Configuration (`app/config.py`)
```python
class Settings(BaseSettings):
    # Stripe configuration
    stripe_secret_key: Optional[str] = None
    stripe_publishable_key: Optional[str] = None
    stripe_webhook_secret: Optional[str] = None
    stripe_price_id: Optional[str] = None

    # Subscription limits
    free_conversion_limit: int = 5

    # Application URL for Stripe redirects
    frontend_url: str = "http://localhost:3000"
```

### 2. Stripe Service (`app/services/stripe_service.py`)

**Reusable service class** that handles all Stripe operations:

- `create_customer()` - Create Stripe customer
- `create_checkout_session()` - Start subscription checkout
- `create_portal_session()` - Customer subscription management portal
- `handle_webhook_event()` - Process Stripe webhooks
- Private methods for specific webhook events

### 3. CRUD Operations (`app/crud.py`)

**Reusable helper functions:**

- `user_can_convert()` - Check if user can perform action
- `get_user_monthly_conversions()` - Get current month usage
- `user_has_active_subscription()` - Check subscription status
- `get_user_usage_stats()` - Get comprehensive usage data
- `create_conversion_usage()` - Track usage

### 4. Dependencies (`app/dependencies.py`)

**Reusable middleware:**

```python
async def get_current_user_with_usage_check(
    current_user: User = Depends(verify_token),
    db: Session = Depends(get_db)
) -> User:
    """Check usage limits before allowing action"""
    if not crud.user_can_convert(db, current_user.id):
        raise HTTPException(status_code=402, detail="Limit reached")
    return current_user
```

### 5. Subscription Router (`app/routers/subscription.py`)

API Endpoints:
- `GET /subscription/status` - Get user's subscription status and usage
- `POST /subscription/create-checkout-session` - Create Stripe Checkout session
- `POST /subscription/create-portal-session` - Create portal session for managing subscription
- `POST /subscription/webhook` - Handle Stripe webhooks (no auth required)

## Frontend Components

### 1. Subscription Page (`frontend/src/pages/SubscriptionPage.tsx`)

Full-featured subscription management UI:
- Current plan display (Free vs Premium)
- Usage statistics with progress bar
- Upgrade flow (redirects to Stripe Checkout)
- Manage subscription (redirects to Stripe Customer Portal)
- Success/cancel handling after Stripe redirect

### 2. Simple Converter with Usage Display (`frontend/src/pages/SimpleConverter.tsx`)

Enhanced converter with:
- Real-time usage tracking display
- Usage limit enforcement
- Subscription status indicator
- Upgrade prompts when limit reached
- Auto-refresh after conversion to update usage

## Usage Flow

### Free Tier Flow

1. User signs up with Clerk
2. User record created in database (via `auth.py`)
3. User can perform up to 5 conversions per month
4. Each conversion tracked in `conversion_usage` table
5. After 5 conversions, middleware blocks further requests with 402 status
6. Frontend prompts user to upgrade

### Upgrade Flow

1. User clicks "Upgrade to Premium" button
2. Frontend calls `/subscription/create-checkout-session`
3. Backend creates Stripe Checkout Session
4. User redirected to Stripe checkout page
5. User completes payment
6. Stripe sends `customer.subscription.created` webhook
7. Backend updates database with subscription status
8. User redirected back to app with `?success=true`
9. User now has unlimited conversions

### Webhook Flow

Stripe sends webhooks for subscription lifecycle events:

- `customer.subscription.created` - New subscription started
- `customer.subscription.updated` - Subscription modified
- `customer.subscription.deleted` - Subscription canceled
- `invoice.paid` - Payment successful
- `invoice.payment_failed` - Payment failed

All webhooks are processed by `StripeService.handle_webhook_event()` which updates the local database.

## Setup Instructions for New Projects

### 1. Backend Setup

1. **Copy files to new project:**
   ```
   app/services/stripe_service.py
   app/dependencies.py
   app/routers/subscription.py
   ```

2. **Update `models.py`:**
   - Copy `Subscription`, `ConversionUsage`, and `SubscriptionStatus` models
   - Add relationships to your `User` model

3. **Update `schemas.py`:**
   - Copy subscription-related schemas

4. **Update `crud.py`:**
   - Copy subscription and usage CRUD functions

5. **Update `config.py`:**
   - Add Stripe configuration fields

6. **Update `main.py`:**
   - Include subscription router

7. **Add dependencies:**
   ```bash
   pip install stripe>=7.0.0
   ```

8. **Create database migration:**
   ```bash
   alembic revision --autogenerate -m "Add subscription models"
   alembic upgrade head
   ```

9. **Set environment variables:**
   ```env
   STRIPE_SECRET_KEY=sk_test_...
   STRIPE_PUBLISHABLE_KEY=pk_test_...
   STRIPE_WEBHOOK_SECRET=whsec_...
   STRIPE_PRICE_ID=price_...
   FREE_CONVERSION_LIMIT=5
   FRONTEND_URL=http://localhost:3000
   ```

### 2. Frontend Setup

1. **Copy files:**
   ```
   src/pages/SubscriptionPage.tsx
   ```

2. **Update App.tsx:**
   - Add `/subscription` route

3. **Update your action component:**
   - Fetch subscription status with `/subscription/status`
   - Check `can_convert` before allowing actions
   - Display usage stats
   - Add upgrade prompts

4. **Add Stripe publishable key to `.env`:**
   ```env
   VITE_STRIPE_PUBLISHABLE_KEY=pk_test_...
   ```

### 3. Stripe Dashboard Setup

1. **Create a Product:**
   - Go to Products in Stripe Dashboard
   - Create new product (e.g., "Premium Subscription")
   - Add pricing: $4.99/month recurring

2. **Copy Price ID:**
   - Get the Price ID (starts with `price_`)
   - Add to `STRIPE_PRICE_ID` environment variable

3. **Set up Webhooks:**
   - Go to Developers → Webhooks
   - Add endpoint: `https://your-domain.com/subscription/webhook`
   - Select events:
     - `customer.subscription.created`
     - `customer.subscription.updated`
     - `customer.subscription.deleted`
     - `invoice.paid`
     - `invoice.payment_failed`
   - Copy webhook secret to `STRIPE_WEBHOOK_SECRET`

4. **Test in test mode:**
   - Use test credit card: `4242 4242 4242 4242`
   - Any future expiry date
   - Any CVC

## Customization

### Change Pricing

1. Update Stripe Product pricing
2. Update Price ID in environment variables
3. Update frontend display in `SubscriptionPage.tsx`

### Change Usage Limits

Update `FREE_CONVERSION_LIMIT` in environment variables or `config.py`

### Add More Tiers

1. Create additional Price IDs in Stripe
2. Update frontend to show multiple tiers
3. Pass desired `price_id` to `create_checkout_session`

### Track Different Actions

Replace `ConversionUsage` with your own usage tracking model:
- Update model name and fields
- Update CRUD functions
- Update usage check logic in `dependencies.py`

## Security Considerations

1. **Webhook Signature Verification:** Always verify Stripe webhook signatures
2. **Authentication:** All subscription endpoints (except webhook) require Clerk authentication
3. **Usage Checks:** Middleware enforces limits before processing requests
4. **Idempotency:** Webhook handlers should be idempotent

## Testing

### Test Free Tier
1. Create new user
2. Make 5 conversions
3. Verify 6th conversion is blocked

### Test Upgrade Flow
1. Click upgrade button
2. Complete Stripe checkout with test card
3. Verify subscription status updates
4. Verify unlimited conversions work

### Test Webhooks
Use Stripe CLI:
```bash
stripe listen --forward-to localhost:8000/subscription/webhook
stripe trigger customer.subscription.created
```

## Troubleshooting

### Webhook not receiving events
- Check webhook URL is publicly accessible
- Verify webhook secret matches Stripe dashboard
- Check Stripe dashboard webhook logs

### Subscription not updating
- Check webhook events are being received
- Check database for subscription record
- Verify Stripe customer ID matches

### Usage not tracking
- Verify conversion endpoint is called
- Check `conversion_usage` table
- Ensure user_id is correct

## Production Checklist

- [ ] Switch from Stripe test keys to live keys
- [ ] Update webhook endpoint to production URL
- [ ] Set up proper error monitoring
- [ ] Configure Stripe email receipts
- [ ] Set up proper logging
- [ ] Test all webhook events in production
- [ ] Set up billing alerts in Stripe dashboard
- [ ] Document cancellation policy for users

## Future Enhancements

- Add annual billing option
- Implement usage-based pricing
- Add team/organization subscriptions
- Implement proration for upgrades/downgrades
- Add invoice history page
- Implement referral system
- Add subscription pause/resume functionality
