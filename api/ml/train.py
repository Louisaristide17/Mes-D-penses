"""Entraîne, compare et enregistre le modèle de catégorisation.

Usage : python -m ml.train [--corrections chemin.csv]

Déroulement :
1. séparation entraînement / test par groupes, pour qu'aucun libellé de base du
   test n'ait été vu, même sous une autre variante, pendant l'entraînement ;
2. comparaison des modèles candidats par validation croisée sur l'entraînement ;
3. évaluation du meilleur sur le test et sur un jeu rédigé à la main ;
4. réentraînement sur toutes les données, puis enregistrement du modèle et du rapport.
"""

import argparse
import json
from datetime import datetime, timezone
from pathlib import Path

import joblib
import numpy as np
import pandas as pd
import sklearn
from sklearn.base import clone
from sklearn.calibration import CalibratedClassifierCV
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import accuracy_score, classification_report, confusion_matrix, f1_score
from sklearn.model_selection import StratifiedGroupKFold, train_test_split
from sklearn.naive_bayes import MultinomialNB
from sklearn.pipeline import FeatureUnion, Pipeline
from sklearn.svm import LinearSVC

from app.services import categorizer
from app.services.categorizer import normalize

ROOT = Path(__file__).parent
CLEAN_PATH = ROOT / "data" / "libelles_propres.csv"
MANUAL_PATH = ROOT / "data" / "test_manuel.csv"
REPORT_DIR = ROOT / "reports"
MODEL_PATH = ROOT.parent / "models" / "categorizer.joblib"
SEED = 2026
FOLDS = 5


def word_features() -> TfidfVectorizer:
    return TfidfVectorizer(analyzer="word", ngram_range=(1, 2), sublinear_tf=True)


def char_features() -> TfidfVectorizer:
    # Les n-grammes de caractères résistent aux fautes de frappe et aux abréviations.
    return TfidfVectorizer(analyzer="char_wb", ngram_range=(2, 5), sublinear_tf=True)


def candidates() -> dict[str, Pipeline]:
    return {
        "Naive Bayes, mots": Pipeline([("tfidf", word_features()), ("clf", MultinomialNB(alpha=0.3))]),
        "Régression logistique, mots": Pipeline(
            [("tfidf", word_features()), ("clf", LogisticRegression(C=10, max_iter=2000))]
        ),
        "Régression logistique, caractères": Pipeline(
            [("tfidf", char_features()), ("clf", LogisticRegression(C=10, max_iter=2000))]
        ),
        "Régression logistique, mots et caractères": Pipeline(
            [
                ("tfidf", FeatureUnion([("mots", word_features()), ("caracteres", char_features())])),
                ("clf", LogisticRegression(C=10, max_iter=2000)),
            ]
        ),
        "SVM linéaire calibré, caractères": Pipeline(
            [("tfidf", char_features()), ("clf", CalibratedClassifierCV(LinearSVC(C=1.0), cv=3))]
        ),
    }


def split_by_group(data: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Réserve un cinquième des libellés de base de chaque catégorie pour le test."""
    splitter = StratifiedGroupKFold(n_splits=5, shuffle=True, random_state=SEED)
    train_index, test_index = next(splitter.split(data["texte"], data["categorie"], data["groupe"]))
    return data.iloc[train_index], data.iloc[test_index]


def scores(truth, predicted) -> dict:
    return {
        "exactitude": round(float(accuracy_score(truth, predicted)), 4),
        "f1_macro": round(float(f1_score(truth, predicted, average="macro")), 4),
    }


def cross_validate(model: Pipeline, train: pd.DataFrame) -> dict:
    splitter = StratifiedGroupKFold(n_splits=FOLDS, shuffle=True, random_state=SEED)
    accuracies, f1_values = [], []
    for fit_index, check_index in splitter.split(train["texte"], train["categorie"], train["groupe"]):
        fitted = clone(model).fit(train["texte"].iloc[fit_index], train["categorie"].iloc[fit_index])
        predicted = fitted.predict(train["texte"].iloc[check_index])
        truth = train["categorie"].iloc[check_index]
        accuracies.append(accuracy_score(truth, predicted))
        f1_values.append(f1_score(truth, predicted, average="macro"))
    return {
        "exactitude": round(float(np.mean(accuracies)), 4),
        "f1_macro": round(float(np.mean(f1_values)), 4),
        "f1_macro_ecart_type": round(float(np.std(f1_values)), 4),
    }


def rules_predict(texts) -> list[str]:
    """Référence : les règles par mots-clés utilisées par l'API avant l'entraînement."""
    predicted = []
    for text in texts:
        suggestion = categorizer._suggest_with_rules(text)
        predicted.append(suggestion.category_name if suggestion else "Autres")
    return predicted


def system_predict(model: Pipeline, texts) -> list[str]:
    """Reproduit la décision de l'API : modèle si sa confiance suffit, sinon règles, sinon Autres."""
    predicted = []
    for text in texts:
        suggestion = categorizer._suggest_with_model(model, text) or categorizer._suggest_with_rules(text)
        predicted.append(suggestion.category_name if suggestion else "Autres")
    return predicted


def random_split_score(model: Pipeline, data: pd.DataFrame) -> dict:
    """Score sur un découpage aléatoire, donné à titre de comparaison.

    Il est optimiste : les variantes d'un même libellé de base se retrouvent à la
    fois dans l'entraînement et dans le test.
    """
    train, test = train_test_split(data, test_size=0.2, stratify=data["categorie"], random_state=SEED)
    fitted = clone(model).fit(train["texte"], train["categorie"])
    return scores(test["categorie"], fitted.predict(test["texte"]))


def load_manual() -> pd.DataFrame:
    manual = pd.read_csv(MANUAL_PATH)
    manual["texte"] = manual["libelle"].map(normalize)
    return manual


def load_corrections(path: Path, known: set[str]) -> pd.DataFrame:
    """Corrections des utilisateurs exportées par ml.export_corrections."""
    extra = pd.read_csv(path)
    extra["texte"] = extra["libelle"].fillna("").map(normalize)
    extra = extra[(extra["texte"].str.len() >= 3) & extra["categorie"].isin(known)]
    # Chaque correction forme son propre groupe : elle ne dérive d'aucun libellé de base.
    extra["groupe"] = ["correction-" + str(index) for index in range(len(extra))]
    return extra[["libelle", "texte", "categorie", "groupe"]]


def run(corrections: Path | None = None, save: bool = True) -> dict:
    data = pd.read_csv(CLEAN_PATH)
    if corrections is not None:
        extra = load_corrections(corrections, set(data["categorie"]))
        data = pd.concat([data, extra], ignore_index=True).drop_duplicates(subset=["texte", "categorie"])
        print(f"{len(extra)} correction(s) ajoutée(s) au jeu d'entraînement")

    train, test = split_by_group(data)
    manual = load_manual()

    comparison = {name: cross_validate(model, train) for name, model in candidates().items()}
    best_name = max(comparison, key=lambda name: comparison[name]["f1_macro"])
    best = clone(candidates()[best_name]).fit(train["texte"], train["categorie"])

    test_predicted = best.predict(test["texte"])
    manual_predicted = best.predict(manual["texte"])
    labels = sorted(data["categorie"].unique())
    report = {
        "date": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "scikit_learn": sklearn.__version__,
        "donnees": {
            "total": len(data),
            "entrainement": len(train),
            "test": len(test),
            "test_manuel": len(manual),
            "par_categorie": data["categorie"].value_counts().sort_index().to_dict(),
        },
        "validation_croisee": comparison,
        "modele_retenu": best_name,
        "test_aleatoire": random_split_score(candidates()[best_name], data),
        "test": scores(test["categorie"], test_predicted),
        "test_manuel": scores(manual["categorie"], manual_predicted),
        "systeme_complet_test_manuel": scores(manual["categorie"], system_predict(best, manual["texte"])),
        "regles": {
            "test": scores(test["categorie"], rules_predict(test["texte"])),
            "test_manuel": scores(manual["categorie"], rules_predict(manual["texte"])),
        },
        "par_categorie_test_manuel": classification_report(
            manual["categorie"], manual_predicted, output_dict=True, zero_division=0
        ),
        "categories": labels,
        "matrice_confusion_test_manuel": confusion_matrix(manual["categorie"], manual_predicted, labels=labels).tolist(),
        "erreurs_test_manuel": [
            {"libelle": label, "attendu": expected, "predit": got}
            for label, expected, got in zip(manual["libelle"], manual["categorie"], manual_predicted)
            if expected != got
        ],
    }

    if save:
        # Le modèle livré apprend de toutes les données générées. Le jeu manuel reste
        # réservé à l'évaluation : s'en servir pour apprendre fausserait la mesure.
        final = clone(candidates()[best_name]).fit(data["texte"], data["categorie"])
        MODEL_PATH.parent.mkdir(exist_ok=True)
        joblib.dump(final, MODEL_PATH)
        REPORT_DIR.mkdir(exist_ok=True)
        (REPORT_DIR / "metrics.json").write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    return report


def main() -> None:
    parser = argparse.ArgumentParser(description="Entraîne le modèle de catégorisation des dépenses.")
    parser.add_argument("--corrections", type=Path, help="CSV de corrections produit par ml.export_corrections")
    report = run(parser.parse_args().corrections)

    print("\nValidation croisée (5 plis, par groupes)")
    for name, result in report["validation_croisee"].items():
        print(f"  {name:<44} F1 macro {result['f1_macro']:.3f}  exactitude {result['exactitude']:.3f}")
    print(f"\nModèle retenu : {report['modele_retenu']}")
    print("\nExactitude")
    print(f"  {'Découpage aléatoire (optimiste)':<44}{report['test_aleatoire']['exactitude']:.3f}")
    print(f"  {'Libellés de base jamais vus (pessimiste)':<44}{report['test']['exactitude']:.3f}   règles : {report['regles']['test']['exactitude']:.3f}")
    print(f"  {'Jeu rédigé à la main':<44}{report['test_manuel']['exactitude']:.3f}   règles : {report['regles']['test_manuel']['exactitude']:.3f}")
    print(f"  {'Jeu manuel, modèle puis règles (API)':<44}{report['systeme_complet_test_manuel']['exactitude']:.3f}")
    print(f"\nModèle enregistré dans {MODEL_PATH}")
    print(f"Rapport enregistré dans {REPORT_DIR / 'metrics.json'}")


if __name__ == "__main__":
    main()
