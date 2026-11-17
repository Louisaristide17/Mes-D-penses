import datetime as dt
from typing import Annotated, Literal

from pydantic import BaseModel, ConfigDict, EmailStr, Field, StringConstraints, field_validator

Month = Annotated[str, StringConstraints(pattern=r"^\d{4}-(0[1-9]|1[0-2])$")]
HexColor = Annotated[str, StringConstraints(pattern=r"^#[0-9A-Fa-f]{6}$")]
Name = Annotated[str, StringConstraints(strip_whitespace=True, min_length=2, max_length=120)]
# bcrypt ignore tout ce qui dépasse 72 octets : on borne la longueur en amont.
Password = Annotated[str, StringConstraints(min_length=8, max_length=72)]


class OrmModel(BaseModel):
    model_config = ConfigDict(from_attributes=True)


# Comptes

class UserCreate(BaseModel):
    name: Name
    email: EmailStr
    password: Password

    @field_validator("email")
    @classmethod
    def lowercase_email(cls, value: str) -> str:
        return value.lower()


class LoginRequest(BaseModel):
    email: EmailStr
    password: str

    @field_validator("email")
    @classmethod
    def lowercase_email(cls, value: str) -> str:
        return value.lower()


class RefreshRequest(BaseModel):
    refresh_token: str


class UserOut(OrmModel):
    id: int
    name: str
    email: EmailStr
    currency: str
    created_at: dt.datetime


class UserUpdate(BaseModel):
    name: Name | None = None
    email: EmailStr | None = None


class PasswordChange(BaseModel):
    current_password: str
    new_password: Password


class TokenPair(BaseModel):
    access_token: str
    refresh_token: str
    token_type: Literal["bearer"] = "bearer"


class AuthResponse(TokenPair):
    user: UserOut


# Catégories

class CategoryBase(BaseModel):
    name: Annotated[str, StringConstraints(strip_whitespace=True, min_length=2, max_length=60)]
    color: HexColor
    icon: Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=40)]


class CategoryCreate(CategoryBase):
    pass


class CategoryUpdate(BaseModel):
    name: Annotated[str, StringConstraints(strip_whitespace=True, min_length=2, max_length=60)] | None = None
    color: HexColor | None = None
    icon: Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=40)] | None = None


class CategoryOut(OrmModel):
    id: int
    name: str
    color: str
    icon: str
    is_default: bool


# Dépenses

Note = Annotated[str, StringConstraints(strip_whitespace=True, max_length=255)]


class ExpenseCreate(BaseModel):
    amount: int = Field(gt=0, le=1_000_000_000, description="Montant en francs CFA")
    date: dt.date
    note: Note = ""
    category_id: int | None = Field(
        default=None, description="Laisser vide pour que la catégorie soit proposée automatiquement"
    )


class ExpenseUpdate(BaseModel):
    amount: int | None = Field(default=None, gt=0, le=1_000_000_000)
    date: dt.date | None = None
    note: Note | None = None
    category_id: int | None = None


class ExpenseOut(OrmModel):
    id: int
    amount: int
    date: dt.date
    note: str
    source: str
    category: CategoryOut
    created_at: dt.datetime


class ExpensePage(BaseModel):
    items: list[ExpenseOut]
    total: int
    limit: int
    offset: int


class SuggestionRequest(BaseModel):
    note: Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=255)]


class SuggestionOut(BaseModel):
    category: CategoryOut | None
    confidence: float
    engine: Literal["modele", "regles"]


class ImportIssue(BaseModel):
    line: int
    message: str


class ImportReport(BaseModel):
    imported: int
    rejected: int
    errors: list[ImportIssue]


# Budgets

class BudgetUpsert(BaseModel):
    category_id: int
    month: Month
    ceiling: int = Field(gt=0, le=1_000_000_000)


class BudgetOut(OrmModel):
    id: int
    month: str
    ceiling: int
    category: CategoryOut


class BudgetStatus(BaseModel):
    budget_id: int
    category: CategoryOut
    month: str
    ceiling: int
    spent: int
    remaining: int
    ratio: float
    level: Literal["ok", "attention", "depasse"]


# Tableau de bord

class CategoryTotal(BaseModel):
    category: CategoryOut
    total: int
    share: float


class MonthTotal(BaseModel):
    month: str
    total: int


class DayTotal(BaseModel):
    date: dt.date
    total: int


class DashboardSummary(BaseModel):
    month: str
    total: int
    count: int
    previous_total: int
    variation: float | None
    by_category: list[CategoryTotal]
    monthly: list[MonthTotal]
    daily: list[DayTotal]
    alerts: list[BudgetStatus]
    recent: list[ExpenseOut]


# Assistant

class AssistantRequest(BaseModel):
    message: Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=1000)]
    conversation_id: int | None = None


class AssistantReply(BaseModel):
    conversation_id: int
    reply: str
    tools_used: list[str]
    data_changed: bool = Field(description="Vrai si l'assistant a enregistré une dépense : le client doit recharger ses données")


class ConversationOut(OrmModel):
    id: int
    title: str
    created_at: dt.datetime


class MessageOut(BaseModel):
    role: Literal["user", "assistant"]
    content: str
    tools_used: list[str]
    created_at: dt.datetime


class ConversationDetail(ConversationOut):
    messages: list[MessageOut]
