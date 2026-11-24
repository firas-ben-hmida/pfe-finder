from langchain_core.documents import Document

from pfefinder.api.services.matching_service import filter_cities
from pfefinder.rag.retrieval import hybrid_ranking as hr


def _doc(text: str, sim: float, ville: str | None = "Tunis") -> Document:
    return Document(page_content=text, metadata={"similarity": sim, "ville": ville, "id": hash(text) % 1000})


def test_normalize_gere_accents_et_ponctuation():
    assert hr.normalize("CI/CD Élevé").split() == ["ci", "cd", "eleve"]


def test_termes_courts_ignores():
    assert hr.profile_terms(["a", "Spring Boot"], []) == {"spring boot"}


def test_le_recoupement_lexical_fait_remonter_le_sujet_du_profil():
    terms = hr.profile_terms(["Java", "Spring Boot", "Angular"], ["génie logiciel"])
    embarque = _doc("Bootloader STM32 C/C++ CAN", sim=0.75)
    logiciel = _doc("Microservices Java Spring Boot Angular", sim=0.70)
    ranked = hr.rank([embarque, logiciel], terms)
    assert ranked[0][0] is logiciel


def test_sans_recoupement_on_garde_l_ordre_vectoriel():
    ranked = hr.rank([_doc("a", 0.6), _doc("b", 0.8)], {"zzz"})
    assert [d.page_content for d, _ in ranked] == ["b", "a"]


def test_filtre_villes():
    docs = [_doc("a", 0.5, "Tunis"), _doc("b", 0.5, "Sfax"), _doc("c", 0.5, None)]
    assert [d.page_content for d in filter_cities(docs, ["sfax"])] == ["b", "c"]
    assert len(filter_cities(docs, None)) == 3


def test_les_termes_rares_pesent_plus_que_les_termes_courants():
    catalogue = ["agents IA Python LLM"] * 8 + ["Java Spring Boot microservices"] + ["bootloader STM32"]
    terms = hr.profile_terms(["Java", "Spring Boot", "microservices", "Python"], ["IA", "LLM"])
    weights = hr.term_weights(terms, catalogue)
    assert weights["spring boot"] > weights["python"]
    docs = [_doc(text, sim=0.74) for text in catalogue]
    assert "Spring Boot" in hr.rank(docs, terms, weights)[0][0].page_content
