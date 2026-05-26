from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    # Application
    APP_NAME: str
    APP_ENV: str
    DEBUG: bool
    API_PREFIX: str = ""
    CORS_ALLOW_ORIGINS: str = ""

    # Database
    DATABASE_URL: str

    # JWT
    JWT_SECRET_KEY: str
    JWT_REFRESH_SECRET: str
    JWT_ALGORITHM: str
    ACCESS_TOKEN_EXPIRE_MINUTES: int
    REFRESH_TOKEN_EXPIRE_DAYS: int

    # Redis
    REDIS_URL: str

    # AWS S3 (파일 업로드 미사용 시 생략 가능)
    AWS_ACCESS_KEY_ID: str | None = None
    AWS_SECRET_ACCESS_KEY: str | None = None
    AWS_REGION: str | None = None
    S3_BUCKET_NAME: str | None = None

    # OAuth2 - Google (소셜 로그인 미사용 시 생략 가능)
    GOOGLE_CLIENT_ID: str | None = None
    GOOGLE_CLIENT_SECRET: str | None = None
    GOOGLE_REDIRECT_URI: str | None = None

    # Celery (비동기 작업 미사용 시 생략 가능)
    CELERY_BROKER_URL: str | None = None
    CELERY_RESULT_BACKEND: str | None = None

    # LLM - Ollama (미사용 시 생략 가능)
    LLM_BASE_URL: str | None = None
    LLM_MODEL: str | None = None

    @property
    def cors_allow_origins(self) -> list[str]:
        origins = [
            origin.strip() for origin in self.CORS_ALLOW_ORIGINS.split(",") if origin.strip()
        ]
        if origins:
            return origins
        return ["*"] if self.DEBUG else []

    @property
    def api_prefix(self) -> str:
        prefix = self.API_PREFIX.strip()
        if not prefix or prefix == "/":
            return ""
        return f"/{prefix.strip('/')}"


def require_s3_settings() -> None:
    required = {
        "AWS_ACCESS_KEY_ID": settings.AWS_ACCESS_KEY_ID,
        "AWS_SECRET_ACCESS_KEY": settings.AWS_SECRET_ACCESS_KEY,
        "AWS_REGION": settings.AWS_REGION,
        "S3_BUCKET_NAME": settings.S3_BUCKET_NAME,
    }
    missing = [key for key, value in required.items() if not value]
    if missing:
        raise RuntimeError(f"S3 settings are required: {', '.join(missing)}")


def require_llm_settings() -> None:
    required = {
        "LLM_BASE_URL": settings.LLM_BASE_URL,
        "LLM_MODEL": settings.LLM_MODEL,
    }
    missing = [key for key, value in required.items() if not value]
    if missing:
        raise RuntimeError(f"LLM settings are required: {', '.join(missing)}")


settings = Settings()
