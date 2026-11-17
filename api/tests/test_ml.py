import pandas as pd
import pytest

import tests.conftest  # noqa: F401  (positionne les variables d'environnement)
from app.services import categorizer
from ml import train
from ml.build_dataset import add_typo, build_rows, strip_accents
from ml.prepare import clean
from ml.vocabulary import BASE_LABELS
from tests.conftest import API


def test_vocabulary_covers_the_default_categories():
    from app.services.categories import DEFAULT_CATEGORIES

    assert set(BASE_LABELS) == {name for name, _color, _icon in DEFAULT_CATEGORIES}
    assert all(len(labels) >= 40 for labels in BASE_LABELS.values())
    # Un même libellé de base ne doit pas appartenir à deux catégories.
    seen = [label.lower() for labels in BASE_LABELS.values() for label in labels]
    assert len(seen) == len(set(seen))


def test_generation_is_reproducible_and_labelled():
    first, second = build_rows(seed=7), build_rows(seed=7)
    assert first == second
    assert first != build_rows(seed=8)
    assert {row["categorie"] for row in first} == set(BASE_LABELS)
    assert all(row["groupe"].startswith(row["categorie"]) for row in first)


def test_noise_helpers():
    import random

    assert strip_accents("Attiéké à Cocody") == "Attieke a Cocody"
    assert add_typo("abc", random.Random(1)) == "abc"
    assert add_typo("Pharmacie", random.Random(1)) != "Pharmacie"


def test_clean_removes_short_duplicate_and_conflicting_rows():
    raw = pd.DataFrame(
        [
            {"libelle": "Taxi Cocody", "categorie": "Transport", "groupe": "Transport-00"},
            {"libelle": "TAXI  cocody!", "categorie": "Transport", "groupe": "Transport-00"},
            {"libelle": "x", "categorie": "Autres", "groupe": "Autres-00"},
            {"libelle": "Orange", "categorie": "Alimentation", "groupe": "Alimentation-00"},
            {"libelle": "orange", "categorie": "Communication", "groupe": "Communication-00"},
            {"libelle": "Loyer", "categorie": "Logement", "groupe": "Logement-00"},
        ]
    )
    data, report = clean(raw)
    assert report == {
        "lignes_brutes": 6, "trop_courts": 1, "doublons": 1, "contradictoires": 2, "lignes_propres": 2,
    }
    assert list(data["texte"]) == ["taxi cocody", "loyer"]


def test_group_split_keeps_base_labels_apart():
    data = pd.read_csv(train.CLEAN_PATH)
    train_part, test_part = train.split_by_group(data)
    assert set(train_part["groupe"]).isdisjoint(test_part["groupe"])
    assert set(test_part["categorie"]) == set(BASE_LABELS)
    assert 0.15 < len(test_part) / len(data) < 0.25


@pytest.fixture(scope="module")
def fitted_model():
    data = pd.read_csv(train.CLEAN_PATH)
    model = train.candidates()["Régression logistique, mots et caractères"]
    return model.fit(data["texte"], data["categorie"])


def test_model_recognises_common_labels(fitted_model):
    texts = ["taxi pour cocody", "facture cie", "recharge orange 1000", "loyer du mois", "pharmacie de garde"]
    expected = ["Transport", "Factures", "Communication", "Logement", "Santé"]
    assert list(fitted_model.predict([categorizer.normalize(text) for text in texts])) == expected


def test_model_beats_the_rules_on_the_manual_set(fitted_model):
    manual = train.load_manual()
    model_score = train.scores(manual["categorie"], fitted_model.predict(manual["texte"]))
    rules_score = train.scores(manual["categorie"], train.rules_predict(manual["texte"]))
    assert model_score["exactitude"] > 0.75
    assert model_score["exactitude"] > rules_score["exactitude"]


def test_categorizer_uses_the_model_then_falls_back(fitted_model, monkeypatch):
    monkeypatch.setattr(categorizer, "_load_model", lambda: fitted_model)
    confident = categorizer.suggest("Loyer payé par Orange Money")
    assert (confident.category_name, confident.engine) == ("Logement", "modele")
    assert 0 < confident.confidence <= 1
    # Un texte sans rapport ne dépasse pas le seuil de confiance et ne correspond à aucune règle.
    assert categorizer.suggest("qwzx vbnk") is None


def test_api_reports_engine(client, auth, fitted_model, monkeypatch):
    assert client.get(f"{API}/model", headers=auth).json()["engine"] == "regles"
    monkeypatch.setattr(categorizer, "_load_model", lambda: fitted_model)
    info = client.get(f"{API}/model", headers=auth).json()
    assert info["engine"] == "modele"
    suggestion = client.post(f"{API}/expenses/suggest-category", headers=auth, json={"note": "Scolarité du trimestre"})
    assert suggestion.json()["engine"] == "modele"
    assert suggestion.json()["category"]["name"] == "Éducation"
    assert client.get(f"{API}/model").status_code == 401
