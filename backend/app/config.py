from pydantic_settings import BaseSettings
from typing import Optional


class Settings(BaseSettings):
    database_url: str
    secret_key: str
    clerk_secret_key: str
    clerk_publishable_key: str
    environment: str = "development"

    # Stripe configuration
    stripe_secret_key: Optional[str] = None
    stripe_publishable_key: Optional[str] = None
    stripe_webhook_secret: Optional[str] = None
    stripe_price_id: Optional[str] = None  # Price ID for $4.99/month subscription

    # Subscription limits
    free_conversion_limit: int = 5

    # Application URL for Stripe redirects
    frontend_url: str = "http://localhost:3000"

    # Sentry configuration
    sentry_dsn: Optional[str] = None

    class Config:
        env_file = ".env"


settings = Settings()