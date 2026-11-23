import pytest

fitz = pytest.importorskip("fitz")

from pfefinder.api.services.cv_parser import extract_text  # noqa: E402


def test_rejects_non_pdf():
    with pytest.raises(ValueError):
        extract_text(b"hello")


def test_reads_text_pdf():
    doc = fitz.open()
    doc.new_page().insert_text((72, 72), "Firas Ben Hmida - ingenieur logiciel, Python, Angular, RAG, LangChain, FastAPI")
    assert "Python" in extract_text(doc.tobytes())
