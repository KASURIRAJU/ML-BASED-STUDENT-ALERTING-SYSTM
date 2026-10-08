"""Authenticated student dashboard endpoints."""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.auth import require_student
from app.db.database import get_db
from app.models import User
from app.schemas.academic_record import AcademicRecordRead
from app.schemas.student import RiskAssessmentRead, StudentProfileRead
from app.services import academic_record_service, risk_service, student_service, ml_service

router = APIRouter(prefix="/api/student", tags=["Student dashboard"])


@router.get("/me", response_model=StudentProfileRead)
def get_my_profile(
    user: User = Depends(require_student), db: Session = Depends(get_db)
) -> StudentProfileRead:
    return StudentProfileRead.model_validate(student_service.get_profile_for_user(db, user.id))


@router.get("/me/academic-records", response_model=list[AcademicRecordRead])
def get_my_academic_records(
    user: User = Depends(require_student), db: Session = Depends(get_db)
) -> list[AcademicRecordRead]:
    records = student_service.get_academic_records_for_user(db, user.id)
    return [AcademicRecordRead.model_validate(record) for record in records]


@router.get("/me/risk", response_model=RiskAssessmentRead)
def get_my_risk(
    user: User = Depends(require_student), db: Session = Depends(get_db)
) -> RiskAssessmentRead:
    student = student_service.get_profile_for_user(db, user.id)
    try:
        prediction = risk_service.get_or_create_current_prediction(db, student.id)
        db.commit()
    except ml_service.ModelNotReadyError as exc:
        db.rollback()
        raise HTTPException(status_code=503, detail="Risk assessment is temporarily unavailable.") from exc
    if prediction is None:
        raise HTTPException(status_code=404, detail="No academic record is available for risk assessment.")
    record = risk_service.latest_academic_record(db, student.id)
    return risk_service.to_risk_response(prediction, record)
