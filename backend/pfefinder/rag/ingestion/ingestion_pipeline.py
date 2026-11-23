"""Pipeline unique d'ingestion : bytes PDF -> extraction LLM -> règles -> embeddings -> Supabase.

C'est le seul chemin d'écriture dans la table sujets (utilisé par le CLI et par l'agent).
"""
import logging
from dataclasses import dataclass

from pfefinder.rag.ingestion.subject_extractor import extract_chain
from pfefinder.config.settings import get_settings
from pfefinder.domain.models import ExtractedBook
from pfefinder.repositories import documents_repository as documents
from pfefinder.repositories import subjects_repository as subjects
from pfefinder.common.fingerprints import normalize_url, sha256_bytes
from pfefinder.rag.embeddings import get_embeddings
from pfefinder.rag.indexing.subject_text import subject_text
from pfefinder.rag.ingestion import validation_rules as rules
from pfefinder.rag.ingestion.pdf_loader import read_pdf
from pfefinder.rag.ingestion.text_blocks import split_into_blocks

log = logging.getLogger(__name__)


@dataclass
class IngestResult:
    status: str  # ingere | deja_connu | illisible | vide
    inseres: int = 0
    actifs: int = 0
    quarantaine: int = 0
    expires: int = 0
    entreprise: str | None = None


def ingest_pdf(data: bytes, source_url: str, origine: str = "agent") -> IngestResult:
    settings = get_settings()
    url_norm = normalize_url(source_url)
    file_hash = sha256_bytes(data)

    if documents.is_known(url_norm, file_hash):
        return IngestResult("deja_connu")
    try:
        text = read_pdf(data, settings.max_pages_par_pdf)
    except ValueError as exc:
        log.warning("PDF ignoré (%s) : %s", source_url, exc)
        documents.mark_processed(url_norm, file_hash, None, None, "illisible", origine)
        return IngestResult("illisible")

    chain = extract_chain()
    books = [chain.invoke({"text": block}) for block in split_into_blocks(text, settings.llm_block_chars)]
    return store_books(books, source_url, url_norm, file_hash, origine)


def store_books(books: list[ExtractedBook], source_url: str, url_norm: str, file_hash: str, origine: str) -> IngestResult:
    """Étapes communes à toutes les sources (PDF lu par le LLM, ou JSON déjà structuré) :
    fusion des métadonnées, règles de validation, embeddings, insertion, mémoire des documents traités."""
    rules.merge_book_metadata(books)  # entreprise, année, contact... se trouvent souvent dans un autre bloc
    first = books[0] if books else None
    rows_meta = []
    for book in books:
        for subject in book.sujets:
            statut, confiance = rules.decide_status(book, subject)
            rows_meta.append((book, subject, statut, confiance))

    if not rows_meta:
        documents.mark_processed(url_norm, file_hash, first.entreprise if first else None, None, "vide", origine)
        return IngestResult("vide")

    rows = [rules.to_row(b, s, st, c, source_url, None) for b, s, st, c in rows_meta]
    actives = [i for i, r in enumerate(rows) if r["statut"] == "actif"]
    if actives:
        vectors = get_embeddings().embed_documents([subject_text(rows[i]) for i in actives])
        for i, vec in zip(actives, vectors):
            rows[i]["embedding"] = vec

    inserted = subjects.insert_many(rows)
    entreprise = first.entreprise if first else None
    annee = first.annee if first else None
    documents.mark_processed(url_norm, file_hash, entreprise, annee, "traite", origine)
    return IngestResult(
        "ingere", inserted,
        actifs=sum(r["statut"] == "actif" for r in rows),
        quarantaine=sum(r["statut"] == "quarantaine" for r in rows),
        expires=sum(r["statut"] == "expire" for r in rows),
        entreprise=entreprise,
    )
