from fastapi import APIRouter, HTTPException

from pfefinder.repositories import subjects_repository as subjects_repo
from pfefinder.domain.models import ApplyInfo, SubjectDetail

router = APIRouter(prefix="/subjects", tags=["subjects"])


def _row(subject_id: int) -> dict:
    row = subjects_repo.get_active(subject_id)
    if row is None:
        raise HTTPException(404, "Sujet introuvable.")
    return row


@router.get("/{subject_id}", response_model=SubjectDetail)
def detail(subject_id: int) -> SubjectDetail:
    return SubjectDetail(**_row(subject_id))


@router.get("/{subject_id}/apply", response_model=ApplyInfo)
def apply_info(subject_id: int) -> ApplyInfo:
    return ApplyInfo(**_row(subject_id))
