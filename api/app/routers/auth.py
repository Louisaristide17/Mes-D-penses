from fastapi import APIRouter, HTTPException, status
from sqlalchemy import select

from app.deps import DbSession
from app.models import User
from app.schemas import AuthResponse, LoginRequest, RefreshRequest, TokenPair, UserCreate, UserOut
from app.security import InvalidToken, create_token, decode_token, hash_password, verify_password

router = APIRouter(prefix="/auth", tags=["Authentification"])


def _token_pair(user_id: int) -> dict[str, str]:
    return {
        "access_token": create_token(user_id, "access"),
        "refresh_token": create_token(user_id, "refresh"),
    }


@router.post("/register", response_model=AuthResponse, status_code=status.HTTP_201_CREATED)
def register(payload: UserCreate, db: DbSession):
    if db.scalar(select(User).where(User.email == payload.email)):
        raise HTTPException(status.HTTP_409_CONFLICT, "Un compte existe déjà avec cette adresse e-mail.")
    user = User(name=payload.name, email=payload.email, password_hash=hash_password(payload.password))
    db.add(user)
    db.commit()
    return AuthResponse(user=UserOut.model_validate(user), **_token_pair(user.id))


@router.post("/login", response_model=AuthResponse)
def login(payload: LoginRequest, db: DbSession):
    user = db.scalar(select(User).where(User.email == payload.email))
    # Même message dans les deux cas pour ne pas révéler quels e-mails sont inscrits.
    if user is None or not verify_password(payload.password, user.password_hash):
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Adresse e-mail ou mot de passe incorrect.")
    return AuthResponse(user=UserOut.model_validate(user), **_token_pair(user.id))


@router.post("/refresh", response_model=TokenPair)
def refresh(payload: RefreshRequest, db: DbSession):
    try:
        user_id = decode_token(payload.refresh_token, "refresh")
    except InvalidToken:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Session expirée. Veuillez vous reconnecter.")
    if db.get(User, user_id) is None:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Session expirée. Veuillez vous reconnecter.")
    return TokenPair(**_token_pair(user_id))
