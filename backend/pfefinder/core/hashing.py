import hashlib
import re
from urllib.parse import parse_qsl, urlencode, urlsplit, urlunsplit

_TRACKING = {"utm_source", "utm_medium", "utm_campaign", "utm_term", "utm_content", "fbclid", "gclid"}


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _norm(text: str) -> str:
    return re.sub(r"\s+", " ", text.strip().lower())


def hash_sujet(entreprise: str, titre: str, annee: int | None) -> str:
    """Empreinte stable d'un sujet : même entreprise + titre + année => même hash."""
    return sha256_bytes(f"{_norm(entreprise)}|{_norm(titre)}|{annee or ''}".encode())


def normalize_url(url: str) -> str:
    """Forme canonique d'une URL pour détecter les doublons."""
    parts = urlsplit(url.strip())
    host = (parts.hostname or "").lower().removeprefix("www.")
    path = parts.path.rstrip("/") or "/"
    query = urlencode(sorted((k, v) for k, v in parse_qsl(parts.query) if k.lower() not in _TRACKING))
    return urlunsplit((parts.scheme.lower() or "https", host, path, query, ""))
