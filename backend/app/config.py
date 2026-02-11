from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import List


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")

    database_url: str | None = None
    jwt_secret: str = "change-me"
    jwt_access_minutes: int = 30
    jwt_refresh_days: int = 7

    # Telegram / public URL (Render)
    telegram_bot_token: str | None = None
    telegram_webhook_secret: str = ""  # empty string means "no secret enforcement"
    public_base_url: str = "http://localhost:8000"

    # CORS
    cors_origins: str = "http://localhost:5173"

    @property
    def cors_origin_list(self) -> List[str]:
        return [o.strip() for o in self.cors_origins.split(",") if o.strip()]


settings = Settings()
