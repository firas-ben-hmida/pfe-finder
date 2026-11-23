from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Paramètres lus depuis les variables d'environnement ou le fichier .env."""

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    supabase_url: str
    supabase_key: str  # clé service_role : uniquement côté serveur
    google_api_key: str

    llm_model: str = "gemini-3.5-flash-lite"
    # Modèles essayés dans l'ordre si le principal est surchargé (503) ou indisponible
    llm_fallback_models: list[str] = ["gemini-3.5-flash", "gemini-3.7-flash"]
    embedding_model: str = "gemini-embedding-001"
    embedding_dim: int = 768

    allowed_origins: list[str] = ["http://localhost:4200"]
    max_cv_bytes: int = 5 * 1024 * 1024
    matching_candidates: int = 40       # sujets récupérés par la recherche vectorielle avant le classement hybride
    matching_rerank_count: int = 25     # sujets soumis au jugement du LLM
    matching_min_relevance: int = 6     # note LLM minimale (0-10) pour afficher un sujet
    matching_min_score: float = 0.0     # (mode dégradé) similarité minimale absolue
    matching_score_margin: float = 0.08  # (mode dégradé) écart maximal au meilleur score

    # Agent de découverte (Programmable Search Engine de Google)
    google_cse_id: str = ""
    google_cse_key: str = ""
    max_pdfs_par_jour: int = 10
    # LLM local (Ollama). Vide = désactivé. Exemple : OLLAMA_MODEL=qwen2.5:3b
    ollama_model: str = ""
    ollama_base_url: str = "http://localhost:11434"
    llm_prefer_local: bool = False  # True : Ollama d'abord, les API Gemini en secours
    llm_block_chars: int = 20_000  # taille max d'un bloc envoyé au LLM (petits blocs = moins de 503)
    max_pages_par_pdf: int = 120
    max_pdf_bytes: int = 30 * 1024 * 1024
    agent_delai_secondes: float = 2.0
    agent_recursion_limit: int = 40


@lru_cache
def get_settings() -> Settings:
    return Settings()
