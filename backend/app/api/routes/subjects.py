from fastapi import APIRouter, HTTPException

from app.repositories import subjects as subjects_repo
from app.schemas.subject import ApplyInfo, SubjectDetail

router = APIRouter(tags=["subjects"])


def _get_or_404(subject_id: int) -> dict:
    row = subjects_repo.get_active(subject_id)
    if row is None:
        raise HTTPException(status_code=404, detail="Sujet introuvable.")
    return row


@router.get("/subjects/{subject_id}", response_model=SubjectDetail)
def get_subject(subject_id: int) -> SubjectDetail:
    return SubjectDetail.model_validate(_get_or_404(subject_id))


@router.get("/subjects/{subject_id}/apply", response_model=ApplyInfo)
def get_apply_info(subject_id: int) -> ApplyInfo:
    return ApplyInfo.model_validate(_get_or_404(subject_id))
