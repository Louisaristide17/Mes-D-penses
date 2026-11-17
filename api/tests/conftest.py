import os

os.environ["DATABASE_URL"] = "sqlite://"
os.environ["JWT_SECRET"] = "secret-reserve-aux-tests-automatises-0123456789"
os.environ["MODEL_PATH"] = "models/absent.joblib"

import pytest
from fastapi.testclient import TestClient

from app.database import Base, engine
from app.main import app

API = "/api/v1"


@pytest.fixture
def client():
    Base.metadata.create_all(engine)
    with TestClient(app) as test_client:
        yield test_client
    Base.metadata.drop_all(engine)


def register(client, email="awa.kone@example.com", name="Awa Koné", password="motdepasse-solide"):
    response = client.post(f"{API}/auth/register", json={"name": name, "email": email, "password": password})
    assert response.status_code == 201, response.text
    return response.json()


@pytest.fixture
def auth(client):
    tokens = register(client)
    return {"Authorization": f"Bearer {tokens['access_token']}"}


@pytest.fixture
def other_auth(client):
    tokens = register(client, email="yao.kouassi@example.com", name="Yao Kouassi")
    return {"Authorization": f"Bearer {tokens['access_token']}"}


@pytest.fixture
def categories(client, auth):
    response = client.get(f"{API}/categories", headers=auth)
    return {category["name"]: category["id"] for category in response.json()}
