from fastapi import APIRouter, HTTPException, status
from sqlalchemy import select

from app.deps import CurrentUser, DbSession
from app.models import User
from app.schemas import PasswordChange, UserOut, UserUpdate
from app.security import hash_password, verify_password

router = APIRouter(prefix="/users", tags=["Profil"])


@router.get("/me", response_model=UserOut)
def read_profile(user: CurrentUser):
    return user


@router.patch("/me", response_model=UserOut)
def update_profile(payload: UserUpdate, user: CurrentUser, db: DbSession):
    if payload.email is not None:
        email = payload.email.lower()
        owner = db.scalar(select(User).where(User.email == email))
        if owner is not None and owner.id != user.id:
            raise HTTPException(status.HTTP_409_CONFLICT, "Cette adresse e-mail est déjà utilisée.")
        user.email = email
    if payload.name is not None:
        user.name = payload.name
    db.commit()
    return user


@router.post("/me/password", status_code=status.HTTP_204_NO_CONTENT)
def change_password(payload: PasswordChange, user: CurrentUser, db: DbSession):
    if not verify_password(payload.current_password, user.password_hash):
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Le mot de passe actuel est incorrect.")
    user.password_hash = hash_password(payload.new_password)
    db.commit()
