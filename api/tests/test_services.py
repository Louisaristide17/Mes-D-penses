import pytest

import tests.conftest  # noqa: F401  (positionne les variables d'environnement)
from app.security import InvalidToken, create_token, decode_token, hash_password, verify_password
from app.services import categorizer
from app.services.budgets import budget_level
from app.services.exports import format_amount
from app.services.imports import InvalidFile, parse_expenses_csv
from app.services.periods import month_bounds, shift_month


@pytest.mark.parametrize(
    ("note", "expected"),
    [
        ("Gbaka Adjamé", "Transport"),
        ("Attiéké poisson au maquis", "Alimentation"),
        ("FACTURE CIE novembre", "Factures"),
        ("Recharge Orange 2000", "Communication"),
        ("Loyer du mois", "Logement"),
        ("Scolarité 2e trimestre", "Éducation"),
        ("Pagne pour la fête", "Habillement"),
    ],
)
def test_rules_recognize_common_labels(note, expected):
    suggestion = categorizer.suggest(note)
    assert suggestion.category_name == expected
    assert suggestion.engine == "regles"
    assert 0 < suggestion.confidence <= 0.9


def test_rules_match_whole_words_only():
    # "police" contient "cie" mais ne doit pas être classé en facture.
    assert categorizer.suggest("police") is None
    assert categorizer.suggest("   ") is None


def test_normalize_strips_accents_and_punctuation():
    assert categorizer.normalize("Attiéké-Poisson, 2 parts!") == "attieke poisson 2 parts"
    assert categorizer.normalize("Œufs et bœuf") == "oeufs et boeuf"


def test_month_helpers():
    assert [d.isoformat() for d in month_bounds("2026-12")] == ["2026-12-01", "2027-01-01"]
    assert [d.isoformat() for d in month_bounds("2028-02")] == ["2028-02-01", "2028-03-01"]
    assert shift_month("2026-01", -1) == "2025-12"
    assert shift_month("2026-11", 3) == "2027-02"


def test_budget_level_thresholds():
    assert budget_level(7999, 10000) == "ok"
    assert budget_level(8000, 10000) == "attention"
    assert budget_level(10000, 10000) == "attention"
    assert budget_level(10001, 10000) == "depasse"


def test_format_amount():
    assert format_amount(1250000) == "1 250 000 FCFA"
    assert format_amount(500) == "500 FCFA"


def test_password_hashing():
    hashed = hash_password("motdepasse-solide")
    assert hashed != "motdepasse-solide"
    assert verify_password("motdepasse-solide", hashed)
    assert not verify_password("autre", hashed)
    assert not verify_password("autre", "pas-un-hash")


def test_token_kind_is_enforced():
    assert decode_token(create_token(7, "access"), "access") == 7
    with pytest.raises(InvalidToken):
        decode_token(create_token(7, "refresh"), "access")
    with pytest.raises(InvalidToken):
        decode_token("n'importe quoi", "access")


def test_csv_parser_accepts_comma_delimiter_and_latin1():
    content = "date,montant,note\n05/11/2026,2500 FCFA,Déjeuner\n".encode("latin-1")
    result = parse_expenses_csv(content)
    assert result.errors == []
    assert (result.rows[0].date.isoformat(), result.rows[0].amount, result.rows[0].note) == (
        "2026-11-05", 2500, "Déjeuner",
    )


def test_csv_parser_rejects_empty_file():
    with pytest.raises(InvalidFile):
        parse_expenses_csv(b"")
