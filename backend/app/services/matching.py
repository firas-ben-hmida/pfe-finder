from pydantic import BaseModel

from app.core.config import get_settings
from app.core.errors import UpstreamError
from app.rag.embeddings import embed_text
from app.rag.llm import generate_structured
from app.rag.prompts import explanation_prompt
from app.repositories import subjects as subjects_repo
from app.schemas.profile import Profile
from app.schemas.subject import SubjectSummary


class _Explanation(BaseModel):
    id: int
    raison: str


class _Explanations(BaseModel):
    items: list[_Explanation]


def _query_text(profile: Profile) -> str:
    parts = [*profile.domaines, *profile.competences, *profile.projets[:5]]
    return "; ".join(p for p in parts if p)[:2000]


def match(profile: Profile) -> list[SubjectSummary]:
    """Sujets les plus proches du profil, avec une phrase d'explication chacun."""
    query = _query_text(profile)
    if not query.strip():
        return []

    rows = subjects_repo.search(embed_text(query), get_settings().matching_top_k)
    results = [
        SubjectSummary.model_validate({**row, "score": round(float(row["similarity"]), 3)})
        for row in rows
    ]
    if not results:
        return []

    # L'explication est un bonus : si le LLM échoue, on garde la liste sans raisons.
    try:
        explanations = generate_structured(
            explanation_prompt(profile.model_dump_json(), rows), _Explanations
        )
        reasons = {item.id: item.raison for item in explanations.items}
        for result in results:
            result.raison = reasons.get(result.id)
    except UpstreamError:
        pass
    return results
