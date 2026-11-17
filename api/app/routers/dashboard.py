from fastapi import APIRouter
from sqlalchemy import func, select
from sqlalchemy.orm import selectinload

from app.deps import CurrentUser, DbSession
from app.models import Category, Expense
from app.schemas import CategoryTotal, DashboardSummary, DayTotal, Month, MonthTotal
from app.services.budgets import budget_statuses
from app.services.categories import to_out
from app.services.expenses import to_out_expense
from app.services.periods import current_month, month_bounds, shift_month

router = APIRouter(prefix="/dashboard", tags=["Tableau de bord"])

HISTORY_MONTHS = 6


def _month_total(db, user, month: str) -> int:
    start, end = month_bounds(month)
    total = db.scalar(
        select(func.coalesce(func.sum(Expense.amount), 0)).where(
            Expense.user_id == user.id, Expense.date >= start, Expense.date < end
        )
    )
    return int(total)


@router.get("/summary", response_model=DashboardSummary)
def read_summary(user: CurrentUser, db: DbSession, month: Month | None = None):
    month = month or current_month()
    start, end = month_bounds(month)
    in_month = (Expense.user_id == user.id, Expense.date >= start, Expense.date < end)

    total, count = db.execute(
        select(func.coalesce(func.sum(Expense.amount), 0), func.count(Expense.id)).where(*in_month)
    ).one()
    total = int(total)

    previous_total = _month_total(db, user, shift_month(month, -1))
    variation = round((total - previous_total) / previous_total, 4) if previous_total else None

    category_rows = db.execute(
        select(Category, func.sum(Expense.amount).label("total"))
        .join(Expense, Expense.category_id == Category.id)
        .where(*in_month)
        .group_by(Category.id)
        .order_by(func.sum(Expense.amount).desc())
    ).all()
    by_category = [
        CategoryTotal(category=to_out(category), total=int(amount), share=round(int(amount) / total, 4))
        for category, amount in category_rows
    ]

    # Une requête par mois : six requêtes simples, portables entre SQLite et PostgreSQL.
    months = [shift_month(month, -offset) for offset in range(HISTORY_MONTHS - 1, 0, -1)]
    monthly = [MonthTotal(month=m, total=_month_total(db, user, m)) for m in months]
    monthly.append(MonthTotal(month=month, total=total))

    daily_rows = db.execute(
        select(Expense.date, func.sum(Expense.amount)).where(*in_month).group_by(Expense.date).order_by(Expense.date)
    ).all()

    recent = db.scalars(
        select(Expense)
        .where(*in_month)
        .options(selectinload(Expense.category))
        .order_by(Expense.date.desc(), Expense.id.desc())
        .limit(5)
    )

    return DashboardSummary(
        month=month,
        total=total,
        count=count,
        previous_total=previous_total,
        variation=variation,
        by_category=by_category,
        monthly=monthly,
        daily=[DayTotal(date=day, total=int(amount)) for day, amount in daily_rows],
        alerts=[status for status in budget_statuses(db, user, month) if status.level != "ok"],
        recent=[to_out_expense(expense) for expense in recent],
    )
