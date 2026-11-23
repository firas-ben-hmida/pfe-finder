from fastapi import APIRouter, Request

from app.core.rate_limit import limiter
from app.schemas.profile import Profile
from app.schemas.subject import SubjectSummary
from app.services import matching

router = APIRouter(tags=["matching"])


@router.post("/matching", response_model=list[SubjectSummary])
@limiter.limit("20/minute")
def match_subjects(request: Request, profile: Profile) -> list[SubjectSummary]:
    """Sujets classés par pertinence pour un profil."""
    return matching.match(profile)
