"""Pydantic schemas for dated student academic input records."""

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class AcademicRecordCreate(BaseModel):
    previous_sgpa: float
    attendance_numeric: float
    current_semester: int = Field(ge=1)
    credits_completed: float
    daily_study_hours: float
    daily_study_sessions: int = Field(ge=0)
    daily_social_media_hours: float
    daily_skill_development_hours: float
    teacher_consultancy: str = Field(min_length=1, max_length=100)
    meritorious_scholarship: str = Field(min_length=1, max_length=100)
    preferred_learning_mode: str = Field(min_length=1, max_length=100)
    english_proficiency: str = Field(min_length=1, max_length=100)
    personal_computer: str = Field(min_length=1, max_length=100)
    smartphone_use: str = Field(min_length=1, max_length=100)
    co_curricular_activities: str = Field(min_length=1, max_length=100)


class AcademicRecordRead(AcademicRecordCreate):
    model_config = ConfigDict(from_attributes=True)

    id: int
    student_id: int
    recorded_at: datetime
