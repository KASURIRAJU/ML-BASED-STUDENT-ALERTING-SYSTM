"""Tests for the Student Alerting System."""

import pytest
from fastapi.testclient import TestClient

from app.main import app

@pytest.fixture(scope="module")
def client():
    with TestClient(app) as c:
        yield c

def test_health(client):
    response = client.get("/api/health")
    assert response.status_code == 200
    data = response.json()
    assert data["backend"] == "available"
    assert data["status"] == "ok"
    assert data["database"] == "connected"
    assert data["ml_model"] == "loaded"

def test_database_health(client):
    response = client.get("/api/db/health")
    assert response.status_code == 200
    assert response.json()["status"] == "connected"

def test_model_status(client):
    response = client.get("/api/ml/model-status")
    assert response.status_code == 200
    assert response.json()["loaded"] is True

def test_authentication_student(client):
    response = client.post("/api/auth/login", json={
        "email": "demo.student@example.test",
        "password": "Password1234!"
    })
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert data["token_type"] == "bearer"
    return data["access_token"]

def test_authentication_invalid(client):
    response = client.post("/api/auth/login", json={
        "email": "demo.student@example.test",
        "password": "wrongpassword"
    })
    assert response.status_code == 401
    assert "Incorrect email or password" in response.json()["detail"]

def test_student_isolation(client):
    token = test_authentication_student(client)
    headers = {"Authorization": f"Bearer {token}"}
    
    # Can access own profile
    response = client.get("/api/student/me", headers=headers)
    assert response.status_code == 200
    assert response.json()["student_identifier"] == "DEMO-STU-001"
    
    # Cannot access faculty endpoints
    response = client.get("/api/faculty/me", headers=headers)
    assert response.status_code == 403

def test_faculty_rbac(client):
    # Login as faculty
    response = client.post("/api/auth/login", json={
        "email": "demo.faculty@example.test",
        "password": "Password1234!"
    })
    assert response.status_code == 200
    token = response.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}
    
    # Can access faculty profile
    response = client.get("/api/faculty/me", headers=headers)
    assert response.status_code == 200
    
    # Cannot access student profile directly
    response = client.get("/api/student/me", headers=headers)
    assert response.status_code == 403

def test_ml_inference(client):
    # Test public inference endpoint
    features = {
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
    response = client.post("/api/ml/predict-risk", json=features)
    assert response.status_code == 200
    data = response.json()
    assert "risk_prediction" in data
    assert "risk_status" in data
    assert data["decision_threshold"] == 0.40

def test_risk_persistence(client):
    # Verify GET risk fetches the appended prediction without duplicating
    token = test_authentication_student(client)
    headers = {"Authorization": f"Bearer {token}"}
    
    # First, post a new academic record to generate a prediction
    record_data = {
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
    
    # Wait, academic records can only be created by faculty/admin.
    # So we need to log in as admin or faculty to post it for this student.
    faculty_resp = client.post("/api/auth/login", json={
        "email": "demo.faculty@example.test",
        "password": "Password1234!"
    })
    faculty_token = faculty_resp.json()["access_token"]
    faculty_headers = {"Authorization": f"Bearer {faculty_token}"}
    
    # Find student ID
    me_resp = client.get("/api/student/me", headers=headers)
    student_id = me_resp.json()["id"]
    
    client.post(f"/api/students/{student_id}/academic-records", json=record_data, headers=faculty_headers)

    response = client.get("/api/student/me/risk", headers=headers)
    assert response.status_code == 200
    data = response.json()
    assert "risk_prediction" in data

    # Perform another GET request
    response2 = client.get("/api/student/me/risk", headers=headers)
    assert response2.status_code == 200
    
    # They should have the same predicted_at if no duplicate was created
    assert data["predicted_at"] == response2.json()["predicted_at"]
