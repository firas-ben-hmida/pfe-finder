from app.rag.llm import generate_structured
from app.rag.prompts import profile_prompt
from app.schemas.profile import Profile


def extract_profile(cv_text: str) -> Profile:
    """Transforme le texte d'un CV en profil structuré."""
    return generate_structured(profile_prompt(cv_text), Profile)
