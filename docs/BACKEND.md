# Backend Documentation

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
