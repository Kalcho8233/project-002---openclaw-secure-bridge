from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    api_key: str = ""
    host: str = "127.0.0.1"
    port: int = 8000
    notify_target: str = "+359877656763"
    notify_queue_dir: str = "./var/notify-queue"
    notify_timeout_seconds: int = 15
    openclaw_command: str = "openclaw"

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")


@lru_cache
def get_settings() -> Settings:
    return Settings()
