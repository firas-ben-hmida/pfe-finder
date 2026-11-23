import fitz  # PyMuPDF


def read_pdf(data: bytes, max_pages: int) -> str:
    """Texte d'un PFE book, avec marqueurs de page. ValueError si inutilisable."""
    if not data.startswith(b"%PDF-"):
        raise ValueError("Pas un PDF.")
    try:
        document = fitz.open(stream=data, filetype="pdf")
    except Exception as exc:
        raise ValueError("PDF illisible.") from exc
    parts: list[str] = []
    with document:
        for index, page in enumerate(document):
            if index >= max_pages:
                break
            parts.append(f"[page {index + 1}]\n{page.get_text()}")
    text = "\n".join(parts).strip()
    if len(text) < 200:
        raise ValueError("PDF sans texte exploitable (scan ?).")
    return text
