from pathlib import Path

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict

# backend/ directory - used so .env and the local SQLite/Chroma files are found
# no matter which folder the server is started from.
BACKEND_DIR = Path(__file__).resolve().parent.parent


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=str(BACKEND_DIR / ".env"),
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # Defaults to a local SQLite file so the project runs without a PostgreSQL server.
    # docker-compose overrides this with the PostgreSQL connection string.
    DATABASE_URL: str = Field(default=f"sqlite:///{(BACKEND_DIR / 'policygpt.db').as_posix()}")
    CHROMA_PERSIST_DIR: str = Field(default=str(BACKEND_DIR / "chroma_db"))
    # Any key starting with "sk-mock" runs the AI features in offline mode (keyword
    # retrieval + template answers) so the app is fully usable without an OpenAI key.
    OPENAI_API_KEY: str = Field(default="sk-mock-key-for-now")
    CLERK_JWKS_URL: str = Field(default="")
    CLERK_FRONTEND_API: str = Field(default="")
    JWT_ALGORITHM: str = Field(default="RS256")
    CORS_ORIGINS: str = Field(default="http://localhost:3000,http://127.0.0.1:3000")
    # Comma-separated emails or Clerk user ids allowed to add / delete schemes.
    # Leave empty in local development to let any signed-in user manage schemes.
    ADMIN_EMAILS: str = Field(default="")
    PROJECT_NAME: str = "PolicyGPT API"
    ENVIRONMENT: str = "development"
    PORT: int = 8000

    @property
    def ai_offline(self) -> bool:
        key = (self.OPENAI_API_KEY or "").strip()
        return not key or key.startswith("sk-mock")

    @property
    def admin_list(self) -> set[str]:
        return {a.strip().lower() for a in self.ADMIN_EMAILS.split(",") if a.strip()}

    @property
    def cors_origin_list(self) -> list[str]:
        return [o.strip() for o in self.CORS_ORIGINS.split(",") if o.strip()]


settings = Settings()
