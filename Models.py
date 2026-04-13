# models.py

import enum
from datetime import date, datetime
from typing import List, Optional

from sqlalchemy import (
    Boolean, Date, DateTime, Enum, Float,
    ForeignKey, String, Text, func,
)
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


# ---------------------------------------------------------------------------
# Base
# ---------------------------------------------------------------------------

class Base(DeclarativeBase):
    pass


# ---------------------------------------------------------------------------
# Enums
# ---------------------------------------------------------------------------

class SuggestionStatus(str, enum.Enum):
    pending    = "pending"
    acted_upon = "acted_upon"
    dismissed  = "dismissed"


# ---------------------------------------------------------------------------
# Models
# ---------------------------------------------------------------------------

class User(Base):
    __tablename__ = "users"

    id:              Mapped[int]      = mapped_column(primary_key=True, autoincrement=True)
    email:           Mapped[str]      = mapped_column(String(255), unique=True, nullable=False, index=True)
    hashed_password: Mapped[str]      = mapped_column(String(255), nullable=False)
    created_at:      Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    # Relationships
    transactions:   Mapped[List["Transaction"]]  = relationship(
        back_populates="user", cascade="all, delete-orphan", lazy="select"
    )
    ai_suggestions: Mapped[List["AiSuggestion"]] = relationship(
        back_populates="user", cascade="all, delete-orphan", lazy="select"
    )

    def __repr__(self) -> str:
        return f"User(id={self.id!r}, email={self.email!r})"


class Transaction(Base):
    __tablename__ = "transactions"

    id:           Mapped[int]           = mapped_column(primary_key=True, autoincrement=True)
    user_id:      Mapped[int]           = mapped_column(ForeignKey("users.id"), nullable=False, index=True)
    date:         Mapped[date]          = mapped_column(Date, nullable=False)
    description:  Mapped[str]           = mapped_column(String(500), nullable=False)
    amount:       Mapped[float]         = mapped_column(Float, nullable=False)
    category:     Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    is_recurring: Mapped[bool]          = mapped_column(Boolean, nullable=False, default=False)
    created_at:   Mapped[datetime]      = mapped_column(DateTime(timezone=True), server_default=func.now())

    # Relationship
    user: Mapped["User"] = relationship(back_populates="transactions")

    def __repr__(self) -> str:
        return f"Transaction(id={self.id!r}, user_id={self.user_id!r}, amount={self.amount!r})"


class AiSuggestion(Base):
    __tablename__ = "ai_suggestions"

    id:              Mapped[int]              = mapped_column(primary_key=True, autoincrement=True)
    user_id:         Mapped[int]              = mapped_column(ForeignKey("users.id"), nullable=False, index=True)
    generated_date:  Mapped[datetime]         = mapped_column(DateTime(timezone=True), server_default=func.now())
    suggestion_text: Mapped[str]              = mapped_column(Text, nullable=False)
    status:          Mapped[SuggestionStatus] = mapped_column(
        Enum(SuggestionStatus), nullable=False, default=SuggestionStatus.pending
    )

    # Relationship
    user: Mapped["User"] = relationship(back_populates="ai_suggestions")

    def __repr__(self) -> str:
        return f"AiSuggestion(id={self.id!r}, user_id={self.user_id!r}, status={self.status!r})"
    