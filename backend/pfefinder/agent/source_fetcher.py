"""Récupération des PDF d'une source, toujours via les garde-fous."""
import time

import requests

from pfefinder.agent import guardrails as g
from pfefinder.config.settings import get_settings


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
