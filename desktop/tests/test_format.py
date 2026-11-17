from datetime import date

from app.charts import build_slices, nice_ceiling
from app.format import (
    current_month,
    format_amount,
    format_compact_amount,
    format_date,
    format_percent,
    month_label,
    month_range,
    parse_amount,
    shift_month,
    short_month_label,
)


def test_format_amount_groups_thousands():
    assert format_amount(1250000) == "1 250 000 FCFA"
    assert format_amount(500) == "500 FCFA"
    assert format_amount(0) == "0 FCFA"


def test_format_compact_amount():
    assert format_compact_amount(950) == "950"
    assert format_compact_amount(45000) == "45 k"
    assert format_compact_amount(1300000) == "1,3 M"


def test_parse_amount_keeps_digits_only():
    assert parse_amount("12 500 FCFA") == 12500
    assert parse_amount("") is None
    assert parse_amount("abc") is None


def test_month_helpers():
    assert current_month(date(2026, 3, 9)) == "2026-03"
    assert shift_month("2026-01", -1) == "2025-12"
    assert shift_month("2026-12", 1) == "2027-01"
    assert month_range("2026-11") == ("2026-11-01", "2026-11-30")
    assert month_range("2026-12") == ("2026-12-01", "2026-12-31")
    assert month_range("2028-02") == ("2028-02-01", "2028-02-29")
    assert month_label("2026-11") == "Novembre 2026"
    assert short_month_label("2026-02") == "févr"


def test_format_date_and_percent():
    assert format_date("2026-11-03") == "3 nov. 2026"
    assert format_percent(0.826) == "83 %"


def test_nice_ceiling():
    assert nice_ceiling(0) == 1
    assert nice_ceiling(87000) == 90000
    assert nice_ceiling(326400) == 400000
    assert nice_ceiling(100000) == 100000


def test_build_slices_groups_small_categories():
    rows = [
        {"category": {"name": f"C{i}", "color": "#0F5D4A"}, "total": 100, "share": 0.125}
        for i in range(8)
    ]
    slices = build_slices(rows)
    assert len(slices) == 7
    assert slices[-1]["name"] == "2 autres"
    assert slices[-1]["total"] == 200
    assert abs(slices[-1]["share"] - 0.25) < 1e-9
    assert len(build_slices(rows[:3])) == 3
