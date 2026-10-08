"""Alert management service for active notifications and workflow."""

import logging
from typing import Any

from sqlalchemy.orm import Session
from sqlalchemy import select

from app.models import Alert, AlertStatus, MLPrediction, Student, Faculty

logger = logging.getLogger(__name__)


def process_prediction_for_alerts(db: Session, prediction: MLPrediction) -> Alert | None:
    """Check a new prediction and generate an alert if the student is at risk."""
    if prediction.risk_prediction != 1:
        return None  # Not at risk

    # Check if there is already an OPEN alert for this student to avoid spamming
    existing_open = db.scalar(
        select(Alert)
        .where(Alert.student_id == prediction.student_id)
        .where(Alert.status == AlertStatus.OPEN)
    )
    if existing_open:
        # Link the new prediction if we want, but usually we just keep the alert open.
        # For simplicity, we just won't create a new alert if one is already open.
        logger.info(f"Student {prediction.student_id} already has an OPEN alert. Skipping new alert.")
        return existing_open

    alert = Alert(
        student_id=prediction.student_id,
        prediction_id=prediction.id,
        status=AlertStatus.OPEN,
        severity=prediction.risk_level,
    )
    db.add(alert)
    db.flush()  # To get alert.id without committing
    
    logger.info(f"Generated new {alert.severity} alert {alert.id} for student {prediction.student_id}")
    return alert


def notify_faculty_background(alert_id: int, student_name: str, risk_level: str) -> None:
    """
    Simulates sending an email/SMS to assigned faculty.
    In a real system, this runs in Celery or FastAPI BackgroundTasks.
    """
    # This is a simulation of the active alerting missing from the prototype.
    logger.info(f"[EMAIL SIMULATION] Sending HIGH PRIORITY email for Alert #{alert_id}")
    logger.info(f"[EMAIL SIMULATION] Subject: ACTION REQUIRED - Student {student_name} is at {risk_level} risk.")
    logger.info(f"[EMAIL SIMULATION] Body: Please log in to the faculty dashboard to review and intervene.")
