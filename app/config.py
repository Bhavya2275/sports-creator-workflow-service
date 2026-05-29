from pydantic_settings import BaseSettings, SettingsConfigDict
from functools import lru_cache


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    # App
    APP_NAME: str = "Creator Workflow Service"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = False
    LOG_LEVEL: str = "INFO"

    # Database — PostgreSQL required
    DATABASE_URL: str = "postgresql+asyncpg://creator:creator_pass@localhost:5432/creator_workflow"

    # AI — OpenAI
    OPENAI_API_KEY: str = ""
    OPENAI_MODEL: str = "gpt-5.4-mini"

    # Qualification scoring thresholds
    QUALIFICATION_SCORE_THRESHOLD: float = 60.0


@lru_cache
def get_settings() -> Settings:
    return Settings()
