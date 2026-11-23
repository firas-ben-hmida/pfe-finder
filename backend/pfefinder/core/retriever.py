from typing import Any

from langchain_core.callbacks import CallbackManagerForRetrieverRun
from langchain_core.documents import Document
from langchain_core.retrievers import BaseRetriever
from pydantic import ConfigDict

from pfefinder.core.db import subjects as subjects_repo
from pfefinder.core.llm import get_embeddings


def subject_text(row: dict[str, Any]) -> str:
    """Texte indexé pour un sujet (un chunk = un sujet entier)."""
    technos = ", ".join(row.get("technos") or [])
    return (f"{row.get('titre', '')}\nEntreprise : {row.get('entreprise', '')}\n"
            f"Technologies : {technos}\n{row.get('description') or ''}").strip()


class SubjectRetriever(BaseRetriever):
    """Retriever LangChain branché sur pgvector (fonction SQL match_sujets)."""

    model_config = ConfigDict(arbitrary_types_allowed=True)
    top_k: int = 8

    def _get_relevant_documents(self, query: str, *, run_manager: CallbackManagerForRetrieverRun) -> list[Document]:
        rows = subjects_repo.search(get_embeddings().embed_query(query), self.top_k)
        return [Document(page_content=subject_text(r), metadata=r) for r in rows]
