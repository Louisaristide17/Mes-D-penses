from tests.conftest import API, register


def test_register_returns_tokens_and_profile(client):
    data = register(client)
    assert data["user"]["email"] == "awa.kone@example.com"
    assert data["user"]["currency"] == "XOF"
    assert data["access_token"] and data["refresh_token"]
    assert "password" not in str(data["user"])


def test_register_rejects_duplicate_email(client):
    register(client)
    response = client.post(
        f"{API}/auth/register",
        json={"name": "Awa Koné", "email": "AWA.KONE@example.com", "password": "motdepasse-solide"},
    )
    assert response.status_code == 409


def test_register_rejects_short_password(client):
    response = client.post(
        f"{API}/auth/register", json={"name": "Awa Koné", "email": "awa@example.com", "password": "court"}
    )
    assert response.status_code == 422


def test_login_and_wrong_password(client):
    register(client)
    ok = client.post(f"{API}/auth/login", json={"email": "awa.kone@example.com", "password": "motdepasse-solide"})
    assert ok.status_code == 200
    wrong = client.post(f"{API}/auth/login", json={"email": "awa.kone@example.com", "password": "autre-chose"})
    unknown = client.post(f"{API}/auth/login", json={"email": "inconnu@example.com", "password": "autre-chose"})
    assert wrong.status_code == unknown.status_code == 401
    assert wrong.json() == unknown.json()


def test_protected_route_requires_token(client):
    assert client.get(f"{API}/users/me").status_code == 401
    assert client.get(f"{API}/users/me", headers={"Authorization": "Bearer faux"}).status_code == 401


def test_refresh_token_cannot_be_used_as_access_token(client):
    tokens = register(client)
    response = client.get(f"{API}/users/me", headers={"Authorization": f"Bearer {tokens['refresh_token']}"})
    assert response.status_code == 401


def test_refresh_issues_working_access_token(client):
    tokens = register(client)
    refreshed = client.post(f"{API}/auth/refresh", json={"refresh_token": tokens["refresh_token"]})
    assert refreshed.status_code == 200
    headers = {"Authorization": f"Bearer {refreshed.json()['access_token']}"}
    assert client.get(f"{API}/users/me", headers=headers).status_code == 200
    rejected = client.post(f"{API}/auth/refresh", json={"refresh_token": tokens["access_token"]})
    assert rejected.status_code == 401


def test_update_profile_and_password(client, auth):
    updated = client.patch(f"{API}/users/me", headers=auth, json={"name": "Awa K. Koné"})
    assert updated.json()["name"] == "Awa K. Koné"

    refused = client.post(
        f"{API}/users/me/password",
        headers=auth,
        json={"current_password": "mauvais", "new_password": "nouveau-mot-de-passe"},
    )
    assert refused.status_code == 400

    changed = client.post(
        f"{API}/users/me/password",
        headers=auth,
        json={"current_password": "motdepasse-solide", "new_password": "nouveau-mot-de-passe"},
    )
    assert changed.status_code == 204
    login = client.post(
        f"{API}/auth/login", json={"email": "awa.kone@example.com", "password": "nouveau-mot-de-passe"}
    )
    assert login.status_code == 200
