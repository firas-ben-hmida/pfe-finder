from app.core.errors import UpstreamError
from app.repositories.db import get_db

# Colonnes renvoyées au détail (sans l'embedding, trop volumineux).
DETAIL_COLUMNS = (
    "id, entreprise, numero, titre, description, technos, ville, pays, annee, "
    "mode_candidature, contact_candidature, documents_requis, etapes_candidature, "
    "date_limite, source_url, page_source"
)


def search(embedding: list[float], k: int, pays: str | None = "Tunisie") -> list[dict]:
    """Sujets actifs les plus proches d'un embedding (fonction SQL match_sujets)."""
    try:
        response = (
            get_db()
            .rpc(
                "match_sujets",
                {"query_embedding": embedding, "match_count": k, "filter_pays": pays},
            )
            .execute()
        )
    except Exception as exc:
        raise UpstreamError("La base de données est indisponible.") from exc
    return response.data or []


def get_active(subject_id: int) -> dict | None:
    """Un sujet actif par identifiant, ou None."""
    try:
        response = (
            get_db()
            .table("sujets")
            .select(DETAIL_COLUMNS)
            .eq("id", subject_id)
            .eq("statut", "actif")
            .limit(1)
            .execute()
        )
    except Exception as exc:
        raise UpstreamError("La base de données est indisponible.") from exc
    return response.data[0] if response.data else None
