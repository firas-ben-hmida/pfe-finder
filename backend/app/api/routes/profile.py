from fastapi import APIRouter, File, HTTPException, Request, UploadFile

from app.core.config import get_settings
from app.core.rate_limit import limiter
from app.schemas.profile import Profile
from app.services import cv_parser, profile_extractor

router = APIRouter(tags=["profile"])


@router.post("/profile", response_model=Profile)
@limiter.limit("10/minute")
def create_profile(request: Request, cv: UploadFile = File(...)) -> Profile:
    """Lit un CV (PDF) et renvoie le profil extrait. Rien n'est enregistré."""
    max_bytes = get_settings().max_cv_bytes
    data = cv.file.read(max_bytes + 1)
    if len(data) > max_bytes:
        raise HTTPException(status_code=413, detail="Fichier trop volumineux.")
    try:
        text = cv_parser.extract_text(data)
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    return profile_extractor.extract_profile(text)
