# Student Alerting System

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
