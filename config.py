from pydantic import AnyHttpUrl, PostgresDsn
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    environment: str = "development"  # "staging" | "production"
    debug: bool = False
    sqlalchemy_use_native_typing: bool = True

    database_url: PostgresDsn

    # Security
    secret_key: str
    allowed_hosts: list[str] = ["*"]
    cors_origins: list[AnyHttpUrl] = []

    open_ai_api_key: str

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
    )


settings = Settings()  # type: ignore
