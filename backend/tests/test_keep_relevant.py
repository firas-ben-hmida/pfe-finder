from langchain_core.documents import Document

from pfefinder.api.services.matching_service import keep_relevant


def _doc(score: float) -> Document:
    return Document(page_content="x", metadata={"similarity": score})


def test_garde_les_sujets_proches_du_meilleur():
    docs = [_doc(0.80), _doc(0.76), _doc(0.70), _doc(0.55)]
    assert [d.metadata["similarity"] for d in keep_relevant(docs, 0.0, 0.08)] == [0.80, 0.76]


def test_seuil_absolu():
    docs = [_doc(0.50), _doc(0.49)]
    assert keep_relevant(docs, 0.6, 0.08) == []


def test_liste_vide():
    assert keep_relevant([], 0.0, 0.08) == []
