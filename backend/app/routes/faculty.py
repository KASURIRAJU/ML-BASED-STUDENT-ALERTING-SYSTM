"""Authenticated faculty dashboard and monitoring endpoints."""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.auth import require_faculty_or_admin
from app.db.database import get_db
from app.models import User
from app.schemas.faculty import FacultyProfileRead
from app.schemas.student import FacultyStudentSummary, StudentFacultyDetail
from app.services import faculty_service, ml_service

router = APIRouter(prefix="/api/faculty", tags=["Faculty dashboard"])


@router.get("/me", response_model=FacultyProfileRead)
def get_my_faculty_profile(
    user: User = Depends(require_faculty_or_admin), db: Session = Depends(get_db)
) -> FacultyProfileRead:
    faculty = faculty_service.get_profile_for_user(db, user.id)
    return FacultyProfileRead.model_validate(faculty)


@router.get("/students", response_model=list[FacultyStudentSummary])
def list_monitored_students(
    _user: User = Depends(require_faculty_or_admin), db: Session = Depends(get_db)
) -> list[FacultyStudentSummary]:
    try:
        return faculty_service.list_students(db)
    except ml_service.ModelNotReadyError as exc:
        db.rollback()
        raise HTTPException(status_code=503, detail="Risk assessment is temporarily unavailable.") from exc


@router.get("/students-at-risk", response_model=list[FacultyStudentSummary])
def list_students_at_risk(
    _user: User = Depends(require_faculty_or_admin), db: Session = Depends(get_db)
) -> list[FacultyStudentSummary]:
    try:
        return faculty_service.list_students_at_risk(db)
    except ml_service.ModelNotReadyError as exc:
        db.rollback()
        raise HTTPException(status_code=503, detail="Risk assessment is temporarily unavailable.") from exc


@router.get("/students/{student_id}", response_model=StudentFacultyDetail)
def get_monitored_student(
    student_id: int,
    _user: User = Depends(require_faculty_or_admin),
    db: Session = Depends(get_db),
) -> StudentFacultyDetail:
    try:
        return faculty_service.get_student_detail(db, student_id)
    except ml_service.ModelNotReadyError as exc:
        db.rollback()
        raise HTTPException(status_code=503, detail="Risk assessment is temporarily unavailable.") from exc
