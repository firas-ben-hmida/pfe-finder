"""Mémoire de l'agent : documents déjà traités et sources à traiter (jamais deux fois le même PDF)."""
from typing import Any

from pfefinder.core.db.client import get_db


def is_known(url_normalisee: str | None = None, hash_fichier: str | None = None) -> bool:
    table = get_db().table("documents_traites")
    if url_normalisee and table.select("id").eq("url_normalisee", url_normalisee).limit(1).execute().data:
        return True
    if hash_fichier and table.select("id").eq("hash_fichier", hash_fichier).limit(1).execute().data:
        return True
    return False


def mark_processed(url_normalisee: str, hash_fichier: str, entreprise: str | None, annee: int | None,
                   statut: str, origine: str = "agent") -> None:
    get_db().table("documents_traites").upsert(
        {"url_normalisee": url_normalisee, "hash_fichier": hash_fichier, "entreprise": entreprise,
         "annee": annee, "statut": statut, "origine": origine},
        on_conflict="url_normalisee",
    ).execute()


def queue_source(url: str, url_normalisee: str, titre: str | None, annee: int | None) -> bool:
    """Ajoute une source à la file ; renvoie False si elle y est déjà."""
    db = get_db()
    if db.table("sources_a_traiter").select("id").eq("url_normalisee", url_normalisee).limit(1).execute().data:
        return False
    db.table("sources_a_traiter").insert(
        {"url": url, "url_normalisee": url_normalisee, "titre": titre, "annee": annee}
    ).execute()
    return True


def pending_sources(limit: int) -> list[dict[str, Any]]:
    return (get_db().table("sources_a_traiter").select("*").eq("statut", "a_traiter")
            .order("id").limit(limit).execute().data or [])


def set_source_status(source_id: int, statut: str) -> None:
    get_db().table("sources_a_traiter").update({"statut": statut}).eq("id", source_id).execute()
