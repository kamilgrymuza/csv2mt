# Port Configuration

## Development Ports

This project uses the following ports in local development:

- **Frontend**: `3000` (React/Vite)
- **Backend**: `8000` (FastAPI)
- **Database**: `5432` (PostgreSQL)

## Environment Variables

### Backend `.env`
```bash
FRONTEND_URL=http://localhost:3000
DATABASE_URL=postgresql://user:password@localhost:5432/your_db
```

### Frontend `.env`
```bash
VITE_API_URL=http://localhost:8000
```

## Docker Compose

The `docker-compose.yml` is configured to use these ports:

```yaml
services:
  postgres:
    ports:
      - "5432:5432"

  backend:
    ports:
      - "8000:8000"

  frontend:
    ports:
      - "3000:3000"
    command: npm run dev -- --host 0.0.0.0 --port 3000
```

## CORS Configuration

The backend allows requests from multiple origins for flexibility:

```python
allowed_origins = [
    "http://localhost:3000",   # Primary development port
    "http://localhost:5173",   # Alternative Vite port
    "https://csv2mt.vercel.app"  # Production
]
```

## Stripe Webhook Configuration

### Local Development (with Stripe CLI):
```bash
stripe listen --forward-to http://localhost:8000/subscription/webhook
```

### Stripe Dashboard Configuration:
- **Success URL**: `http://localhost:3000/subscription?success=true`
- **Cancel URL**: `http://localhost:3000/subscription?canceled=true`

These are configured in the backend's `StripeService.create_checkout_session()` method and use the `FRONTEND_URL` environment variable.

## Accessing the Application

When running locally:

- **Frontend**: http://localhost:3000
- **Backend API**: http://localhost:8000
- **API Docs**: http://localhost:8000/docs (FastAPI Swagger UI)
- **Database**: localhost:5432 (via psql or database client)

## Production Considerations

In production, update:

1. **Backend `.env`**:
   ```bash
   FRONTEND_URL=https://your-production-domain.com
   ```

2. **Frontend `.env`**:
   ```bash
   VITE_API_URL=https://your-api-domain.com
   ```

3. **Stripe Dashboard**:
   - Update webhook endpoint URL
   - Update success/cancel redirect URLs (automatically handled via `FRONTEND_URL`)

## Troubleshooting

### "CORS error when calling API"
- Verify frontend is running on port 3000
- Check `VITE_API_URL` points to `http://localhost:8000`
- Confirm backend CORS includes `http://localhost:3000`

### "Stripe redirect fails"
- Check `FRONTEND_URL` in backend `.env` is `http://localhost:3000`
- Verify frontend is accessible at that URL

### "Webhook not received"
- Ensure Stripe CLI is forwarding to `http://localhost:8000/subscription/webhook`
- Check backend is running on port 8000
- Verify webhook signature secret matches

## Changing Ports

If you need to use different ports:

1. Update `docker-compose.yml` port mappings
2. Update `FRONTEND_URL` in backend `.env`
3. Update `VITE_API_URL` in frontend `.env`
4. Update backend CORS configuration in `main.py`
5. Restart all services
