"""Exporte les corrections des utilisateurs pour réentraîner le modèle.

Usage : python -m ml.export_corrections [--toutes]

Chaque fois que l'API propose une catégorie, elle enregistre la proposition et la
catégorie finalement retenue (table predictions). Par défaut, seules les dépenses
où l'utilisateur a choisi une autre catégorie que celle proposée sont exportées :
ce sont les cas où le modèle s'est trompé. Avec --toutes, les propositions
acceptées le sont aussi.

Seules les catégories par défaut sont exportées : le modèle ne connaît pas les
catégories personnelles. Les libellés viennent des notes des utilisateurs : le
fichier produit ne doit pas être publié.
"""

import argparse
import csv
from pathlib import Path

from sqlalchemy import select

from app.database import SessionLocal
from app.models import Category, Expense, Prediction

OUTPUT = Path(__file__).parent / "data" / "corrections.csv"


def collect(include_confirmed: bool = False) -> list[tuple[str, str]]:
    query = (
        select(Expense.note, Category.name)
        .join(Prediction, Prediction.expense_id == Expense.id)
        .join(Category, Category.id == Prediction.final_category_id)
        .where(Category.user_id.is_(None), Expense.note != "")
    )
    if not include_confirmed:
        query = query.where(Prediction.final_category_id != Prediction.predicted_category_id)
    with SessionLocal() as db:
        return sorted({(note, name) for note, name in db.execute(query)})


def main() -> None:
    parser = argparse.ArgumentParser(description="Exporte les corrections de catégorie.")
    parser.add_argument("--toutes", action="store_true", help="inclure aussi les propositions acceptées")
    rows = collect(parser.parse_args().toutes)
    with OUTPUT.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.writer(handle)
        writer.writerow(["libelle", "categorie"])
        writer.writerows(rows)
    print(f"{len(rows)} ligne(s) écrite(s) dans {OUTPUT}")
    print("Réentraînement : python -m ml.train --corrections ml/data/corrections.csv")


if __name__ == "__main__":
    main()
