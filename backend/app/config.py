from functools import lru_cache
from typing import Literal

from pydantic_settings import (
    BaseSettings,
    SettingsConfigDict,
)


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    database_url: str = (
        "postgresql+asyncpg://"
        "detective:detective@localhost:5432/"
        "daily_detective"
    )

    llm_provider: Literal[
        "openai",
        "ollama",
    ] = "ollama"

    openai_model: str = "gpt-5-mini"
    openai_timeout_seconds: float = 30.0
    openai_max_retries: int = 2

    ollama_host: str = (
        "http://127.0.0.1:11434"
    )
    ollama_model: str = "gemma4:12b"
    ollama_timeout_seconds: float = 180.0
    ollama_num_ctx: int = 8192


@lru_cache
def get_settings() -> Settings:
    return Settings()