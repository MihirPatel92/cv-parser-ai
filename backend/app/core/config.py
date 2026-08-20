from pydantic_settings import BaseSettings
from typing import Optional


class Settings(BaseSettings):
    # Database URL — Render injects postgresql://, we auto-upgrade to asyncpg driver
    DATABASE_URL: str = "postgresql+asyncpg://cvparser:cvparser_secret@localhost:5432/cvparser"

    @property
    def async_database_url(self) -> str:
        """Ensure the URL always uses the asyncpg driver, even if Render injects a plain postgresql:// URL."""
        url = self.DATABASE_URL
        if url.startswith("postgresql://"):
            url = url.replace("postgresql://", "postgresql+asyncpg://", 1)
        elif url.startswith("postgres://"):
            # Heroku / Render sometimes use postgres:// shorthand
            url = url.replace("postgres://", "postgresql+asyncpg://", 1)
        return url

    # Security
    SECRET_KEY: str = "supersecretkey-change-in-production-min-32-chars"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 480  # 8 hours

    # AI Providers
    GEMINI_API_KEY: Optional[str] = None
    OPENAI_API_KEY: Optional[str] = None
    OLLAMA_BASE_URL: str = "http://localhost:11434"
    DEFAULT_AI_PROVIDER: str = "gemini"

    # File Upload
    UPLOAD_DIR: str = "./uploads"
    MAX_FILE_SIZE_MB: int = 25

    class Config:
        env_file = ".env"
        case_sensitive = True


settings = Settings()
