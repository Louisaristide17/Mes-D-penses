"""Proposition d'une catégorie à partir du libellé d'une dépense.

Le modèle entraîné (pipeline scikit-learn sérialisé avec joblib) est utilisé
quand le fichier existe. Sinon, un jeu de règles par mots-clés prend le relais,
ce qui garde l'API utilisable avant le premier entraînement.
"""

import logging
import re
import unicodedata
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path

from app.config import get_settings

logger = logging.getLogger(__name__)

MIN_MODEL_CONFIDENCE = 0.35

KEYWORDS: dict[str, tuple[str, ...]] = {
    "Transport": (
        "gbaka", "woro", "taxi", "yango", "heetch", "sotra", "bus", "carburant", "essence",
        "gasoil", "peage", "moto", "transport", "utb", "billet car", "vidange",
    ),
    "Alimentation": (
        "garba", "attieke", "alloco", "marche", "riz", "poisson", "poulet", "maquis", "restaurant",
        "dejeuner", "diner", "petit dejeuner", "pain", "supermarche", "carrefour", "prosuma",
        "huile", "legumes", "viande", "boisson", "eau minerale", "placali", "foutou",
    ),
    "Factures": ("cie", "sodeci", "electricite", "facture", "canal", "abonnement", "startimes", "impots"),
    "Communication": (
        "recharge", "credit", "orange", "mtn", "moov", "forfait", "internet", "pass", "wifi", "fibre",
    ),
    "Logement": ("loyer", "caution", "gardien", "menage", "plombier", "electricien", "meuble", "gaz"),
    "Santé": ("pharmacie", "medicament", "consultation", "clinique", "hopital", "analyse", "dentiste", "ordonnance"),
    "Éducation": ("scolarite", "ecole", "fournitures", "cahier", "livre", "formation", "inscription", "cours"),
    "Loisirs": ("cinema", "concert", "sortie", "plage", "bassam", "assinie", "match", "jeu", "netflix"),
    "Habillement": ("pagne", "couturier", "tailleur", "chaussures", "chemise", "robe", "vetement", "coiffure", "tresses"),
}


@dataclass(frozen=True)
class Suggestion:
    category_name: str
    confidence: float
    engine: str  # "modele" ou "regles"


def normalize(text: str) -> str:
    # Les ligatures ne se décomposent pas avec NFKD : sans ce remplacement, "œufs" deviendrait "ufs".
    lowered = text.lower().replace("œ", "oe").replace("æ", "ae")
    decomposed = unicodedata.normalize("NFKD", lowered)
    without_accents = "".join(char for char in decomposed if not unicodedata.combining(char))
    return re.sub(r"[^a-z0-9]+", " ", without_accents).strip()


@lru_cache
def _load_model():
    path = Path(get_settings().model_path)
    if not path.is_file():
        return None
    try:
        import joblib

        return joblib.load(path)
    except Exception:
        logger.exception("Chargement du modèle impossible (%s), repli sur les règles", path)
        return None


def model_loaded() -> bool:
    return _load_model() is not None


def _suggest_with_model(model, text: str) -> Suggestion | None:
    probabilities = model.predict_proba([text])[0]
    best = probabilities.argmax()
    confidence = float(probabilities[best])
    if confidence < MIN_MODEL_CONFIDENCE:
        return None
    return Suggestion(str(model.classes_[best]), round(confidence, 3), "modele")


def _suggest_with_rules(text: str) -> Suggestion | None:
    padded = f" {text} "
    scores = {
        name: sum(1 for keyword in keywords if f" {keyword} " in padded)
        for name, keywords in KEYWORDS.items()
    }
    best = max(scores, key=scores.get)
    if scores[best] == 0:
        return None
    # Confiance volontairement prudente : une règle n'est pas une probabilité.
    confidence = min(0.6 + 0.15 * (scores[best] - 1), 0.9)
    return Suggestion(best, confidence, "regles")


def suggest(note: str) -> Suggestion | None:
    text = normalize(note)
    if not text:
        return None
    model = _load_model()
    if model is not None:
        suggestion = _suggest_with_model(model, text)
        if suggestion is not None:
            return suggestion
    return _suggest_with_rules(text)
