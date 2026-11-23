from typing import Annotated

from fastapi import APIRouter, Form, HTTPException, Request, UploadFile

from pfefinder.api.rate_limit import limiter
from pfefinder.api.services import cv_text_extractor, matching_service
from pfefinder.config.settings import get_settings
from pfefinder.domain.models import SubjectSummary
from pfefinder.repositories import subjects_repository as subjects_repo

router = APIRouter(tags=["matching"])


@router.post("/match", response_model=list[SubjectSummary])
@limiter.limit("10/minute")
async def match_cv(request: Request, file: UploadFile,
                   villes: Annotated[list[str] | None, Form()] = None) -> list[SubjectSummary]:
    """Reçoit un CV PDF (et les villes souhaitées), renvoie les sujets pertinents classés. Le CV n'est jamais stocké."""
    max_bytes = get_settings().max_cv_bytes
    data = await file.read(max_bytes + 1)
    if len(data) > max_bytes:
        raise HTTPException(413, "Fichier trop volumineux.")
    try:
        text = cv_text_extractor.extract_text(data)
    except ValueError as exc:
        raise HTTPException(422, str(exc)) from exc
    return matching_service.match(matching_service.extract_profile(text), text, villes)


@router.get("/cities", response_model=list[str])
def cities() -> list[str]:
    """Villes où des sujets sont proposés, pour le choix de l'étudiant."""
    return subjects_repo.active_cities()
