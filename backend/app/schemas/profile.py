from pydantic import BaseModel, Field


class Profile(BaseModel):
    """Profil d'un étudiant extrait de son CV. Jamais stocké côté serveur."""

    competences: list[str] = Field(default_factory=list, description="Compétences techniques")
    domaines: list[str] = Field(default_factory=list, description="Domaines visés (IA, web, DevOps...)")
    projets: list[str] = Field(default_factory=list, description="Projets, une phrase chacun")
    experiences: list[str] = Field(default_factory=list, description="Stages et expériences")
    formation: str | None = None
    langues: list[str] = Field(default_factory=list)
