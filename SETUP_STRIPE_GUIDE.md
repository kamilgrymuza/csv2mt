# Quick Setup Guide: Stripe Subscription Integration

This guide will help you get the Stripe subscription system up and running with Docker.

## Prerequisites

- Docker and Docker Compose installed
- Stripe account (free to create at https://stripe.com)
- Clerk account with user authentication working

## Step 1: Get Stripe API Keys

1. Go to https://dashboard.stripe.com/
2. Click **Developers** in the left sidebar
3. Click **API keys**
4. Copy your **Publishable key** and **Secret key** (use test mode keys for development)

## Step 2: Create Stripe Product & Price

1. In Stripe Dashboard, go to **Products**
2. Click **+ Add product**
3. Fill in:
   - **Name:** Premium Subscription (or your product name)
   - **Description:** Unlimited conversions and premium features
   - **Pricing:**
     - Type: Recurring
     - Price: $4.99 USD
     - Billing period: Monthly
4. Click **Save product**
5. **Copy the Price ID** (starts with `price_`) - you'll need this!

## Step 3: Set up Stripe Webhooks (Development)

### For local development with Stripe CLI:

1. Install Stripe CLI on your **host machine** (not in Docker):
   ```bash
   # macOS
   brew install stripe/stripe-cli/stripe

   # Windows
   scoop bucket add stripe https://github.com/stripe/scoop-stripe-cli.git
   scoop install stripe

   # Linux
   # Download from https://github.com/stripe/stripe-cli/releases/latest
   ```

2. Login to Stripe CLI:
   ```bash
   stripe login
   ```

3. Start webhook forwarding (in a separate terminal):
   ```bash
   stripe listen --forward-to http://localhost:8000/subscription/webhook
   ```

4. Copy the webhook secret (starts with `whsec_`) that appears in the terminal

### For production:

1. In Stripe Dashboard, go to **Developers** → **Webhooks**
2. Click **+ Add endpoint**
3. Enter your endpoint URL: `https://your-domain.com/subscription/webhook`
4. Select these events:
   - `customer.subscription.created`
   - `customer.subscription.updated`
   - `customer.subscription.deleted`
   - `invoice.paid`
   - `invoice.payment_failed`
5. Click **Add endpoint**
6. Copy the **Signing secret**

## Step 4: Configure Environment Variables

### Root Directory (.env file):

Create a `.env` file in the **root directory** (where `docker-compose.yml` is located):

```bash
# Clerk Keys
CLERK_SECRET_KEY=sk_test_...
CLERK_PUBLISHABLE_KEY=pk_test_...

# Stripe Keys (from Step 1)
STRIPE_SECRET_KEY=sk_test_51...
STRIPE_PUBLISHABLE_KEY=pk_test_51...
STRIPE_WEBHOOK_SECRET=whsec_...  # From Step 3
STRIPE_PRICE_ID=price_...  # From Step 2

# Subscription settings
FREE_CONVERSION_LIMIT=5
FRONTEND_URL=http://localhost:3000
```

### Backend Directory (backend/.env file):

Create `backend/.env` with full configuration:

```bash
# Database (matches docker-compose.yml)
DATABASE_URL=postgresql://user:password@postgres:5432/micro_saas_db

# App
SECRET_KEY=your-secret-key-change-in-production
ENVIRONMENT=development

# Clerk
CLERK_SECRET_KEY=sk_test_...
CLERK_PUBLISHABLE_KEY=pk_test_...

# Stripe (from Step 1)
STRIPE_SECRET_KEY=sk_test_51...
STRIPE_PUBLISHABLE_KEY=pk_test_51...
STRIPE_WEBHOOK_SECRET=whsec_...  # From Step 3
STRIPE_PRICE_ID=price_...  # From Step 2

# Subscription settings
FREE_CONVERSION_LIMIT=5
FRONTEND_URL=http://localhost:3000
```

### Frontend Directory (frontend/.env file):

Create `frontend/.env`:

```bash
VITE_API_URL=http://localhost:8000
VITE_CLERK_PUBLISHABLE_KEY=pk_test_...
VITE_STRIPE_PUBLISHABLE_KEY=pk_test_51...  # From Step 1
```

## Step 5: Start Docker Containers

```bash
# Start all services (postgres, backend, frontend)
docker-compose up -d

# View logs (optional)
docker-compose logs -f
```

This will start:
- PostgreSQL database on port 5432
- Backend API on port 8000
- Frontend on port 3000

## Step 6: Run Database Migration

Run the migration **inside the backend container**:

```bash
# Run Alembic migration
docker-compose exec backend alembic upgrade head

# Verify migration succeeded
docker-compose exec backend alembic current
```

If you need to create a new migration (already done for you):
```bash
docker-compose exec backend alembic revision --autogenerate -m "Add subscription models"
```

## Step 7: Verify Services are Running

```bash
# Check all services are up
docker-compose ps

# Should show:
# - postgres (healthy)
# - backend (up)
# - frontend (up)
```

Test the endpoints:
```bash
# Test backend health
curl http://localhost:8000/health

# Test frontend
open http://localhost:3000
```

## Step 8: Start Stripe Webhook Listener

In a **separate terminal** on your host machine (not in Docker):

```bash
stripe listen --forward-to http://localhost:8000/subscription/webhook
```

Keep this terminal open while testing. You'll see webhook events appear here.

## Step 9: Test the Integration

### Test Free Tier:

1. Open browser to http://localhost:3000
2. Create a new account at http://localhost:3000/sign-up
3. Go to the converter at http://localhost:3000/convert
4. Check the sidebar - it should show "Free Plan" with "0 / 5" conversions
5. Make a conversion
6. Check that the counter increases to "1 / 5"

### Test Subscription:

1. Click "Subscription" in the top navigation
2. Click "Upgrade to Premium" button
3. You'll be redirected to Stripe Checkout
4. Use test card details:
   - Card number: `4242 4242 4242 4242`
   - Expiry: Any future date (e.g., 12/25)
   - CVC: Any 3 digits (e.g., 123)
   - ZIP: Any 5 digits (e.g., 12345)
5. Complete the payment
6. Watch the Stripe CLI terminal - you should see webhook events
7. You should be redirected back with a success message
8. Your plan should now show "Premium Plan" with "Unlimited Conversions"

### Test Usage Limit:

1. Sign out and create a new account
2. Make 5 conversions
3. Try to make a 6th conversion - it should be blocked with an error message
4. The frontend should prompt you to upgrade

## Useful Docker Commands

```bash
# View logs
docker-compose logs -f backend    # Backend logs
docker-compose logs -f frontend   # Frontend logs
docker-compose logs -f postgres   # Database logs

# Restart a service
docker-compose restart backend
docker-compose restart frontend

# Stop all services
docker-compose down

# Stop and remove volumes (CAUTION: deletes database data)
docker-compose down -v

# Rebuild containers (after code changes)
docker-compose up -d --build

# Access backend shell
docker-compose exec backend bash

# Access database shell
docker-compose exec postgres psql -U user -d micro_saas_db

# Run Python commands in backend
docker-compose exec backend python -c "from app.config import settings; print(settings.stripe_secret_key)"
```

## Database Commands (via Docker)

```bash
# Check subscriptions table
docker-compose exec postgres psql -U user -d micro_saas_db -c "SELECT * FROM subscriptions;"

# Check usage
docker-compose exec postgres psql -U user -d micro_saas_db -c "SELECT COUNT(*) FROM conversion_usage WHERE user_id = 1;"

# Check current month's usage for user
docker-compose exec postgres psql -U user -d micro_saas_db -c "
  SELECT COUNT(*) FROM conversion_usage
  WHERE user_id = 1
  AND EXTRACT(MONTH FROM conversion_date) = EXTRACT(MONTH FROM NOW());
"

# Reset usage for testing (replace user_id)
docker-compose exec postgres psql -U user -d micro_saas_db -c "DELETE FROM conversion_usage WHERE user_id = 1;"

# View all tables
docker-compose exec postgres psql -U user -d micro_saas_db -c "\dt"
```

## Troubleshooting

### "Services won't start"
```bash
# Check logs
docker-compose logs

# Ensure no port conflicts
lsof -i :3000  # Frontend
lsof -i :8000  # Backend
lsof -i :5432  # Postgres

# Rebuild from scratch
docker-compose down -v
docker-compose up -d --build
```

### "Webhook signature verification failed"
- Make sure `STRIPE_WEBHOOK_SECRET` in `backend/.env` matches the secret from Stripe CLI
- Check that Stripe CLI is running and forwarding to correct port
- Verify backend container can receive requests on port 8000

### "Stripe error: No such price"
- Verify `STRIPE_PRICE_ID` in `backend/.env` matches your Stripe product price ID exactly
- Make sure you're using the test mode price ID in development
- Check the backend logs: `docker-compose logs backend`

### "Conversions not being tracked"
```bash
# Check database
docker-compose exec postgres psql -U user -d micro_saas_db -c "SELECT * FROM conversion_usage;"

# Check backend logs
docker-compose logs backend | grep -i conversion

# Verify authentication token is being sent
docker-compose logs backend | grep -i authorization
```

### "Subscription status not updating after payment"
```bash
# Check if webhook was received
docker-compose logs backend | grep -i webhook

# Check Stripe CLI terminal for webhook events

# Check subscriptions table
docker-compose exec postgres psql -U user -d micro_saas_db -c "SELECT * FROM subscriptions;"

# Manually trigger webhook test
stripe trigger customer.subscription.created
```

### "Database connection failed"
```bash
# Check postgres is running
docker-compose ps postgres

# Check postgres health
docker-compose exec postgres pg_isready -U user

# Check DATABASE_URL in backend/.env
# Should be: postgresql://user:password@postgres:5432/micro_saas_db
# Note: Use 'postgres' as host (Docker service name), not 'localhost'
```

### "Module not found" errors
```bash
# Rebuild containers to install new dependencies
docker-compose up -d --build

# Or manually install in running container
docker-compose exec backend pip install -r requirements.txt
docker-compose exec frontend npm install
```

## Environment Variable Notes

**Important:** The backend container needs `DATABASE_URL` with host as `postgres` (Docker service name), not `localhost`:

```bash
# ✅ Correct (for Docker)
DATABASE_URL=postgresql://user:password@postgres:5432/micro_saas_db

# ❌ Wrong (this is for running directly on host)
DATABASE_URL=postgresql://user:password@localhost:5432/micro_saas_db
```

## Testing in Production

When ready to go live:

1. Switch to **Live mode** in Stripe Dashboard
2. Get your **live** API keys (without `_test_`)
3. Create a **live** webhook endpoint in Stripe Dashboard
4. Update all `.env` files with live keys
5. Update `FRONTEND_URL` to your production domain
6. **Test thoroughly before real payments!**

## Common Test Cards

Stripe provides test cards for different scenarios:

- **Success:** `4242 4242 4242 4242`
- **Payment declined:** `4000 0000 0000 0002`
- **Insufficient funds:** `4000 0000 0000 9995`
- **3D Secure authentication:** `4000 0025 0000 3155`

See more at: https://stripe.com/docs/testing

## Development Workflow

```bash
# 1. Start your day
docker-compose up -d
stripe listen --forward-to http://localhost:8000/subscription/webhook

# 2. Make code changes (hot reload is enabled)
# Backend: Edit files in backend/ - auto reloads
# Frontend: Edit files in frontend/ - auto reloads

# 3. View logs while developing
docker-compose logs -f backend frontend

# 4. Run migrations after model changes
docker-compose exec backend alembic revision --autogenerate -m "Description"
docker-compose exec backend alembic upgrade head

# 5. End your day
docker-compose down
# Stop Stripe CLI (Ctrl+C)
```

## Support

- **Stripe Docs:** https://stripe.com/docs
- **Stripe Support:** support@stripe.com
- **Clerk Docs:** https://clerk.com/docs
- **Docker Compose Docs:** https://docs.docker.com/compose/

## Next Steps

Once everything is working:

1. Customize the pricing and features in `frontend/src/pages/SubscriptionPage.tsx`
2. Update the free tier limit in `backend/.env`
3. Add more subscription tiers if desired
4. Set up proper error monitoring
5. Configure email notifications from Stripe
6. Test all webhook scenarios thoroughly
7. Plan your production deployment

## Quick Reference: Important URLs

- **Frontend:** http://localhost:3000
- **Backend API:** http://localhost:8000
- **API Docs:** http://localhost:8000/docs (Swagger UI)
- **Stripe Dashboard:** https://dashboard.stripe.com
- **Webhook Logs:** https://dashboard.stripe.com/test/webhooks

## Security Reminders

- ✅ Never commit `.env` files to git (already in `.gitignore`)
- ✅ Always use test keys in development
- ✅ Verify webhook signatures
- ✅ Use HTTPS in production
- ✅ Keep Stripe keys secure
- ✅ Regularly rotate API keys
- ✅ Monitor Stripe dashboard for suspicious activity
- ✅ Use different `.env` files for development and production
