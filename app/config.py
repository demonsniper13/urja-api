from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    urja_base_url: str = "https://urja-ops.flockenergy.tech"
    urja_email: str
    urja_password: str
    cache_ttl_seconds: int = 300
    request_timeout_seconds: float = 30.0

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")


@lru_cache
def get_settings() -> Settings:
    return Settings()
