import os

# Valeurs factices : les tests ne contactent aucun service externe.
os.environ.setdefault("SUPABASE_URL", "http://localhost")
os.environ.setdefault("SUPABASE_KEY", "test")
os.environ.setdefault("GOOGLE_API_KEY", "test")
