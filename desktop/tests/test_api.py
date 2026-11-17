import pytest
import requests

from app.api import ApiClient, ApiError, MemoryTokenStore


class FakeResponse:
    def __init__(self, status=200, payload=None, headers=None, content=None):
        self.status_code = status
        self._payload = payload
        self.headers = headers or {}
        self.content = content if content is not None else (b"{}" if payload is not None else b"")

    @property
    def ok(self):
        return 200 <= self.status_code < 300

    def json(self):
        if self._payload is None:
            raise ValueError("pas de JSON")
        return self._payload


class FakeHttp:
    """Rejoue une liste de réponses et garde la trace des requêtes reçues."""

    def __init__(self, responses):
        self.responses = list(responses)
        self.calls = []

    def request(self, method, url, headers=None, timeout=None, **kwargs):
        self.calls.append((method, url, headers or {}, kwargs))
        result = self.responses.pop(0)
        if isinstance(result, Exception):
            raise result
        return result

    def post(self, url, json=None, timeout=None):
        return self.request("POST", url, json=json)


TOKENS = {"access_token": "acces-1", "refresh_token": "renouvellement-1"}
USER = {"id": 1, "name": "Awa Koné", "email": "awa.kone@example.com"}


def client_with(responses, logged_in=True):
    store = MemoryTokenStore()
    http = FakeHttp(responses)
    client = ApiClient("http://api.test", store=store, http=http)
    if logged_in:
        client._set_tokens(TOKENS)
    return client, http, store


def test_login_stores_tokens_and_returns_user():
    client, http, store = client_with([FakeResponse(payload={**TOKENS, "user": USER})], logged_in=False)
    assert client.login("awa.kone@example.com", "secret") == USER
    assert client.has_session
    assert store.tokens == {"access": "acces-1", "refresh": "renouvellement-1"}
    method, url, headers, _ = http.calls[0]
    assert (method, url) == ("POST", "http://api.test/api/v1/auth/login")
    assert "Authorization" not in headers


def test_requests_carry_the_access_token_and_skip_empty_filters():
    client, http, _ = client_with([FakeResponse(payload={"items": [], "total": 0})])
    client.expenses(q="", category_id=None, date_from="2026-11-01", limit=20)
    _, _, headers, kwargs = http.calls[0]
    assert headers["Authorization"] == "Bearer acces-1"
    assert kwargs["params"] == {"date_from": "2026-11-01", "limit": 20}


def test_expired_token_is_renewed_once_then_request_is_replayed():
    renewed = {"access_token": "acces-2", "refresh_token": "renouvellement-2"}
    client, http, store = client_with(
        [FakeResponse(status=401, payload={"detail": "expiré"}), FakeResponse(payload=renewed), FakeResponse(payload=USER)]
    )
    assert client.profile() == USER
    assert [call[1].rsplit("/", 1)[-1] for call in http.calls] == ["me", "refresh", "me"]
    assert http.calls[2][2]["Authorization"] == "Bearer acces-2"
    assert store.tokens["refresh"] == "renouvellement-2"


def test_failed_renewal_closes_the_session():
    client, _, store = client_with(
        [FakeResponse(status=401, payload={"detail": "expiré"}), FakeResponse(status=401, payload={"detail": "refusé"})]
    )
    expired = []
    client.on_session_expired = lambda: expired.append(True)
    with pytest.raises(ApiError) as failure:
        client.profile()
    assert failure.value.status == 401
    assert expired == [True]
    assert not client.has_session and store.tokens is None


def test_wrong_password_does_not_trigger_a_renewal():
    client, http, _ = client_with([FakeResponse(status=401, payload={"detail": "Adresse e-mail ou mot de passe incorrect."})])
    with pytest.raises(ApiError) as failure:
        client.login("awa.kone@example.com", "mauvais")
    assert failure.value.message == "Adresse e-mail ou mot de passe incorrect."
    assert len(http.calls) == 1


def test_error_messages():
    client, _, _ = client_with(
        [
            FakeResponse(status=409, payload={"detail": "Une catégorie porte déjà ce nom."}),
            FakeResponse(status=422, payload={"detail": [{"loc": ["body", "amount"]}]}),
            FakeResponse(status=500),
            requests.ConnectionError("hors ligne"),
        ]
    )
    messages = []
    for _ in range(4):
        with pytest.raises(ApiError) as failure:
            client.categories()
        messages.append(failure.value.message)
    assert messages[0] == "Une catégorie porte déjà ce nom."
    assert "invalides" in messages[1]
    assert "Réessayez" in messages[2]
    assert "Connexion au serveur impossible" in messages[3]


def test_export_returns_filename_and_content():
    response = FakeResponse(
        headers={"Content-Disposition": 'attachment; filename="mes-depenses_2026-11-01.csv"'}, content=b"date;montant"
    )
    client, _, _ = client_with([response])
    assert client.export_expenses("csv", date_from="2026-11-01") == ("mes-depenses_2026-11-01.csv", b"date;montant")


def test_restore_session_reads_the_store():
    store = MemoryTokenStore()
    store.save({"access": "a", "refresh": "r"})
    client = ApiClient("http://api.test", store=store, http=FakeHttp([]))
    assert not client.has_session
    client.restore_session()
    assert client.has_session


def test_assistant_request_carries_the_conversation():
    answer = {"conversation_id": 4, "reply": "Bonjour", "tools_used": [], "data_changed": False}
    client, http, _ = client_with([FakeResponse(payload=answer), FakeResponse(payload=answer)])
    assert client.ask_assistant("Bonjour") == answer
    client.ask_assistant("Et hier ?", 4)
    assert http.calls[0][3]["json"] == {"message": "Bonjour"}
    assert http.calls[1][3]["json"] == {"message": "Et hier ?", "conversation_id": 4}
    assert http.calls[1][1].endswith("/assistant/messages")
