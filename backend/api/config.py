from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    database_url: str = "postgresql+asyncpg://nelvra:nelvra@localhost:5432/nelvra"
    redis_url: str = "redis://localhost:6379"
    jwt_secret: str = "dev-secret-change-in-production"
    environment: str = "development"
    log_level: str = "INFO"

    # Rate limiting: max events per minute per API key
    events_rate_limit: int = 1000

    # Shared secret between Next.js frontend and this API for the /v1/auth/register endpoint
    internal_secret: str = "dev-internal-secret-change-in-production"

    # Anthropic API key — required for quality scoring, drift explanation, prompt optimization
    anthropic_api_key: str = ""

    # Stripe
    stripe_secret_key: str = ""
    stripe_webhook_secret: str = ""
    stripe_price_pro: str = ""  # price_xxx for Pro plan
    stripe_price_team: str = ""  # price_xxx for Team plan

    # Email alerts (SMTP)
    smtp_host: str = "smtp.gmail.com"
    smtp_port: int = 587
    smtp_username: str = ""
    smtp_password: str = ""
    smtp_from: str = "alerts@nelvra.io"

    # Feature flags
    quality_scoring_enabled: bool = True


settings = Settings()
