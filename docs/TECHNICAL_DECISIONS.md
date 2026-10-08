# Technical Decisions Log

## 2026-10-08
* **Frozen ML Pipeline:** Chose to freeze the pipeline using `joblib` and load it at server startup to prevent blocking HTTP requests during inference.
* **Append-only Predictions:** Risk scores are calculated only when a new `AcademicRecord` is created, preserving history.
