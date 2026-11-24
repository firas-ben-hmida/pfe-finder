import pytest

from pfefinder.agent import guardrails as g


def test_blocked_social_domains():
    assert g.is_blocked("https://www.linkedin.com/jobs/1")
    assert g.is_blocked("https://fr.linkedin.com/x")
    assert not g.is_blocked("https://pfebooks.com/catalogue/")


def test_check_url_rejects_bad_scheme_and_blocked():
    for bad in ("ftp://site.tn/a.pdf", "javascript:alert(1)", "https://x.com/post"):
        with pytest.raises(g.GuardrailError):
            g.check_url(bad)


def test_allowlist():
    assert g.is_allowed_for_auto_ingest("https://pfebooks.com/book.pdf")
    assert not g.is_allowed_for_auto_ingest("https://inconnu.tn/book.pdf")


def test_robots_disallow():
    robots = "User-agent: *\nDisallow: /private/\n"
    assert not g.evaluate_robots(robots, "https://s.tn/private/a.pdf").allowed
    assert g.evaluate_robots(robots, "https://s.tn/public/a.pdf").allowed


def test_no_robots_means_allowed():
    assert g.evaluate_robots(None, "https://s.tn/a.pdf").allowed


def test_content_signal_blocks_ai_use():
    robots = "User-agent: *\nContent-Signal: search=yes, ai-train=no\nAllow: /\n"
    decision = g.evaluate_robots(robots, "https://s.tn/a.pdf")
    assert not decision.allowed and "ai-train" in decision.reason


def test_find_pdf_links_same_domain_only():
    html = '<a href="/a.pdf">a</a><a href="https://autre.com/b.pdf">b</a><a href="c.html">c</a>'
    assert g.find_pdf_links(html, "https://s.tn/catalogue/") == ["https://s.tn/a.pdf"]


def test_find_links_meme_domaine_et_pfe_en_premier():
    html = ('<a href="/contact">Contact</a><a href="/catalogue-pfe-2027">Catalogue PFE 2027</a>'
            '<a href="https://autre.com/x.pdf">ext</a><a href="https://linkedin.com/y">li</a>')
    links = g.find_links(html, "https://s.tn/")
    assert [l["url"] for l in links] == ["https://s.tn/catalogue-pfe-2027", "https://s.tn/contact"]
    assert links[0]["texte"] == "Catalogue PFE 2027"
