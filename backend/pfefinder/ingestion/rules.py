"""Règles de validation. Le LLM propose, ce code décide du statut final (actif / quarantaine / expire)."""
from datetime import date
from typing import Any

from pfefinder.core.dates import is_expired, target_year
from pfefinder.core.hashing import hash_sujet
from pfefinder.core.schemas import ExtractedBook, ExtractedSubject

TUNISIAN_CITIES = {
    "tunis", "ariana", "ben arous", "manouba", "la marsa", "lac", "les berges du lac", "sousse", "sfax",
    "monastir", "nabeul", "bizerte", "gabes", "gabès", "kairouan", "mahdia", "charguia", "ennasr",
    "la goulette", "carthage", "hammamet", "djerba", "gafsa", "tozeur", "beja", "béja", "jendouba",
}
MIN_TITLE = 8


def is_tunisian(book: ExtractedBook, subject: ExtractedSubject) -> bool:
    pays = (book.pays or "").strip().lower()
    if pays:
        return pays in {"tunisie", "tunisia", "tn"}
    ville = (subject.ville or book.ville or "").strip().lower()
    return ville in TUNISIAN_CITIES


def decide_status(book: ExtractedBook, subject: ExtractedSubject, today: date | None = None) -> tuple[str, float]:
    """Retourne (statut, confiance). Doute => quarantaine, jamais publication."""
    today = today or date.today()
    if not book.entreprise or len(subject.titre.strip()) < MIN_TITLE:
        return "quarantaine", 0.2
    if is_expired(book.date_limite, book.annee, today):
        return "expire", 1.0
    if book.annee is None or book.annee < target_year(today):
        return "quarantaine", 0.4
    if not is_tunisian(book, subject):
        return "quarantaine", 0.4
    score = 0.6 + (0.15 if subject.description else 0) + (0.1 if subject.technos else 0) \
        + (0.15 if book.mode_candidature != "inconnu" else 0)
    return "actif", round(min(score, 1.0), 2)


def to_row(book: ExtractedBook, subject: ExtractedSubject, statut: str, confiance: float,
           source_url: str, embedding: list[float] | None) -> dict[str, Any]:
    return {
        "hash_sujet": hash_sujet(book.entreprise or "", subject.titre, book.annee),
        "entreprise": book.entreprise or "inconnue",
        "numero": subject.numero,
        "titre": subject.titre.strip(),
        "description": subject.description,
        "technos": subject.technos,
        "ville": subject.ville or book.ville,
        "pays": "Tunisie" if is_tunisian(book, subject) else (book.pays or "inconnu"),
        "annee": book.annee,
        "mode_candidature": book.mode_candidature,
        "contact_candidature": book.contact_candidature,
        "documents_requis": book.documents_requis,
        "etapes_candidature": book.etapes_candidature,
        "date_limite": book.date_limite.isoformat() if book.date_limite else None,
        "statut": statut,
        "confiance": confiance,
        "source_url": source_url,
        "page_source": subject.page_source,
        "embedding": embedding if statut == "actif" else None,
    }
