"""Outils exposés à l'agent. Chacun applique les garde-fous avant d'agir."""
import requests
from langchain_core.tools import tool

from pfefinder.agent import guardrails as g
from pfefinder.common.fingerprints import normalize_url
from pfefinder.config.settings import get_settings
from pfefinder.repositories import documents_repository as documents

_calls = {"search": 0}
MAX_SEARCH_CALLS = 15  # pages explorées par exécution
MAX_SUBMISSIONS = 10
_submitted: list[str] = []


def reset_quotas() -> None:
    _calls["search"] = 0
    _submitted.clear()


@tool
def explore_page(url: str) -> list[dict]:
    """Ouvre une page d'un site de confiance et renvoie ses liens (url, texte). Sert à trouver les PFE books."""
    if _calls["search"] >= MAX_SEARCH_CALLS:
        return [{"erreur": "Quota de pages explorées atteint pour cette exécution."}]
    if not g.is_allowed_for_auto_ingest(url):
        return [{"erreur": "Domaine hors liste blanche : exploration refusée."}]
    _calls["search"] += 1
    try:
        data, _ = g.safe_get(url, get_settings().max_pdf_bytes, g.HTML_TYPES)
    except (g.GuardrailError, requests.RequestException) as exc:
        return [{"erreur": f"Page inaccessible : {exc}"}]
    return g.find_links(data.decode("utf-8", errors="ignore"), url)


@tool
def submit_source(url: str, titre: str = "", annee: int | None = None) -> str:
    """Propose une page ou un PDF de PFE book. Le code vérifie l'URL puis l'ajoute à la file de traitement."""
    if len(_submitted) >= MAX_SUBMISSIONS:
        return "Refusé : maximum de sources atteint pour cette exécution."
    try:
        g.check_url(url)
    except g.GuardrailError as exc:
        return f"Refusé : {exc}"
    added = documents.queue_source(url, normalize_url(url), titre or None, annee)
    if added:
        _submitted.append(url)
    return "Ajoutée à la file." if added else "Déjà connue, ignorée."
