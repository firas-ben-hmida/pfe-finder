import logging
import time

from langchain_core.documents import Document

from pfefinder.config.settings import get_settings
from pfefinder.domain.models import Profile, SubjectSummary
from pfefinder.rag.generation.matching_chains import profile_chain, rerank_chain
from pfefinder.rag.indexing.subject_text import subject_text
from pfefinder.rag.retrieval import hybrid_ranking
from pfefinder.rag.retrieval.subject_retriever import SubjectRetriever
from pfefinder.repositories import subjects_repository as subjects_repo

log = logging.getLogger(__name__)

DESCRIPTION_CHARS = 500  # extrait de description transmis au LLM par sujet


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


def gather_candidates(query: str, terms: set[str], weights: dict[str, float],
                      rows: dict[int, dict], n: int) -> list[Document]:
    """Candidats = meilleurs sujets par recherche vectorielle + meilleurs par mots-clés sur tout le catalogue.

    Chaque méthode rattrape les oublis de l'autre (un sujet très proche du CV par ses technologies
    peut avoir un embedding moyen, et inversement).
    """
    docs: dict[int, Document] = {}
    for d in SubjectRetriever(top_k=n).invoke(query):
        full = rows.get(d.metadata["id"], {})
        d.metadata["description"] = full.get("description") or ""
        d.page_content = subject_text({**d.metadata, **full})
        docs[d.metadata["id"]] = d
    floor = min((d.metadata.get("similarity") or 0 for d in docs.values()), default=0.0)
    scored = sorted(((hybrid_ranking.lexical_overlap(terms, subject_text(r), weights), r) for r in rows.values()),
                    key=lambda x: x[0], reverse=True)
    for score, r in scored[:n]:
        if score > 0 and r["id"] not in docs:
            docs[r["id"]] = Document(page_content=subject_text(r), metadata={**r, "similarity": floor})
    return list(docs.values())


def judge(profile: Profile, docs: list[Document], batch: int) -> dict:
    """Fait noter les candidats par le LLM, par lots appelés en parallèle (plus rapide qu'un seul gros appel)."""
    chain = rerank_chain()
    payloads = [{"profile": profile.model_dump_json(), "subjects": _listing(docs[i:i + batch])}
                for i in range(0, len(docs), batch)]
    results = chain.batch(payloads, config={"max_concurrency": 4})
    return {j.id: j for r in results for j in r.sujets}


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
    terms = hybrid_ranking.profile_terms(profile.competences, profile.domaines)
    rows = {r["id"]: r for r in subjects_repo.active_subjects()}
    weights = hybrid_ranking.term_weights(terms, [subject_text(r) for r in rows.values()])
    found = gather_candidates(query, terms, weights, rows, settings.matching_candidates)
    found = filter_cities(found, cities)
    if not found:
        return []
    ranked = hybrid_ranking.rank(found, terms, weights)[: settings.matching_rerank_count]
    log.info("Recherche hybride : %d candidats en %.1f s", len(ranked), time.perf_counter() - start)
    for rank, (d, score) in enumerate(ranked[:5], 1):
        log.info("  #%d  combiné=%.2f  %s | %s", rank, score, d.metadata.get("entreprise", "")[:12],
                 d.metadata.get("titre", "")[:70])

    start = time.perf_counter()
    try:
        judged = judge(profile, [d for d, _ in ranked], settings.matching_rerank_batch)
        log.info("Notation par le LLM de %d sujets en %.1f s", len(judged), time.perf_counter() - start)
        for d, _ in ranked:
            j = judged.get(d.metadata["id"])
            log.info("  note=%s  %s | %s", j.pertinence if j else "-", d.metadata.get("entreprise", "")[:10],
                     d.metadata.get("titre", "")[:60])
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
