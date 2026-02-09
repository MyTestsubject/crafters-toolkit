from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env", env_file_encoding="utf-8", extra="ignore"
    )
    DATABASE_URL = (
        "postgresql+psycopg://postgres:postgres@localhost:5432/crafters_toolkit"
    )
    Debug: bool = False


settings = Settings()
