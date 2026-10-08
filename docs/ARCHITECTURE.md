# System Architecture

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
