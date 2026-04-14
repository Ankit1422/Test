# main.py

from fastapi import Depends, FastAPI, HTTPException, status
from sqlalchemy.orm import Session
from ai_engine import categorize_transaction
import crud
import models
import schemas
from database import engine, get_db

# ---------------------------------------------------------------------------
# Table creation on startup
# ---------------------------------------------------------------------------

models.Base.metadata.create_all(bind=engine)

# ---------------------------------------------------------------------------
# App instance
# ---------------------------------------------------------------------------

app = FastAPI(
    title="AI Budget API",
    description="Personal finance backend with AI-powered suggestions.",
    version="0.1.0",
)


# ===========================================================================
# USER ENDPOINTS
# ===========================================================================

@app.post(
    "/users/",
    response_model=schemas.UserResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Register a new user",
    tags=["Users"],
)
def create_user(
    payload: schemas.UserCreate,
    db: Session = Depends(get_db),
):
    """Create a new user account.

    - Rejects the request with **409 Conflict** if the email is already registered.
    - The plain-text password is hashed inside `crud.create_user()` before storage.
    - The response never includes `hashed_password`.
    """
    existing = crud.get_user_by_email(db, email=payload.email)
    if existing:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Email '{payload.email}' is already registered.",
        )
    return crud.create_user(db, payload)


@app.get(
    "/users/{user_id}",
    response_model=schemas.UserResponse,
    summary="Get a user by ID",
    tags=["Users"],
)
def get_user(
    user_id: int,
    db: Session = Depends(get_db),
):
    """Fetch a single user by their primary key.

    - Returns **404 Not Found** if no user exists with the given ID.
    """
    user = crud.get_user_by_id(db, user_id=user_id)
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"User with id={user_id} not found.",
        )
    return user


# ===========================================================================
# TRANSACTION ENDPOINTS
# ===========================================================================

@app.post(
    "/users/{user_id}/transactions/",
    response_model=schemas.TransactionResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a transaction for a user",
    tags=["Transactions"],
)
def create_transaction(
    user_id: int,
    payload: schemas.TransactionCreate,
    db: Session = Depends(get_db),
):
    """Record a new financial transaction for the specified user.

    If no category is provided (or it is an empty string), the description
    is automatically sent to Gemini to assign a category before saving.

    - Returns **404 Not Found** if the user does not exist.
    - Returns **503 Service Unavailable** if AI categorization fails, so the
      transaction is never silently saved with a missing category.
    """
    # 1. Confirm the user exists
    user = crud.get_user_by_id(db, user_id=user_id)
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"User with id={user_id} not found.",
        )

    # 2. Auto-categorize if category is missing or blank
    if not payload.category or not payload.category.strip():
        try:
            assigned_category = categorize_transaction(payload.description)
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail=f"AI categorization failed: {str(e)}. "
                        "Provide a category manually or retry later.",
            )
        # Pydantic models are immutable — rebuild with the new category
        payload = payload.model_copy(update={"category": assigned_category})

    # 3. Save to database
    return crud.create_transaction(db, payload, user_id=user_id)

# ===========================================================================
# AI SUGGESTION ENDPOINTS
# ===========================================================================

@app.get(
    "/users/{user_id}/suggestions/",
    response_model=list[schemas.AiSuggestionResponse],
    summary="List all AI suggestions for a user",
    tags=["AI Suggestions"],
)
def list_suggestions(
    user_id: int,
    skip: int = 0,
    limit: int = 50,
    db: Session = Depends(get_db),
):
    """Return paginated AI suggestions for the specified user,
    ordered by **generated_date descending**.

    - Returns **404 Not Found** if the user does not exist.
    """
    user = crud.get_user_by_id(db, user_id=user_id)
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"User with id={user_id} not found.",
        )
    return crud.get_suggestions_by_user(db, user_id=user_id, skip=skip, limit=limit)


@app.patch(
    "/suggestions/{suggestion_id}/status",
    response_model=schemas.AiSuggestionResponse,
    summary="Update the status of an AI suggestion",
    tags=["AI Suggestions"],
)
def update_suggestion_status(
    suggestion_id: int,
    payload: schemas.AiSuggestionStatusUpdate,
    db: Session = Depends(get_db),
):
    """Allow a user to mark a suggestion as `acted_upon` or `dismissed`.

    - Returns **404 Not Found** if the suggestion does not exist.
    - Only the `status` field is mutable — `suggestion_text` is immutable by design.
    """
    suggestion = crud.update_suggestion_status(db, suggestion_id, payload)
    if suggestion is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Suggestion with id={suggestion_id} not found.",
        )
    return suggestion