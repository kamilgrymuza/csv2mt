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
    stripe_price_id: Optional[str] = None  # Price ID for $4.99/month subscription (USD) - kept for backward compatibility
    stripe_price_id_usd: Optional[str] = None  # Price ID for $4.99/month subscription (USD)
    stripe_price_id_pln: Optional[str] = None  # Price ID for 19.99 PLN/month subscription

    # Subscription limits
    free_conversion_limit: int = 5
    premium_conversion_limit: int = 100

    # Application URL for Stripe redirects
    frontend_url: str = "http://localhost:3000"

    # Sentry configuration
    sentry_dsn: Optional[str] = None

    # Claude AI configuration
    anthropic_api_key: Optional[str] = None

    # OpenAI configuration
    openai_api_key: Optional[str] = None

    # AI model selection (claude-sonnet, claude-haiku, gpt-4o)
    ai_model: str = "claude-sonnet"

    class Config:
        env_file = ".env"


settings = Settings()