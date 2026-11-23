"""Pipeline unique d'ingestion : bytes PDF -> extraction LLM -> règles -> embeddings -> Supabase.

C'est le seul chemin d'écriture dans la table sujets (utilisé par le CLI et par l'agent).
"""
import logging
from dataclasses import dataclass

from pfefinder.core.chains import extract_chain
from pfefinder.core.config import get_settings
from pfefinder.core.db import documents, subjects
from pfefinder.core.hashing import normalize_url, sha256_bytes
from pfefinder.core.llm import get_embeddings
from pfefinder.core.retriever import subject_text
from pfefinder.ingestion import rules
from pfefinder.ingestion.pdf_reader import read_pdf

log = logging.getLogger(__name__)
CHUNK_CHARS = 60_000  # un catalogue long est découpé en blocs envoyés séparément au LLM


@dataclass
class IngestResult:
    status: str  # ingere | deja_connu | illisible | vide
    inseres: int = 0
    actifs: int = 0
    quarantaine: int = 0
    expires: int = 0
    entreprise: str | None = None


def _blocks(text: str) -> list[str]:
    return [text[i : i + CHUNK_CHARS] for i in range(0, len(text), CHUNK_CHARS)]


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
    first = None
    rows_meta = []
    for block in _blocks(text):
        book = chain.invoke({"text": block})
        first = first or book
        if book.entreprise is None and first.entreprise:
            book.entreprise = first.entreprise
        if book.annee is None:
            book.annee = first.annee
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
