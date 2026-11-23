"""Classement hybride : ressemblance vectorielle + recoupement lexical profil / sujet.

L'embedding capte le sens général mais ses scores sont très serrés d'un sujet à l'autre.
Le recoupement des compétences du profil avec les technologies et le texte du sujet
départage mieux les sujets proches (ex. Java/Spring Boot vs systèmes embarqués).
"""
import re
import unicodedata

from langchain_core.documents import Document

VECTOR_WEIGHT = 0.4
LEXICAL_WEIGHT = 0.6


def normalize(text: str) -> str:
    """Minuscules, sans accents, ponctuation remplacée par des espaces ('CI/CD' -> 'ci cd')."""
    decomposed = unicodedata.normalize("NFKD", text.lower())
    ascii_only = "".join(c for c in decomposed if not unicodedata.combining(c))
    return " " + re.sub(r"[^a-z0-9+#]+", " ", ascii_only).strip() + " "


def profile_terms(skills: list[str], domains: list[str]) -> set[str]:
    terms = {normalize(t).strip() for t in [*skills, *domains]}
    return {t for t in terms if len(t) >= 2}


def lexical_overlap(terms: set[str], haystack: str) -> float:
    """Part des termes du profil retrouvés (mots entiers) dans le texte du sujet."""
    if not terms:
        return 0.0
    text = normalize(haystack)
    return sum(1 for t in terms if f" {t} " in text) / len(terms)


def rank(docs: list[Document], terms: set[str]) -> list[tuple[Document, float]]:
    """Retourne (document, score combiné 0..1) trié du meilleur au moins bon."""
    if not docs:
        return []
    sims = [d.metadata.get("similarity") or 0.0 for d in docs]
    lexical = [lexical_overlap(terms, d.page_content) for d in docs]
    lo, hi = min(sims), max(sims)
    max_lex = max(lexical)
    scored = []
    for d, sim, lex in zip(docs, sims, lexical):
        vec_n = (sim - lo) / (hi - lo) if hi > lo else 1.0
        lex_n = lex / max_lex if max_lex > 0 else 0.0
        score = VECTOR_WEIGHT * vec_n + LEXICAL_WEIGHT * lex_n if max_lex > 0 else vec_n
        scored.append((d, score))
    return sorted(scored, key=lambda x: x[1], reverse=True)
