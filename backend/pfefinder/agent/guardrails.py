"""Garde-fous de l'agent. Ils vivent dans le code : aucun prompt ne peut les contourner."""
import json
import re
import urllib.robotparser
from dataclasses import dataclass
from pathlib import Path
from urllib.parse import urljoin, urlsplit

import requests

USER_AGENT = "PFEFinderBot/0.1 (projet étudiant; contact: voir README)"
_DOMAINS = json.loads((Path(__file__).parent / "domains.json").read_text(encoding="utf-8"))
ALLOWED_DOMAINS: set[str] = set(_DOMAINS["allowed"])
BLOCKED_DOMAINS: set[str] = set(_DOMAINS["blocked"])
SEED_URLS: list[str] = list(_DOMAINS.get("seeds", []))
PDF_TYPES = {"application/pdf", "application/octet-stream"}
HTML_TYPES = {"text/html", "application/xhtml+xml"}


class GuardrailError(Exception):
    """Une action est refusée par un garde-fou."""


def host_of(url: str) -> str:
    return (urlsplit(url).hostname or "").lower().removeprefix("www.")


def _matches(host: str, domains: set[str]) -> bool:
    return any(host == d or host.endswith("." + d) for d in domains)


def is_http_url(url: str) -> bool:
    return urlsplit(url).scheme in {"http", "https"} and bool(host_of(url))


def is_blocked(url: str) -> bool:
    return _matches(host_of(url), BLOCKED_DOMAINS)


def is_allowed_for_auto_ingest(url: str) -> bool:
    return _matches(host_of(url), ALLOWED_DOMAINS)


def parse_content_signals(robots_text: str) -> dict[str, bool]:
    """Lit les lignes 'Content-Signal: ai-train=no, search=yes' (Cloudflare). True = autorisé."""
    signals: dict[str, bool] = {}
    for line in robots_text.splitlines():
        line = line.split("#", 1)[0].strip()
        if line.lower().startswith("content-signal:"):
            for item in line.split(":", 1)[1].split(","):
                if "=" in item:
                    key, value = item.split("=", 1)
                    signals[key.strip().lower()] = value.strip().lower() == "yes"
    return signals


@dataclass
class RobotsDecision:
    allowed: bool
    reason: str


def evaluate_robots(robots_text: str | None, url: str) -> RobotsDecision:
    """robots.txt absent => autorisé ; sinon on respecte les règles et les Content-Signals."""
    if robots_text is None:
        return RobotsDecision(True, "pas de robots.txt")
    parser = urllib.robotparser.RobotFileParser()
    parser.parse(robots_text.splitlines())
    if not parser.can_fetch(USER_AGENT, url):
        return RobotsDecision(False, "interdit par robots.txt")
    signals = parse_content_signals(robots_text)
    for key in ("ai-input", "ai-train"):
        if signals.get(key) is False:
            return RobotsDecision(False, f"Content-Signal {key}=no")
    return RobotsDecision(True, "autorisé")


def fetch_robots(url: str, timeout: float = 10) -> str | None:
    parts = urlsplit(url)
    try:
        resp = requests.get(f"{parts.scheme}://{parts.netloc}/robots.txt", headers={"User-Agent": USER_AGENT}, timeout=timeout)
    except requests.RequestException as exc:
        raise GuardrailError("robots.txt injoignable : par prudence, on n'y va pas.") from exc
    if resp.status_code == 404:
        return None
    if resp.status_code != 200:
        raise GuardrailError(f"robots.txt illisible (HTTP {resp.status_code}).")
    return resp.text


def check_url(url: str) -> None:
    """Contrôles sans réseau : schéma et domaines bloqués."""
    if not is_http_url(url):
        raise GuardrailError("URL invalide.")
    if is_blocked(url):
        raise GuardrailError(f"Domaine interdit : {host_of(url)}.")


def safe_get(url: str, max_bytes: int, accept: set[str], timeout: float = 30) -> tuple[bytes, str]:
    """Télécharge en respectant robots.txt, le type de contenu et la taille maximale."""
    check_url(url)
    decision = evaluate_robots(fetch_robots(url), url)
    if not decision.allowed:
        raise GuardrailError(f"{host_of(url)} : {decision.reason}.")
    with requests.get(url, headers={"User-Agent": USER_AGENT}, timeout=timeout, stream=True, allow_redirects=True) as resp:
        resp.raise_for_status()
        final = str(resp.url)
        check_url(final)  # une redirection ne doit pas mener vers un domaine interdit
        ctype = resp.headers.get("content-type", "").split(";")[0].strip().lower()
        if ctype not in accept:
            raise GuardrailError(f"Type de contenu refusé : {ctype or 'inconnu'}.")
        declared = int(resp.headers.get("content-length") or 0)
        if declared > max_bytes:
            raise GuardrailError("Fichier trop volumineux.")
        data = b""
        for chunk in resp.iter_content(65536):
            data += chunk
            if len(data) > max_bytes:
                raise GuardrailError("Fichier trop volumineux.")
    return data, ctype


def find_pdf_links(html: str, base_url: str, limit: int = 20) -> list[str]:
    """Liens vers des PDF dans une page HTML (même domaine uniquement)."""
    links: list[str] = []
    for href in re.findall(r'href=["\']([^"\']+)["\']', html, flags=re.IGNORECASE):
        if ".pdf" in href.lower():
            absolute = urljoin(base_url, href)
            if host_of(absolute) == host_of(base_url) and absolute not in links:
                links.append(absolute)
        if len(links) >= limit:
            break
    return links


def find_links(html: str, base_url: str, limit: int = 60) -> list[dict]:
    """Liens d'une page HTML (même domaine uniquement), avec leur texte. Ceux qui parlent de PFE passent en premier."""
    found: dict[str, str] = {}
    for href, label in re.findall(r'<a\s[^>]*?href=["\']([^"\'#]+)["\'][^>]*>(.*?)</a>', html, flags=re.IGNORECASE | re.DOTALL):
        absolute = urljoin(base_url, href.strip())
        if not is_http_url(absolute) or is_blocked(absolute) or host_of(absolute) != host_of(base_url):
            continue
        text = re.sub(r"<[^>]+>", " ", label)
        found.setdefault(absolute, " ".join(text.split())[:80])
    ranked = sorted(found.items(), key=lambda kv: not re.search(r"pfe|stage|catalogue|book|\.pdf", kv[0] + kv[1], re.IGNORECASE))
    return [{"url": u, "texte": txt} for u, txt in ranked[:limit]]
