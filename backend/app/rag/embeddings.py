from google.genai import types

from app.core.config import get_settings
from app.core.errors import UpstreamError
from app.rag.client import get_client


def embed_text(text: str, task_type: str = "RETRIEVAL_QUERY") -> list[float]:
    """Vecteur d'un texte.

    Utiliser RETRIEVAL_DOCUMENT pour indexer un sujet et RETRIEVAL_QUERY pour
    une recherche. Le modèle et la dimension doivent être identiques partout,
    et correspondre à la colonne vector(...) de la base.
    """
    settings = get_settings()
    try:
        response = get_client().models.embed_content(
            model=settings.embedding_model,
            contents=text,
            config=types.EmbedContentConfig(
                task_type=task_type,
                output_dimensionality=settings.embedding_dim,
            ),
        )
        return list(response.embeddings[0].values)
    except Exception as exc:
        raise UpstreamError("Le service d'embeddings est indisponible.") from exc
