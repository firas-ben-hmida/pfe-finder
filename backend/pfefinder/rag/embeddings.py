"""Embeddings Gemini (768 dimensions) : le même modèle indexe les sujets et encode les requêtes."""
import logging
from functools import lru_cache

from google import genai
from google.genai import types
from langchain_core.embeddings import Embeddings

from pfefinder.common.errors import UpstreamError
from pfefinder.config.settings import get_settings


log = logging.getLogger(__name__)


class GeminiEmbeddings(Embeddings):
    """Adaptateur LangChain : RETRIEVAL_DOCUMENT pour indexer, RETRIEVAL_QUERY pour chercher."""

    def __init__(self, api_key: str, model: str, dim: int, batch_size: int = 50):
        self._client = genai.Client(api_key=api_key)
        self._model = model
        self._dim = dim
        self._batch = batch_size

    def _embed(self, texts: list[str], task_type: str) -> list[list[float]]:
        vectors: list[list[float]] = []
        try:
            for i in range(0, len(texts), self._batch):
                result = self._client.models.embed_content(
                    model=self._model,
                    contents=texts[i : i + self._batch],
                    config=types.EmbedContentConfig(task_type=task_type, output_dimensionality=self._dim),
                )
                vectors.extend(list(e.values) for e in result.embeddings)
        except Exception as exc:
            log.error("Échec embeddings (%d textes, %d caractères) : %s", len(texts), sum(map(len, texts)), exc)
            raise UpstreamError("Échec de l'API d'embeddings.") from exc
        return vectors

    def embed_documents(self, texts: list[str]) -> list[list[float]]:
        return self._embed(texts, "RETRIEVAL_DOCUMENT")

    def embed_queries(self, texts: list[str]) -> list[list[float]]:
        """Plusieurs requêtes de recherche en un seul appel API."""
        return self._embed(texts, "RETRIEVAL_QUERY")

    def embed_query(self, text: str) -> list[float]:
        return self._embed([text], "RETRIEVAL_QUERY")[0]


@lru_cache
def get_embeddings() -> GeminiEmbeddings:
    s = get_settings()
    return GeminiEmbeddings(s.google_api_key, s.embedding_model, s.embedding_dim)
