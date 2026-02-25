from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")

    # Application
    ENVIRONMENT: str = "development"
    APP_VERSION: str = "0.1.0"
    LOG_LEVEL: str = "DEBUG"

    # Database
    DATABASE_URL: str = "postgresql+asyncpg://enex:dev_password@localhost:5432/enex"
    DB_POOL_SIZE: int = 10
    DB_MAX_OVERFLOW: int = 5

    # Redis
    REDIS_URL: str = "redis://localhost:6379/0"

    # JWT
    JWT_SECRET: str = "change-me-use-a-long-random-string-in-production"
    JWT_ALGORITHM: str = "HS256"
    JWT_ACCESS_TOKEN_EXPIRE_HOURS: int = 24
    JWT_REFRESH_TOKEN_EXPIRE_DAYS: int = 30

    # CORS
    CORS_ORIGINS: str = "http://localhost:3000"

    # OTP
    OTP_LENGTH: int = 6
    OTP_EXPIRE_MINUTES: int = 5
    OTP_MAX_ATTEMPTS: int = 3
    OTP_RATE_LIMIT_PER_HOUR: int = 5
    OTP_COOLDOWN_SECONDS: int = 60

    # Google OAuth
    GOOGLE_CLIENT_ID: str = ""
    GOOGLE_CLIENT_SECRET: str = ""

    # MSG91
    MSG91_AUTH_KEY: str = ""
    MSG91_SENDER_ID: str = "ENEXIN"
    MSG91_TEMPLATE_ID: str = ""

    # Email (Resend)
    RESEND_API_KEY: str = ""
    RESEND_FROM_EMAIL: str = "noreply@enex.in"

    # AI (Anthropic)
    ANTHROPIC_API_KEY: str = ""
    ANTHROPIC_MODEL: str = "claude-sonnet-4-6"
    ANTHROPIC_MAX_INPUT_TOKENS: int = 8000

    # Price Data
    DEFAULT_EVAL_MONTHS: int = 12
    OUTCOME_TOLERANCE_PCT: float = 5.0

    # Wayback Machine
    WAYBACK_ARCHIVAL_ENABLED: bool = False
    WAYBACK_TIMEOUT_SECONDS: int = 10

    # Notifications
    NOTIFICATION_EMAIL_ENABLED: bool = False
    NOTIFICATION_BATCH_SIZE: int = 100

    @property
    def cors_origins_list(self) -> list[str]:
        return [origin.strip() for origin in self.CORS_ORIGINS.split(",")]


@lru_cache
def get_settings() -> Settings:
    return Settings()
