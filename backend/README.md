# Student Alerting System Backend

This FastAPI backend provides PostgreSQL persistence for users, student/faculty profiles, academic records, and prediction history, along with health and ML inference endpoints. The ML service loads the frozen pipeline at `ml/artifacts/student_risk_pipeline_FINAL.joblib`; it never trains, copies, or alters the model.

The model was serialized with scikit-learn 1.6.1. Use Python 3.12 and the pinned dependencies in `requirements.txt` to keep its loading environment compatible. Database packages are pinned separately and do not change the ML dependency versions.

## Python environment

The verified environment for this project is `backend/.venv` with Python 3.12.12. From the repository root, activate it and install the pinned requirements:

```powershell
backend/.venv/Scripts/Activate.ps1
uv pip install --python backend/.venv/Scripts/python.exe -r backend/requirements.txt
```

Both commands above were run successfully in this workspace. The venv excludes system packages. If recreating the environment on another Windows machine, install Python 3.12 first, then run `python -m venv backend/.venv` with that interpreter and install the requirements; verify `python --version` reports Python 3.12 before installing. The Python launcher command varies by machine.

## PostgreSQL setup

### Current workspace: project-local development cluster

This workspace uses an isolated PostgreSQL 18.6 cluster at `backend/.postgres-data`, bound to `127.0.0.1:55432` with SCRAM password authentication. Its data directory is ignored by Git. The existing Windows service `postgresql-x64-18` remains separate on port 5432 and was not modified.

From `backend/`, start the project-local cluster in a PowerShell terminal and leave that terminal open:

```powershell
& 'C:\Program Files\PostgreSQL\18\bin\postgres.exe' -D '.postgres-data' -h 127.0.0.1 -p 55432
```

Stop it from another PowerShell terminal:

```powershell
& 'C:\Program Files\PostgreSQL\18\bin\pg_ctl.exe' -D '.postgres-data' stop -m fast -w
```

The project-local database and application role are `student_alerting` and `student_alerting_app`. `backend/.env` contains the local connection URL and is ignored by Git; do not share or commit it. `backend/.env` also contains a randomly generated JWT secret; it is ignored by Git and must not be shared or committed.

### Setting up another machine

Install PostgreSQL 18 for Windows using the [official PostgreSQL Windows installer page](https://www.postgresql.org/download/windows/), start its service, and create the application role and database if they do not already exist. Copy `backend/.env.example` to `backend/.env` and set `DATABASE_URL` to the real `student_alerting_app` credentials, using the Psycopg 3 URL form `postgresql+psycopg://...`. URL-encode special characters in the password. Keep `.env` private. Set `SECRET_KEY` to a generated random value of at least 32 bytes before starting the backend (the example placeholder is intentionally rejected); the synthetic seed prompts for passwords without echoing them. If PostgreSQL command-line tools are not on `PATH`, run them from the installation's `bin` directory.

## Database initialization and demo data

At startup, the backend uses SQLAlchemy `Base.metadata.create_all()` to create missing tables. It does not drop tables or alter existing schemas. Use Alembic migrations when future changes need to modify existing tables.

To insert the small, idempotent synthetic demo dataset, run this from `backend/` after PostgreSQL is configured:

```powershell
.venv/Scripts/python.exe -m app.db.seed
```

It creates four synthetic users (a student with a profile, an unused student account, a faculty member, and an administrator), one faculty profile, and two synthetic academic records. The database stores Argon2 hashes. The seed prompts silently for each demo account password; it never saves plaintext passwords to files or the database. Keep the passwords private. The script prints the unused student's `user_id`; use that ID in the admin-only `POST /api/students`. Running the seed again does not add duplicate demo records.

## Start the server

From the repository root:

```powershell
backend/.venv/Scripts/uvicorn.exe app.main:app --reload --app-dir backend
```

Or, from inside `backend/`:

```powershell
.venv/Scripts/uvicorn.exe app.main:app --reload --app-dir .
```

The model path is resolved relative to the service source file, so this documented command does not depend on the current working directory. The server also accepts requests if model loading fails, while `/api/ml/model-status` reports the error and predictions return HTTP 503.

## Authentication and authorization

- `POST /api/auth/register` creates a STUDENT account only; role fields are rejected. Passwords must be at least 12 characters.
- `POST /api/auth/login` verifies credentials and returns a short-lived JWT bearer token.
- `GET /api/auth/me` returns the authenticated account and its linked student/faculty profile.
- `POST /api/admin/users` allows ADMIN-only controlled creation of STUDENT, FACULTY, or ADMIN accounts.
- `GET /api/students` is FACULTY/ADMIN only. `POST /api/students` is ADMIN only. Students can retrieve only their own profile and academic records; FACULTY/ADMIN can retrieve any. Academic record creation is FACULTY/ADMIN only.
- Health and ML inference remain public; inference scores only submitted features and does not retrieve stored private student records.

In Swagger, use **Authorize** and enter the login token to call protected endpoints.

## API

- `GET /api/health` — confirms that the API is responding.
- `GET /api/db/health` — checks PostgreSQL using `SELECT 1`.
- `GET /api/students` and `POST /api/students` — list/create student profiles.
- `GET /api/students/{student_id}` — retrieve one student.
- `GET /api/students/{student_id}/academic-records` and `POST /api/students/{student_id}/academic-records` — list/create academic records.
- `GET /api/ml/model-status` — reports model readiness and type.
- `POST /api/ml/predict-risk` — scores one input record.

The request contains the 15 input fields listed in the model metadata. For the complete request and response schemas, open Swagger at <http://127.0.0.1:8000/docs> after starting the server.

Test health in PowerShell:

```powershell
Invoke-RestMethod http://127.0.0.1:8000/api/health
Invoke-RestMethod http://127.0.0.1:8000/api/db/health
```

Student creation requires a pre-existing `STUDENT` user. After seeding, use the printed unused `user_id`:

```powershell
$newStudentUserId = [int](Read-Host 'Enter the unused user_id printed by the seed script')
$studentBody = @{
  user_id = $newStudentUserId
  student_identifier = 'DEMO-STU-002'
  first_name = 'Mina'
  last_name = 'Example'
  current_semester = 2
  program = 'Demo Computer Science'
} | ConvertTo-Json
$createdStudent = Invoke-RestMethod -Method Post -Uri http://127.0.0.1:8000/api/students -ContentType 'application/json' -Body $studentBody
$createdStudent
Invoke-RestMethod "http://127.0.0.1:8000/api/students/$($createdStudent.id)"
```

Use the returned student `id` to create an academic record:

```powershell
$recordBody = @{
  previous_sgpa = 3.2
  attendance_numeric = 90
  current_semester = 3
  credits_completed = 45
  daily_study_hours = 3
  daily_study_sessions = 2
  daily_social_media_hours = 2
  daily_skill_development_hours = 1
  teacher_consultancy = 'No'
  meritorious_scholarship = 'No'
  preferred_learning_mode = 'Online'
  english_proficiency = 'Intermediate'
  personal_computer = 'Yes'
  smartphone_use = 'Yes'
  co_curricular_activities = 'No'
} | ConvertTo-Json
Invoke-RestMethod -Method Post -Uri "http://127.0.0.1:8000/api/students/$($createdStudent.id)/academic-records" -ContentType 'application/json' -Body $recordBody
Invoke-RestMethod "http://127.0.0.1:8000/api/students/$($createdStudent.id)/academic-records"
```

Example ML request using frontend-friendly field names (also available in Swagger):

```json
{
  "previous_sgpa": 3.2,
  "attendance_numeric": 90,
  "current_semester": 3,
  "credits_completed": 45,
  "daily_study_hours": 3,
  "daily_study_sessions": 2,
  "daily_social_media_hours": 2,
  "daily_skill_development_hours": 1,
  "teacher_consultancy": "No",
  "meritorious_scholarship": "No",
  "preferred_learning_mode": "Online",
  "english_proficiency": "Intermediate",
  "personal_computer": "Yes",
  "smartphone_use": "Yes",
  "co_curricular_activities": "No"
}
```

Send it to `POST /api/ml/predict-risk`. The endpoint continues to use the frozen model and the metadata's 0.40 decision threshold.

```powershell
$predictionBody = @{
  previous_sgpa = 3.2
  attendance_numeric = 90
  current_semester = 3
  credits_completed = 45
  daily_study_hours = 3
  daily_study_sessions = 2
  daily_social_media_hours = 2
  daily_skill_development_hours = 1
  teacher_consultancy = 'No'
  meritorious_scholarship = 'No'
  preferred_learning_mode = 'Online'
  english_proficiency = 'Intermediate'
  personal_computer = 'Yes'
  smartphone_use = 'Yes'
  co_curricular_activities = 'No'
} | ConvertTo-Json
Invoke-RestMethod -Method Post -Uri http://127.0.0.1:8000/api/ml/predict-risk -ContentType 'application/json' -Body $predictionBody
```

The target definition is At Risk when current CGPA is below 3.0; current CGPA is not a prediction input. The API uses the model's class 1 score and the metadata's 0.40 threshold to produce `risk_prediction` (`1` means At Risk). `risk_score` is the model's uncalibrated score, not a literal probability of failure. `risk_level` uses the prototype's score bands: LOW below 0.35, MEDIUM from 0.35 through below 0.70, and HIGH at or above 0.70. The overall health endpoint reports `degraded` while either PostgreSQL or the ML model is unavailable; the ML prediction route remains separate from database persistence.
