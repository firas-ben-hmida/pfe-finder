"""Exécution quotidienne : expiration -> découverte (agent) -> traitement de la file (code).

    python -m pfefinder.agent.daily_run            # tout
    python -m pfefinder.agent.daily_run --no-discovery
"""
import argparse
import logging
import time

import requests

from pfefinder.agent import guardrails as g
from pfefinder.agent.discovery_agent import build_agent
from pfefinder.agent.discovery_tools import reset_quotas
from pfefinder.agent.source_fetcher import fetch_pdfs_from_source
from pfefinder.config.settings import get_settings
from pfefinder.common.academic_year import target_year
from pfefinder.repositories import documents_repository as documents
from pfefinder.rag.ingestion.subject_expiry import run_expiry
from pfefinder.rag.ingestion.ingestion_pipeline import ingest_pdf

log = logging.getLogger("agent")


def discover() -> None:
    settings = get_settings()
    reset_quotas()
    year = target_year()
    task = f"Trouve des PFE books {year} d'entreprises tunisiennes et soumets les meilleures sources."
    build_agent().invoke({"messages": [("user", task)]}, config={"recursion_limit": settings.agent_recursion_limit})


def process_queue() -> None:
    settings = get_settings()
    budget = settings.max_pdfs_par_jour
    for source in documents.pending_sources(limit=50):
        if budget <= 0:
            log.info("Quota journalier atteint, le reste attend demain.")
            return
        url = source["url"]
        if not g.is_allowed_for_auto_ingest(url):
            documents.set_source_status(source["id"], "a_valider")  # un humain décide
            log.info("Hors liste blanche, mise en attente : %s", url)
            continue
        try:
            pdfs = fetch_pdfs_from_source(url)
        except (g.GuardrailError, requests.RequestException) as exc:
            log.warning("Source refusée (%s) : %s", url, exc)
            documents.set_source_status(source["id"], "refusee")
            continue
        for pdf_url, data in pdfs:
            if budget <= 0:
                break
            result = ingest_pdf(data, pdf_url)
            if result.status != "deja_connu":
                budget -= 1
            log.info("%s -> %s", pdf_url, result)
            time.sleep(settings.agent_delai_secondes)
        documents.set_source_status(source["id"], "traitee")


def main() -> None:
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
    parser = argparse.ArgumentParser()
    parser.add_argument("--no-discovery", action="store_true")
    args = parser.parse_args()
    log.info("%d sujet(s) expiré(s).", run_expiry())
    if not args.no_discovery:
        discover()
    process_queue()


if __name__ == "__main__":
    main()
