from datetime import date
from typing import Annotated

from fastapi import APIRouter, File, HTTPException, Query, UploadFile, status
from sqlalchemy import func, select

from app.deps import CurrentUser, DbSession
from app.models import Expense
from app.schemas import (
    ExpenseCreate,
    ExpenseOut,
    ExpensePage,
    ExpenseUpdate,
    ImportIssue,
    ImportReport,
    SuggestionOut,
    SuggestionRequest,
)
from app.services import categorizer
from app.services.categories import find_by_name, get_visible_category, to_out
from app.services.expenses import create_expense, filtered_query, to_out_expense
from app.services.imports import InvalidFile, parse_expenses_csv

router = APIRouter(prefix="/expenses", tags=["Dépenses"])

MAX_IMPORT_BYTES = 2 * 1024 * 1024


def _get_own_expense(db, user, expense_id: int) -> Expense:
    expense = db.get(Expense, expense_id)
    if expense is None or expense.user_id != user.id:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Dépense introuvable.")
    return expense


@router.get("", response_model=ExpensePage)
def list_expenses(
    user: CurrentUser,
    db: DbSession,
    date_from: date | None = None,
    date_to: date | None = None,
    category_id: int | None = None,
    q: Annotated[str | None, Query(max_length=100, description="Recherche dans la note")] = None,
    limit: Annotated[int, Query(ge=1, le=200)] = 50,
    offset: Annotated[int, Query(ge=0)] = 0,
):
    query = filtered_query(user, date_from, date_to, category_id, q)
    total = db.scalar(select(func.count()).select_from(query.order_by(None).subquery()))
    rows = db.scalars(query.order_by(Expense.date.desc(), Expense.id.desc()).limit(limit).offset(offset))
    return ExpensePage(items=[to_out_expense(row) for row in rows], total=total, limit=limit, offset=offset)


@router.post("", response_model=ExpenseOut, status_code=status.HTTP_201_CREATED)
def add_expense(payload: ExpenseCreate, user: CurrentUser, db: DbSession):
    expense = create_expense(
        db,
        user,
        amount=payload.amount,
        spent_on=payload.date,
        note=payload.note,
        category_id=payload.category_id,
    )
    db.commit()
    return to_out_expense(expense)


@router.post("/suggest-category", response_model=SuggestionOut)
def suggest_category(payload: SuggestionRequest, user: CurrentUser, db: DbSession):
    """Propose une catégorie pendant la saisie, sans rien enregistrer."""
    suggestion = categorizer.suggest(payload.note)
    category = find_by_name(db, user, suggestion.category_name) if suggestion else None
    if category is None:
        return SuggestionOut(category=None, confidence=0.0, engine="regles")
    return SuggestionOut(category=to_out(category), confidence=suggestion.confidence, engine=suggestion.engine)


@router.post("/import", response_model=ImportReport)
async def import_expenses(user: CurrentUser, db: DbSession, file: Annotated[UploadFile, File()]):
    """Importe un fichier CSV avec les colonnes date, montant, note et categorie (les deux dernières facultatives)."""
    content = await file.read(MAX_IMPORT_BYTES + 1)
    if len(content) > MAX_IMPORT_BYTES:
        raise HTTPException(413, "Le fichier dépasse 2 Mo.")
    try:
        parsed = parse_expenses_csv(content)
    except InvalidFile as exc:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, str(exc))

    for row in parsed.rows:
        named = find_by_name(db, user, row.category_name) if row.category_name else None
        create_expense(
            db,
            user,
            amount=row.amount,
            spent_on=row.date,
            note=row.note,
            category_id=named.id if named else None,
            source="import",
        )
    db.commit()
    return ImportReport(
        imported=len(parsed.rows),
        rejected=len(parsed.errors),
        errors=[ImportIssue(line=line, message=message) for line, message in parsed.errors[:50]],
    )


@router.get("/{expense_id}", response_model=ExpenseOut)
def read_expense(expense_id: int, user: CurrentUser, db: DbSession):
    return to_out_expense(_get_own_expense(db, user, expense_id))


@router.patch("/{expense_id}", response_model=ExpenseOut)
def update_expense(expense_id: int, payload: ExpenseUpdate, user: CurrentUser, db: DbSession):
    expense = _get_own_expense(db, user, expense_id)
    changes = payload.model_dump(exclude_unset=True, exclude_none=True)
    if "category_id" in changes:
        category = get_visible_category(db, user, changes["category_id"])
        expense.category = category
        if expense.prediction is not None:
            expense.prediction.final_category_id = category.id
    for field in ("amount", "date", "note"):
        if field in changes:
            setattr(expense, field, changes[field])
    db.commit()
    return to_out_expense(expense)


@router.delete("/{expense_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_expense(expense_id: int, user: CurrentUser, db: DbSession):
    db.delete(_get_own_expense(db, user, expense_id))
    db.commit()
