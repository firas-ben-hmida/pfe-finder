"""Découpage d'un long texte en blocs pour le LLM, en coupant entre deux pages (jamais au milieu)."""
import re

PAGE_MARKER = re.compile(r"(?=^\[page \d+\]$)", re.MULTILINE)


def split_into_blocks(text: str, max_chars: int) -> list[str]:
    """Regroupe des pages entières jusqu'à max_chars ; une page trop longue est coupée en dernier recours."""
    pages = [p for p in PAGE_MARKER.split(text) if p.strip()]
    blocks: list[str] = []
    current = ""
    for page in pages:
        if current and len(current) + len(page) > max_chars:
            blocks.append(current)
            current = ""
        while len(page) > max_chars:
            blocks.append(page[:max_chars])
            page = page[max_chars:]
        current += page
    if current.strip():
        blocks.append(current)
    return blocks
