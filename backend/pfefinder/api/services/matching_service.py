import logging
import time

from pfefinder.rag.generation.matching_chains import profile_chain, reason_chain
from pfefinder.config.settings import get_settings
from pfefinder.rag.retrieval.subject_retriever import SubjectRetriever
from pfefinder.domain.models import Profile, SubjectSummary


log = logging.getLogger(__name__)


def profile_query(profile: Profile) -> str:
    """Texte de recherche construit à partir du profil (même espace que les sujets indexés)."""
    parts = [*profile.domaines, *profile.competences, *profile.projets[:3], *profile.experiences[:2]]
    return "\n".join(p for p in parts if p)


def keep_relevant(docs: list, min_score: float, margin: float) -> list:
    """Ne garde que les sujets qui correspondent au CV : score absolu suffisant ET proche du meilleur.

    Les scores d'embeddings n'ont pas de valeur universelle : on mesure donc l'écart au meilleur sujet
    plutôt que de fixer un seuil unique.
    """
    if not docs:
        return []
    scores = [d.metadata.get("similarity") or 0 for d in docs]
    cutoff = max(min_score, max(scores) - margin)
    return [d for d, s in zip(docs, scores) if s >= cutoff]


def extract_profile(cv_text: str) -> Profile:
    start = time.perf_counter()
    try:
        profile = profile_chain().invoke({"cv": cv_text})
        log.info("Profil extrait en %.1f s", time.perf_counter() - start)
        return profile
    except Exception as exc:
        # Mode dégradé : sans LLM, la recherche vectorielle utilise directement le texte du CV.
        log.warning("Analyse du CV par le LLM indisponible, recherche sur le texte brut : %s", exc)
        return Profile()


def match(profile: Profile, cv_text: str = "") -> list[SubjectSummary]:
    """RAG : retrieve (pgvector) puis le LLM justifie uniquement à partir des sujets récupérés."""
    query = profile_query(profile).strip() or cv_text[:4000].strip()  # profil vide : on cherche avec le texte du CV
    if not query:
        return []
    settings = get_settings()
    start = time.perf_counter()
    found = SubjectRetriever(top_k=settings.matching_top_k).invoke(query)
    docs = keep_relevant(found, settings.matching_min_score, settings.matching_score_margin)
    log.info("Recherche vectorielle : %d sujets pertinents sur %d en %.1f s", len(docs), len(found), time.perf_counter() - start)
    for rank, d in list(enumerate(docs, 1))[:5] + list(enumerate(docs, 1))[-2:]:
        log.info("  #%d  score=%.3f  %s | %s", rank, d.metadata.get("similarity") or 0,
                 d.metadata.get("entreprise", "")[:12], d.metadata.get("titre", "")[:70])
    log.info("Requête de recherche (%d car.) : %s", len(query), query[:300].replace("\n", " ; "))
    if not docs:
        return []

    # Le LLM ne justifie que les sujets de tête : écrire 100 raisons prendrait plusieurs minutes.
    reasons: dict[int, str] = {}
    start = time.perf_counter()
    try:
        listing = "\n\n".join(f"[id={d.metadata['id']}] {d.page_content}" for d in docs[: settings.matching_reasons_count])
        result = reason_chain().invoke({"profile": profile.model_dump_json(), "subjects": listing})
        reasons = {r.id: r.raison for r in result.raisons}
        log.info("Raisons générées en %.1f s", time.perf_counter() - start)
    except Exception as exc:
        log.warning("Raisons indisponibles après %.1f s : %s", time.perf_counter() - start, exc)  # la liste reste utile sans les justifications

    return [
        SubjectSummary(**{f: d.metadata.get(f) for f in SubjectSummary.model_fields if f not in ("score", "raison")},
                       score=d.metadata.get("similarity"), raison=reasons.get(d.metadata["id"]))
        for d in docs
    ]
