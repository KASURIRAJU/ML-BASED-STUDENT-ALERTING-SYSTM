"""Academic history queries and deliberate prediction events on record creation."""

import logging

from fastapi import HTTPException, BackgroundTasks
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import AcademicRecord, Student
from app.services import ml_service, risk_service

logger = logging.getLogger(__name__)


def list_for_student(db: Session, student_id: int) -> list[AcademicRecord]:
    if db.get(Student, student_id) is None:
        raise HTTPException(status_code=404, detail="Student was not found.")
    query = select(AcademicRecord).where(AcademicRecord.student_id == student_id).order_by(
        AcademicRecord.recorded_at, AcademicRecord.id
    )
    return list(db.scalars(query).all())


def create_for_student(db: Session, student_id: int, values: dict, background_tasks: BackgroundTasks) -> AcademicRecord:
    if db.get(Student, student_id) is None:
        raise HTTPException(status_code=404, detail="Student was not found.")

    record = AcademicRecord(student_id=student_id, **values)
    db.add(record)
    db.commit()
    db.refresh(record)

    # A successful record submission is an explicit assessment event. The source
    # record is durable even if model inference is temporarily unavailable.
    try:
        risk_service.get_or_create_current_prediction(db, student_id, create=True, background_tasks=background_tasks)
        db.commit()
    except Exception:
        db.rollback()
        logger.exception("Could not create the risk assessment for academic record %s", record.id)
        if not ml_service.get_model_status()["loaded"]:
            return record
        raise
    return record
