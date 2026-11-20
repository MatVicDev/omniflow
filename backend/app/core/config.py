from functools import lru_cache
from typing import Literal

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    app_name: str = "OmniFlow"
    version: str = "1.0.0"
    database_url: str = "sqlite:///./omniflow.db"
    cors_origins: list[str] = ["http://localhost:5173"]
    seed_on_startup: bool = True

    ai_provider: Literal["auto", "offline", "anthropic", "openai"] = "auto"
    anthropic_api_key: str | None = None
    anthropic_model: str = "claude-opus-5-5"
    openai_api_key: str | None = None
    openai_model: str = "gpt-5-mini"

    whatsapp_verify_token: str = "omniflow-verify"
    whatsapp_token: str | None = None
    whatsapp_phone_number_id: str | None = None

    @property
    def resolved_provider(self) -> str:
        if self.ai_provider != "auto":
            return self.ai_provider
        if self.anthropic_api_key:
            return "anthropic"
        if self.openai_api_key:
            return "openai"
        return "offline"


@lru_cache
def get_settings() -> Settings:
    return Settings()
