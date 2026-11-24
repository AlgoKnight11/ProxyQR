import json
import time
from fastapi.testclient import TestClient
from backend.main import app

client = TestClient(app)

def test_full_workflow():
    print("\n--- 1. Testing Faculty Login ---")
    res = client.post("/api/auth/login", json={"identifier": "abhijeet@college.edu", "password": "Faculty@123"})
    assert res.status_code == 200, f"Faculty login failed: {res.text}"
    teacher_token = res.json()["access_token"]
    print("Faculty authenticated successfully. Token received.")

    teacher_headers = {"Authorization": f"Bearer {teacher_token}"}

    print("\n--- 2. Testing Fetching Faculty Courses ---")
    res = client.get("/api/courses/teacher", headers=teacher_headers)
    assert res.status_code == 200
    courses = res.json()
    print(f"Teacher courses found: {[c['course_code'] for c in courses]}")
    cs301 = next(c for c in courses if c["course_code"] == "CS301")

    print("\n--- 3. Testing Starting Session ---")
    res = client.post("/api/sessions/start", json={"course_id": cs301["id"]}, headers=teacher_headers)
    assert res.status_code == 200, f"Start session failed: {res.text}"
    session_data = res.json()
    session_id = session_data["session_id"]
    print(f"Session started! Session ID: {session_id}")

    print("\n--- 4. Testing Live Dynamic QR Code Generation ---")
    res = client.get(f"/api/sessions/{session_id}/live-qr", headers=teacher_headers)
    assert res.status_code == 200, f"QR generation failed: {res.text}"
    qr_data = res.json()
    assert qr_data["qr_image_base64"].startswith("data:image/png;base64,")
    token = qr_data["token"]
    print(f"Dynamic QR generated. Token: {token[:8]}..., Expires in: {qr_data['expires_in_seconds']}s")

    print("\n--- 5. Testing Student Login ---")
    res = client.post("/api/auth/login", json={"identifier": "251620101035", "password": "Student@123"})
    assert res.status_code == 200, f"Student login failed: {res.text}"
    student_token = res.json()["access_token"]
    print("Student (Rajpreet Singh) authenticated successfully.")

    student_headers = {"Authorization": f"Bearer {student_token}"}

    print("\n--- 6. Testing Marking Attendance (Legitimate Scan) ---")
    payload = json.dumps({"s": session_id, "t": token})
    res = client.post("/api/attendance/mark", json={"qr_payload": payload}, headers=student_headers)
    assert res.status_code == 200, f"Mark attendance failed: {res.text}"
    mark_res = res.json()
    print(f"Attendance recorded: {mark_res['message']} at {mark_res['marked_at']}")

    print("\n--- 7. Testing Anti-Proxy: Duplicate Scan Prevention ---")
    res = client.post("/api/attendance/mark", json={"qr_payload": payload}, headers=student_headers)
    assert res.status_code == 409, f"Expected 409 duplicate scan error, got {res.status_code}"
    print(f"Correctly blocked duplicate scan: {res.json()['detail']}")

    print("\n--- 8. Testing Anti-Proxy: Fake / Expired Token ---")
    fake_payload = json.dumps({"s": session_id, "t": "fake_expired_token_1234"})
    res = client.post("/api/attendance/mark", json={"qr_payload": fake_payload}, headers=student_headers)
    assert res.status_code == 400
    print(f"Correctly rejected counterfeit token: {res.json()['detail']}")

    print("\n--- 9. Testing Teacher Live Stream & Attendance List ---")
    res = client.get(f"/api/sessions/{session_id}/attendances", headers=teacher_headers)
    assert res.status_code == 200
    attendees_data = res.json()
    print(f"Teacher live feed updated: {attendees_data['total_present']} student(s) logged in real-time.")
    assert any(s["roll_no"] == "251620101035" for s in attendees_data["students"])

    print("\n--- 10. Testing Student Dashboard Stats & History ---")
    res = client.get("/api/courses/student", headers=student_headers)
    assert res.status_code == 200
    student_courses = res.json()
    my_cs301 = next(c for c in student_courses if c["course_code"] == "CS301")
    print(f"Student CS301 Attendance: {my_cs301['attended_classes']}/{my_cs301['total_classes']} ({my_cs301['percentage']}%)")

    print("\n--- 11. Testing Ending Session ---")
    res = client.post(f"/api/sessions/{session_id}/end", headers=teacher_headers)
    assert res.status_code == 200
    print(f"Session ended. Total logged: {res.json()['total_present']}")

    print("\n--- 12. Testing CSV Attendance Report Export ---")
    res = client.get(f"/api/attendance/export/{cs301['id']}", headers=teacher_headers)
    assert res.status_code == 200
    assert "text/csv" in res.headers["content-type"]
    assert "Roll Number,Student Name" in res.text
    print("CSV Report generated and validated successfully.")

    print("\n[SUCCESS] ALL 12 INTEGRATION TESTS PASSED PERFECTLY!")

if __name__ == "__main__":
    test_full_workflow()
