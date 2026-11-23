from datetime import date


def target_year(today: date | None = None) -> int:
    """Année des PFE recherchés : à partir de septembre, on vise l'année suivante."""
    today = today or date.today()
    return today.year + 1 if today.month >= 9 else today.year


def is_expired(date_limite: date | None, annee: int | None, today: date | None = None) -> bool:
    """Un sujet expire si sa date limite est passée ou si son année est dépassée."""
    today = today or date.today()
    if date_limite is not None and date_limite < today:
        return True
    return annee is not None and annee < target_year(today)
