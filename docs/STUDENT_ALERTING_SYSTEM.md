# Student Alerting System

## How it works (Active Workflow)
1. Faculty creates an `AcademicRecord` for a student.
2. The `risk_service` extracts the features and synchronously evaluates the ML pipeline.
3. If the score is >= 0.40, the system triggers the `alert_service`.
4. The `alert_service` checks if the student already has an `OPEN` alert. If not, it creates a new `Alert` record in the database.
5. The `alert_service` dispatches a `BackgroundTask` (non-blocking) to notify faculty via email/SMS (currently simulated).

## Alert Lifecycle
Alerts have explicit state management:
* **OPEN:** A new risk prediction was generated. Faculty action required.
* **ACKNOWLEDGED:** Faculty has seen the alert and is investigating.
* **RESOLVED:** Faculty has intervened and closed the alert.
* **FALSE_POSITIVE:** Faculty dismissed the alert as incorrect.

## API Endpoints
* `GET /api/alerts?status_filter=OPEN` - List alerts.
* `PATCH /api/alerts/{id}/status` - Update an alert's state.
