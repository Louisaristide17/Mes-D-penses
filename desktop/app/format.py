import re
from datetime import date

MONTHS = [
    "janvier", "février", "mars", "avril", "mai", "juin",
    "juillet", "août", "septembre", "octobre", "novembre", "décembre",
]
SHORT_MONTHS = ["janv.", "févr.", "mars", "avr.", "mai", "juin", "juil.", "août", "sept.", "oct.", "nov.", "déc."]

NBSP = " "


def format_amount(amount: int) -> str:
    """1250000 devient "1 250 000 FCFA", avec des espaces insécables."""
    return f"{amount:,}".replace(",", NBSP) + f"{NBSP}FCFA"


def format_compact_amount(amount: float) -> str:
    """Forme abrégée pour les axes des graphiques : 45000 devient "45 k"."""
    if amount >= 1_000_000:
        return f"{amount / 1_000_000:.1f}".replace(".", ",") + " M"
    if amount >= 1_000:
        return f"{round(amount / 1_000)} k"
    return str(round(amount))


def format_percent(ratio: float) -> str:
    return f"{round(ratio * 100)}{NBSP}%"


def format_date(iso_day: str) -> str:
    day = date.fromisoformat(iso_day)
    return f"{day.day} {SHORT_MONTHS[day.month - 1]} {day.year}"


def parse_amount(text: str) -> int | None:
    """Ne garde que les chiffres d'une saisie. Renvoie None si elle n'en contient aucun."""
    digits = re.sub(r"\D", "", text)
    return int(digits) if digits else None


def current_month(today: date | None = None) -> str:
    today = today or date.today()
    return f"{today.year:04d}-{today.month:02d}"


def shift_month(month: str, offset: int) -> str:
    year, number = int(month[:4]), int(month[5:7])
    index = year * 12 + (number - 1) + offset
    return f"{index // 12:04d}-{index % 12 + 1:02d}"


def month_range(month: str) -> tuple[str, str]:
    """Premier et dernier jour du mois, au format AAAA-MM-JJ."""
    first_of_next = date.fromisoformat(f"{shift_month(month, 1)}-01")
    last = date.fromordinal(first_of_next.toordinal() - 1)
    return f"{month}-01", last.isoformat()


def month_label(month: str) -> str:
    return f"{MONTHS[int(month[5:7]) - 1].capitalize()} {month[:4]}"


def short_month_label(month: str) -> str:
    return SHORT_MONTHS[int(month[5:7]) - 1].rstrip(".")
