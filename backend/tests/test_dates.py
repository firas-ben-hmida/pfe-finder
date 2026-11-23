from datetime import date

from pfefinder.core.dates import is_expired, target_year


def test_target_year_before_september():
    assert target_year(date(2026, 8, 31)) == 2026


def test_target_year_from_september():
    assert target_year(date(2026, 9, 1)) == 2027


def test_expired_by_deadline():
    assert is_expired(date(2026, 10, 1), 2027, today=date(2026, 11, 1))


def test_expired_by_year():
    assert is_expired(None, 2026, today=date(2026, 11, 1))


def test_still_active():
    assert not is_expired(date(2027, 1, 1), 2027, today=date(2026, 11, 1))
