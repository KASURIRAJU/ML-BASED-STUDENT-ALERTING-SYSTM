# Machine Learning System

## Pipeline
The model is a `GradientBoostingClassifier` trained via scikit-learn.

* **Artifacts:** Stored in `ml/artifacts/`.
* **Features:** Relies on 15 academic and behavioral features (e.g., `previous_sgpa`, `attendance_numeric`, `daily_study_hours`).
* **Target:** Predicts academic risk (0 = Not At Risk, 1 = At Risk).
* **Threshold:** The decision threshold is mathematically calibrated to 0.40 to balance Recall and F1 score.

## Integration
The backend `ml_service.py` loads the frozen pipeline (`.joblib`) and a metadata JSON file on startup. 
It performs inference synchronously during `AcademicRecord` creation.

## Missing
* Data drift monitoring.
* Automated retraining loops.
* Model Explainability (SHAP values) to tell faculty *why* a student is at risk.
