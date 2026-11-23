from fastapi import APIRouter, HTTPException, Request, UploadFile

from pfefinder.api.rate_limit import limiter
from pfefinder.api.services import cv_text_extractor, matching_service
from pfefinder.config.settings import get_settings
from pfefinder.domain.models import SubjectSummary

router = APIRouter(tags=["matching"])


@router.post("/match", response_model=list[SubjectSummary])
@limiter.limit("10/minute")
async def match_cv(request: Request, file: UploadFile) -> list[SubjectSummary]:
    """Reçoit un CV PDF, renvoie les sujets classés. Le CV n'est jamais stocké."""
    max_bytes = get_settings().max_cv_bytes
    data = await file.read(max_bytes + 1)
    if len(data) > max_bytes:
        raise HTTPException(413, "Fichier trop volumineux.")
    try:
        text = cv_text_extractor.extract_text(data)
    except ValueError as exc:
        raise HTTPException(422, str(exc)) from exc
    return matching_service.match(matching_service.extract_profile(text), text)
