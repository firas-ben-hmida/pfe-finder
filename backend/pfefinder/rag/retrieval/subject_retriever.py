from langchain_core.callbacks import CallbackManagerForRetrieverRun
from langchain_core.documents import Document
from langchain_core.retrievers import BaseRetriever
from pydantic import ConfigDict

from pfefinder.rag.embeddings import get_embeddings
from pfefinder.rag.indexing.subject_text import subject_text
from pfefinder.repositories import subjects_repository as subjects_repo


class SubjectRetriever(BaseRetriever):
    """Retriever LangChain branché sur pgvector (fonction SQL match_sujets)."""

    model_config = ConfigDict(arbitrary_types_allowed=True)
    top_k: int = 8

    def _get_relevant_documents(self, query: str, *, run_manager: CallbackManagerForRetrieverRun) -> list[Document]:
        rows = subjects_repo.search(get_embeddings().embed_query(query), self.top_k)
        return [Document(page_content=subject_text(r), metadata=r) for r in rows]
