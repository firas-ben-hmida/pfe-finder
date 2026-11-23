import pytest

from app.services.cv_parser import extract_text


def test_refuse_un_fichier_qui_n_est_pas_un_pdf():
    with pytest.raises(ValueError):
        extract_text(b"ceci n'est pas un pdf")


def test_refuse_un_pdf_corrompu():
    with pytest.raises(ValueError):
        extract_text(b"%PDF-1.4 contenu invalide")
