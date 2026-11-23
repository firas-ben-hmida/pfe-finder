from datetime import date

from pfefinder.core.dates import target_year
from pfefinder.core.db import subjects


def run_expiry(today: date | None = None) -> int:
    today = today or date.today()
    return subjects.expire_outdated(today, target_year(today))
