# Testing Strategy

**Framework:** Pytest

## Current Coverage
* `test_health.py`: Verifies DB and ML model loading.
* `test_system.py`: End-to-end integration tests for RBAC, JWT generation, and ML inference persistence.

## Run tests
`PYTHONPATH=. pytest backend/tests/`

## Needed Tests
* Unit tests for `risk_service` and `ml_service` mocking the database.
* Edge case testing (missing features, boundary scores).
