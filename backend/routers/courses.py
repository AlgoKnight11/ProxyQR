from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List, Dict, Any

from backend.database import get_db
from backend.models import User, Course, Enrollment, Session as ClassSession, Attendance
from backend.auth import get_current_user, require_teacher, require_student

router = APIRouter(prefix="/api/courses", tags=["Courses"])

@router.get("/teacher")
def get_teacher_courses(
    current_user: User = Depends(require_teacher),
    db: Session = Depends(get_db)
):
    courses = db.query(Course).filter(Course.teacher_id == current_user.id).all()
    results = []
    for course in courses:
        enrolled_count = db.query(Enrollment).filter(Enrollment.course_id == course.id).count()
        active_session = db.query(ClassSession).filter(
            ClassSession.course_id == course.id,
            ClassSession.is_active == True
        ).first()

        results.append({
            "id": course.id,
            "course_code": course.course_code,
            "course_name": course.course_name,
            "enrolled_count": enrolled_count,
            "has_active_session": active_session is not None,
            "active_session_id": active_session.id if active_session else None
        })
    return results

@router.get("/student")
def get_student_courses(
    current_user: User = Depends(require_student),
    db: Session = Depends(get_db)
):
    enrollments = db.query(Enrollment).filter(Enrollment.student_id == current_user.id).all()
    results = []

    for enr in enrollments:
        course = enr.course
        total_sessions = db.query(ClassSession).filter(ClassSession.course_id == course.id).count()
        attended_sessions = db.query(Attendance).join(ClassSession).filter(
            ClassSession.course_id == course.id,
            Attendance.student_id == current_user.id
        ).count()

        percentage = round((attended_sessions / total_sessions * 100), 1) if total_sessions > 0 else 100.0

        results.append({
            "course_id": course.id,
            "course_code": course.course_code,
            "course_name": course.course_name,
            "teacher_name": course.teacher.full_name if course.teacher else "Faculty",
            "total_classes": total_sessions,
            "attended_classes": attended_sessions,
            "percentage": percentage,
            "is_low_attendance": percentage < 75.0 and total_sessions > 0
        })

    return results

@router.get("/{course_id}/students")
def get_course_roster(
    course_id: int,
    current_user: User = Depends(require_teacher),
    db: Session = Depends(get_db)
):
    course = db.query(Course).filter(Course.id == course_id, Course.teacher_id == current_user.id).first()
    if not course:
        raise HTTPException(status_code=404, detail="Course not found or unauthorized")

    enrollments = db.query(Enrollment).filter(Enrollment.course_id == course_id).all()
    total_sessions = db.query(ClassSession).filter(ClassSession.course_id == course_id).count()

    roster = []
    for enr in enrollments:
        student = enr.student
        attended = db.query(Attendance).join(ClassSession).filter(
            ClassSession.course_id == course_id,
            Attendance.student_id == student.id
        ).count()
        pct = round((attended / total_sessions * 100), 1) if total_sessions > 0 else 100.0

        roster.append({
            "student_id": student.id,
            "full_name": student.full_name,
            "roll_no": student.roll_no,
            "email": student.email,
            "attended": attended,
            "total": total_sessions,
            "percentage": pct,
            "is_low": pct < 75.0 and total_sessions > 0
        })

    # Sort alphabetically by roll number
    roster.sort(key=lambda s: s["roll_no"] or "")
    return {
        "course": {
            "id": course.id,
            "course_code": course.course_code,
            "course_name": course.course_name,
            "total_classes": total_sessions,
        },
        "students": roster
    }
