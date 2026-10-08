"""Insert small, synthetic, development-only records into a configured database."""

import os
from getpass import getpass

from sqlalchemy import select

from app.db.database import SessionLocal, initialize_database
from app.core.security import hash_password
from app.models import AcademicRecord, Faculty, Student, User, UserRole


def _demo_password(name: str) -> str:
    password = os.getenv(name, "")
    if not password:
        label = name.removeprefix("DEMO_").removesuffix("_PASSWORD").lower()
        password = getpass(f"Set synthetic {label} demo password (input hidden): ")
        confirmation = getpass("Confirm demo password (input hidden): ")
        if password != confirmation:
            raise RuntimeError("The demo password entries did not match.")
    if len(password) < 12:
        raise RuntimeError(f"{name} must be set to a synthetic password of at least 12 characters.")
    return password


def seed_development_data() -> None:
    """Create/update synthetic student, faculty, and admin accounts and related demo data."""
    if not initialize_database() or SessionLocal is None:
        raise RuntimeError("PostgreSQL must be configured and reachable before seeding.")

    with SessionLocal() as session, session.begin():
        student_user = session.scalar(
            select(User).where(User.email == "demo.student@example.test")
        )
        if student_user is None:
            student_user = User(
                email="demo.student@example.test",
                password_hash=hash_password(_demo_password("DEMO_STUDENT_PASSWORD")),
                role=UserRole.STUDENT,
            )
            session.add(student_user)
            session.flush()
        else:
            student_user.password_hash = hash_password(_demo_password("DEMO_STUDENT_PASSWORD"))

        # Keep one unused STUDENT account available to exercise POST /api/students.
        pending_student_user = session.scalar(
            select(User).where(User.email == "demo.student.new@example.test")
        )
        if pending_student_user is None:
            pending_student_user = User(
                email="demo.student.new@example.test",
                password_hash=hash_password(_demo_password("DEMO_STUDENT_PASSWORD")),
                role=UserRole.STUDENT,
            )
            session.add(pending_student_user)
            session.flush()
        else:
            pending_student_user.password_hash = hash_password(_demo_password("DEMO_STUDENT_PASSWORD"))

        faculty_user = session.scalar(
            select(User).where(User.email == "demo.faculty@example.test")
        )
        if faculty_user is None:
            faculty_user = User(
                email="demo.faculty@example.test",
                password_hash=hash_password(_demo_password("DEMO_FACULTY_PASSWORD")),
                role=UserRole.FACULTY,
            )
            session.add(faculty_user)
            session.flush()
        else:
            faculty_user.password_hash = hash_password(_demo_password("DEMO_FACULTY_PASSWORD"))

        admin_user = session.scalar(select(User).where(User.email == "demo.admin@example.test"))
        if admin_user is None:
            admin_user = User(
                email="demo.admin@example.test",
                password_hash=hash_password(_demo_password("DEMO_ADMIN_PASSWORD")),
                role=UserRole.ADMIN,
            )
            session.add(admin_user)
        else:
            admin_user.password_hash = hash_password(_demo_password("DEMO_ADMIN_PASSWORD"))

        student = session.scalar(select(Student).where(Student.user_id == student_user.id))
        if student is None:
            student = Student(
                user_id=student_user.id,
                student_identifier="DEMO-STU-001",
                first_name="Asha",
                last_name="Demo",
                current_semester=3,
                program="Demo Computer Science",
            )
            session.add(student)
            session.flush()

        faculty = session.scalar(select(Faculty).where(Faculty.user_id == faculty_user.id))
        if faculty is None:
            session.add(
                Faculty(
                    user_id=faculty_user.id,
                    employee_identifier="DEMO-FAC-001",
                    first_name="Ravi",
                    last_name="Demo",
                    department="Demo Computer Science",
                )
            )

        record_count = session.scalar(
            select(AcademicRecord.id).where(AcademicRecord.student_id == student.id).limit(1)
        )
        if record_count is None:
            demo_records = [
                {
                    "previous_sgpa": 3.2,
                    "attendance_numeric": 90.0,
                    "current_semester": 3,
                    "credits_completed": 45.0,
                    "daily_study_hours": 3.0,
                    "daily_study_sessions": 2,
                    "daily_social_media_hours": 2.0,
                    "daily_skill_development_hours": 1.0,
                    "teacher_consultancy": "No",
                    "meritorious_scholarship": "No",
                    "preferred_learning_mode": "Online",
                    "english_proficiency": "Intermediate",
                    "personal_computer": "Yes",
                    "smartphone_use": "Yes",
                    "co_curricular_activities": "No",
                },
                {
                    "previous_sgpa": 3.4,
                    "attendance_numeric": 94.0,
                    "current_semester": 3,
                    "credits_completed": 48.0,
                    "daily_study_hours": 3.5,
                    "daily_study_sessions": 2,
                    "daily_social_media_hours": 1.5,
                    "daily_skill_development_hours": 1.5,
                    "teacher_consultancy": "Yes",
                    "meritorious_scholarship": "Yes",
                    "preferred_learning_mode": "In-person",
                    "english_proficiency": "Good",
                    "personal_computer": "Yes",
                    "smartphone_use": "Yes",
                    "co_curricular_activities": "Yes",
                },
            ]
            session.add_all(
                AcademicRecord(student_id=student.id, **record) for record in demo_records
            )

    print(
        "Development demo data is ready (4 fake users, 1 student, 1 faculty, 2 records). "
        f"Use user_id={pending_student_user.id} to test POST /api/students."
    )


if __name__ == "__main__":
    seed_development_data()
