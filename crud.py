# crud.py

from sqlalchemy.orm import Session
from sqlalchemy import select

import models
import schemas
from passlib.context import CryptContext

# ---------------------------------------------------------------------------
# Password hashing
# ---------------------------------------------------------------------------

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def hash_password(plain_password: str) -> str:
    return pwd_context.hash(plain_password)

def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)


# ===========================================================================
# USER
# ===========================================================================

def get_user_by_email(db: Session, email: str) -> models.User | None:
    """Return the User row matching the given email, or None if not found.

    Uses a SELECT ... WHERE with an index scan (email is indexed in the model).
    Safe against case-sensitive duplicates — normalise email to lowercase before
    calling this if your app allows mixed-case registration.
    """
    stmt = select(models.User).where(models.User.email == email)
    return db.execute(stmt).scalars().first()


def get_user_by_id(db: Session, user_id: int) -> models.User | None:
    """Return the User row matching the given primary key, or None if not found."""
    return db.get(models.User, user_id)


def create_user(db: Session, payload: schemas.UserCreate) -> models.User:
    """Insert a new User row.

    Hashes the plain-text password from the schema before writing to the DB.
    Raises IntegrityError (propagated to the caller) if the email already exists.
    """
    user = models.User(
        email=payload.email,
        hashed_password=hash_password(payload.password),
    )
    db.add(user)
    db.commit()
    db.refresh(user)   # repopulates server-side defaults (id, created_at)
    return user


# ===========================================================================
# TRANSACTION
# ===========================================================================

def get_transactions_by_user(
    db: Session,
    user_id: int,
    *,
    skip: int = 0,
    limit: int = 100,
) -> list[models.Transaction]:
    """Return a paginated list of Transactions belonging to the given user.

    Results are ordered by date descending (most recent first).
    Use skip/limit for cursor-style pagination in the route layer.
    """
    stmt = (
        select(models.Transaction)
        .where(models.Transaction.user_id == user_id)
        .order_by(models.Transaction.date.desc())
        .offset(skip)
        .limit(limit)
    )
    return db.execute(stmt).scalars().all()


def get_transaction_by_id(
    db: Session,
    transaction_id: int,
) -> models.Transaction | None:
    """Return a single Transaction by primary key, or None if not found."""
    return db.get(models.Transaction, transaction_id)


def create_transaction(
    db: Session,
    payload: schemas.TransactionCreate,
    user_id: int,
) -> models.Transaction:
    """Insert a new Transaction row linked to the given user.

    user_id is passed explicitly from the auth layer — it is never read from
    the request body to prevent a user from writing to another user's account.
    """
    transaction = models.Transaction(
        user_id=user_id,
        date=payload.date,
        description=payload.description,
        amount=payload.amount,
        category=payload.category,
        is_recurring=payload.is_recurring,
    )
    db.add(transaction)
    db.commit()
    db.refresh(transaction)
    return transaction


# ===========================================================================
# AI SUGGESTION
# ===========================================================================

def get_suggestions_by_user(
    db: Session,
    user_id: int,
    *,
    skip: int = 0,
    limit: int = 50,
) -> list[models.AiSuggestion]:
    """Return a paginated list of AiSuggestions for the given user,
    ordered by generated_date descending (newest first).
    """
    stmt = (
        select(models.AiSuggestion)
        .where(models.AiSuggestion.user_id == user_id)
        .order_by(models.AiSuggestion.generated_date.desc())
        .offset(skip)
        .limit(limit)
    )
    return db.execute(stmt).scalars().all()


def create_suggestion(
    db: Session,
    payload: schemas.AiSuggestionCreate,
    user_id: int,
) -> models.AiSuggestion:
    """Insert a new AiSuggestion row. Called by your AI generation service,
    not directly by the user.
    """
    suggestion = models.AiSuggestion(
        user_id=user_id,
        suggestion_text=payload.suggestion_text,
        status=payload.status,
    )
    db.add(suggestion)
    db.commit()
    db.refresh(suggestion)
    return suggestion


def update_suggestion_status(
    db: Session,
    suggestion_id: int,
    payload: schemas.AiSuggestionStatusUpdate,
) -> models.AiSuggestion | None:
    """Update only the status field of an existing AiSuggestion.
    Returns None if the suggestion does not exist.
    """
    suggestion = db.get(models.AiSuggestion, suggestion_id)
    if suggestion is None:
        return None
    suggestion.status = payload.status
    db.commit()
    db.refresh(suggestion)
    return suggestion