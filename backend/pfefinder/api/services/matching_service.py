import logging
import time

from langchain_core.documents import Document

from pfefinder.config.settings import get_settings
from pfefinder.domain.models import Profile, SubjectSummary
from pfefinder.rag.generation.matching_chains import profile_chain, rerank_chain
from pfefinder.rag.retrieval import hybrid_ranking
from pfefinder.rag.retrieval.subject_retriever import SubjectRetriever
from pfefinder.repositories import subjects_repository as subjects_repo

log = logging.getLogger(__name__)

DESCRIPTION_CHARS = 700  # extrait de description transmis au LLM par sujet


def profile_query(profile: Profile) -> str:
    """Texte de recherche construit à partir du profil (même espace que les sujets indexés)."""
    parts = [*profile.domaines, *profile.competences, *profile.projets[:3], *profile.experiences[:2]]
    return "\n".join(p for p in parts if p)


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


def filter_cities(docs: list[Document], cities: list[str] | None) -> list[Document]:
    """Garde les sujets des villes choisies (et ceux dont la ville est inconnue). Aucune ville = toutes."""
    wanted = {c.strip().lower() for c in cities or [] if c.strip()}
    if not wanted:
        return docs
    return [d for d in docs if not d.metadata.get("ville") or d.metadata["ville"].strip().lower() in wanted]


def keep_relevant(docs: list, min_score: float, margin: float) -> list:
    """(Mode dégradé) garde les sujets dont le score est proche du meilleur."""
    if not docs:
        return []
    scores = [d.metadata.get("similarity") or 0 for d in docs]
    cutoff = max(min_score, max(scores) - margin)
    return [d for d, s in zip(docs, scores) if s >= cutoff]


def _listing(docs: list[Document]) -> str:
    blocks = []
    for d in docs:
        m = d.metadata
        technos = ", ".join(m.get("technos") or [])
        blocks.append(f"[id={m['id']}] {m.get('titre', '')} ({m.get('entreprise', '')})\n"
                      f"Technologies : {technos}\n{(m.get('description') or '')[:DESCRIPTION_CHARS]}")
    return "\n\n".join(blocks)


def _summary(doc: Document, score: float, reason: str | None) -> SubjectSummary:
    fields = {f: doc.metadata.get(f) for f in SubjectSummary.model_fields if f not in ("score", "raison")}
    return SubjectSummary(**fields, score=round(score, 3), raison=reason)


def match(profile: Profile, cv_text: str = "", cities: list[str] | None = None) -> list[SubjectSummary]:
    """RAG hybride : retrieve (pgvector) -> classement lexical+vectoriel -> le LLM note les meilleurs candidats.

    Seuls les sujets réellement pertinents pour le CV sont renvoyés, du plus au moins pertinent.
    """
    settings = get_settings()
    query = profile_query(profile).strip() or cv_text[:4000].strip()  # profil vide : texte brut du CV
    if not query:
        return []

    start = time.perf_counter()
    found = filter_cities(SubjectRetriever(top_k=settings.matching_candidates).invoke(query), cities)
    if not found:
        return []
    texts = subjects_repo.descriptions([d.metadata["id"] for d in found])
    for d in found:
        d.metadata["description"] = texts.get(d.metadata["id"], "")
        d.page_content = f"{d.page_content}\n{d.metadata['description']}"
    terms = hybrid_ranking.profile_terms(profile.competences, profile.domaines)
    ranked = hybrid_ranking.rank(found, terms)[: settings.matching_rerank_count]
    log.info("Recherche hybride : %d candidats en %.1f s", len(ranked), time.perf_counter() - start)
    for rank, (d, score) in enumerate(ranked[:5], 1):
        log.info("  #%d  combiné=%.2f  %s | %s", rank, score, d.metadata.get("entreprise", "")[:12],
                 d.metadata.get("titre", "")[:70])

    start = time.perf_counter()
    try:
        result = rerank_chain().invoke({"profile": profile.model_dump_json(), "subjects": _listing([d for d, _ in ranked])})
        judged = {j.id: j for j in result.sujets}
        log.info("Notation par le LLM de %d sujets en %.1f s", len(judged), time.perf_counter() - start)
    except Exception as exc:
        log.warning("Notation indisponible après %.1f s, classement hybride seul : %s", time.perf_counter() - start, exc)
        judged = {}

    if judged:
        kept = [(d, score, judged[d.metadata["id"]]) for d, score in ranked
                if d.metadata["id"] in judged and judged[d.metadata["id"]].pertinence >= settings.matching_min_relevance]
        kept.sort(key=lambda x: (x[2].pertinence, x[1]), reverse=True)
        log.info("%d sujets pertinents (note >= %d) sur %d candidats", len(kept), settings.matching_min_relevance, len(ranked))
        return [_summary(d, j.pertinence / 10, j.raison) for d, _, j in kept]

    # Mode dégradé : pas de LLM, on garde les sujets proches du meilleur score hybride.
    best = ranked[0][1]
    return [_summary(d, score, None) for d, score in ranked if score >= best - 0.25]
