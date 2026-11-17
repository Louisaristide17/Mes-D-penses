import json
from datetime import date

import pytest

from app.main import app
from app.services import agent
from app.services.llm import LLMUnavailable, get_llm
from tests.conftest import API
from tests.test_budgets_dashboard import set_budget
from tests.test_expenses import add

TODAY = date.today().isoformat()
MONTH = TODAY[:7]


def call(name, **arguments):
    return {"id": f"appel-{name}", "type": "function", "function": {"name": name, "arguments": json.dumps(arguments)}}


class ScriptedLLM:
    """Faux modèle : rejoue des réponses écrites à l'avance et garde les messages reçus."""

    def __init__(self, *replies):
        self.replies = list(replies)
        self.seen = []

    def complete(self, messages, tools):
        self.seen.append([dict(message) for message in messages])
        reply = self.replies.pop(0)
        if isinstance(reply, Exception):
            raise reply
        return reply

    def tool_results(self):
        return [json.loads(message["content"]) for message in self.seen[-1] if message["role"] == "tool"]


@pytest.fixture
def use_llm():
    def install(llm):
        app.dependency_overrides[get_llm] = lambda: llm
        return llm

    yield install
    app.dependency_overrides.pop(get_llm, None)


def ask(client, auth, message, conversation_id=None):
    payload = {"message": message} | ({"conversation_id": conversation_id} if conversation_id else {})
    return client.post(f"{API}/assistant/messages", headers=auth, json=payload)


def test_assistant_is_disabled_without_api_key(client, auth):
    response = ask(client, auth, "Bonjour")
    assert response.status_code == 503
    assert "GROQ_API_KEY" in response.json()["detail"]


def test_agent_answers_from_tool_results(client, auth, categories, use_llm):
    add(client, auth, note="Taxi", amount=3000, date=TODAY, category_id=categories["Transport"])
    add(client, auth, note="Gbaka", amount=500, date=TODAY, category_id=categories["Transport"])
    add(client, auth, note="Garba", amount=1000, date=TODAY, category_id=categories["Alimentation"])
    llm = use_llm(
        ScriptedLLM(
            {"content": None, "tool_calls": [call("total_depenses", date_debut=TODAY, date_fin=TODAY, categorie="transport")]},
            {"content": "Vous avez dépensé 3 500 FCFA en transport aujourd'hui."},
        )
    )
    response = ask(client, auth, "Combien en transport aujourd'hui ?")
    assert response.status_code == 200, response.text
    body = response.json()
    assert body["reply"] == "Vous avez dépensé 3 500 FCFA en transport aujourd'hui."
    assert body["tools_used"] == ["total_depenses"] and body["data_changed"] is False
    assert llm.tool_results() == [{"total_fcfa": 3500, "nombre_de_depenses": 2, "categorie": "Transport"}]
    system = llm.seen[0][0]["content"]
    assert TODAY in system and "Awa Koné" in system and "Transport" in system
    # L'assistant doit rester ancré sur les outils pour les données personnelles, et accepter les questions générales.
    assert "doit venir d'un outil" in system and "questions générales" in system


def test_tools_only_see_the_current_user(client, auth, other_auth, use_llm):
    add(client, other_auth, note="Dépense d'un autre compte", amount=99999, date=TODAY)
    llm = use_llm(
        ScriptedLLM(
            {"tool_calls": [
                call("total_depenses", date_debut="2000-01-01", date_fin="2100-01-01"),
                call("lister_depenses", date_debut="2000-01-01", date_fin="2100-01-01"),
                call("depenses_par_categorie", date_debut="2000-01-01", date_fin="2100-01-01"),
            ]},
            {"content": "Aucune dépense enregistrée."},
        )
    )
    assert ask(client, auth, "Tout mon historique").status_code == 200
    total, listing, breakdown = llm.tool_results()
    assert total["total_fcfa"] == 0 and listing["depenses"] == [] and breakdown["categories"] == []


def test_agent_can_add_an_expense(client, auth, use_llm):
    llm = use_llm(
        ScriptedLLM(
            {"tool_calls": [call("ajouter_depense", montant=2000, note="Taxi pour Cocody")]},
            {"content": "C'est noté : 2 000 FCFA en Transport."},
        )
    )
    body = ask(client, auth, "Ajoute 2000 de taxi pour Cocody").json()
    assert body["data_changed"] is True and body["tools_used"] == ["ajouter_depense"]
    assert llm.tool_results()[0] | {"enregistree": True} == {
        "enregistree": True, "montant_fcfa": 2000, "date": TODAY, "note": "Taxi pour Cocody", "categorie": "Transport",
    }
    items = client.get(f"{API}/expenses", headers=auth).json()["items"]
    assert [(item["amount"], item["category"]["name"]) for item in items] == [(2000, "Transport")]


def test_invalid_tool_arguments_are_returned_to_the_model(client, auth, use_llm):
    llm = use_llm(
        ScriptedLLM(
            {"tool_calls": [
                call("ajouter_depense", montant=-5, note="x"),
                call("total_depenses", date_debut="hier", date_fin=TODAY),
                call("total_depenses", date_debut=TODAY, date_fin=TODAY, categorie="Voyages"),
                call("supprimer_tout"),
                {"id": "appel-casse", "type": "function", "function": {"name": "etat_budgets", "arguments": "{pas du json"}},
            ]},
            {"content": "Je n'ai pas pu traiter cette demande."},
        )
    )
    body = ask(client, auth, "Fais n'importe quoi").json()
    results = llm.tool_results()
    assert all("erreur" in result for result in results) and len(results) == 5
    assert "Catégories existantes" in results[2]["erreur"] and "Outil inconnu" in results[3]["erreur"]
    assert body["data_changed"] is False
    assert client.get(f"{API}/expenses", headers=auth).json()["total"] == 0


def test_budget_tool(client, auth, categories, use_llm):
    set_budget(client, auth, categories["Loisirs"], 10000, month=MONTH)
    add(client, auth, note="Concert", amount=12000, date=TODAY, category_id=categories["Loisirs"])
    llm = use_llm(ScriptedLLM({"tool_calls": [call("etat_budgets", mois=MONTH)]}, {"content": "Budget Loisirs dépassé."}))
    ask(client, auth, "Où en sont mes budgets ?")
    assert llm.tool_results()[0]["budgets"] == [
        {"categorie": "Loisirs", "plafond_fcfa": 10000, "depense_fcfa": 12000, "reste_fcfa": -2000, "etat": "depasse"}
    ]


def test_conversation_history_is_stored_and_sent_back(client, auth, other_auth, use_llm):
    llm = use_llm(ScriptedLLM({"content": "Bonjour Awa."}, {"content": "Je ne traite que vos dépenses."}))
    first = ask(client, auth, "Bonjour").json()
    second = ask(client, auth, "Quelle est la capitale du Ghana ?", first["conversation_id"]).json()
    assert second["conversation_id"] == first["conversation_id"]
    assert [message["content"] for message in llm.seen[1][1:]] == ["Bonjour", "Bonjour Awa.", "Quelle est la capitale du Ghana ?"]

    listing = client.get(f"{API}/assistant/conversations", headers=auth).json()
    assert [item["title"] for item in listing] == ["Bonjour"]
    detail = client.get(f"{API}/assistant/conversations/{first['conversation_id']}", headers=auth).json()
    assert [message["role"] for message in detail["messages"]] == ["user", "assistant", "user", "assistant"]

    url = f"{API}/assistant/conversations/{first['conversation_id']}"
    assert client.get(url, headers=other_auth).status_code == 404
    assert ask(client, other_auth, "Bonjour", first["conversation_id"]).status_code == 404
    assert client.get(f"{API}/assistant/conversations", headers=other_auth).json() == []
    assert client.delete(url, headers=auth).status_code == 204
    assert client.get(url, headers=auth).status_code == 404


def test_provider_failure_saves_nothing(client, auth, use_llm):
    use_llm(
        ScriptedLLM({"tool_calls": [call("ajouter_depense", montant=2000, note="Taxi")]}, LLMUnavailable())
    )
    response = ask(client, auth, "Ajoute 2000 de taxi")
    assert response.status_code == 502
    assert client.get(f"{API}/expenses", headers=auth).json()["total"] == 0
    assert client.get(f"{API}/assistant/conversations", headers=auth).json() == []


def test_agent_stops_after_too_many_steps(client, auth, use_llm):
    looping = {"tool_calls": [call("etat_budgets", mois=MONTH)]}
    use_llm(ScriptedLLM(*[looping] * agent.MAX_STEPS))
    body = ask(client, auth, "Boucle").json()
    assert body["reply"] == agent.FALLBACK_REPLY


def test_markdown_is_removed_from_replies(client, auth, use_llm):
    use_llm(ScriptedLLM({"content": "## Bilan\n**Total** : 3 500 FCFA\n- Transport : 3 500 FCFA"}))
    assert ask(client, auth, "Bilan").json()["reply"] == "Bilan\nTotal : 3 500 FCFA\n- Transport : 3 500 FCFA"


def test_message_length_is_limited(client, auth, use_llm):
    use_llm(ScriptedLLM())
    assert ask(client, auth, "x" * 1001).status_code == 422
    assert ask(client, auth, "   ").status_code == 422
