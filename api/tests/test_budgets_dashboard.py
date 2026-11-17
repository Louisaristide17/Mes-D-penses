from tests.conftest import API
from tests.test_expenses import add


def set_budget(client, auth, category_id, ceiling, month="2026-11"):
    response = client.put(
        f"{API}/budgets", headers=auth, json={"category_id": category_id, "month": month, "ceiling": ceiling}
    )
    assert response.status_code == 200, response.text
    return response.json()


def test_budget_upsert_replaces_ceiling(client, auth, categories):
    first = set_budget(client, auth, categories["Transport"], 20000)
    second = set_budget(client, auth, categories["Transport"], 30000)
    assert first["id"] == second["id"]
    budgets = client.get(f"{API}/budgets", headers=auth, params={"month": "2026-11"}).json()
    assert [budget["ceiling"] for budget in budgets] == [30000]


def test_budget_status_levels(client, auth, categories):
    set_budget(client, auth, categories["Transport"], 10000)
    set_budget(client, auth, categories["Alimentation"], 10000)
    set_budget(client, auth, categories["Loisirs"], 10000)
    add(client, auth, note="Taxi", amount=3000, category_id=categories["Transport"])
    add(client, auth, note="Marché", amount=8000, category_id=categories["Alimentation"])
    add(client, auth, note="Concert", amount=12000, category_id=categories["Loisirs"])
    # Une dépense d'un autre mois ne doit pas compter.
    add(client, auth, note="Taxi", amount=9000, category_id=categories["Transport"], date="2026-10-15")

    statuses = client.get(f"{API}/budgets/status", headers=auth, params={"month": "2026-11"}).json()
    levels = {status["category"]["name"]: status for status in statuses}
    assert levels["Transport"]["level"] == "ok" and levels["Transport"]["spent"] == 3000
    assert levels["Alimentation"]["level"] == "attention"
    assert levels["Loisirs"]["level"] == "depasse" and levels["Loisirs"]["remaining"] == -2000


def test_budget_rejects_bad_month_and_foreign_budget(client, auth, other_auth, categories):
    bad = client.put(
        f"{API}/budgets", headers=auth, json={"category_id": categories["Transport"], "month": "2026-13", "ceiling": 1}
    )
    assert bad.status_code == 422
    budget = set_budget(client, auth, categories["Transport"], 10000)
    assert client.delete(f"{API}/budgets/{budget['id']}", headers=other_auth).status_code == 404
    assert client.delete(f"{API}/budgets/{budget['id']}", headers=auth).status_code == 204


def test_dashboard_summary(client, auth, categories):
    add(client, auth, note="Loyer", amount=100000, date="2026-11-01", category_id=categories["Logement"])
    add(client, auth, note="Marché", amount=30000, date="2026-11-03", category_id=categories["Alimentation"])
    add(client, auth, note="Garba", amount=20000, date="2026-11-03", category_id=categories["Alimentation"])
    add(client, auth, note="Loyer", amount=100000, date="2026-10-01", category_id=categories["Logement"])
    set_budget(client, auth, categories["Alimentation"], 40000)

    summary = client.get(f"{API}/dashboard/summary", headers=auth, params={"month": "2026-11"}).json()
    assert summary["total"] == 150000 and summary["count"] == 3
    assert summary["previous_total"] == 100000 and summary["variation"] == 0.5
    assert [(row["category"]["name"], row["total"]) for row in summary["by_category"]] == [
        ("Logement", 100000),
        ("Alimentation", 50000),
    ]
    assert abs(sum(row["share"] for row in summary["by_category"]) - 1) < 0.001
    assert [row["month"] for row in summary["monthly"]] == [
        "2026-06", "2026-07", "2026-08", "2026-09", "2026-10", "2026-11",
    ]
    assert summary["monthly"][-2]["total"] == 100000
    assert summary["daily"] == [{"date": "2026-11-01", "total": 100000}, {"date": "2026-11-03", "total": 50000}]
    assert [alert["level"] for alert in summary["alerts"]] == ["depasse"]
    assert len(summary["recent"]) == 3


def test_dashboard_empty_month(client, auth):
    summary = client.get(f"{API}/dashboard/summary", headers=auth, params={"month": "2026-01"}).json()
    assert summary["total"] == 0 and summary["variation"] is None
    assert summary["by_category"] == [] and summary["recent"] == []
    assert summary["monthly"][0]["month"] == "2025-08"
