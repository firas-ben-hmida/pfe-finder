from typing import TypeVar

from google.genai import types
from pydantic import BaseModel

from app.core.config import get_settings
from app.core.errors import UpstreamError
from app.rag.client import get_client

T = TypeVar("T", bound=BaseModel)


def generate_structured(prompt: str, schema: type[T], temperature: float = 0.2) -> T:
    """Appelle le LLM et valide la réponse JSON avec un modèle Pydantic."""
    settings = get_settings()
    try:
        response = get_client().models.generate_content(
            model=settings.llm_model,
            contents=prompt,
            config=types.GenerateContentConfig(
                response_mime_type="application/json",
                response_schema=schema,
                temperature=temperature,
            ),
        )
        return schema.model_validate_json(response.text)
    except Exception as exc:
        raise UpstreamError("Le service de génération est indisponible.") from exc
