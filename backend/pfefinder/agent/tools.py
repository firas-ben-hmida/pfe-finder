"""Outils exposés à l'agent. Chacun applique les garde-fous avant d'agir."""
import time

import requests
from langchain_core.tools import tool

from pfefinder.agent import guardrails as g
from pfefinder.core.config import get_settings
from pfefinder.core.db import documents
from pfefinder.core.hashing import normalize_url

_calls = {"search": 0}
MAX_SEARCH_CALLS = 6
MAX_SUBMISSIONS = 10
_submitted: list[str] = []


def reset_quotas() -> None:
    _calls["search"] = 0
    _submitted.clear()


@tool
def search_pfe_books(query: str) -> list[dict]:
    """Cherche des PFE books tunisiens sur le web (Google Programmable Search). Renvoie titre, url, extrait."""
    s = get_settings()
    if _calls["search"] >= MAX_SEARCH_CALLS:
        return [{"erreur": "Quota de recherches atteint pour cette exécution."}]
    if not (s.google_cse_id and s.google_cse_key):
        return [{"erreur": "Moteur de recherche non configuré."}]
    _calls["search"] += 1
    resp = requests.get(
        "https://www.googleapis.com/customsearch/v1",
        params={"key": s.google_cse_key, "cx": s.google_cse_id, "q": query, "num": 10},
        timeout=20,
    )
    if resp.status_code != 200:
        return [{"erreur": f"Recherche indisponible (HTTP {resp.status_code})."}]
    results = []
    for item in resp.json().get("items", []):
        url = item.get("link", "")
        if g.is_http_url(url) and not g.is_blocked(url):
            results.append({"titre": item.get("title", ""), "url": url, "extrait": item.get("snippet", "")})
    return results


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


def fetch_pdfs_from_source(url: str) -> list[tuple[str, bytes]]:
    """Récupère les PDF d'une source : le PDF lui-même, ou ceux listés sur une page. Délai entre requêtes."""
    s = get_settings()
    data, ctype = g.safe_get(url, s.max_pdf_bytes, g.PDF_TYPES | g.HTML_TYPES)
    if data.startswith(b"%PDF-"):
        return [(url, data)]
    if ctype not in g.HTML_TYPES:
        return []
    out: list[tuple[str, bytes]] = []
    for link in g.find_pdf_links(data.decode("utf-8", errors="ignore"), url):
        time.sleep(s.agent_delai_secondes)
        try:
            pdf, _ = g.safe_get(link, s.max_pdf_bytes, g.PDF_TYPES)
        except (g.GuardrailError, requests.RequestException):
            continue
        if pdf.startswith(b"%PDF-"):
            out.append((link, pdf))
    return out
