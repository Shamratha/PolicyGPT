import os
# pyrefly: ignore [missing-import]
from pydantic_settings import BaseSettings
# pyrefly: ignore [missing-import]
from pydantic import Field

class Settings(BaseSettings):
    DATABASE_URL: str = Field(
        default="postgresql+psycopg://postgres:postgres@localhost:5432/policygpt",
        validation_alias="DATABASE_URL"
    )
    CHROMA_PERSIST_DIR: str = Field(
        default="./chroma_db",
        validation_alias="CHROMA_PERSIST_DIR"
    )
    OPENAI_API_KEY: str = Field(
        default="sk-mock-key-for-now",
        validation_alias="OPENAI_API_KEY"
    )
    CLERK_JWKS_URL: str = Field(
        default="",
        validation_alias="CLERK_JWKS_URL"
    )
    CLERK_FRONTEND_API: str = Field(
        default="",
        validation_alias="CLERK_FRONTEND_API"
    )
    JWT_ALGORITHM: str = Field(
        default="RS256",
        validation_alias="JWT_ALGORITHM"
    )
    PROJECT_NAME: str = "PolicyGPT API"
    ENVIRONMENT: str = "development"
    PORT: int = 8000

    class Config:
        env_file = ".env"
        extra = "ignore"

settings = Settings()
