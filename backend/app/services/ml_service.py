"""Load and call the frozen student risk pipeline; this module never trains."""

import json
import logging
from pathlib import Path
from typing import Any

import joblib
import pandas as pd

logger = logging.getLogger(__name__)

# Resolve from this file, so the terminal's current directory does not matter.
PROJECT_ROOT = Path(__file__).resolve().parents[3]
MODEL_PATH = PROJECT_ROOT / "ml" / "artifacts" / "student_risk_pipeline_FINAL.joblib"
METADATA_PATH = PROJECT_ROOT / "ml" / "artifacts" / "student_risk_model_metadata_FINAL.json"

_model: Any | None = None
_metadata: dict[str, Any] | None = None
_load_error: str | None = None
_load_attempted = False


class ModelNotReadyError(RuntimeError):
    """Raised when prediction is requested before the model is available."""


def initialize_model() -> None:
    """Load the pipeline and its metadata once during application startup."""
    global _model, _metadata, _load_error, _load_attempted
    if _load_attempted:
        return

    _load_attempted = True
    try:
        if not MODEL_PATH.is_file():
            raise FileNotFoundError(f"Trained model artifact not found: {MODEL_PATH}")
        if not METADATA_PATH.is_file():
            raise FileNotFoundError(f"Model metadata not found: {METADATA_PATH}")

        with METADATA_PATH.open(encoding="utf-8") as metadata_file:
            metadata = json.load(metadata_file)
        if not metadata.get("features") or not isinstance(metadata.get("features"), list):
            raise ValueError("Model metadata must contain a non-empty features list")

        _model = joblib.load(MODEL_PATH)
        _metadata = metadata
        _load_error = None
        logger.info("Loaded frozen ML pipeline from %s", MODEL_PATH)
    except Exception as exc:
        _model = None
        _metadata = None
        _load_error = f"{type(exc).__name__}: {exc}"
        logger.exception("Could not load frozen ML pipeline from %s", MODEL_PATH)


def get_model_status() -> dict[str, Any]:
    """Return readiness details without exposing a stack trace."""
    return {
        "loaded": _model is not None,
        "model_path": str(MODEL_PATH),
        "model_type": _classifier_type() if _model is not None else None,
        "error": _load_error,
    }


def get_model_version() -> str:
    """Return the version declared alongside the loaded frozen model artifact."""
    if not _load_attempted:
        initialize_model()
    if _metadata is None:
        raise ModelNotReadyError("The trained model is unavailable.")
    return str(_metadata.get("model_version", "unknown"))


def _classifier_type() -> str:
    classifier = _model.named_steps.get("classifier") if hasattr(_model, "named_steps") else _model
    return type(classifier).__name__


def predict_risk(features: dict[str, Any]) -> dict[str, Any]:
    """Return the model's uncalibrated At Risk score and thresholded label."""
    if not _load_attempted:
        initialize_model()
    if _model is None or _metadata is None:
        raise ModelNotReadyError("The trained model is unavailable. Check /api/ml/model-status and server logs.")

    expected_features = _metadata["features"]
    missing = [name for name in expected_features if name not in features]
    extra = [name for name in features if name not in expected_features]
    if missing or extra:
        details = []
        if missing:
            details.append(f"missing model features: {missing}")
        if extra:
            details.append(f"unexpected features: {extra}")
        raise ValueError("Invalid feature record (" + "; ".join(details) + ")")

    row = pd.DataFrame([{name: features[name] for name in expected_features}], columns=expected_features)
    classifier = _model
    if not hasattr(classifier, "predict_proba"):
        raise RuntimeError("The loaded pipeline does not support predict_proba")

    probabilities = classifier.predict_proba(row)[0]
    classes = list(classifier.classes_)
    try:
        at_risk_index = classes.index(1)
    except ValueError as exc:
        raise RuntimeError("The loaded pipeline does not contain the expected At Risk class (1)") from exc

    score = float(probabilities[at_risk_index])
    threshold = float(_metadata["decision_threshold"])
    prediction = int(score >= threshold)
    # These LOW/MEDIUM/HIGH bands match the prototype notebook. The score is
    # uncalibrated, so it is an internal model score rather than failure odds.
    level = "HIGH" if score >= 0.70 else "MEDIUM" if score >= 0.35 else "LOW"
    return {
        "risk_prediction": prediction,
        "risk_status": "At Risk" if prediction else "Not At Risk",
        "risk_level": level,
        "risk_score": score,
        "decision_threshold": threshold,
    }


def log_prediction_failure() -> None:
    """Log inference details for developers while keeping responses concise."""
    logger.exception("Prediction failed while calling the frozen ML pipeline")
