from pydantic import AnyHttpUrl, PostgresDsn
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    environment: str = "development"  # "staging" | "production"
    debug: bool = False
    sqlalchemy_use_native_typing: bool = True

    postgres_user: str
    postgres_password: str
    postgres_db: str
    database_url: PostgresDsn

    # Security
    secret_key: str
    allowed_hosts: list[str] = ["*"]
    cors_origins: list[AnyHttpUrl] = []

    # AI Services
    open_ai_api_key: str
    ollama_url: AnyHttpUrl

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
    )


settings = Settings()  # type: ignore
