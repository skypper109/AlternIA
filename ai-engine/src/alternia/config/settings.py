from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict


PROJECT_ROOT = Path(__file__).resolve().parents[4]


class Settings(BaseSettings):

    app_name: str = "AlternIA"
    app_env: str = "development"
    debug: bool = True

    llm_provider: str = ""
    llm_model: str = ""
    llm_api_key: str = ""

    vector_db_provider: str = ""
    vector_db_url: str = ""

    backend_host: str = "127.0.0.1"
    backend_port: int = 8000

    default_class: str = "10eme"

    embedding_model_path: str = str(
        PROJECT_ROOT / "models" / "embeddings" / "all-MiniLM-L6-v2"
    )

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )


settings = Settings()