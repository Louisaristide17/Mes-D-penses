from fastapi import APIRouter, HTTPException, status
from sqlalchemy import func, select

from app.deps import CurrentUser, DbSession
from app.models import Category, Expense
from app.schemas import CategoryCreate, CategoryOut, CategoryUpdate
from app.services.categories import find_by_name, get_visible_category, to_out, visible_categories

router = APIRouter(prefix="/categories", tags=["Catégories"])


def _get_own_category(db, user, category_id: int) -> Category:
    category = get_visible_category(db, user, category_id)
    if category.user_id is None:
        raise HTTPException(status.HTTP_403_FORBIDDEN, "Les catégories par défaut ne peuvent pas être modifiées.")
    return category


@router.get("", response_model=list[CategoryOut])
def list_categories(user: CurrentUser, db: DbSession):
    return [to_out(category) for category in visible_categories(db, user)]


@router.post("", response_model=CategoryOut, status_code=status.HTTP_201_CREATED)
def create_category(payload: CategoryCreate, user: CurrentUser, db: DbSession):
    if find_by_name(db, user, payload.name):
        raise HTTPException(status.HTTP_409_CONFLICT, "Une catégorie porte déjà ce nom.")
    category = Category(user_id=user.id, **payload.model_dump())
    db.add(category)
    db.commit()
    return to_out(category)


@router.patch("/{category_id}", response_model=CategoryOut)
def update_category(category_id: int, payload: CategoryUpdate, user: CurrentUser, db: DbSession):
    category = _get_own_category(db, user, category_id)
    changes = payload.model_dump(exclude_unset=True, exclude_none=True)
    if "name" in changes:
        homonym = find_by_name(db, user, changes["name"])
        if homonym is not None and homonym.id != category.id:
            raise HTTPException(status.HTTP_409_CONFLICT, "Une catégorie porte déjà ce nom.")
    for field, value in changes.items():
        setattr(category, field, value)
    db.commit()
    return to_out(category)


@router.delete("/{category_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_category(category_id: int, user: CurrentUser, db: DbSession):
    category = _get_own_category(db, user, category_id)
    in_use = db.scalar(select(func.count()).select_from(Expense).where(Expense.category_id == category.id))
    if in_use:
        raise HTTPException(
            status.HTTP_409_CONFLICT,
            f"Cette catégorie est utilisée par {in_use} dépense(s). Reclassez-les avant de la supprimer.",
        )
    db.delete(category)
    db.commit()
