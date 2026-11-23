"""Vérifie que Supabase et Gemini répondent. À lancer depuis le dossier backend :

    python test_connexion.py
"""
import os

from dotenv import load_dotenv
from google import genai
from google.genai import types
from supabase import create_client

load_dotenv()

LLM_MODEL = os.getenv("LLM_MODEL", "gemini-2.5-flash")
EMBEDDING_MODEL = os.getenv("EMBEDDING_MODEL", "gemini-embedding-001")
EMBEDDING_DIM = int(os.getenv("EMBEDDING_DIM", "768"))

db = create_client(os.environ["SUPABASE_URL"], os.environ["SUPABASE_KEY"])
print("Supabase OK, lignes dans sujets :", db.table("sujets").select("id").limit(1).execute().data)

client = genai.Client(api_key=os.environ["GOOGLE_API_KEY"])

reponse = client.models.generate_content(model=LLM_MODEL, contents="Dis bonjour en une phrase.")
print("Gemini OK :", reponse.text)

embedding = client.models.embed_content(
    model=EMBEDDING_MODEL,
    contents="test",
    config=types.EmbedContentConfig(output_dimensionality=EMBEDDING_DIM),
)
print(f"Embedding OK, dimension : {len(embedding.embeddings[0].values)} (attendu : {EMBEDDING_DIM})")
