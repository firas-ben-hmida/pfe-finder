"""LLM de chat (Gemini via LangChain), avec nouvelles tentatives et modèles de secours."""
from collections.abc import Callable
from functools import lru_cache

from langchain_core.runnables import Runnable
from langchain_google_genai import ChatGoogleGenerativeAI

from pfefinder.config.settings import get_settings


@lru_cache
def get_llm(model: str | None = None) -> ChatGoogleGenerativeAI:
    s = get_settings()
    return ChatGoogleGenerativeAI(model=model or s.llm_model, google_api_key=s.google_api_key, temperature=0, max_retries=3)


def resilient(build: Callable[[ChatGoogleGenerativeAI], Runnable]) -> Runnable:
    """Construit une chaîne pour le modèle principal puis pour chaque modèle de secours.

    Chaque chaîne réessaie 3 fois (attente croissante) avant de passer au modèle suivant.
    Les erreurs 503 « forte demande » du palier gratuit sont ainsi absorbées.
    """
    s = get_settings()
    models = [s.llm_model, *[m for m in s.llm_fallback_models if m != s.llm_model]]
    chains = [build(get_llm(m)).with_retry(stop_after_attempt=3, wait_exponential_jitter=True) for m in models]
    return chains[0].with_fallbacks(chains[1:])
