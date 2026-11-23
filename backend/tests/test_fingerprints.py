from pfefinder.common.fingerprints import hash_sujet, normalize_url


def test_hash_ignores_case_and_spaces():
    assert hash_sujet("Wevioo", "Plateforme  RAG", 2027) == hash_sujet(" wevioo ", "plateforme rag", 2027)


def test_hash_differs_by_year():
    assert hash_sujet("A", "B", 2026) != hash_sujet("A", "B", 2027)


def test_normalize_url_strips_tracking_and_www():
    assert normalize_url("HTTPS://www.Site.tn/pfe/?utm_source=x&b=2&a=1#top") == "https://site.tn/pfe?a=1&b=2"
