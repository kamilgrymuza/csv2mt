# Quick Reference Card - Stripe Subscription System

## 🚀 Quick Start

```bash
# 1. Get Stripe keys from dashboard.stripe.com
# 2. Add to backend/.env
# 3. Run migration
docker-compose exec backend alembic upgrade head

# 4. Start backend
docker-compose up -d

# 5. Start frontend
# Services start via docker-compose

# 6. Start Stripe webhook listener (separate terminal)
stripe listen --forward-to http://localhost:8000/subscription/webhook
```

## 📝 Environment Variables Template

```bash
# Backend .env
STRIPE_SECRET_KEY=sk_test_...
STRIPE_PUBLISHABLE_KEY=pk_test_...
STRIPE_WEBHOOK_SECRET=whsec_...
STRIPE_PRICE_ID=price_...
FREE_CONVERSION_LIMIT=5
FRONTEND_URL=http://localhost:3000
```

## 🔑 Test Credit Card

```
Card: 4242 4242 4242 4242
Expiry: 12/34 (any future date)
CVC: 123 (any 3 digits)
ZIP: 12345 (any 5 digits)
```

## 📚 API Endpoints

```bash
# Get subscription status
GET /subscription/status
Headers: Authorization: Bearer {clerk_token}

# Create checkout session (upgrade)
POST /subscription/create-checkout-session
Headers: Authorization: Bearer {clerk_token}
Body: {}

# Create portal session (manage)
POST /subscription/create-portal-session
Headers: Authorization: Bearer {clerk_token}
Body: {}

# Webhook (no auth)
POST /subscription/webhook
Headers: stripe-signature: {signature}
```

## 🗄️ Database Tables

```sql
-- Check subscription
SELECT * FROM subscriptions WHERE user_id = 1;

-- Check usage
SELECT COUNT(*) FROM conversion_usage
WHERE user_id = 1
AND EXTRACT(MONTH FROM conversion_date) = EXTRACT(MONTH FROM NOW());

-- Reset usage (for testing)
DELETE FROM conversion_usage WHERE user_id = 1;
```

## 🔧 Common Customizations

### Change pricing:
1. Update Stripe product price
2. Update `STRIPE_PRICE_ID` in .env
3. Update frontend display in `SubscriptionPage.tsx`

### Change free limit:
```python
# backend/app/config.py
free_conversion_limit: int = 10  # Change from 5 to 10
```

### Rename "conversion" to your action:
1. Rename `ConversionUsage` model
2. Update CRUD function names
3. Update usage tracking endpoint
4. Update frontend terminology

## 🐛 Troubleshooting Commands

```bash
# Check Stripe CLI is working
stripe --version

# Listen for webhooks
stripe listen --forward-to http://localhost:8000/subscription/webhook

# Trigger test webhook
stripe trigger customer.subscription.created

# Check backend logs
tail -f backend/logs/app.log

# Check database
docker-compose exec postgres psql -U user -d micro_saas_db -c "SELECT * FROM subscriptions;"

# Reset Stripe test data
# Go to: https://dashboard.stripe.com/test/developers
# Click "Delete all test data"
```

## 📱 Frontend Routes

```
/ - Home page
/sign-in - Sign in page
/sign-up - Sign up page
/convert - Main converter (requires auth)
/subscription - Subscription management (requires auth)
/dashboard - User dashboard (requires auth)
```

## 🔐 Access Control Patterns

```python
# Option 1: Check usage limits
@router.post("/action")
async def action(
    user: User = Depends(get_current_user_with_usage_check)
):
    # User can only proceed if under limit or subscribed
    pass

# Option 2: Require active subscription
@router.post("/premium-feature")
async def premium(
    user: User = Depends(get_current_user_subscription_required)
):
    # User must be subscribed
    pass

# Option 3: Just require auth
@router.get("/profile")
async def profile(
    user: User = Depends(verify_token)
):
    # Any authenticated user
    pass
```

## 📊 Usage Tracking Pattern

```python
# Track usage after successful action
usage = ConversionUsageCreate(
    user_id=current_user.id,
    # Add any metadata you want to track
)
crud.create_conversion_usage(db, usage)
```

## 🎨 Frontend Usage Display

```tsx
// Fetch subscription status
const { data: status } = useQuery({
  queryKey: ['subscriptionStatus'],
  queryFn: async () => {
    const token = await getToken()
    const response = await axios.get(
      `${API_URL}/subscription/status`,
      { headers: { Authorization: `Bearer ${token}` }}
    )
    return response.data
  }
})

// Display usage
{status.has_active_subscription ? (
  <div>Premium - Unlimited</div>
) : (
  <div>{status.conversions_used} / {status.conversions_limit}</div>
)}
```

## 🔄 Stripe Webhook Events

```
✅ customer.subscription.created - New subscription
✅ customer.subscription.updated - Subscription changed
✅ customer.subscription.deleted - Subscription canceled
✅ invoice.paid - Payment successful
✅ invoice.payment_failed - Payment failed
```

## 📦 Key Files to Customize

```bash
# Backend (Keep mostly as-is):
backend/app/services/stripe_service.py  # ✅ Reusable
backend/app/dependencies.py             # ✅ Reusable
backend/app/routers/subscription.py     # ✅ Reusable

# Backend (Customize for your app):
backend/app/routers/conversion.py       # 🔧 Rename/modify
backend/app/models.py                   # 🔧 Add your models
backend/app/config.py                   # 🔧 Add your settings

# Frontend (Keep mostly as-is):
frontend/src/pages/SubscriptionPage.tsx # ✅ Just update text

# Frontend (Customize for your app):
frontend/src/pages/SimpleConverter.tsx  # 🔧 Replace with your app
```

## 🎯 Testing Checklist

```bash
✅ Sign up new user
✅ Make conversion → usage tracked
✅ Make 5 conversions → blocked at 6
✅ Upgrade → redirected to Stripe
✅ Complete payment → webhook received
✅ Subscription status updated → unlimited access
✅ Open portal → can manage subscription
✅ Cancel subscription → status updated
```

## 📞 Support Links

- **Stripe Dashboard**: https://dashboard.stripe.com
- **Stripe Docs**: https://stripe.com/docs
- **Webhook Logs**: https://dashboard.stripe.com/test/webhooks
- **Test Cards**: https://stripe.com/docs/testing

## 💾 Backup Commands

```bash
# Backup database
pg_dump your_db > backup.sql

# Restore database
psql your_db < backup.sql

# Export Stripe data
# (Do this from Stripe Dashboard > Data > Export)
```

## 🚀 Deploy to Production Checklist

```bash
✅ Switch to Stripe live keys
✅ Update STRIPE_WEBHOOK_SECRET with live webhook
✅ Update FRONTEND_URL to production domain
✅ Set webhook URL to https://your-domain.com/subscription/webhook
✅ Test webhook in production
✅ Test full subscription flow
✅ Set up error monitoring
✅ Configure email receipts in Stripe
✅ Test cancellation flow
✅ Monitor Stripe dashboard for issues
```

## 📖 Documentation Hierarchy

1. **`QUICK_REFERENCE.md`** ← You are here (cheat sheet)
2. **`SETUP_STRIPE_GUIDE.md`** ← First-time setup
3. **`SUBSCRIPTION_ARCHITECTURE.md`** ← Deep dive
4. **`REUSABLE_TEMPLATE_GUIDE.md`** ← For future projects
5. **`STRIPE_IMPLEMENTATION_SUMMARY.md`** ← Overview

## 🎓 Learn More

```bash
# Stripe Testing
https://stripe.com/docs/testing

# Stripe Webhooks
https://stripe.com/docs/webhooks/best-practices

# FastAPI Depends
https://fastapi.tiangolo.com/tutorial/dependencies/

# SQLAlchemy Relationships
https://docs.sqlalchemy.org/en/14/orm/basic_relationships.html
```

---

**Pro Tip**: Bookmark this page and keep it open while developing! 🔖
