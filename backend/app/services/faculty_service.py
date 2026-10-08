"""Faculty monitoring queries with intentionally limited profile fields."""

from fastapi import HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import AcademicRecord, Faculty, Student
from app.schemas.faculty import FacultyProfileRead
from app.schemas.student import FacultyStudentSummary, StudentFacultyDetail
from app.services import risk_service


def get_profile_for_user(db: Session, user_id: int) -> Faculty:
    faculty = db.scalar(select(Faculty).where(Faculty.user_id == user_id))
    if faculty is None:
        raise HTTPException(status_code=404, detail="Faculty profile was not found.")
    return faculty


def _student_summary(db: Session, student: Student) -> FacultyStudentSummary:
    record = risk_service.latest_academic_record(db, student.id)
    prediction = risk_service.get_or_create_current_prediction(db, student.id)
    return FacultyStudentSummary(
        id=student.id,
        student_identifier=student.student_identifier,
        first_name=student.first_name,
        last_name=student.last_name,
        current_semester=student.current_semester,
        program=student.program,
        latest_record_at=record.recorded_at if record else None,
        risk=risk_service.to_risk_response(prediction, record),
    )


def list_students(db: Session) -> list[FacultyStudentSummary]:
    students = db.scalars(select(Student).order_by(Student.id)).all()
    summaries = [_student_summary(db, student) for student in students]
    db.commit()
    return summaries


def list_students_at_risk(db: Session) -> list[FacultyStudentSummary]:
    return [summary for summary in list_students(db) if summary.risk and summary.risk.risk_prediction == 1]


def get_student_detail(db: Session, student_id: int) -> StudentFacultyDetail:
    student = db.get(Student, student_id)
    if student is None:
        raise HTTPException(status_code=404, detail="Student was not found.")
    summary = _student_summary(db, student)
    records = list(
        db.scalars(
            select(AcademicRecord)
            .where(AcademicRecord.student_id == student.id)
            .order_by(AcademicRecord.recorded_at, AcademicRecord.id)
        ).all()
    )
    db.commit()
    return StudentFacultyDetail(student=summary, academic_records=records, risk=summary.risk)
