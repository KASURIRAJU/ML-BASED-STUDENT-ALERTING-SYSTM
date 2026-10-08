"""Backend and database health endpoints."""

import logging
from typing import Any

from fastapi import APIRouter, HTTPException, status

from app.db.database import check_database_connection
from app.services import ml_service

logger = logging.getLogger(__name__)
router = APIRouter(tags=["Health"])


@router.get("/api/health")
def health() -> dict[str, Any]:
    """Show API, database, and frozen model status without exposing secrets."""
    database_connected, _ = check_database_connection()
    model_loaded = bool(ml_service.get_model_status()["loaded"])
    return {
        "backend": "available",
        "status": "ok" if database_connected and model_loaded else "degraded",
        "database": "connected" if database_connected else "disconnected",
        "ml_model": "loaded" if model_loaded else "not_loaded",
    }


@router.get("/api/db/health")
def database_health() -> dict[str, str]:
    """Check PostgreSQL with SELECT 1; never report an unverified success."""
    connected, error = check_database_connection()
    if not connected:
        logger.warning("Database health endpoint reports unavailable: %s", error)
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=error or "PostgreSQL is unavailable.",
        )
    return {"status": "connected"}
