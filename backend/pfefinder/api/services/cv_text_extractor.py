import fitz  # PyMuPDF

MAX_PAGES = 6
MIN_CHARS = 50


def extract_text(data: bytes) -> str:
    """Texte d'un CV PDF. ValueError si inutilisable. Le fichier reste en mémoire, jamais sur disque."""
    if not data.startswith(b"%PDF-"):
        raise ValueError("Le fichier n'est pas un PDF valide.")
    try:
        document = fitz.open(stream=data, filetype="pdf")
    except Exception as exc:
        raise ValueError("Impossible de lire ce PDF.") from exc

    parts: list[str] = []
    with document:
        for index, page in enumerate(document):
            if index >= MAX_PAGES:
                break
            parts.append(page.get_text())

    text = "\n".join(parts).strip()
    if len(text) < MIN_CHARS:
        raise ValueError("Aucun texte exploitable : ce PDF semble être une image scannée.")
    return text
