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
    
    # Local LLM (Hiérarchie par puissance : 14B > 7B > 3B > 1.5B)
    @staticmethod
    def _find_best_llm_model() -> Path:
        models_dir = PROJECT_ROOT / "ai-engine" / "models" / "llm"
        candidates = [
            "qwen2.5-14b-instruct-q4_k_m.gguf",
            "qwen2.5-7b-instruct-q5_k_m.gguf",
            "qwen2.5-7b-instruct-q4_k_m.gguf",
            "qwen2.5-3b-instruct-q4_k_m.gguf",
            "qwen2.5-1.5b-instruct-q4_k_m.gguf",
        ]
        for candidate in candidates:
            p = models_dir / candidate
            if p.exists():
                return p
        # Si un autre fichier .gguf existe dans le dossier
        if models_dir.exists():
            ggufs = list(models_dir.glob("*.gguf"))
            if ggufs:
                return ggufs[0]
        return models_dir / "qwen2.5-7b-instruct-q4_k_m.gguf"

    local_llm_model_path: str = str(_find_best_llm_model())

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