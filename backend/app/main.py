"""FastAPI application entry point."""

from contextlib import asynccontextmanager
from typing import Any

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, ConfigDict, Field

from app.core.config import validate_auth_config
from app.db.database import close_database, initialize_database
from app.routes.health import router as health_router
from app.routes.auth import router as auth_router
from app.routes.admin import router as admin_router
from app.routes.student import router as student_dashboard_router
from app.routes.faculty import router as faculty_dashboard_router
from app.routes.students import router as students_router
from app.services import ml_service


class StudentRiskFeatures(BaseModel):
    """The exact features and names recorded in the frozen model metadata."""

    model_config = ConfigDict(populate_by_name=True, extra="forbid")

    previous_sgpa: float = Field(alias="What was your previous SGPA?")
    attendance_numeric: float
    current_semester: int = Field(alias="Current Semester")
    credits_completed: float = Field(alias="How many Credit did you have completed?")
    daily_study_hours: float = Field(alias="How many hour do you study daily?")
    daily_study_sessions: int = Field(alias="How many times do you seat for study in a day?")
    daily_social_media_hours: float = Field(alias="How many hour do you spent daily in social media?")
    daily_skill_development_hours: float = Field(alias="How many hour do you spent daily on your skill development?")
    teacher_consultancy: str = Field(
        alias="Do you attend in teacher consultancy for any kind of academical problems?"
    )
    meritorious_scholarship: str = Field(alias="Do you have meritorious scholarship ?")
    preferred_learning_mode: str = Field(alias="What is your preferable learning mode?")
    english_proficiency: str = Field(alias="Status of your English language proficiency")
    personal_computer: str = Field(alias="Do you have personal Computer?")
    smartphone_use: str = Field(alias="Do you use smart phone?")
    co_curricular_activities: str = Field(alias="Are you engaged with any co-curriculum activities?")


class PredictionResponse(BaseModel):
    risk_prediction: int = Field(description="0 = Not At Risk; 1 = At Risk")
    risk_status: str
    risk_level: str
    risk_score: float = Field(description="Uncalibrated model score for the At Risk class, not a probability of failure")
    decision_threshold: float


@asynccontextmanager
async def lifespan(application: FastAPI):
    """Initialize the database safely and load the frozen model once."""
    try:
        validate_auth_config()
        initialize_database()
        # The service records failures so status routes stay available if loading fails.
        ml_service.initialize_model()
        yield
    finally:
        close_database()


app = FastAPI(
    title="Student Alerting System API",
    description="Student and academic APIs with JWT authentication, role-based access, and frozen-model inference.",
    version="0.1.0",
    lifespan=lifespan,
)
app.include_router(health_router)
app.include_router(auth_router)
app.include_router(admin_router)
app.include_router(students_router)
app.include_router(student_dashboard_router)
app.include_router(faculty_dashboard_router)


@app.get("/api/ml/model-status", tags=["Machine learning"])
def model_status() -> dict[str, Any]:
    """Report whether the real frozen model is ready for predictions."""
    return ml_service.get_model_status()


@app.post(
    "/api/ml/predict-risk",
    response_model=PredictionResponse,
    tags=["Machine learning"],
)
def predict_risk(payload: StudentRiskFeatures) -> PredictionResponse:
    """Score one student record using the saved pipeline."""
    try:
        result = ml_service.predict_risk(payload.model_dump(by_alias=True))
    except ml_service.ModelNotReadyError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc
    except Exception as exc:
        ml_service.log_prediction_failure()
        raise HTTPException(
            status_code=500,
            detail="The model could not process this prediction. Check the submitted values and server logs.",
        ) from exc
    return PredictionResponse(**result)
