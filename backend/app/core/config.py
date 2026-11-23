from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Paramètres lus depuis les variables d'environnement ou le fichier .env."""

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    supabase_url: str
    supabase_key: str  # clé service_role : uniquement côté serveur
    google_api_key: str

    llm_model: str = "gemini-2.5-flash"
    embedding_model: str = "gemini-embedding-001"
    embedding_dim: int = 768

    allowed_origins: list[str] = ["http://localhost:4200"]
    max_cv_bytes: int = 5 * 1024 * 1024
    matching_top_k: int = 8


@lru_cache
def get_settings() -> Settings:
    return Settings()
