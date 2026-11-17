import csv
import io
from dataclasses import dataclass, field
from datetime import date, datetime

MAX_ROWS = 5000
REQUIRED_COLUMNS = {"date", "montant"}


@dataclass
class ParsedRow:
    line: int
    date: date
    amount: int
    note: str
    category_name: str


@dataclass
class ParseResult:
    rows: list[ParsedRow] = field(default_factory=list)
    errors: list[tuple[int, str]] = field(default_factory=list)


class InvalidFile(Exception):
    pass


def _parse_date(raw: str) -> date:
    for pattern in ("%Y-%m-%d", "%d/%m/%Y", "%d-%m-%Y"):
        try:
            return datetime.strptime(raw, pattern).date()
        except ValueError:
            continue
    raise ValueError("date illisible (formats acceptés : AAAA-MM-JJ ou JJ/MM/AAAA)")


def _parse_amount(raw: str) -> int:
    cleaned = raw.replace("FCFA", "").replace("F", "").replace(" ", "").replace(" ", "")
    if not cleaned.isdigit():
        raise ValueError("montant illisible (nombre entier attendu, en FCFA)")
    amount = int(cleaned)
    if amount <= 0:
        raise ValueError("le montant doit être supérieur à zéro")
    return amount


def parse_expenses_csv(content: bytes) -> ParseResult:
    try:
        text = content.decode("utf-8-sig")
    except UnicodeDecodeError:
        text = content.decode("latin-1")

    first_line = text.split("\n", 1)[0]
    delimiter = ";" if first_line.count(";") >= first_line.count(",") else ","
    reader = csv.DictReader(io.StringIO(text), delimiter=delimiter)
    if reader.fieldnames is None:
        raise InvalidFile("Le fichier est vide.")
    reader.fieldnames = [name.strip().lower() for name in reader.fieldnames]
    missing = REQUIRED_COLUMNS - set(reader.fieldnames)
    if missing:
        raise InvalidFile(f"Colonnes manquantes : {', '.join(sorted(missing))}.")

    result = ParseResult()
    for line, row in enumerate(reader, start=2):
        if line - 1 > MAX_ROWS:
            raise InvalidFile(f"Le fichier dépasse {MAX_ROWS} lignes.")
        if not any((value or "").strip() for value in row.values()):
            continue
        try:
            result.rows.append(
                ParsedRow(
                    line=line,
                    date=_parse_date((row.get("date") or "").strip()),
                    amount=_parse_amount((row.get("montant") or "").strip()),
                    note=(row.get("note") or "").strip()[:255],
                    category_name=(row.get("categorie") or "").strip(),
                )
            )
        except ValueError as exc:
            result.errors.append((line, str(exc)))
    return result
