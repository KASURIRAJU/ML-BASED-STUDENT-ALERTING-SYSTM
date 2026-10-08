"""Alert workflow endpoints for faculty."""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session
from pydantic import BaseModel, ConfigDict
from datetime import datetime

from app.db.database import get_db
from app.core.auth import require_faculty_or_admin
from app.models import Alert, AlertStatus, User

router = APIRouter(prefix="/api/alerts", tags=["Alerts"])

class AlertRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    student_id: int
    prediction_id: int
    status: AlertStatus
    severity: str
    created_at: datetime
    updated_at: datetime

class AlertStatusUpdate(BaseModel):
    status: AlertStatus

@router.get("", response_model=list[AlertRead])
def list_alerts(
    status_filter: AlertStatus | None = None,
    skip: int = 0,
    limit: int = 50,
    db: Session = Depends(get_db),
    _user: User = Depends(require_faculty_or_admin),
) -> list[Alert]:
    query = select(Alert).order_by(Alert.created_at.desc())
    if status_filter:
        query = query.where(Alert.status == status_filter)
    query = query.offset(skip).limit(limit)
    return list(db.scalars(query).all())

@router.patch("/{alert_id}/status", response_model=AlertRead)
def update_alert_status(
    alert_id: int,
    payload: AlertStatusUpdate,
    db: Session = Depends(get_db),
    _user: User = Depends(require_faculty_or_admin),
) -> Alert:
    alert = db.get(Alert, alert_id)
    if alert is None:
        raise HTTPException(status_code=404, detail="Alert not found.")
    
    alert.status = payload.status
    db.commit()
    db.refresh(alert)
    return alert
