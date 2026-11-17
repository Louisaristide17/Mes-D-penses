"""Nettoie le jeu de libellés bruts.

Usage : python -m ml.prepare

Étapes :
1. normalisation du texte, avec la même fonction que l'API au moment de prédire ;
2. suppression des libellés vides ou trop courts ;
3. suppression des doublons exacts après normalisation ;
4. suppression des libellés contradictoires (même texte, catégories différentes).
"""

from pathlib import Path

import pandas as pd

from app.services.categorizer import normalize

DATA_DIR = Path(__file__).parent / "data"
RAW_PATH = DATA_DIR / "libelles_bruts.csv"
CLEAN_PATH = DATA_DIR / "libelles_propres.csv"
MIN_LENGTH = 3


def clean(raw: pd.DataFrame) -> tuple[pd.DataFrame, dict]:
    """Renvoie le jeu nettoyé et le nombre de lignes retirées à chaque étape."""
    report = {"lignes_brutes": len(raw)}
    data = raw.copy()
    data["texte"] = data["libelle"].fillna("").map(normalize)

    too_short = data["texte"].str.len() < MIN_LENGTH
    report["trop_courts"] = int(too_short.sum())
    data = data[~too_short]

    duplicated = data.duplicated(subset=["texte", "categorie"])
    report["doublons"] = int(duplicated.sum())
    data = data[~duplicated]

    categories_per_text = data.groupby("texte")["categorie"].transform("nunique")
    conflicting = categories_per_text > 1
    report["contradictoires"] = int(conflicting.sum())
    data = data[~conflicting]

    report["lignes_propres"] = len(data)
    return data.reset_index(drop=True)[["libelle", "texte", "categorie", "groupe"]], report


def main() -> None:
    data, report = clean(pd.read_csv(RAW_PATH))
    data.to_csv(CLEAN_PATH, index=False)
    for step, count in report.items():
        print(f"{step:>16} : {count}")
    print(f"Jeu nettoyé écrit dans {CLEAN_PATH}")


if __name__ == "__main__":
    main()
