# database.py

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from models import Base  # imports the shared DeclarativeBase from your models file

# ---------------------------------------------------------------------------
# Connection URL
# ---------------------------------------------------------------------------

SQLALCHEMY_DATABASE_URL = "postgresql://localhost/ai_budget"

# ---------------------------------------------------------------------------
# Engine
# ---------------------------------------------------------------------------

engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    pool_pre_ping=True,       # drops and recreates stale connections automatically
    pool_size=10,             # number of persistent connections in the pool
    max_overflow=20,          # extra connections allowed beyond pool_size under load
    echo=False,               # set True during development to log all SQL statements
)

# ---------------------------------------------------------------------------
# Session factory
# ---------------------------------------------------------------------------

SessionLocal = sessionmaker(
    bind=engine,
    autocommit=False,   # never commit unless explicitly told to
    autoflush=False,    # don't flush pending changes before every query
    expire_on_commit=True,
)

# ---------------------------------------------------------------------------
# Table creation helper (call once at startup, or use Alembic instead)
# ---------------------------------------------------------------------------

def create_tables() -> None:
    """Create all tables defined in the models if they do not already exist.

    Prefer Alembic for production migrations. This function is useful for
    local development and testing when you want a quick schema bootstrap.
    """
    Base.metadata.create_all(bind=engine)


# ---------------------------------------------------------------------------
# FastAPI dependency
# ---------------------------------------------------------------------------

def get_db():
    """Yield a database session and guarantee it is closed after the request.

    Usage in a router:
        @router.get("/transactions")
        def list_transactions(db: Session = Depends(get_db)):
            return db.query(Transaction).all()
    """
    db: Session = SessionLocal()
    try:
        yield db
        db.commit()       # auto-commit if the request completes without error
    except Exception:
        db.rollback()     # roll back on any unhandled exception
        raise
    finally:
        db.close()        # always release the connection back to the pool