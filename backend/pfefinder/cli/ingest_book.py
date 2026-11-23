"""Ingestion manuelle (tests locaux) :

    python -m pfefinder.cli.ingest_book fichier.pdf --url https://site.tn/pfe-book-2027.pdf
    python -m pfefinder.cli.ingest_book --expire
"""
import argparse
import logging
from pathlib import Path

from pfefinder.rag.ingestion.subject_expiry import run_expiry
from pfefinder.rag.ingestion.ingestion_pipeline import ingest_pdf


def main() -> None:
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
    parser = argparse.ArgumentParser(description="Ingestion de PFE books")
    parser.add_argument("pdf", nargs="?", type=Path, help="Chemin d'un PDF local")
    parser.add_argument("--url", help="URL d'origine du PDF (sert de source et à la déduplication)")
    parser.add_argument("--expire", action="store_true", help="Expire les sujets périmés")
    args = parser.parse_args()

    if args.expire:
        print(f"{run_expiry()} sujet(s) expiré(s).")
    if args.pdf:
        if not args.url:
            parser.error("--url est obligatoire avec un PDF")
        print(ingest_pdf(args.pdf.read_bytes(), args.url, origine="manuel"))


if __name__ == "__main__":
    main()
