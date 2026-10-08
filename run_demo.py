import httpx
import json

BASE_URL = "http://127.0.0.1:8000"

def run_demonstration():
    print("--- STUDENT ALERTING SYSTEM: LIVE DEMONSTRATION ---\n")
    
    with httpx.Client(base_url=BASE_URL) as client:
        # 1. Check health
        print("1. Checking API Health...")
        health = client.get("/api/health").json()
        print(f"Health Response: {json.dumps(health, indent=2)}\n")
        
        # 2. Login as Faculty
        print("2. Logging in as Faculty (demo.faculty@example.test)...")
        auth_resp = client.post("/api/auth/login", json={
            "email": "demo.faculty@example.test",
            "password": "Password1234!"
        })
        faculty_token = auth_resp.json().get("access_token")
        faculty_headers = {"Authorization": f"Bearer {faculty_token}"}
        print("Login successful. Got JWT token.\n")
        
        # 3. Find a student
        print("3. Fetching student list...")
        students = client.get("/api/students", headers=faculty_headers).json()
        if not students:
            print("No students found. Run the seed script first.")
            return
            
        student_id = students[0]["id"]
        print(f"Found student: {students[0]['first_name']} {students[0]['last_name']} (ID: {student_id})\n")
        
        # 4. Submit an At-Risk Academic Record
        print("4. Submitting a new academic record with VERY POOR metrics...")
        record_data = {
            "previous_sgpa": 1.1,
            "attendance_numeric": 35,
            "current_semester": 2,
            "credits_completed": 15,
            "daily_study_hours": 0.5,
            "daily_study_sessions": 1,
            "daily_social_media_hours": 8,
            "daily_skill_development_hours": 0,
            "teacher_consultancy": "No",
            "meritorious_scholarship": "No",
            "preferred_learning_mode": "Online",
            "english_proficiency": "Poor",
            "personal_computer": "No",
            "smartphone_use": "Yes",
            "co_curricular_activities": "No"
        }
        record_resp = client.post(f"/api/students/{student_id}/academic-records", json=record_data, headers=faculty_headers)
        print(f"Record created successfully. ID: {record_resp.json()['id']}\n")
        
        # 5. Check if an alert was generated
        print("5. Checking Alert System for new OPEN alerts...")
        alerts_resp = client.get("/api/alerts?status_filter=OPEN", headers=faculty_headers)
        alerts = alerts_resp.json()
        
        print(f"Found {len(alerts)} OPEN alerts.")
        if alerts:
            latest_alert = alerts[0]
            print("Latest Alert Details:")
            print(json.dumps(latest_alert, indent=2))
            
            # 6. Acknowledge the alert
            print("\n6. Faculty acknowledges the alert...")
            ack_resp = client.patch(f"/api/alerts/{latest_alert['id']}/status", json={"status": "ACKNOWLEDGED"}, headers=faculty_headers)
            print(f"Alert Status is now: {ack_resp.json()['status']}")

if __name__ == "__main__":
    try:
        run_demonstration()
    except httpx.ConnectError:
        print("Error: The FastAPI server is not running on http://127.0.0.1:8000")
