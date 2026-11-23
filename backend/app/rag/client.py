from functools import lru_cache

from google import genai

from app.core.config import get_settings


@lru_cache
def get_client() -> genai.Client:
    return genai.Client(api_key=get_settings().google_api_key)
