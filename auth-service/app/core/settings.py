from pathlib import Path
from functools import lru_cache

from pydantic import BaseModel, SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict

BASE_DIR = Path(__file__).resolve().parent.parent.parent


class UrlPrefix(BaseModel):
    prefix: str


class FastapiConfig(BaseModel):
    host: str
    port: int


class DatabaseConfig(BaseModel):
    url: SecretStr
    echo: bool
    echo_pool: bool
    pool_pre_ping: bool
    pool_size: int
    max_overflow: int


class AuthConfig(BaseModel):
    secret_key: SecretStr
    algorithm: str
    access_token_expire_minutes: int
    refresh_token_expire_days: int


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=(
            BASE_DIR / ".env.develop",
            BASE_DIR / ".env",
        ),
        extra="ignore",
        env_prefix="APP_CONFIG__",
        env_nested_delimiter="__",
    )
    url_prefix: UrlPrefix
    fastapi: FastapiConfig
    database: DatabaseConfig
    auth: AuthConfig


@lru_cache
def get_settings() -> Settings:
    return Settings()
