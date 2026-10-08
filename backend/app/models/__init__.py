"""ORM models registered on the shared metadata."""

from app.models.academic_record import AcademicRecord
from app.models.faculty import Faculty
from app.models.prediction import MLPrediction
from app.models.student import Student
from app.models.user import User, UserRole

__all__ = ["AcademicRecord", "Faculty", "MLPrediction", "Student", "User", "UserRole"]
