"""Student self-service queries constrained to the authenticated account."""

from fastapi import HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import AcademicRecord, Student


def get_profile_for_user(db: Session, user_id: int) -> Student:
    student = db.scalar(select(Student).where(Student.user_id == user_id))
    if student is None:
        raise HTTPException(status_code=404, detail="Student profile was not found.")
    return student


def get_academic_records_for_user(db: Session, user_id: int) -> list[AcademicRecord]:
    student = get_profile_for_user(db, user_id)
    query = (
        select(AcademicRecord)
        .where(AcademicRecord.student_id == student.id)
        .order_by(AcademicRecord.recorded_at, AcademicRecord.id)
    )
    return list(db.scalars(query).all())
