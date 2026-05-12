from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    """Application settings loaded from environment variables."""
    # Virtuoso settings
    TRIPLESTORE_HOST: str
    TRIPLESTORE_PORT: int
    TRIPLESTORE_USER: str
    TRIPLESTORE_PASSWORD: str
    TRIPLESTORE_TIMEOUT: str
    TRIPLESTORE_ENDPOINT: str
    SOLANA_GRAPH: str
    ONTOLOGY_PATH: str

    # LLM settings
    LLM_ONTOLOGY_PATH: str
    MODEL_CONTEXT_CAP: int
    CHAR_PER_TOKEN: int

    # Monitoring settings
    ENABLE_TRACING: bool
    LOG_LEVEL: str

    # CAP settings
    APP_HOST: str
    APP_PORT: int

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
        case_sensitive=True
    )

settings = Settings()