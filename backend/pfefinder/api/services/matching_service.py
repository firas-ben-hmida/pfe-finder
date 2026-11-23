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


def diversify(docs: list, k: int, max_per_company: int = 3) -> list:
    """Garde l'ordre de pertinence mais limite le nombre de sujets par entreprise,
    pour que le classement ne soit pas monopolisé par un seul PFE book."""
    counts: dict[str, int] = {}
    picked = []
    for d in docs:
        company = d.metadata.get("entreprise") or ""
        if counts.get(company, 0) >= max_per_company:
            continue
        counts[company] = counts.get(company, 0) + 1
        picked.append(d)
        if len(picked) == k:
            break
    return picked


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
    start = time.perf_counter()
    k = get_settings().matching_top_k
    candidates = SubjectRetriever(top_k=k * 5).invoke(query)
    docs = diversify(candidates, k)
    log.info("Recherche vectorielle : %d sujets en %.1f s", len(docs), time.perf_counter() - start)
    if not docs:
        return []

    reasons: dict[int, str] = {}
    start = time.perf_counter()
    try:
        listing = "\n\n".join(f"[id={d.metadata['id']}] {d.page_content}" for d in docs)
        result = reason_chain().invoke({"profile": profile.model_dump_json(), "subjects": listing})
        reasons = {r.id: r.raison for r in result.raisons}
        log.info("Raisons générées en %.1f s", time.perf_counter() - start)
    except Exception as exc:
        log.warning("Raisons indisponibles après %.1f s : %s", time.perf_counter() - start, exc)  # la liste reste utile sans les justifications

    return [
        SubjectSummary(**{k: d.metadata.get(k) for k in SubjectSummary.model_fields if k not in ("score", "raison")},
                       score=d.metadata.get("similarity"), raison=reasons.get(d.metadata["id"]))
        for d in docs
    ]
