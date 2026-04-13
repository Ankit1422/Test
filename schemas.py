# schemas.py

import enum
from datetime import date, datetime
from typing import List, Optional

from pydantic import BaseModel, ConfigDict, EmailStr, Field


# ---------------------------------------------------------------------------
# Mirrored Enum (must match models.SuggestionStatus exactly)
# ---------------------------------------------------------------------------

class SuggestionStatus(str, enum.Enum):
    pending    = "pending"
    acted_upon = "acted_upon"
    dismissed  = "dismissed"


# ===========================================================================
# USER
# ===========================================================================

class UserBase(BaseModel):
    """Fields shared by all User schemas."""
    email: EmailStr


class UserCreate(UserBase):
    """Accepted on POST /users — raw password, hashed before storage."""
    password: str = Field(..., min_length=8, description="Plain-text password (hashed before DB write)")


class UserResponse(UserBase):
    """Returned in API responses — never exposes hashed_password."""
    id:         int
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


# ===========================================================================
# TRANSACTION
# ===========================================================================

class TransactionBase(BaseModel):
    """Fields shared by all Transaction schemas."""
    date:         date
    description:  str         = Field(..., max_length=500)
    amount:       float       = Field(..., description="Positive = income, negative = expense")
    category:     Optional[str] = Field(None, max_length=100)
    is_recurring: bool        = Field(False)


class TransactionCreate(TransactionBase):
    """Accepted on POST /transactions — user_id injected from the auth token, not the body."""
    pass


class TransactionResponse(TransactionBase):
    """Returned in API responses."""
    id:         int
    user_id:    int
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


# ===========================================================================
# AI SUGGESTION
# ===========================================================================

class AiSuggestionBase(BaseModel):
    """Fields shared by all AiSuggestion schemas."""
    suggestion_text: str
    status:          SuggestionStatus = SuggestionStatus.pending


class AiSuggestionCreate(AiSuggestionBase):
    """Accepted when a new AI suggestion is written — user_id comes from the auth layer."""
    pass


class AiSuggestionStatusUpdate(BaseModel):
    """Accepted on PATCH /suggestions/{id} — only the status field is mutable by the client."""
    status: SuggestionStatus


class AiSuggestionResponse(AiSuggestionBase):
    """Returned in API responses."""
    id:             int
    user_id:        int
    generated_date: datetime

    model_config = ConfigDict(from_attributes=True)


# ===========================================================================
# NESTED RESPONSE  (User with related records inlined)
# ===========================================================================

class UserDetailResponse(UserResponse):
    """Extended User response that embeds related transactions and suggestions.

    Use this for a GET /users/{id} detail endpoint. Avoid it on list endpoints
    — fetching nested collections for every row in a list is an N+1 query trap.
    """
    transactions:   List[TransactionResponse]  = []
    ai_suggestions: List[AiSuggestionResponse] = []

    model_config = ConfigDict(from_attributes=True)