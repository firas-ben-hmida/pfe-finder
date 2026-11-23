"""Modèles Pydantic partagés par l'API, l'ingestion et l'agent."""
from datetime import date
from typing import Any, Literal

from pydantic import BaseModel, Field, field_validator


def _none_to_list(value: Any) -> Any:
    return [] if value is None else value


class Profile(BaseModel):
    """Profil d'un étudiant extrait de son CV. Jamais stocké côté serveur."""

    competences: list[str] = Field(default_factory=list, description="Compétences techniques")
    domaines: list[str] = Field(default_factory=list, description="Domaines visés (IA, web, DevOps...)")
    projets: list[str] = Field(default_factory=list, description="Projets, une phrase chacun")
    experiences: list[str] = Field(default_factory=list, description="Stages et expériences")
    formation: str | None = None
    langues: list[str] = Field(default_factory=list)


class SubjectSummary(BaseModel):
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
    numero: str | None = None
    description: str | None = None
    source_url: str | None = None
    page_source: int | None = None
    date_limite: date | None = None


class ApplyInfo(BaseModel):
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


class ExtractedSubject(BaseModel):
    """Un sujet extrait d'un PFE book par le LLM. Rien d'inventé : champs absents = None."""

    numero: str | None = None
    titre: str
    description: str | None = None
    technos: list[str] = Field(default_factory=list)
    ville: str | None = None
    page_source: int | None = None


class ExtractedBook(BaseModel):
    """Résultat structuré de l'extraction d'un PFE book."""

    entreprise: str | None = None
    annee: int | None = None
    pays: str | None = None
    ville: str | None = None
    mode_candidature: Literal["email", "formulaire", "portail", "inconnu"] = "inconnu"
    contact_candidature: str | None = None
    documents_requis: list[str] = Field(default_factory=list)
    etapes_candidature: str | None = None
    date_limite: date | None = None
    sujets: list[ExtractedSubject] = Field(default_factory=list)
