"""Ingestion manuelle (tests locaux) :

    python -m pfefinder.ingestion.cli fichier.pdf --url https://site.tn/pfe-book-2027.pdf
    python -m pfefinder.ingestion.cli --expire
"""
import argparse
import logging
from pathlib import Path

from pfefinder.ingestion.expiry import run_expiry
from pfefinder.ingestion.pipeline import ingest_pdf


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
