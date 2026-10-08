"""Risk service for managing ML prediction history and integration."""

import logging
from fastapi import HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import AcademicRecord, MLPrediction, Student
from app.schemas.student import RiskAssessmentRead
from app.services import ml_service

logger = logging.getLogger(__name__)


def latest_academic_record(db: Session, student_id: int) -> AcademicRecord | None:
    query = (
        select(AcademicRecord)
        .where(AcademicRecord.student_id == student_id)
        .order_by(AcademicRecord.recorded_at.desc(), AcademicRecord.id.desc())
    )
    return db.scalars(query).first()


def get_latest_prediction(db: Session, student_id: int) -> MLPrediction | None:
    """Return the most recent prediction for a student."""
    query = (
        select(MLPrediction)
        .where(MLPrediction.student_id == student_id)
        .order_by(MLPrediction.predicted_at.desc(), MLPrediction.id.desc())
    )
    return db.scalars(query).first()


def get_or_create_current_prediction(db: Session, student_id: int, create: bool = False) -> MLPrediction | None:
    latest_record = latest_academic_record(db, student_id)
    if not latest_record:
        return None

    latest_pred = get_latest_prediction(db, student_id)
    if latest_pred and latest_pred.predicted_at >= latest_record.recorded_at:
        return latest_pred

    if not create:
        return latest_pred

    features = {
        "What was your previous SGPA?": latest_record.previous_sgpa,
        "attendance_numeric": latest_record.attendance_numeric,
        "Current Semester": latest_record.current_semester,
        "How many Credit did you have completed?": latest_record.credits_completed,
        "How many hour do you study daily?": latest_record.daily_study_hours,
        "How many times do you seat for study in a day?": latest_record.daily_study_sessions,
        "How many hour do you spent daily in social media?": latest_record.daily_social_media_hours,
        "How many hour do you spent daily on your skill development?": latest_record.daily_skill_development_hours,
        "Do you attend in teacher consultancy for any kind of academical problems?": latest_record.teacher_consultancy,
        "Do you have meritorious scholarship ?": latest_record.meritorious_scholarship,
        "What is your preferable learning mode?": latest_record.preferred_learning_mode,
        "Status of your English language proficiency": latest_record.english_proficiency,
        "Do you have personal Computer?": latest_record.personal_computer,
        "Do you use smart phone?": latest_record.smartphone_use,
        "Are you engaged with any co-curriculum activities?": latest_record.co_curricular_activities,
    }

    try:
        prediction_result = ml_service.predict_risk(features)
        model_version = ml_service.get_model_version()
    except ml_service.ModelNotReadyError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc
    except Exception as exc:
        ml_service.log_prediction_failure()
        raise HTTPException(status_code=500, detail="Prediction failed") from exc

    prediction = MLPrediction(
        student_id=student_id,
        risk_score=prediction_result["risk_score"],
        risk_prediction=prediction_result["risk_prediction"],
        risk_status=prediction_result["risk_status"],
        risk_level=prediction_result["risk_level"],
        decision_threshold=prediction_result["decision_threshold"],
        model_version=model_version,
    )

    db.add(prediction)
    return prediction

def to_risk_response(prediction: MLPrediction | None, record: AcademicRecord | None) -> RiskAssessmentRead | None:
    if not prediction or not record:
        return None
    return RiskAssessmentRead(
        risk_prediction=prediction.risk_prediction,
        risk_status=prediction.risk_status,
        risk_level=prediction.risk_level,
        risk_score=prediction.risk_score,
        decision_threshold=prediction.decision_threshold,
        model_version=prediction.model_version,
        predicted_at=prediction.predicted_at,
        source_record_at=record.recorded_at
    )
