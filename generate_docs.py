import os

docs_dir = "docs"

files = {
    "PROJECT_OVERVIEW.md": """# Project Overview

## Purpose
The Student Alerting System aims to identify students at risk of academic failure or dropout and expose these predictions to faculty members. 

## Current Scope
The project currently consists of a Python FastAPI backend and a frozen scikit-learn machine learning pipeline. It is capable of receiving academic records, evaluating them through the ML model, and persisting a risk score.

## What it is NOT (yet)
It is not a complete alerting system. Active notifications (emails, SMS) and a frontend UI are currently missing.
""",
    "PROJECT_STATUS.md": """# Central Project Status & Record

**Date:** 2026-10-08

## Current Development Stage
Prototype / Integration Phase

## Overall Completion
45%

## Confidence
95% (Verified via code inspection and test execution)

## Status Breakdown
* **Backend:** 85% - API foundation is robust, typed, and tested.
* **ML:** 90% - Model is trained, tuned, calibrated, and frozen securely.
* **Alerting System:** 10% - Risk scores are saved, but active notifications are entirely missing.
* **Database:** 90% - PostgreSQL schema and relationships are correct. Missing Alembic migrations.
* **Testing:** 60% - 9 integration tests pass, but edge cases are untested.
* **Security:** 70% - RBAC and JWT are solid. `.env` secret management is poor.
* **Deployment:** 10% - Highly coupled to the local virtual environment. No Dockerfile or `pyproject.toml`.
* **Frontend:** 0% - Missing.

## Next Milestone
* Clean up the virtual environment from the project root.
* Establish `pyproject.toml` for dependency management.
* Initialize Git repository.
""",
    "ARCHITECTURE.md": """# System Architecture

## Current Architecture
The system uses a monolithic API architecture separating routing, business logic, and data access.

```text
HTTP Request (Client - MISSING)
       ↓
FastAPI Routes (app/routes/)
       ↓
Auth / RBAC Dependency Injection (app/core/auth.py)
       ↓
Services (app/services/)  <───> ML Service (app/services/ml_service.py) -> Loads .joblib
       ↓
SQLAlchemy ORM (app/models/)
       ↓
PostgreSQL Database
```

## Architectural Feedback
* **Good:** Dependency injection is used perfectly for DB sessions and user auth.
* **Good:** The ML model is loaded globally at startup to prevent blocking HTTP requests.
* **Bad:** Background tasks are missing. The alerting logic (when built) should not block the HTTP thread.
""",
    "BACKEND.md": """# Backend Documentation

The backend is built with **FastAPI** and **SQLAlchemy**.

## Directory Structure
* `app/core/`: Configuration and Security (JWT).
* `app/db/`: Database connection pooling and session management.
* `app/models/`: SQLAlchemy ORM definitions.
* `app/schemas/`: Pydantic models for request/response validation.
* `app/routes/`: API endpoints grouped by domain.
* `app/services/`: Core business logic and ML integration.
* `tests/`: Pytest integration suite.

## Missing/Needed Improvements
* Pagination on list endpoints (`/api/faculty/students`).
* Alembic migrations.
* Rate limiting for auth endpoints.
""",
    "ML_SYSTEM.md": """# Machine Learning System

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
""",
    "STUDENT_ALERTING_SYSTEM.md": """# Student Alerting System

## How it works currently
1. Faculty creates an `AcademicRecord` for a student.
2. The `risk_service` extracts the features.
3. The `ml_service` generates a risk score (0.0 to 1.0).
4. If the score is >= 0.40, `risk_prediction` is 1 (At Risk).
5. The prediction is saved in the `ml_predictions` table.

## Crucial Gaps
This is a **risk prediction** system, not an **alerting** system. 
* No emails, SMS, or webhooks are fired when a student becomes "At Risk".
* Faculty must manually check the `/api/faculty/students-at-risk` endpoint to see updates.
* There is no workflow for acknowledging, resolving, or dismissing a false positive alert.
""",
    "API_DOCUMENTATION.md": """# API Documentation

## Auth
* `POST /api/auth/register` - Register a student.
* `POST /api/auth/login` - Authenticate and get JWT.
* `GET /api/auth/me` - Get current user profile.

## Students
* `GET /api/students` - List all students (Faculty/Admin).
* `GET /api/students/{id}` - Get specific student.
* `POST /api/students/{id}/academic-records` - Add a record and trigger ML prediction.

## Faculty
* `GET /api/faculty/students` - List monitored students.
* `GET /api/faculty/students-at-risk` - Filter students by risk prediction = 1.

*Note: FastAPI automatically generates OpenAPI docs at `/docs` when running.*
""",
    "DATABASE.md": """# Database Schema

**Engine:** PostgreSQL

## Tables
1. **users**: Auth credentials, role (STUDENT, FACULTY, ADMIN).
2. **students**: Student profile (First name, last name, program).
3. **faculty**: Faculty profile (Department, employee ID).
4. **academic_records**: A timestamped snapshot of a student's academic and behavioral metrics.
5. **ml_predictions**: Historical risk scores tied 1:1 with academic records.

## Weaknesses
* Using `Base.metadata.create_all` instead of Alembic.
* Risk levels/statuses are hardcoded strings instead of Enums.
""",
    "SETUP.md": """# Setup Instructions

*PENDING FIX: The project currently lacks standard dependency management.*

Once `pyproject.toml` is created, setup will be:
1. `uv sync` or `pip install -e .`
2. Configure `.env` with `DATABASE_URL` and `SECRET_KEY`.
3. `fastapi dev app/main.py`
""",
    "DEPLOYMENT.md": """# Deployment Guide

*Currently incomplete.*

Required before deployment:
1. Dockerfile to isolate the environment.
2. Separation of PostgreSQL from the application host.
3. Secret rotation (remove hardcoded secrets from `.env`).
""",
    "TESTING.md": """# Testing Strategy

**Framework:** Pytest

## Current Coverage
* `test_health.py`: Verifies DB and ML model loading.
* `test_system.py`: End-to-end integration tests for RBAC, JWT generation, and ML inference persistence.

## Run tests
`PYTHONPATH=. pytest backend/tests/`

## Needed Tests
* Unit tests for `risk_service` and `ml_service` mocking the database.
* Edge case testing (missing features, boundary scores).
""",
    "SECURITY.md": """# Security Review

## Strengths
* Strict RBAC is enforced on routes.
* Passwords hashed via `pwdlib` with anti-timing-attack dummy verification.
* Valid JWT required for all domain endpoints.
* ORM prevents SQL injection.

## Weaknesses (Action Required)
* **CRITICAL:** Secrets (`SECRET_KEY`, DB creds) are stored in an uncommitted `.env` file, but there is no `.env.example`.
* **MEDIUM:** Missing rate-limiting on login endpoints.
""",
    "TECHNICAL_DECISIONS.md": """# Technical Decisions Log

## 2026-10-08
* **Frozen ML Pipeline:** Chose to freeze the pipeline using `joblib` and load it at server startup to prevent blocking HTTP requests during inference.
* **Append-only Predictions:** Risk scores are calculated only when a new `AcademicRecord` is created, preserving history.
""",
    "KNOWN_ISSUES.md": """# Known Issues

1. **Missing Dependency Management:** Project root is a virtual environment.
2. **Missing Active Alerts:** No background workers for emails/SMS.
3. **No UI:** Frontend is entirely absent.
4. **No Git Repo:** The project is not under source control.
""",
    "CHANGELOG.md": """# Changelog

## [Unreleased]
### Added
* Comprehensive documentation structure (`docs/`).
* Project audit completed.
"""
}

for filename, content in files.items():
    filepath = os.path.join(docs_dir, filename)
    with open(filepath, "w", encoding="utf-8") as f:
        f.write(content)

print("Documentation generated successfully.")
