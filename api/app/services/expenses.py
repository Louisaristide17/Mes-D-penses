from datetime import date

from sqlalchemy import Select, select
from sqlalchemy.orm import Session, selectinload

from app.models import Expense, Prediction, User
from app.schemas import ExpenseOut
from app.services import categorizer
from app.services.categories import FALLBACK_CATEGORY, find_by_name, get_visible_category, to_out


def filtered_query(
    user: User,
    date_from: date | None = None,
    date_to: date | None = None,
    category_id: int | None = None,
    search: str | None = None,
) -> Select:
    query = select(Expense).where(Expense.user_id == user.id).options(selectinload(Expense.category))
    if date_from:
        query = query.where(Expense.date >= date_from)
    if date_to:
        query = query.where(Expense.date <= date_to)
    if category_id:
        query = query.where(Expense.category_id == category_id)
    if search:
        escaped = search.replace("\\", "\\\\").replace("%", "\\%").replace("_", "\\_")
        query = query.where(Expense.note.ilike(f"%{escaped}%", escape="\\"))
    return query


def create_expense(
    db: Session,
    user: User,
    *,
    amount: int,
    spent_on: date,
    note: str = "",
    category_id: int | None = None,
    source: str = "manuel",
) -> Expense:
    """Crée une dépense. Sans catégorie fournie, celle proposée par le modèle est retenue.

    La proposition est enregistrée même quand l'utilisateur choisit lui-même la
    catégorie : l'écart entre les deux sert à mesurer et à réentraîner le modèle.
    """
    suggestion = categorizer.suggest(note) if note else None
    predicted = find_by_name(db, user, suggestion.category_name) if suggestion else None

    if category_id is not None:
        category = get_visible_category(db, user, category_id)
    else:
        category = predicted or find_by_name(db, user, FALLBACK_CATEGORY)
        if category is None:
            raise RuntimeError("Catégories par défaut absentes de la base")

    expense = Expense(
        user_id=user.id, category_id=category.id, amount=amount, date=spent_on, note=note, source=source
    )
    if predicted is not None:
        expense.prediction = Prediction(
            predicted_category_id=predicted.id,
            final_category_id=category.id,
            confidence=suggestion.confidence,
            engine=suggestion.engine,
        )
    db.add(expense)
    db.flush()
    expense.category = category
    return expense


def to_out_expense(expense: Expense) -> ExpenseOut:
    return ExpenseOut(
        id=expense.id,
        amount=expense.amount,
        date=expense.date,
        note=expense.note,
        source=expense.source,
        category=to_out(expense.category),
        created_at=expense.created_at,
    )
