from datetime import date

from pfefinder.common.academic_year import target_year
from pfefinder.repositories import subjects_repository as subjects


def run_expiry(today: date | None = None) -> int:
    today = today or date.today()
    return subjects.expire_outdated(today, target_year(today))
