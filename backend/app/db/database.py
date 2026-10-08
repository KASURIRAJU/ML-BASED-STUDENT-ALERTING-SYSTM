"""PostgreSQL engine, session dependency, and safe table initialization."""

import logging
from collections.abc import Generator

from fastapi import HTTPException, status
from sqlalchemy import create_engine, text
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.engine import Engine
from sqlalchemy.orm import Session, sessionmaker

from app.core.config import DATABASE_CONFIG_ERROR, DATABASE_URL
from app.db.base import Base

logger = logging.getLogger(__name__)

engine: Engine | None = None
SessionLocal: sessionmaker[Session] | None = None
_engine_error: str | None = DATABASE_CONFIG_ERROR

if DATABASE_URL:
    try:
        engine = create_engine(
            DATABASE_URL,
            pool_pre_ping=True,
            connect_args={"connect_timeout": 3},
        )
        SessionLocal = sessionmaker(
            bind=engine,
            class_=Session,
            autoflush=False,
            expire_on_commit=False,
        )
        _engine_error = None
    except Exception as exc:
        _engine_error = f"Could not configure the PostgreSQL engine ({type(exc).__name__})."
        logger.exception("Could not configure the database engine")


def check_database_connection() -> tuple[bool, str | None]:
    """Check a real PostgreSQL connection without returning credentials."""
    if engine is None:
        return False, _engine_error or "Database engine is not configured."
    try:
        with engine.connect() as connection:
            connection.execute(text("SELECT 1"))
        return True, None
    except SQLAlchemyError:
        logger.exception("PostgreSQL health check failed")
        return False, "PostgreSQL is unavailable. Check that it is running and DATABASE_URL is correct."


def initialize_database() -> bool:
    """Create missing tables without dropping or replacing existing tables."""
    connected, error = check_database_connection()
    if not connected:
        logger.warning("Database initialization skipped: %s", error)
        return False

    try:
        # Database tables are now managed by Alembic migrations.
        # Ensure 'uv run alembic upgrade head' is executed instead of create_all().
        logger.info("Database connection verified. Alembic migrations should be run to ensure tables exist.")
        return True
    except SQLAlchemyError:
        logger.exception("Could not initialize database tables")
        return False


def close_database() -> None:
    """Release pooled connections when the FastAPI process shuts down."""
    if engine is not None:
        engine.dispose()


def get_db() -> Generator[Session, None, None]:
    """Provide one database session per request and always close it."""
    if SessionLocal is None:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=_engine_error or "Database is not configured.",
        )

    session = SessionLocal()
    try:
        yield session
    except SQLAlchemyError as exc:
        session.rollback()
        logger.exception("Database request failed")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Database operation failed. Check PostgreSQL availability and server logs.",
        ) from exc
    finally:
        session.close()
