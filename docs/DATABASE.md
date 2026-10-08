# Database Schema

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
