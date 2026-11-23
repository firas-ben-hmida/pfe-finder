from datetime import date
from typing import Any

from pfefinder.repositories.supabase_client import get_db
from pfefinder.common.errors import UpstreamError

SUMMARY_FIELDS = "id,entreprise,titre,technos,ville,pays,annee"


def search(embedding: list[float], top_k: int) -> list[dict[str, Any]]:
    """Recherche vectorielle via la fonction SQL match_sujets (sujets actifs, Tunisie)."""
    try:
        return get_db().rpc("match_sujets", {"query_embedding": embedding, "match_count": top_k}).execute().data or []
    except Exception as exc:
        raise UpstreamError("Échec de la recherche vectorielle.") from exc


def descriptions(ids: list[int]) -> dict[int, str]:
    """Descriptions complètes des sujets (la recherche vectorielle ne renvoie que le résumé)."""
    if not ids:
        return {}
    try:
        rows = get_db().table("sujets").select("id,description").in_("id", ids).execute().data or []
    except Exception as exc:
        raise UpstreamError("Échec de la lecture des sujets.") from exc
    return {r["id"]: r.get("description") or "" for r in rows}


def active_cities() -> list[str]:
    """Villes proposées dans les sujets actifs, triées."""
    try:
        rows = get_db().table("sujets").select("ville").eq("statut", "actif").limit(5000).execute().data or []
    except Exception as exc:
        raise UpstreamError("Échec de la lecture des villes.") from exc
    return sorted({r["ville"] for r in rows if r.get("ville")})


def get_active(subject_id: int) -> dict[str, Any] | None:
    try:
        rows = get_db().table("sujets").select("*").eq("id", subject_id).eq("statut", "actif").limit(1).execute().data
    except Exception as exc:
        raise UpstreamError("Échec de lecture du sujet.") from exc
    return rows[0] if rows else None


def exists_hash(hash_value: str) -> bool:
    rows = get_db().table("sujets").select("id").eq("hash_sujet", hash_value).limit(1).execute().data
    return bool(rows)


def insert_many(rows: list[dict[str, Any]]) -> int:
    """Insère des sujets ; hash_sujet est unique, les doublons sont ignorés."""
    if not rows:
        return 0
    result = get_db().table("sujets").upsert(rows, on_conflict="hash_sujet", ignore_duplicates=True).execute()
    return len(result.data or [])


def expire_outdated(today: date, year: int) -> int:
    """Passe en 'expire' les sujets dont la date limite ou l'année est dépassée."""
    db = get_db()
    by_date = db.table("sujets").update({"statut": "expire"}).eq("statut", "actif").lt("date_limite", today.isoformat()).execute()
    by_year = db.table("sujets").update({"statut": "expire"}).eq("statut", "actif").lt("annee", year).execute()
    return len(by_date.data or []) + len(by_year.data or [])
