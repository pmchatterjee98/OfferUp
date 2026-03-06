from __future__ import annotations

from functools import lru_cache
from typing import Optional

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_ignore_empty=True)

    environment: str = Field(default="dev", validation_alias="ENVIRONMENT")
    base_url: str = Field(default="http://localhost:8000", validation_alias="BASE_URL")

    database_url: str = Field(default="sqlite:///./data/app.db", validation_alias="DATABASE_URL")

    session_secret_key: str = Field(default="dev-secret-change-me", validation_alias="SESSION_SECRET_KEY")
    session_cookie_name: str = Field(default="nc_session", validation_alias="SESSION_COOKIE_NAME")

    demo_api_key: Optional[str] = Field(default=None, validation_alias="DEMO_API_KEY")
    demo_user_email: str = Field(default="demo@example.com", validation_alias="DEMO_USER_EMAIL")

    google_client_id: Optional[str] = Field(default=None, validation_alias="GOOGLE_CLIENT_ID")
    google_client_secret: Optional[str] = Field(default=None, validation_alias="GOOGLE_CLIENT_SECRET")
    google_redirect_uri: str = Field(
        default="http://localhost:8000/integrations/google/callback",
        validation_alias="GOOGLE_REDIRECT_URI",
    )
    google_scopes: str = Field(
        default="openid email profile "
        "https://www.googleapis.com/auth/gmail.readonly "
        "https://www.googleapis.com/auth/calendar.events",
        validation_alias="GOOGLE_SCOPES",
    )

    llm_provider: str = Field(default="mock", validation_alias="LLM_PROVIDER")
    openai_api_key: Optional[str] = Field(default=None, validation_alias="OPENAI_API_KEY")
    openai_model: str = Field(default="gpt-4o-mini", validation_alias="OPENAI_MODEL")


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    return Settings()
