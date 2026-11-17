from fastapi import APIRouter, HTTPException, status
from sqlalchemy import select

from app.deps import CurrentUser, DbSession
from app.models import Budget
from app.schemas import BudgetOut, BudgetStatus, BudgetUpsert, Month
from app.services.budgets import budget_statuses
from app.services.categories import get_visible_category, to_out

router = APIRouter(prefix="/budgets", tags=["Budgets"])


def _to_out(budget: Budget) -> BudgetOut:
    return BudgetOut(id=budget.id, month=budget.month, ceiling=budget.ceiling, category=to_out(budget.category))


@router.get("", response_model=list[BudgetOut])
def list_budgets(month: Month, user: CurrentUser, db: DbSession):
    budgets = db.scalars(select(Budget).where(Budget.user_id == user.id, Budget.month == month).order_by(Budget.id))
    return [_to_out(budget) for budget in budgets]


@router.put("", response_model=BudgetOut)
def set_budget(payload: BudgetUpsert, user: CurrentUser, db: DbSession):
    """Crée le budget de la catégorie pour le mois, ou remplace son plafond s'il existe."""
    category = get_visible_category(db, user, payload.category_id)
    budget = db.scalar(
        select(Budget).where(
            Budget.user_id == user.id, Budget.category_id == category.id, Budget.month == payload.month
        )
    )
    if budget is None:
        budget = Budget(user_id=user.id, category_id=category.id, month=payload.month, ceiling=payload.ceiling)
        db.add(budget)
    else:
        budget.ceiling = payload.ceiling
    db.commit()
    return _to_out(budget)


@router.get("/status", response_model=list[BudgetStatus])
def read_budget_statuses(month: Month, user: CurrentUser, db: DbSession):
    return budget_statuses(db, user, month)


@router.delete("/{budget_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_budget(budget_id: int, user: CurrentUser, db: DbSession):
    budget = db.get(Budget, budget_id)
    if budget is None or budget.user_id != user.id:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Budget introuvable.")
    db.delete(budget)
    db.commit()
