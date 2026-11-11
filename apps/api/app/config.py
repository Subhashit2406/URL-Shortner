from enum import Enum
from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Environment(str, Enum):
    development = "development"
    staging = "staging"
    production = "production"


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore"
    )

    app_env: Environment = Field(default=Environment.development, alias="APP_ENV")
    port: int = Field(alias="PORT")
    database_url: str = Field(
        default="postgres://postgres:postgres@localhost:5432/upsk_sdf",
        alias="DATABASE_URL"
    )
    redis_url: str = Field(
        default="redis://localhost:6379",
        alias="REDIS_URL"
    )
    jwt_secret: str = Field(
        default="replace-me-locally-secret-key-32-chars-long",
        alias="JWT_SECRET"
    )
    admin_api_key: str = Field(
        default="dev_admin_api_key_secret_123",
        alias="ADMIN_API_KEY"
    )
    cors_origin: str = Field(
        default="*",
        alias="CORS_ORIGIN"
    )
    log_level: str = Field(
        default="info",
        alias="LOG_LEVEL"
    )

    @field_validator("admin_api_key")
    @classmethod
    def validate_admin_api_key(cls, v: str) -> str:
        cleaned = v.strip()
        if not cleaned:
            raise ValueError("ADMIN_API_KEY cannot be empty")
        if len(cleaned) < 8:
            raise ValueError("ADMIN_API_KEY must be at least 8 characters long")
        return cleaned

    @field_validator("port")
    @classmethod
    def validate_port(cls, v: int) -> int:
        if v < 1 or v > 65535:
            raise ValueError(
                f"Invalid PORT {v}. PORT must be an integer between 1 and 65535."
            )
        return v


settings = Settings()
