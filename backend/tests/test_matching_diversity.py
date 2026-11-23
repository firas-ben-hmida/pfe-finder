from langchain_core.documents import Document

from pfefinder.api.services.matching_service import diversify


def _doc(company: str, n: int) -> Document:
    return Document(page_content=f"{company}-{n}", metadata={"entreprise": company, "id": n})


def test_limite_le_nombre_de_sujets_par_entreprise():
    docs = [_doc("A", i) for i in range(6)] + [_doc("B", 10), _doc("C", 11)]
    result = diversify(docs, k=5, max_per_company=3)
    assert [d.metadata["entreprise"] for d in result] == ["A", "A", "A", "B", "C"]


def test_respecte_k_et_l_ordre():
    docs = [_doc("A", 1), _doc("B", 2), _doc("A", 3)]
    assert [d.metadata["id"] for d in diversify(docs, k=2)] == [1, 2]


def test_le_plafond_suit_la_taille_de_la_liste():
    docs = [_doc(c, i) for i in range(12) for c in "ABC"]
    assert len(diversify(docs, k=30)) == 30
