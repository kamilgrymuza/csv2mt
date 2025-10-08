from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from .routers import users, health, test, conversion, subscription
from .database import engine, Base
from .config import settings
import sentry_sdk
from sentry_sdk.integrations.fastapi import FastApiIntegration
from sentry_sdk.integrations.starlette import StarletteIntegration

# Initialize Sentry only for staging and production environments
if settings.environment in ["staging", "production"] and settings.sentry_dsn:
    sentry_sdk.init(
        dsn=settings.sentry_dsn,
        environment=settings.environment,
        integrations=[
            StarletteIntegration(transaction_style="endpoint"),
            FastApiIntegration(transaction_style="endpoint"),
        ],
        # Set traces_sample_rate to 1.0 to capture 100% of transactions for performance monitoring.
        # Adjust this value in production.
        traces_sample_rate=1.0 if settings.environment == "staging" else 0.1,
        # Set profiles_sample_rate to 1.0 to profile 100% of sampled transactions.
        # Adjust this value in production.
        profiles_sample_rate=1.0 if settings.environment == "staging" else 0.1,
        # Enable request bodies in error reports
        send_default_pii=False,
        # Attach tracebacks
        attach_stacktrace=True,
    )

# Create database tables
Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="Micro-SaaS API",
    description="A FastAPI backend for Micro-SaaS MVP",
    version="1.0.0"
)

# Configure CORS
# Configure CORS with Railway environment variables
import os

allowed_origins = ["http://localhost:3000", "http://localhost:5173", "https://csv2mt.vercel.app"]  # Local development

# Add Railway domains if available
if railway_domain := os.getenv("RAILWAY_PUBLIC_DOMAIN"):
    allowed_origins.append(f"https://{railway_domain}")
if railway_static := os.getenv("RAILWAY_STATIC_URL"):
    allowed_origins.append(railway_static)

app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["*"],
)

# Include routers
app.include_router(health.router)
app.include_router(users.router)
app.include_router(test.router)
app.include_router(conversion.router)
app.include_router(subscription.router)


@app.get("/")
async def root():
    return {"message": "Welcome to Micro-SaaS API", "environment": settings.environment}