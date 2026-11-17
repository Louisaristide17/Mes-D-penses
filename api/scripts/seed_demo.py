"""Crée un compte de démonstration avec quatre mois de dépenses réalistes.

Usage : python -m scripts.seed_demo
Le script ne fait rien si le compte existe déjà.
"""

import random
from datetime import date, timedelta

from sqlalchemy import select

from app.database import SessionLocal
from app.models import Budget, User
from app.security import hash_password
from app.services.categories import ensure_default_categories, find_by_name
from app.services.expenses import create_expense
from app.services.periods import current_month, month_bounds, shift_month

DEMO_EMAIL = "awa.kone@example.com"
DEMO_PASSWORD = "demonstration-2026"

# (catégorie, libellé, montant minimum, montant maximum, occurrences par mois)
RECURRING = [
    ("Logement", "Loyer studio Angré", 90000, 90000, 1),
    ("Factures", "Facture CIE", 14000, 22000, 1),
    ("Factures", "Facture SODECI", 5000, 8500, 1),
    ("Factures", "Abonnement Canal+", 10000, 10000, 1),
    ("Communication", "Forfait internet Orange", 10000, 10000, 1),
]
VARIABLE = [
    ("Transport", "Gbaka Angré - Plateau", 300, 600, 12),
    ("Transport", "Woro-woro Cocody", 200, 500, 8),
    ("Transport", "Taxi retour du travail", 1500, 3500, 4),
    ("Transport", "Yango Riviera", 1500, 4000, 2),
    ("Alimentation", "Garba à midi", 500, 1500, 10),
    ("Alimentation", "Attiéké poisson", 1000, 2500, 5),
    ("Alimentation", "Déjeuner au maquis", 2000, 6000, 4),
    ("Alimentation", "Pain et lait", 500, 1500, 5),
    ("Alimentation", "Marché de Cocody", 5000, 15000, 4),
    ("Alimentation", "Courses supermarché", 8000, 25000, 2),
    ("Communication", "Recharge Orange", 500, 2000, 3),
    ("Communication", "Pass internet semaine", 1000, 2500, 2),
    ("Santé", "Pharmacie des Lagunes", 2500, 12000, 1),
    ("Loisirs", "Cinéma Majestic", 3000, 6000, 1),
    ("Loisirs", "Sortie à Grand-Bassam", 10000, 25000, 1),
    ("Habillement", "Couturier", 5000, 20000, 1),
    ("Éducation", "Livre de programmation", 5000, 15000, 1),
]
BUDGETS = {"Alimentation": 90000, "Transport": 25000, "Loisirs": 20000, "Communication": 15000}


def round_amount(value: int) -> int:
    step = 500 if value >= 5000 else 100
    return max(step, round(value / step) * step)


def seed() -> None:
    rng = random.Random(2026)
    with SessionLocal() as db:
        ensure_default_categories(db)
        if db.scalar(select(User).where(User.email == DEMO_EMAIL)):
            print("Le compte de démonstration existe déjà.")
            return

        user = User(name="Awa Koné", email=DEMO_EMAIL, password_hash=hash_password(DEMO_PASSWORD))
        db.add(user)
        db.flush()
        categories = {name: find_by_name(db, user, name) for name, *_ in RECURRING + VARIABLE}

        today = date.today()
        month = current_month(today)
        count = 0
        for offset in range(-3, 1):
            start, end = month_bounds(shift_month(month, offset))
            last_day = min(end - timedelta(days=1), today)
            days = (last_day - start).days + 1
            # Le mois en cours n'est rempli qu'au prorata des jours écoulés.
            progress = days / (end - start).days

            for name, label, low, high, _ in RECURRING:
                day = start + timedelta(days=rng.randint(0, min(6, days - 1)))
                create_expense(
                    db, user, amount=round_amount(rng.randint(low, high)), spent_on=day,
                    note=label, category_id=categories[name].id,
                )
                count += 1
            for name, label, low, high, per_month in VARIABLE:
                for _ in range(round(per_month * progress)):
                    create_expense(
                        db, user, amount=round_amount(rng.randint(low, high)),
                        spent_on=start + timedelta(days=rng.randint(0, days - 1)),
                        note=label, category_id=categories[name].id,
                    )
                    count += 1

        for name, ceiling in BUDGETS.items():
            db.add(Budget(user_id=user.id, category_id=categories[name].id, month=month, ceiling=ceiling))
        db.commit()
        print(f"Compte créé : {DEMO_EMAIL} / {DEMO_PASSWORD} ({count} dépenses)")


if __name__ == "__main__":
    seed()
