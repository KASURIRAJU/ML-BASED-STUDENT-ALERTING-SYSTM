"""Historical ML predictions, separate from source academic records."""

from datetime import datetime

from sqlalchemy import DateTime, Float, ForeignKey, Integer, String, func
import sqlalchemy as sa
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class MLPrediction(Base):
    __tablename__ = "ml_predictions"

    id: Mapped[int] = mapped_column(primary_key=True)
    student_id: Mapped[int] = mapped_column(
        ForeignKey("students.id", ondelete="CASCADE"), index=True, nullable=False
    )
    risk_score: Mapped[float] = mapped_column(Float, nullable=False)
    risk_prediction: Mapped[int] = mapped_column(Integer, nullable=False)
    risk_status: Mapped[str] = mapped_column(String(40), nullable=False)
    risk_level: Mapped[str] = mapped_column(String(20), nullable=False)
    decision_threshold: Mapped[float] = mapped_column(Float, nullable=False)
    model_version: Mapped[str] = mapped_column(String(40), nullable=False)
    explanation: Mapped[dict | None] = mapped_column(type_=sa.JSON, nullable=True)
    predicted_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    student: Mapped["Student"] = relationship(back_populates="predictions")
    alert: Mapped["Alert | None"] = relationship(back_populates="prediction", uselist=False)
