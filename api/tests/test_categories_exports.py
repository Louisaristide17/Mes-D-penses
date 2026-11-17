from tests.conftest import API
from tests.test_expenses import add


def test_default_categories_are_listed(client, auth, categories):
    assert {"Alimentation", "Transport", "Factures", "Autres"} <= set(categories)
    assert len(categories) == 10


def test_custom_category_lifecycle(client, auth, other_auth):
    created = client.post(
        f"{API}/categories", headers=auth, json={"name": "Tontine", "color": "#336699", "icon": "users"}
    )
    assert created.status_code == 201 and created.json()["is_default"] is False
    category_id = created.json()["id"]

    duplicate = client.post(
        f"{API}/categories", headers=auth, json={"name": "tontine", "color": "#336699", "icon": "users"}
    )
    assert duplicate.status_code == 409

    hidden = {category["name"] for category in client.get(f"{API}/categories", headers=other_auth).json()}
    assert "Tontine" not in hidden

    add(client, auth, note="Cotisation", category_id=category_id)
    assert client.delete(f"{API}/categories/{category_id}", headers=auth).status_code == 409

    renamed = client.patch(f"{API}/categories/{category_id}", headers=auth, json={"name": "Épargne tontine"})
    assert renamed.json()["name"] == "Épargne tontine"


def test_default_categories_are_read_only(client, auth, categories):
    url = f"{API}/categories/{categories['Transport']}"
    assert client.patch(url, headers=auth, json={"name": "Déplacements"}).status_code == 403
    assert client.delete(url, headers=auth).status_code == 403


def test_category_rejects_invalid_color(client, auth):
    response = client.post(f"{API}/categories", headers=auth, json={"name": "Dons", "color": "vert", "icon": "gift"})
    assert response.status_code == 422


def test_export_csv(client, auth, other_auth):
    add(client, auth, note="Facture SODECI", amount=7500, date="2026-11-04")
    add(client, auth, note="Attiéké poisson", amount=1500, date="2026-11-06")
    add(client, other_auth, note="Dépense d'un autre compte", amount=999)

    response = client.get(f"{API}/exports/expenses.csv", headers=auth)
    assert response.status_code == 200
    assert response.headers["content-type"].startswith("text/csv")
    assert "attachment" in response.headers["content-disposition"]
    lines = response.content.decode("utf-8-sig").strip().split("\r\n")
    assert lines == [
        "date;categorie;montant;note",
        "2026-11-04;Factures;7500;Facture SODECI",
        "2026-11-06;Alimentation;1500;Attiéké poisson",
    ]


def test_export_pdf(client, auth):
    add(client, auth, note="Facture SODECI", amount=7500, date="2026-11-04")
    response = client.get(
        f"{API}/exports/expenses.pdf", headers=auth, params={"date_from": "2026-11-01", "date_to": "2026-11-30"}
    )
    assert response.status_code == 200
    assert response.headers["content-type"] == "application/pdf"
    assert response.content.startswith(b"%PDF")
    assert "2026-11-01_2026-11-30.pdf" in response.headers["content-disposition"]
