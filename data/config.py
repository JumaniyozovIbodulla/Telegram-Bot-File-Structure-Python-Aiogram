from __future__ import annotations

from functools import lru_cache
from typing import Annotated

from pydantic import Field, SecretStr, field_validator
from pydantic_settings import BaseSettings, NoDecode, SettingsConfigDict


class Settings(BaseSettings):
    """Application configuration loaded from environment variables or `.env`."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    bot_token: SecretStr = Field(alias="BOT_TOKEN")
    admins: Annotated[list[int], NoDecode] = Field(default_factory=list, alias="ADMINS")
    db_path: str = Field(default="data/bot.db", alias="DB_PATH")

    guest_mode_default: bool = Field(default=True, alias="GUEST_MODE_DEFAULT")
    guest_daily_limit: int = Field(default=20, ge=1, alias="GUEST_DAILY_LIMIT")
    rate_limit_guest: float = Field(default=1.5, ge=0.0, alias="RATE_LIMIT_GUEST")
    rate_limit_user: float = Field(default=0.5, ge=0.0, alias="RATE_LIMIT_USER")
    log_level: str = Field(default="INFO", alias="LOG_LEVEL")

    @field_validator("bot_token")
    @classmethod
    def validate_bot_token(cls, value: SecretStr) -> SecretStr:
        token = value.get_secret_value().strip()
        if not token or ":" not in token:
            raise ValueError(
                "BOT_TOKEN is missing or invalid. Set a valid token from @BotFather in your .env file."
            )
        return SecretStr(token)

    @field_validator("admins", mode="before")
    @classmethod
    def parse_admins(cls, value: object) -> list[int]:
        if value is None or value == "":
            return []
        if isinstance(value, int):
            return [value]
        if isinstance(value, (list, tuple, set)):
            return [int(item) for item in value if str(item).strip()]
        if isinstance(value, str):
            raw = value.strip().strip("[]")
            if not raw:
                return []
            return [int(part.strip()) for part in raw.split(",") if part.strip()]
        raise ValueError("ADMINS must be a comma-separated list of integer Telegram IDs.")


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    """Return cached application settings."""
    return Settings()
