"""Database model for active and historical alerts."""

from datetime import datetime
from enum import Enum

from sqlalchemy import DateTime, Enum as SqlEnum, ForeignKey, String, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class AlertStatus(str, Enum):
    OPEN = "OPEN"
    ACKNOWLEDGED = "ACKNOWLEDGED"
    RESOLVED = "RESOLVED"
    FALSE_POSITIVE = "FALSE_POSITIVE"


class Alert(Base):
    __tablename__ = "alerts"

    id: Mapped[int] = mapped_column(primary_key=True)
    student_id: Mapped[int] = mapped_column(
        ForeignKey("students.id", ondelete="CASCADE"), index=True, nullable=False
    )
    prediction_id: Mapped[int] = mapped_column(
        ForeignKey("ml_predictions.id", ondelete="CASCADE"), unique=True, nullable=False
    )
    status: Mapped[AlertStatus] = mapped_column(
        SqlEnum(
            AlertStatus,
            native_enum=False,
            create_constraint=True,
            name="alert_status",
            validate_strings=True,
        ),
        default=AlertStatus.OPEN,
        nullable=False,
    )
    severity: Mapped[str] = mapped_column(String(20), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    student: Mapped["Student"] = relationship(back_populates="alerts")
    prediction: Mapped["MLPrediction"] = relationship(back_populates="alert")
