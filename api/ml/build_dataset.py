"""Génère le jeu de libellés bruts à partir du vocabulaire.

Usage : python -m ml.build_dataset

Le jeu est synthétique : chaque libellé de base, rédigé à la main, est décliné
en variantes proches de ce qu'un utilisateur saisit réellement (lieu, précision,
abréviation, majuscules, accents oubliés, faute de frappe). La colonne "groupe"
identifie le libellé de base : elle sert à séparer entraînement et test sans
qu'un même libellé de base se retrouve des deux côtés.
"""

import csv
import random
import re
import unicodedata
from pathlib import Path

from ml.vocabulary import ABBREVIATIONS, BASE_LABELS, DETAILS, PLACE_CATEGORIES, PLACES, PREFIXES

DATA_DIR = Path(__file__).parent / "data"
RAW_PATH = DATA_DIR / "libelles_bruts.csv"
VARIANTS_PER_LABEL = 14
SEED = 2026


def strip_accents(text: str) -> str:
    decomposed = unicodedata.normalize("NFKD", text)
    return "".join(char for char in decomposed if not unicodedata.combining(char))


def add_typo(text: str, rng: random.Random) -> str:
    """Introduit une faute de frappe : lettre oubliée, doublée ou inversée avec sa voisine."""
    positions = [index for index, char in enumerate(text) if char.isalpha()]
    if len(positions) < 4:
        return text
    index = rng.choice(positions[1:-1])
    kind = rng.choice(["drop", "double", "swap"])
    if kind == "drop":
        return text[:index] + text[index + 1:]
    if kind == "double":
        return text[:index] + text[index] + text[index:]
    if index + 1 < len(text) and text[index + 1].isalpha():
        return text[:index] + text[index + 1] + text[index] + text[index + 2:]
    return text


def abbreviate(text: str) -> str:
    # Les expressions de plusieurs mots ("orange money") sont remplacées d'abord, puis les mots isolés.
    for phrase, short in ABBREVIATIONS.items():
        if " " in phrase:
            text = re.sub(rf"\b{re.escape(phrase)}\b", short, text, flags=re.IGNORECASE)
    words = [ABBREVIATIONS.get(word.lower(), word) for word in text.split(" ")]
    return " ".join(words)


def make_variant(base: str, category: str, rng: random.Random) -> str:
    text = base
    if rng.random() < 0.15:
        text = f"{rng.choice(PREFIXES)} {text[0].lower()}{text[1:]}"
    if category in PLACE_CATEGORIES and rng.random() < 0.35:
        text = f"{text} {rng.choice(PLACES)}"
    if rng.random() < 0.40:
        text = f"{text} {rng.choice(DETAILS)}"
    if rng.random() < 0.20:
        text = abbreviate(text)

    style = rng.random()
    if style < 0.35:
        text = text.lower()
    elif style < 0.45:
        text = text.upper()
    if rng.random() < 0.35:
        text = strip_accents(text)
    if rng.random() < 0.15:
        text = add_typo(text, rng)
    return text


def build_rows(seed: int = SEED) -> list[dict]:
    rng = random.Random(seed)
    rows = []
    for category, labels in BASE_LABELS.items():
        for index, base in enumerate(labels):
            group = f"{category}-{index:02d}"
            rows.append({"libelle": base, "categorie": category, "groupe": group})
            for _ in range(VARIANTS_PER_LABEL):
                rows.append({"libelle": make_variant(base, category, rng), "categorie": category, "groupe": group})
    rng.shuffle(rows)
    return rows


def main() -> None:
    rows = build_rows()
    DATA_DIR.mkdir(exist_ok=True)
    with RAW_PATH.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=["libelle", "categorie", "groupe"])
        writer.writeheader()
        writer.writerows(rows)
    print(f"{len(rows)} libellés bruts écrits dans {RAW_PATH}")


if __name__ == "__main__":
    main()
