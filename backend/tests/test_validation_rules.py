from datetime import date

from pfefinder.domain.models import ExtractedBook, ExtractedSubject
from pfefinder.rag.ingestion.validation_rules import decide_status

TODAY = date(2026, 11, 23)


def book(**kw):
    base = dict(entreprise="Wevioo", annee=2027, pays="Tunisie", mode_candidature="email")
    return ExtractedBook(**{**base, **kw})


def subj(**kw):
    base = dict(titre="Plateforme RAG pour la veille", description="Desc", technos=["Python"])
    return ExtractedSubject(**{**base, **kw})


def test_valid_subject_is_active():
    statut, conf = decide_status(book(), subj(), TODAY)
    assert statut == "actif" and conf >= 0.8


def test_past_year_is_expired():
    assert decide_status(book(annee=2026), subj(), TODAY)[0] == "expire"


def test_past_deadline_is_expired():
    assert decide_status(book(date_limite=date(2026, 10, 1)), subj(), TODAY)[0] == "expire"


def test_missing_year_goes_to_quarantine():
    assert decide_status(book(annee=None), subj(), TODAY)[0] == "quarantaine"


def test_foreign_country_goes_to_quarantine():
    assert decide_status(book(pays="France"), subj(), TODAY)[0] == "quarantaine"


def test_unknown_country_but_tunisian_city_is_active():
    assert decide_status(book(pays=None), subj(ville="Sfax"), TODAY)[0] == "actif"


def test_short_title_goes_to_quarantine():
    assert decide_status(book(), subj(titre="RAG"), TODAY)[0] == "quarantaine"


def test_merge_book_metadata_spreads_info_across_blocks():
    from pfefinder.rag.ingestion.validation_rules import merge_book_metadata

    first = ExtractedBook(entreprise="Wevioo", annee=2027, sujets=[ExtractedSubject(titre="Sujet un assez long")])
    second = ExtractedBook(contact_candidature="pfe@wevioo.com", mode_candidature="email",
                           documents_requis=["CV"], sujets=[ExtractedSubject(titre="Sujet deux assez long")])
    merge_book_metadata([first, second])
    assert first.contact_candidature == "pfe@wevioo.com" and first.mode_candidature == "email"
    assert second.entreprise == "Wevioo" and second.annee == 2027
    assert first.documents_requis == ["CV"]
