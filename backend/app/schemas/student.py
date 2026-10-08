"""Public student API schemas; credential fields are never serialized."""

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

from app.schemas.academic_record import AcademicRecordRead


class StudentProfileRead(BaseModel):
    """Safe student-facing profile fields, without account identifiers or credentials."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    student_identifier: str
    first_name: str
    last_name: str
    current_semester: int
    program: str
    created_at: datetime


class FacultyStudentSummary(BaseModel):
    """Minimum student profile information used by academic monitoring."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    student_identifier: str
    first_name: str
    last_name: str
    current_semester: int
    program: str
    latest_record_at: datetime | None = None
    risk: "RiskAssessmentRead | None" = None


class RiskAssessmentRead(BaseModel):
    """Saved risk assessment; risk_score is uncalibrated, not a failure probability."""

    risk_status: str
    risk_level: str
    risk_prediction: int
    risk_score: float = Field(description="Uncalibrated model score; not a probability of failure")
    decision_threshold: float
    model_version: str
    predicted_at: datetime
    source_record_at: datetime


class StudentFacultyDetail(BaseModel):
    """Faculty view of a student's profile and academic history."""

    student: FacultyStudentSummary
    academic_records: list[AcademicRecordRead]
    risk: "RiskAssessmentRead | None" = None


class StudentCreate(BaseModel):
    user_id: int = Field(gt=0)
    student_identifier: str = Field(min_length=1, max_length=64)
    first_name: str = Field(min_length=1, max_length=100)
    last_name: str = Field(min_length=1, max_length=100)
    current_semester: int = Field(ge=1)
    program: str = Field(min_length=1, max_length=150)


class StudentRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    user_id: int
    student_identifier: str
    first_name: str
    last_name: str
    current_semester: int
    program: str
    created_at: datetime
    updated_at: datetime
