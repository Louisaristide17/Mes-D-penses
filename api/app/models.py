from datetime import date, datetime, timezone

from sqlalchemy import Date, DateTime, Float, ForeignKey, Index, Integer, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


def utcnow() -> datetime:
    return datetime.now(timezone.utc)


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(120))
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True)
    password_hash: Mapped[str] = mapped_column(String(255))
    currency: Mapped[str] = mapped_column(String(3), default="XOF")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)

    expenses: Mapped[list["Expense"]] = relationship(back_populates="user", cascade="all, delete-orphan")
    budgets: Mapped[list["Budget"]] = relationship(back_populates="user", cascade="all, delete-orphan")
    categories: Mapped[list["Category"]] = relationship(back_populates="user", cascade="all, delete-orphan")
    conversations: Mapped[list["Conversation"]] = relationship(
        back_populates="user", cascade="all, delete-orphan"
    )


class Category(Base):
    """Catégorie de dépense. user_id vide : catégorie par défaut, visible de tous."""

    __tablename__ = "categories"
    __table_args__ = (UniqueConstraint("user_id", "name", name="uq_categories_user_name"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int | None] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    name: Mapped[str] = mapped_column(String(60))
    color: Mapped[str] = mapped_column(String(7))
    icon: Mapped[str] = mapped_column(String(40))

    user: Mapped[User | None] = relationship(back_populates="categories")


class Expense(Base):
    __tablename__ = "expenses"
    __table_args__ = (Index("ix_expenses_user_date", "user_id", "date"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"))
    category_id: Mapped[int] = mapped_column(ForeignKey("categories.id", ondelete="RESTRICT"), index=True)
    # Le franc CFA n'a pas de subdivision en usage : le montant est un entier.
    amount: Mapped[int] = mapped_column(Integer)
    date: Mapped[date] = mapped_column(Date)
    note: Mapped[str] = mapped_column(String(255), default="")
    source: Mapped[str] = mapped_column(String(10), default="manuel")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)

    user: Mapped[User] = relationship(back_populates="expenses")
    category: Mapped[Category] = relationship()
    prediction: Mapped["Prediction | None"] = relationship(
        back_populates="expense", cascade="all, delete-orphan", uselist=False
    )


class Budget(Base):
    __tablename__ = "budgets"
    __table_args__ = (UniqueConstraint("user_id", "category_id", "month", name="uq_budgets_user_category_month"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    category_id: Mapped[int] = mapped_column(ForeignKey("categories.id", ondelete="CASCADE"))
    month: Mapped[str] = mapped_column(String(7))  # AAAA-MM
    ceiling: Mapped[int] = mapped_column(Integer)

    user: Mapped[User] = relationship(back_populates="budgets")
    category: Mapped[Category] = relationship()


class Prediction(Base):
    """Trace de la catégorie proposée par le modèle et de celle finalement retenue."""

    __tablename__ = "predictions"

    id: Mapped[int] = mapped_column(primary_key=True)
    expense_id: Mapped[int] = mapped_column(ForeignKey("expenses.id", ondelete="CASCADE"), unique=True)
    predicted_category_id: Mapped[int] = mapped_column(ForeignKey("categories.id", ondelete="CASCADE"))
    final_category_id: Mapped[int] = mapped_column(ForeignKey("categories.id", ondelete="CASCADE"))
    confidence: Mapped[float] = mapped_column(Float)
    engine: Mapped[str] = mapped_column(String(10))  # "modele" ou "regles"
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)

    expense: Mapped[Expense] = relationship(back_populates="prediction")


class Conversation(Base):
    __tablename__ = "conversations"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    title: Mapped[str] = mapped_column(String(120))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)

    user: Mapped[User] = relationship(back_populates="conversations")
    messages: Mapped[list["Message"]] = relationship(
        back_populates="conversation", cascade="all, delete-orphan", order_by="Message.id"
    )


class Message(Base):
    __tablename__ = "messages"

    id: Mapped[int] = mapped_column(primary_key=True)
    conversation_id: Mapped[int] = mapped_column(ForeignKey("conversations.id", ondelete="CASCADE"), index=True)
    role: Mapped[str] = mapped_column(String(10))
    content: Mapped[str] = mapped_column(Text)
    tool_name: Mapped[str | None] = mapped_column(String(60))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)

    conversation: Mapped[Conversation] = relationship(back_populates="messages")
