"""LLM de chat (Gemini via LangChain), avec nouvelles tentatives et modèles de secours."""
from collections.abc import Callable
from functools import lru_cache

from langchain_core.runnables import Runnable
from langchain_google_genai import ChatGoogleGenerativeAI

from pfefinder.config.settings import get_settings


@lru_cache
def get_llm(model: str | None = None) -> ChatGoogleGenerativeAI:
    s = get_settings()
    return ChatGoogleGenerativeAI(model=model or s.llm_model, google_api_key=s.google_api_key, temperature=0,
                                  max_retries=1, timeout=40)


def get_local_llm() -> Runnable:
    """LLM local via Ollama (gratuit, sans quota). Import tardif : le paquet n'est requis que si utilisé."""
    from langchain_ollama import ChatOllama

    s = get_settings()
    return ChatOllama(model=s.ollama_model, base_url=s.ollama_base_url, temperature=0,
                      client_kwargs={"timeout": 900})


def resilient(build: Callable[[Runnable], Runnable], allow_local: bool = True) -> Runnable:
    """Construit une chaîne par modèle (Gemini principal, secours, et Ollama si configuré).

    Chaque appel est coupé après 40 s et réessayé une fois avant de passer au modèle suivant : les 503 « forte demande »
    du palier gratuit sont absorbés, et un LLM local peut prendre le relais sans quota
    (allow_local=False pour l'API web : un étudiant ne doit pas attendre un modèle local lent).
    """
    s = get_settings()
    cloud = [get_llm(m) for m in [s.llm_model, *[m for m in s.llm_fallback_models if m != s.llm_model]]]
    models: list[Runnable] = cloud
    if s.ollama_model and allow_local:
        models = [get_local_llm(), *cloud] if s.llm_prefer_local else [*cloud, get_local_llm()]
    chains = [build(m).with_retry(stop_after_attempt=2, wait_exponential_jitter=True) for m in models]
    return chains[0].with_fallbacks(chains[1:])
