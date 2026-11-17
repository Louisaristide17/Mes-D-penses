from fastapi import HTTPException, status
from sqlalchemy import or_, select
from sqlalchemy.orm import Session

from app.models import Category, User
from app.schemas import CategoryOut

FALLBACK_CATEGORY = "Autres"

# Couleurs choisies pour rester lisibles sur fond clair et distinctes entre elles.
DEFAULT_CATEGORIES: list[tuple[str, str, str]] = [
    ("Alimentation", "#0F5D4A", "utensils"),
    ("Transport", "#2F6FB0", "bus"),
    ("Logement", "#7A5AA6", "home"),
    ("Factures", "#B7791F", "receipt"),
    ("Communication", "#1E8A8A", "smartphone"),
    ("Santé", "#B4483A", "heart-pulse"),
    ("Éducation", "#4F5FB8", "graduation-cap"),
    ("Loisirs", "#C0567F", "ticket"),
    ("Habillement", "#8A6D3B", "shirt"),
    (FALLBACK_CATEGORY, "#5B6661", "circle-ellipsis"),
]


def ensure_default_categories(db: Session) -> None:
    existing = set(db.scalars(select(Category.name).where(Category.user_id.is_(None))))
    for name, color, icon in DEFAULT_CATEGORIES:
        if name not in existing:
            db.add(Category(user_id=None, name=name, color=color, icon=icon))
    db.commit()


def visible_categories(db: Session, user: User) -> list[Category]:
    query = (
        select(Category)
        .where(or_(Category.user_id.is_(None), Category.user_id == user.id))
        .order_by(Category.user_id.is_not(None), Category.name)
    )
    return list(db.scalars(query))


def get_visible_category(db: Session, user: User, category_id: int) -> Category:
    category = db.get(Category, category_id)
    if category is None or category.user_id not in (None, user.id):
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Catégorie introuvable.")
    return category


def find_by_name(db: Session, user: User, name: str) -> Category | None:
    wanted = name.casefold()
    for category in visible_categories(db, user):
        if category.name.casefold() == wanted:
            return category
    return None


def to_out(category: Category) -> CategoryOut:
    return CategoryOut(
        id=category.id,
        name=category.name,
        color=category.color,
        icon=category.icon,
        is_default=category.user_id is None,
    )
