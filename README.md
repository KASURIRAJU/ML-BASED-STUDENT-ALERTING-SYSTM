# Student Alerting System

A predictive risk alerting system that evaluates student academic records through a Machine Learning pipeline and actively alerts faculty to students at risk of failure.

**Current Stage:** Implementation & Hardening (Maturity 7/10)

## Features
- **Machine Learning Integration:** Uses a calibrated scikit-learn Gradient Boosting model.
- **Active Alert Workflow:** Manages alert lifecycles (OPEN, ACKNOWLEDGED, RESOLVED).
- **Role-Based Access Control:** Secure JWT authentication for Students, Faculty, and Admins.
- **Asynchronous Notifications:** Uses FastAPI BackgroundTasks for non-blocking email simulation.
- **Rate Limiting & Pagination:** `slowapi` protects authentication endpoints against brute force, and list endpoints are paginated.

## Technology Stack
- **Backend:** Python 3.12, FastAPI, SQLAlchemy, Pydantic, Uvicorn
- **Database:** PostgreSQL (with Alembic for migrations)
- **Machine Learning:** scikit-learn 1.6.1 (Pinned), pandas, joblib
- **Package Manager:** uv

*(Note: Model Explainability via SHAP is temporarily unavailable due to Windows AppLocker blocking `numba` compiled DLL extensions on this machine. The codebase has been cleanly reverted to exclude it without breaking the pipeline.)*

## Fresh Machine Setup Guide

### Prerequisites
1. **Python 3.12+**: `python --version`
2. **uv (Package Manager)**: `uv --version` (Install via `pip install uv` or official script)
3. **PostgreSQL**: Running locally on port `5432` with a database named `student_alerting`.

### 1. Clone & Configure
```bash
git clone <repository_url>
cd student_alerting_systems

# Setup environment variables
cp backend/.env.example backend/.env
# Edit backend/.env and ensure DATABASE_URL matches your local PostgreSQL instance
```

### 2. Install Dependencies
```bash
uv sync
```
*Note: We strictly pin `scikit-learn==1.6.1` to maintain compatibility with the frozen model artifact (`.joblib`). Do not upgrade it without retraining the model.*

### 3. Database Initialization
This project uses Alembic for safe schema migrations.
```bash
# Run migrations to create tables
uv run alembic upgrade head

# Seed the database with demo users (Optional)
$env:PYTHONPATH="backend"
$env:DEMO_STUDENT_PASSWORD="Password1234!"
$env:DEMO_FACULTY_PASSWORD="Password1234!"
$env:DEMO_ADMIN_PASSWORD="Password1234!"
uv run python backend/app/db/seed.py
```

### 4. Run the Backend
```bash
$env:PYTHONPATH="backend"
uv run uvicorn app.main:app --port 8000
```
API Documentation will be available at: `http://127.0.0.1:8000/docs`

### 5. Testing
```bash
$env:PYTHONPATH="backend"
uv run pytest backend/tests
```

## Architecture Workflow
1. **Input:** Faculty posts a student's `AcademicRecord`.
2. **Prediction:** `risk_service.py` evaluates the `joblib` model.
3. **Alert Creation:** `alert_service.py` prevents duplicates and creates an `OPEN` alert.
4. **Notification:** A background task simulates sending an email to the faculty.
5. **Resolution:** Faculty uses `/api/alerts` to ACKNOWLEDGE and RESOLVE the alert.
