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


settings = Settings()
