# API Documentation

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
