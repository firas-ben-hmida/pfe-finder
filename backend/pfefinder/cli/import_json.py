"""Importe un catalogue déjà structuré (JSON au format ExtractedBook), sans appeler le LLM :

    python -m pfefinder.cli.import_json data/wevioo-2027.json --url https://site.tn/pfe-book.pdf

Les règles de validation, les embeddings et la déduplication sont les mêmes que pour un PDF.
"""
import argparse
import json
import logging
from pathlib import Path

from pfefinder.common.fingerprints import normalize_url, sha256_bytes
from pfefinder.domain.models import ExtractedBook
from pfefinder.rag.ingestion.ingestion_pipeline import store_books
from pfefinder.repositories import documents_repository as documents


def main() -> None:
    logging.basicConfig(level=logging.WARNING)
    parser = argparse.ArgumentParser(description="Import d'un catalogue JSON")
    parser.add_argument("json_file", type=Path)
    parser.add_argument("--url", required=True, help="URL d'origine du catalogue (source affichée aux étudiants)")
    args = parser.parse_args()

    raw = args.json_file.read_bytes()
    url_norm, file_hash = normalize_url(args.url), sha256_bytes(raw)
    if documents.is_known(url_norm, file_hash):
        print("Déjà importé.")
        return
    data = json.loads(raw.decode("utf-8"))
    books = [ExtractedBook.model_validate(b) for b in (data if isinstance(data, list) else [data])]
    print(store_books(books, args.url, url_norm, file_hash, origine="manuel"))


if __name__ == "__main__":
    main()
