"""Tests for the new Alerting System."""

import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.models.alert import AlertStatus

@pytest.fixture(scope="module")
def client():
    with TestClient(app) as c:
        yield c

def test_alert_lifecycle(client):
    # Log in as faculty
    faculty_resp = client.post("/api/auth/login", json={
        "email": "demo.faculty@example.test",
        "password": "Password1234!"
    })
    faculty_token = faculty_resp.json()["access_token"]
    faculty_headers = {"Authorization": f"Bearer {faculty_token}"}
    
    # 1. Faculty checks for existing OPEN alerts
    resp = client.get("/api/alerts?status_filter=OPEN", headers=faculty_headers)
    assert resp.status_code == 200
    initial_alerts_count = len(resp.json())
    
    # Log in as student to get ID
    student_resp = client.post("/api/auth/login", json={
        "email": "demo.student@example.test",
        "password": "Password1234!"
    })
    student_headers = {"Authorization": f"Bearer {student_resp.json()['access_token']}"}
    me_resp = client.get("/api/student/me", headers=student_headers)
    student_id = me_resp.json()["id"]

    # 2. Faculty posts an at-risk academic record
    record_data = {
        "previous_sgpa": 1.5, # Very low
        "attendance_numeric": 50, # Very low
        "current_semester": 3,
        "credits_completed": 30,
        "daily_study_hours": 0.5,
        "daily_study_sessions": 1,
        "daily_social_media_hours": 6,
        "daily_skill_development_hours": 0,
        "teacher_consultancy": "No",
        "meritorious_scholarship": "No",
        "preferred_learning_mode": "Online",
        "english_proficiency": "Poor",
        "personal_computer": "No",
        "smartphone_use": "Yes",
        "co_curricular_activities": "No"
    }
    
    client.post(f"/api/students/{student_id}/academic-records", json=record_data, headers=faculty_headers)

    # 3. Verify an alert was created
    resp = client.get("/api/alerts?status_filter=OPEN", headers=faculty_headers)
    assert resp.status_code == 200
    new_alerts = resp.json()
    assert len(new_alerts) > initial_alerts_count
    
    alert = new_alerts[0]
    alert_id = alert["id"]
    assert alert["status"] == "OPEN"
    
    # 4. Faculty acknowledges the alert
    resp = client.patch(f"/api/alerts/{alert_id}/status", json={"status": AlertStatus.ACKNOWLEDGED}, headers=faculty_headers)
    assert resp.status_code == 200
    assert resp.json()["status"] == "ACKNOWLEDGED"
    
    # 5. Faculty resolves the alert
    resp = client.patch(f"/api/alerts/{alert_id}/status", json={"status": AlertStatus.RESOLVED}, headers=faculty_headers)
    assert resp.status_code == 200
    assert resp.json()["status"] == "RESOLVED"

