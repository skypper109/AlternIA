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
    
    # Local LLM
    local_llm_model_path: str = str(
        PROJECT_ROOT
        / "ai-engine"
        / "models"
        / "llm"
        / "qwen2.5-3b-instruct-q4_k_m.gguf"
        if (PROJECT_ROOT / "ai-engine" / "models" / "llm" / "qwen2.5-3b-instruct-q4_k_m.gguf").exists()
        else PROJECT_ROOT / "ai-engine" / "models" / "llm" / "qwen2.5-1.5b-instruct-q4_k_m.gguf"
    )

    local_llm_context_size: int = 4096
    local_llm_threads: int = 4
    local_llm_batch_size: int = 512
    local_llm_gpu_layers: int = 0
    local_llm_temperature: float = 0.2
    local_llm_max_tokens: int = 0  # 0 = illimité : le modèle s'arrête sur son token de fin naturel

    vector_db_provider: str = ""
    vector_db_url: str = ""

    backend_host: str = "127.0.0.1"
    backend_port: int = 8000

    default_class: str = "12eme"
    tts_voice: str = "vivienne"
    tts_rate: int = 190

    embedding_model_path: str = str(
        PROJECT_ROOT / "models" / "embeddings" / "paraphrase-multilingual-MiniLM-L12-v2"
        if (PROJECT_ROOT / "models" / "embeddings" / "paraphrase-multilingual-MiniLM-L12-v2").exists()
        else PROJECT_ROOT / "models" / "embeddings" / "all-MiniLM-L6-v2"
    )

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )


settings = Settings()