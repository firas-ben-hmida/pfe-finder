from datetime import date
from typing import Any

from pydantic import BaseModel, Field, field_validator


def _none_to_list(value: Any) -> Any:
    return [] if value is None else value


class SubjectSummary(BaseModel):
    """Sujet affiché dans la liste des résultats."""

    id: int
    entreprise: str
    titre: str
    technos: list[str] = Field(default_factory=list)
    ville: str | None = None
    pays: str | None = None
    annee: int | None = None
    score: float | None = None
    raison: str | None = None

    _technos_defaut = field_validator("technos", mode="before")(_none_to_list)


class SubjectDetail(SubjectSummary):
    """Détail complet d'un sujet."""

    numero: str | None = None
    description: str | None = None
    source_url: str | None = None
    page_source: int | None = None
    date_limite: date | None = None


class ApplyInfo(BaseModel):
    """Comment postuler à un sujet."""

    mode_candidature: str = "inconnu"  # email | formulaire | portail | inconnu
    contact_candidature: str | None = None
    documents_requis: list[str] = Field(default_factory=list)
    etapes_candidature: str | None = None
    date_limite: date | None = None
    source_url: str | None = None

    _documents_defaut = field_validator("documents_requis", mode="before")(_none_to_list)

    @field_validator("mode_candidature", mode="before")
    @classmethod
    def _mode_defaut(cls, value: Any) -> Any:
        return value or "inconnu"
