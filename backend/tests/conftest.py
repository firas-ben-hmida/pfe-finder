import os

# Valeurs factices : les tests ne contactent ni Supabase ni Gemini.
os.environ.setdefault("SUPABASE_URL", "https://example.supabase.co")
os.environ.setdefault("SUPABASE_KEY", "test-key")
os.environ.setdefault("GOOGLE_API_KEY", "test-key")
