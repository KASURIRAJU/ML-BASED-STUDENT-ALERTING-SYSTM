"""A dated snapshot of the application fields used by the risk model."""

from datetime import datetime

from sqlalchemy import DateTime, Float, ForeignKey, Integer, String, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class AcademicRecord(Base):
    __tablename__ = "academic_records"

    id: Mapped[int] = mapped_column(primary_key=True)
    student_id: Mapped[int] = mapped_column(
        ForeignKey("students.id", ondelete="CASCADE"), index=True, nullable=False
    )
    recorded_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    previous_sgpa: Mapped[float] = mapped_column(Float, nullable=False)
    attendance_numeric: Mapped[float] = mapped_column(Float, nullable=False)
    current_semester: Mapped[int] = mapped_column(Integer, nullable=False)
    credits_completed: Mapped[float] = mapped_column(Float, nullable=False)
    daily_study_hours: Mapped[float] = mapped_column(Float, nullable=False)
    daily_study_sessions: Mapped[int] = mapped_column(Integer, nullable=False)
    daily_social_media_hours: Mapped[float] = mapped_column(Float, nullable=False)
    daily_skill_development_hours: Mapped[float] = mapped_column(Float, nullable=False)
    teacher_consultancy: Mapped[str] = mapped_column(String(100), nullable=False)
    meritorious_scholarship: Mapped[str] = mapped_column(String(100), nullable=False)
    preferred_learning_mode: Mapped[str] = mapped_column(String(100), nullable=False)
    english_proficiency: Mapped[str] = mapped_column(String(100), nullable=False)
    personal_computer: Mapped[str] = mapped_column(String(100), nullable=False)
    smartphone_use: Mapped[str] = mapped_column(String(100), nullable=False)
    co_curricular_activities: Mapped[str] = mapped_column(String(100), nullable=False)

    student: Mapped["Student"] = relationship(back_populates="academic_records")
