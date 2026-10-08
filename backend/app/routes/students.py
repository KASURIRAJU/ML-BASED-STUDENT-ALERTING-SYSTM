"""Student and academic record endpoints for the database foundation."""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.core.auth import get_current_user, require_admin, require_faculty_or_admin
from app.models import AcademicRecord, Student, User, UserRole
from app.schemas.academic_record import AcademicRecordCreate, AcademicRecordRead
from app.schemas.student import StudentCreate, StudentRead
from app.services import academic_record_service

router = APIRouter(prefix="/api/students", tags=["Students"])


@router.get("", response_model=list[StudentRead])
def list_students(
    db: Session = Depends(get_db),
    _user: User = Depends(require_faculty_or_admin),
) -> list[Student]:
    return list(db.scalars(select(Student).order_by(Student.id)).all())


@router.post("", response_model=StudentRead, status_code=status.HTTP_201_CREATED)
def create_student(
    payload: StudentCreate,
    db: Session = Depends(get_db),
    _admin: User = Depends(require_admin),
) -> Student:
    user = db.get(User, payload.user_id)
    if user is None:
        raise HTTPException(status_code=404, detail="User account was not found.")
    if user.role != UserRole.STUDENT:
        raise HTTPException(status_code=409, detail="The user account is not assigned the STUDENT role.")
    if user.student is not None:
        raise HTTPException(status_code=409, detail="A student profile already exists for this user.")

    student = Student(**payload.model_dump())
    db.add(student)
    try:
        db.commit()
    except IntegrityError as exc:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Student identifier or user account is already assigned.",
        ) from exc
    db.refresh(student)
    return student


@router.get("/{student_id}", response_model=StudentRead)
def get_student(
    student_id: int,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> Student:
    student = db.scalar(select(Student).where(Student.id == student_id))
    if student is None:
        raise HTTPException(status_code=404, detail="Student was not found.")
    if user.role == UserRole.STUDENT and student.user_id != user.id:
        raise HTTPException(status_code=404, detail="Student was not found.")
    return student


@router.get("/{student_id}/academic-records", response_model=list[AcademicRecordRead])
def list_academic_records(
    student_id: int,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> list[AcademicRecord]:
    student = db.get(Student, student_id)
    if student is None or (user.role == UserRole.STUDENT and student.user_id != user.id):
        raise HTTPException(status_code=404, detail="Student was not found.")
    return academic_record_service.list_for_student(db, student_id)


@router.post(
    "/{student_id}/academic-records",
    response_model=AcademicRecordRead,
    status_code=status.HTTP_201_CREATED,
)
def create_academic_record(
    student_id: int,
    payload: AcademicRecordCreate,
    db: Session = Depends(get_db),
    _user: User = Depends(require_faculty_or_admin),
) -> AcademicRecord:
    return academic_record_service.create_for_student(db, student_id, payload.model_dump())
