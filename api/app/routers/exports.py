from datetime import date

from fastapi import APIRouter, Response

from app.deps import CurrentUser, DbSession
from app.models import Expense
from app.services.expenses import filtered_query
from app.services.exports import expenses_to_csv, expenses_to_pdf

router = APIRouter(prefix="/exports", tags=["Exports"])


def _load(db, user, date_from, date_to, category_id) -> list[Expense]:
    query = filtered_query(user, date_from, date_to, category_id).order_by(Expense.date, Expense.id)
    return list(db.scalars(query))


def _filename(extension: str, date_from: date | None, date_to: date | None) -> str:
    parts = ["mes-depenses"]
    if date_from:
        parts.append(date_from.isoformat())
    if date_to:
        parts.append(date_to.isoformat())
    return "_".join(parts) + "." + extension


@router.get("/expenses.csv", response_class=Response, responses={200: {"content": {"text/csv": {}}}})
def export_csv(
    user: CurrentUser,
    db: DbSession,
    date_from: date | None = None,
    date_to: date | None = None,
    category_id: int | None = None,
):
    content = expenses_to_csv(_load(db, user, date_from, date_to, category_id))
    headers = {"Content-Disposition": f'attachment; filename="{_filename("csv", date_from, date_to)}"'}
    return Response(content, media_type="text/csv; charset=utf-8", headers=headers)


@router.get("/expenses.pdf", response_class=Response, responses={200: {"content": {"application/pdf": {}}}})
def export_pdf(
    user: CurrentUser,
    db: DbSession,
    date_from: date | None = None,
    date_to: date | None = None,
    category_id: int | None = None,
):
    expenses = _load(db, user, date_from, date_to, category_id)
    content = expenses_to_pdf(user, expenses, date_from, date_to)
    headers = {"Content-Disposition": f'attachment; filename="{_filename("pdf", date_from, date_to)}"'}
    return Response(content, media_type="application/pdf", headers=headers)
