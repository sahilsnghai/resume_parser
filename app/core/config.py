import os
from typing import List
from pydantic_settings import BaseSettings
from pydantic import Field, field_validator


class Settings(BaseSettings):
    """Application settings loaded from environment variables"""

    APP_NAME: str = "Resume Parser API"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = Field(default=False)
    HOST: str = Field(default="0.0.0.0")
    PORT: int = Field(default=8000)
    API_V1_STR: str = "/api"

    DATABASE_URL: str = Field(...)

    OPENAI_API_KEY: str = Field(...)
    OPENAI_MODEL: str = Field(default="gpt-4")
    OPENAI_TEMPERATURE: float = Field(default=0.1)
    OPENAI_MAX_TOKENS: int = Field(default=4000)

    MAX_FILE_SIZE: int = Field(default=10485760)
    ALLOWED_EXTENSIONS: List[str] = Field(default=[".pdf", ".docx"])

    LOG_LEVEL: str = Field(default="INFO")

    BACKEND_CORS_ORIGINS: List[str] = Field(
        default=["http://localhost:8501", "http://127.0.0.1:8501"]
    )

    UPLOAD_DIR: str = Field(default="data/uploads")

    model_config = {
        "env_file": ".env",
        "env_file_encoding": "utf-8",
        "case_sensitive": False,
        "extra": "ignore",
    }

    @field_validator("ALLOWED_EXTENSIONS", mode="before")
    @classmethod
    def validate_allowed_extensions(cls, v):
        """Validate and parse allowed extensions"""
        if isinstance(v, str):
            return [ext.strip() for ext in v.split(",")]
        return v

    @field_validator("BACKEND_CORS_ORIGINS", mode="before")
    @classmethod
    def validate_cors_origins(cls, v):
        """Validate and parse CORS origins"""
        if isinstance(v, str):
            return [origin.strip() for origin in v.split(",")]
        return v

    @property
    def is_debug(self) -> bool:
        """Check if debug mode is enabled"""
        return self.DEBUG

    @property
    def database_url_async(self) -> str:
        """Get async database URL for SQLAlchemy"""
        if "asyncpg" not in self.DATABASE_URL:

            return self.DATABASE_URL.replace("postgresql://", "postgresql+asyncpg://")
        return self.DATABASE_URL

    def ensure_upload_directory(self) -> None:
        """Ensure upload directory exists"""
        os.makedirs(self.UPLOAD_DIR, exist_ok=True)


settings = Settings()


settings.ensure_upload_directory()
