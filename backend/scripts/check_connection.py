"""Vérifie Supabase, le LLM et les embeddings, chacun séparément. Depuis le dossier backend :

    python -m scripts.check_connection
"""
from pfefinder.config.settings import get_settings
from pfefinder.rag.chat_model import get_llm
from pfefinder.rag.embeddings import get_embeddings
from pfefinder.repositories.supabase_client import get_db

settings = get_settings()


def check(name: str, action) -> None:
    try:
        print(f"{name} OK :", action())
    except Exception as exc:  # affichage court : l'erreur complète est inutile ici
        print(f"{name} ÉCHEC : {type(exc).__name__} - {str(exc)[:300]}")


check("Supabase", lambda: get_db().table("sujets").select("id").limit(1).execute().data)
check(f"Embeddings ({settings.embedding_model})",
      lambda: f"dimension {len(get_embeddings().embed_query('test'))} (attendu {settings.embedding_dim})")
check(f"LLM ({settings.llm_model})", lambda: get_llm().invoke("Dis bonjour en une phrase.").content)
