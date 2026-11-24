import json
import csv
import io
import datetime
from fastapi import APIRouter, Depends, HTTPException, status, Response
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
from typing import List

from backend.database import get_db
from backend.models import User, Course, Enrollment, Session as ClassSession, Attendance
from backend.auth import get_current_user, require_student, require_teacher
from backend.schemas import MarkAttendanceRequest, ManualAttendanceRequest
from backend.routers.sessions import is_token_valid_for_session

router = APIRouter(prefix="/api/attendance", tags=["Attendance Management"])

@router.post("/mark")
def mark_attendance(
    req: MarkAttendanceRequest,
    current_user: User = Depends(require_student),
    db: Session = Depends(get_db)
):
    # Parse payload
    raw_payload = req.qr_payload.strip()
    session_id = None
    token = None

    try:
        # Expected format: JSON {"s": session_id, "t": token}
        data = json.loads(raw_payload)
        session_id = int(data.get("s"))
        token = str(data.get("t"))
    except Exception:
        # Fallback format: "PROXYQR:session_id:token" or "session_id:token"
        parts = raw_payload.split(":")
        if len(parts) == 3 and parts[0] == "PROXYQR":
            session_id = int(parts[1])
            token = parts[2]
        elif len(parts) == 2:
            session_id = int(parts[0])
            token = parts[1]

    if not session_id or not token:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid QR code format. Please scan an authentic classroom QR code."
        )

    # 1. Verify session exists
    session = db.query(ClassSession).filter(ClassSession.id == session_id).first()
    if not session:
        raise HTTPException(status_code=404, detail="Lecture session not found.")

    # 2. Check if session is currently active
    if not session.is_active:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="This attendance session has already ended."
        )

    # 3. Check student enrollment in the course
    enrollment = db.query(Enrollment).filter(
        Enrollment.course_id == session.course_id,
        Enrollment.student_id == current_user.id
    ).first()
    if not enrollment:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"You are not enrolled in {session.course.course_code} ({session.course.course_name})."
        )

    # 4. Anti-Proxy: Verify rotating token validity (with grace period)
    is_valid = (session.active_token == token) or is_token_valid_for_session(session_id, token)
    if not is_valid:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="QR code expired. Please scan the refreshed code displayed on the classroom screen."
        )

    # 5. Check duplicate submission
    existing = db.query(Attendance).filter(
        Attendance.session_id == session.id,
        Attendance.student_id == current_user.id
    ).first()
    if existing:
        formatted_time = existing.marked_at.strftime("%I:%M:%S %p")
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Attendance already recorded for this lecture at {formatted_time}."
        )

    # 6. Record attendance
    now = datetime.datetime.utcnow()
    att_record = Attendance(
        session_id=session.id,
        student_id=current_user.id,
        marked_at=now,
        status="present"
    )
    db.add(att_record)
    db.commit()
    db.refresh(att_record)

    return {
        "success": True,
        "message": "Attendance successfully marked!",
        "course_code": session.course.course_code,
        "course_name": session.course.course_name,
        "student_name": current_user.full_name,
        "roll_no": current_user.roll_no,
        "marked_at": now.strftime("%I:%M:%S %p, %d %b %Y")
    }

@router.post("/manual")
def manual_mark_attendance(
    req: ManualAttendanceRequest,
    current_user: User = Depends(require_teacher),
    db: Session = Depends(get_db)
):
    session = db.query(ClassSession).filter(ClassSession.id == req.session_id).first()
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    if session.course.teacher_id != current_user.id:
        raise HTTPException(status_code=403, detail="Unauthorized")

    student = db.query(User).filter(User.id == req.student_id, User.role == "student").first()
    if not student:
        raise HTTPException(status_code=404, detail="Student not found")

    # Check enrollment
    is_enrolled = db.query(Enrollment).filter(
        Enrollment.course_id == session.course_id,
        Enrollment.student_id == student.id
    ).first()
    if not is_enrolled:
        raise HTTPException(status_code=400, detail="Student is not enrolled in this course")

    existing = db.query(Attendance).filter(
        Attendance.session_id == session.id,
        Attendance.student_id == student.id
    ).first()

    now = datetime.datetime.utcnow()
    if existing:
        existing.status = req.status
        existing.marked_at = now
        db.commit()
        return {"message": f"Updated attendance status for {student.full_name}"}
    else:
        new_att = Attendance(
            session_id=session.id,
            student_id=student.id,
            marked_at=now,
            status=req.status
        )
        db.add(new_att)
        db.commit()
        return {"message": f"Manually marked attendance for {student.full_name}"}

@router.get("/student/history")
def get_student_history(
    current_user: User = Depends(require_student),
    db: Session = Depends(get_db)
):
    # Get all enrollments for this student
    enrollments = db.query(Enrollment).filter(Enrollment.student_id == current_user.id).all()
    course_ids = [e.course_id for e in enrollments]

    # Get all sessions for these courses
    sessions = db.query(ClassSession).filter(
        ClassSession.course_id.in_(course_ids)
    ).order_by(ClassSession.session_date.desc()).all()

    # Get student attendances
    student_attendances = {
        att.session_id: att
        for att in db.query(Attendance).filter(Attendance.student_id == current_user.id).all()
    }

    history = []
    for s in sessions:
        att = student_attendances.get(s.id)
        history.append({
            "session_id": s.id,
            "course_code": s.course.course_code,
            "course_name": s.course.course_name,
            "session_date": s.session_date.strftime("%d %b %Y, %I:%M %p"),
            "status": "Present" if att else "Absent",
            "marked_at": att.marked_at.strftime("%I:%M:%S %p") if att else None,
            "status_type": att.status if att else "absent"
        })

    return history

@router.get("/export/{course_id}")
def export_course_attendance_csv(
    course_id: int,
    current_user: User = Depends(require_teacher),
    db: Session = Depends(get_db)
):
    course = db.query(Course).filter(Course.id == course_id, Course.teacher_id == current_user.id).first()
    if not course:
        raise HTTPException(status_code=404, detail="Course not found or unauthorized")

    # Fetch sessions and enrolled students
    sessions = db.query(ClassSession).filter(ClassSession.course_id == course_id).order_by(ClassSession.session_date.asc()).all()
    enrollments = db.query(Enrollment).filter(Enrollment.course_id == course_id).all()

    total_sessions_count = len(sessions)

    # Build CSV output in memory
    output = io.StringIO()
    writer = csv.writer(output)

    # Header Row
    session_date_headers = [f"Session {i+1} ({s.session_date.strftime('%d-%b')})" for i, s in enumerate(sessions)]
    header = ["Roll Number", "Student Name", "Email"] + session_date_headers + ["Total Present", "Total Classes", "Attendance %", "Defaulter (<75%)"]
    writer.writerow(header)

    for enr in enrollments:
        student = enr.student
        student_att = {
            att.session_id: att.status
            for att in db.query(Attendance).filter(Attendance.student_id == student.id).all()
        }

        row = [student.roll_no or "N/A", student.full_name, student.email or "N/A"]
        present_count = 0

        for s in sessions:
            if s.id in student_att:
                row.append("P")
                present_count += 1
            else:
                row.append("A")

        pct = round((present_count / total_sessions_count * 100), 1) if total_sessions_count > 0 else 100.0
        is_defaulter = "YES (Below 75%)" if pct < 75.0 and total_sessions_count > 0 else "NO"

        row.extend([present_count, total_sessions_count, f"{pct}%", is_defaulter])
        writer.writerow(row)

    output.seek(0)
    filename = f"Attendance_{course.course_code}_{datetime.date.today()}.csv"

    return StreamingResponse(
        io.BytesIO(output.getvalue().encode("utf-8")),
        media_type="text/csv",
        headers={"Content-Disposition": f"attachment; filename={filename}"}
    )
