from tests.conftest import API


def add(client, auth, **fields):
    payload = {"amount": 1500, "date": "2026-11-10", "note": "Garba à midi"} | fields
    response = client.post(f"{API}/expenses", headers=auth, json=payload)
    assert response.status_code == 201, response.text
    return response.json()


def test_create_uses_suggested_category_when_none_given(client, auth):
    expense = add(client, auth, note="Gbaka Yopougon - Plateau", amount=500)
    assert expense["category"]["name"] == "Transport"
    assert expense["source"] == "manuel"


def test_create_falls_back_to_other_category(client, auth):
    assert add(client, auth, note="Divers")["category"]["name"] == "Autres"
    assert add(client, auth, note="")["category"]["name"] == "Autres"


def test_create_keeps_explicit_category(client, auth, categories):
    expense = add(client, auth, note="Recharge Orange", category_id=categories["Loisirs"])
    assert expense["category"]["name"] == "Loisirs"


def test_create_rejects_invalid_amounts(client, auth):
    for amount in (0, -200, 12.5):
        response = client.post(
            f"{API}/expenses", headers=auth, json={"amount": amount, "date": "2026-11-10", "note": "Test"}
        )
        assert response.status_code == 422


def test_list_filters_and_pagination(client, auth, categories):
    add(client, auth, note="Loyer novembre", amount=120000, date="2026-11-01")
    add(client, auth, note="Facture CIE", amount=18500, date="2026-11-05")
    add(client, auth, note="Taxi Cocody", amount=2000, date="2026-10-28")

    everything = client.get(f"{API}/expenses", headers=auth).json()
    assert everything["total"] == 3
    assert [item["date"] for item in everything["items"]] == ["2026-11-05", "2026-11-01", "2026-10-28"]

    november = client.get(f"{API}/expenses", headers=auth, params={"date_from": "2026-11-01"}).json()
    assert november["total"] == 2

    by_category = client.get(
        f"{API}/expenses", headers=auth, params={"category_id": categories["Transport"]}
    ).json()
    assert [item["note"] for item in by_category["items"]] == ["Taxi Cocody"]

    search = client.get(f"{API}/expenses", headers=auth, params={"q": "cie"}).json()
    assert [item["note"] for item in search["items"]] == ["Facture CIE"]

    page = client.get(f"{API}/expenses", headers=auth, params={"limit": 1, "offset": 1}).json()
    assert page["total"] == 3 and len(page["items"]) == 1


def test_update_and_delete(client, auth, categories):
    expense = add(client, auth)
    updated = client.patch(
        f"{API}/expenses/{expense['id']}",
        headers=auth,
        json={"amount": 2000, "category_id": categories["Loisirs"]},
    )
    assert updated.status_code == 200
    assert updated.json()["amount"] == 2000
    assert updated.json()["category"]["name"] == "Loisirs"
    assert updated.json()["note"] == "Garba à midi"

    assert client.delete(f"{API}/expenses/{expense['id']}", headers=auth).status_code == 204
    assert client.get(f"{API}/expenses/{expense['id']}", headers=auth).status_code == 404


def test_expenses_are_private_to_their_owner(client, auth, other_auth):
    expense = add(client, auth)
    url = f"{API}/expenses/{expense['id']}"
    assert client.get(url, headers=other_auth).status_code == 404
    assert client.patch(url, headers=other_auth, json={"amount": 1}).status_code == 404
    assert client.delete(url, headers=other_auth).status_code == 404
    assert client.get(f"{API}/expenses", headers=other_auth).json()["total"] == 0


def test_suggest_category_endpoint(client, auth):
    known = client.post(f"{API}/expenses/suggest-category", headers=auth, json={"note": "Pharmacie des Lagunes"})
    assert known.json()["category"]["name"] == "Santé"
    assert known.json()["engine"] == "regles"
    unknown = client.post(f"{API}/expenses/suggest-category", headers=auth, json={"note": "xyz"})
    assert unknown.json()["category"] is None


def test_import_csv_reports_rejected_lines(client, auth):
    content = (
        "date;montant;note;categorie\n"
        "2026-11-02;15000;Marché de Treichville;Alimentation\n"
        "03/11/2026;1 000;Recharge MTN;\n"
        "2026-11-04;abc;Ligne invalide;\n"
        "pas une date;500;Autre ligne invalide;\n"
    ).encode("utf-8")
    response = client.post(
        f"{API}/expenses/import", headers=auth, files={"file": ("depenses.csv", content, "text/csv")}
    )
    assert response.status_code == 200, response.text
    report = response.json()
    assert report["imported"] == 2 and report["rejected"] == 2
    assert [error["line"] for error in report["errors"]] == [4, 5]

    items = client.get(f"{API}/expenses", headers=auth).json()["items"]
    assert {item["source"] for item in items} == {"import"}
    assert {item["category"]["name"] for item in items} == {"Alimentation", "Communication"}


def test_import_rejects_file_without_required_columns(client, auth):
    response = client.post(
        f"{API}/expenses/import", headers=auth, files={"file": ("x.csv", b"a;b\n1;2\n", "text/csv")}
    )
    assert response.status_code == 400
