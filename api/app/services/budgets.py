from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models import Budget, Expense, User
from app.schemas import BudgetStatus
from app.services.categories import to_out
from app.services.periods import month_bounds

WARNING_RATIO = 0.8


def budget_level(spent: int, ceiling: int) -> str:
    if spent > ceiling:
        return "depasse"
    if spent >= ceiling * WARNING_RATIO:
        return "attention"
    return "ok"


def budget_statuses(db: Session, user: User, month: str) -> list[BudgetStatus]:
    start, end = month_bounds(month)
    spent_by_category = dict(
        db.execute(
            select(Expense.category_id, func.sum(Expense.amount))
            .where(Expense.user_id == user.id, Expense.date >= start, Expense.date < end)
            .group_by(Expense.category_id)
        ).all()
    )
    budgets = db.scalars(
        select(Budget).where(Budget.user_id == user.id, Budget.month == month).order_by(Budget.id)
    )
    statuses = []
    for budget in budgets:
        spent = int(spent_by_category.get(budget.category_id, 0))
        statuses.append(
            BudgetStatus(
                budget_id=budget.id,
                category=to_out(budget.category),
                month=budget.month,
                ceiling=budget.ceiling,
                spent=spent,
                remaining=budget.ceiling - spent,
                ratio=round(spent / budget.ceiling, 4),
                level=budget_level(spent, budget.ceiling),
            )
        )
    return statuses
