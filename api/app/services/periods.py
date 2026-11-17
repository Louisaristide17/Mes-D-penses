from datetime import date


def month_bounds(month: str) -> tuple[date, date]:
    """Premier jour du mois et premier jour du mois suivant, pour un mois AAAA-MM."""
    year, number = int(month[:4]), int(month[5:7])
    start = date(year, number, 1)
    end = date(year + 1, 1, 1) if number == 12 else date(year, number + 1, 1)
    return start, end


def shift_month(month: str, offset: int) -> str:
    year, number = int(month[:4]), int(month[5:7])
    index = year * 12 + (number - 1) + offset
    return f"{index // 12:04d}-{index % 12 + 1:02d}"


def current_month(today: date | None = None) -> str:
    today = today or date.today()
    return f"{today.year:04d}-{today.month:02d}"
