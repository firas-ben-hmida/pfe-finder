"""Texte indexé pour un sujet : un chunk = un sujet entier."""
from typing import Any


def subject_text(row: dict[str, Any]) -> str:
    """Texte indexé pour un sujet (un chunk = un sujet entier)."""
    technos = ", ".join(row.get("technos") or [])
    return (f"{row.get('titre', '')}\nEntreprise : {row.get('entreprise', '')}\n"
            f"Technologies : {technos}\n{row.get('description') or ''}").strip()
