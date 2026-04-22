from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    PROJECT_NAME: str = "LyraSync.ai"
    DATABASE_URL: str
    OPENAI_API_KEY: str
    HUGGINGFACE_API_KEY: str = ""
    TWILIO_ACCOUNT_SID: str
    TWILIO_AUTH_TOKEN: str
    TWILIO_PHONE_NUMBER: str
    ADMIN_SECRET_KEY: str
    DEBUG: bool = False

    # ── JWT Security ──────────────────────────────────────────────────────────
    SECRET_KEY: str
    ALGORITHM: str
    ACCESS_TOKEN_EXPIRE_MINUTES: int

    # ── Storage Backend ───────────────────────────────────────────────────────
    # Set to "azure" in production, "local" for development
    STORAGE_BACKEND: str = "local"

    # Azure Blob Storage (required when STORAGE_BACKEND=azure)
    AZURE_STORAGE_CONNECTION_STRING: str = ""
    AZURE_STORAGE_ACCOUNT_NAME: str = ""
    AZURE_STORAGE_ACCOUNT_KEY: str = ""
    AZURE_STORAGE_CONTAINER_NAME: str = "lyrasync-documents"
    AZURE_SAS_EXPIRY_HOURS: int = 24

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )


settings = Settings()
