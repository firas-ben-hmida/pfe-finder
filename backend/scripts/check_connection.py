"""Vérifie Supabase, Gemini (LLM + embeddings) depuis le dossier backend :

    python -m scripts.check_connection
"""
from pfefinder.core.config import get_settings
from pfefinder.core.db.client import get_db
from pfefinder.core.llm import get_embeddings, get_llm

settings = get_settings()
rows = get_db().table("sujets").select("id").limit(1).execute().data
print("Supabase OK, table sujets accessible :", rows)
print("Gemini LLM OK :", get_llm().invoke("Dis bonjour en une phrase.").content)
dim = len(get_embeddings().embed_query("test"))
print(f"Embeddings OK, dimension {dim} (attendu {settings.embedding_dim})")
