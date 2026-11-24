"""Classement hybride : ressemblance vectorielle + recoupement lexical profil / sujet.

L'embedding capte le sens général mais ses scores sont très serrés d'un sujet à l'autre.
Le recoupement des compétences du profil avec les technologies et le texte du sujet
départage mieux les sujets proches (ex. Java/Spring Boot vs systèmes embarqués).
"""
import math
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


_SPLIT = re.compile(r"[,;|·•\n]|\s/\s|\set\s")
MAX_TERM_WORDS = 4


def profile_terms(skills: list[str], domains: list[str]) -> set[str]:
    """Termes de recherche tirés du profil.

    Le LLM renvoie parfois une catégorie entière dans un seul élément (« Back-end : Spring Boot, FastAPI, … ») :
    on retire l'étiquette avant « : », puis on sépare sur les virgules et les séparateurs courants.
    Les termes trop longs (plus de 4 mots) ne correspondraient à aucun sujet et sont écartés.
    """
    terms: set[str] = set()
    for item in [*skills, *domains]:
        label_free = item.split(":", 1)[1] if ":" in item else item
        for part in _SPLIT.split(label_free):
            term = normalize(part).strip()
            if len(term) >= 2 and len(term.split()) <= MAX_TERM_WORDS:
                terms.add(term)
    return terms


def term_weights(terms: set[str], catalogue_texts: list[str]) -> dict[str, float]:
    """Poids de chaque terme du profil selon sa rareté dans le catalogue (IDF).

    « spring boot » (rare) discrimine bien ; « ia » ou « python » (présents dans presque tous
    les sujets) comptent beaucoup moins.
    """
    normalized = [normalize(x) for x in catalogue_texts]
    n = len(normalized)
    weights = {}
    for term in terms:
        df = sum(1 for text in normalized if f" {term} " in text)
        weights[term] = math.log((n + 1) / (df + 1)) + 0.1
    return weights


def cv_emphasis(terms: set[str], cv_text: str) -> dict[str, float]:
    """Importance d'un terme dans le CV : plus il revient (stages, projets, compétences), plus il compte.

    Un mot cité une seule fois (« passionné par l'IA ») pèse moins que la stack réellement pratiquée.
    """
    text = normalize(cv_text)
    return {t: 1.0 + math.log(1 + text.count(f" {t} ")) for t in terms}


def combine_weights(*maps: dict[str, float]) -> dict[str, float]:
    """Multiplie plusieurs pondérations terme par terme."""
    keys = set().union(*maps) if maps else set()
    out = {}
    for k in keys:
        value = 1.0
        for m in maps:
            value *= m.get(k, 1.0)
        out[k] = value
    return out


def lexical_overlap(terms: set[str], haystack: str, weights: dict[str, float] | None = None) -> float:
    """Part (pondérée) des termes du profil retrouvés, en mots entiers, dans le texte du sujet."""
    if not terms:
        return 0.0
    text = normalize(haystack)
    w = weights or {}
    total = sum(w.get(t, 1.0) for t in terms)
    found = sum(w.get(t, 1.0) for t in terms if f" {t} " in text)
    return found / total if total else 0.0


def rank(docs: list[Document], terms: set[str],
         weights: dict[str, float] | None = None) -> list[tuple[Document, float]]:
    """Retourne (document, score combiné 0..1) trié du meilleur au moins bon."""
    if not docs:
        return []
    sims = [d.metadata.get("similarity") or 0.0 for d in docs]
    lexical = [lexical_overlap(terms, d.page_content, weights) for d in docs]
    lo, hi = min(sims), max(sims)
    max_lex = max(lexical)
    scored = []
    for d, sim, lex in zip(docs, sims, lexical):
        vec_n = (sim - lo) / (hi - lo) if hi > lo else 1.0
        lex_n = lex / max_lex if max_lex > 0 else 0.0
        score = VECTOR_WEIGHT * vec_n + LEXICAL_WEIGHT * lex_n if max_lex > 0 else vec_n
        scored.append((d, score))
    return sorted(scored, key=lambda x: x[1], reverse=True)
