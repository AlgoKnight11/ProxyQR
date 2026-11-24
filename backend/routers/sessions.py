import io
import base64
import json
import secrets
import datetime
from typing import Dict, List, Tuple
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
import qrcode
from PIL import Image

from backend.database import get_db
from backend.models import User, Course, Session as ClassSession, Attendance
from backend.auth import require_teacher
from backend.config import QR_ROTATION_INTERVAL_SECONDS, QR_GRACE_PERIOD_SECONDS
from backend.schemas import SessionCreate, DynamicQRResponse

router = APIRouter(prefix="/api/sessions", tags=["Class Sessions"])

# In-memory token cache to support grace-period verification
# Structure: { session_id: [ (token_str, valid_until_datetime), ... ] }
SESSION_TOKEN_HISTORY: Dict[int, List[Tuple[str, datetime.datetime]]] = {}

def add_token_to_history(session_id: int, token: str):
    now = datetime.datetime.utcnow()
    # Valid for normal interval + grace period
    valid_until = now + datetime.timedelta(seconds=QR_ROTATION_INTERVAL_SECONDS + QR_GRACE_PERIOD_SECONDS)
    
    if session_id not in SESSION_TOKEN_HISTORY:
        SESSION_TOKEN_HISTORY[session_id] = []
    
    # Add new token
    SESSION_TOKEN_HISTORY[session_id].append((token, valid_until))
    # Prune expired tokens older than valid_until
    SESSION_TOKEN_HISTORY[session_id] = [
        item for item in SESSION_TOKEN_HISTORY[session_id] if item[1] > now
    ]

def is_token_valid_for_session(session_id: int, token: str) -> bool:
    now = datetime.datetime.utcnow()
    valid_tokens = SESSION_TOKEN_HISTORY.get(session_id, [])
    for tok, valid_until in valid_tokens:
        if tok == token and valid_until >= now:
            return True
    return False

def generate_qr_base64(data_payload: str) -> str:
    qr = qrcode.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_M,
        box_size=10,
        border=2,
    )
    qr.add_data(data_payload)
    qr.make(fit=True)
    img = qr.make_image(fill_color="#0f172a", back_color="#ffffff")

    buffer = io.BytesIO()
    img.save(buffer, format="PNG")
    b64_str = base64.b64encode(buffer.getvalue()).decode("utf-8")
    return f"data:image/png;base64,{b64_str}"

@router.post("/start")
def start_session(
    data: SessionCreate,
    current_user: User = Depends(require_teacher),
    db: Session = Depends(get_db)
):
    course = db.query(Course).filter(
        Course.id == data.course_id,
        Course.teacher_id == current_user.id
    ).first()
    if not course:
        raise HTTPException(status_code=404, detail="Course not found or unauthorized")

    # Deactivate existing active sessions for this course
    db.query(ClassSession).filter(
        ClassSession.course_id == course.id,
        ClassSession.is_active == True
    ).update({"is_active": False})

    # Generate initial token
    now = datetime.datetime.utcnow()
    token = secrets.token_urlsafe(16)
    expires_at = now + datetime.timedelta(seconds=QR_ROTATION_INTERVAL_SECONDS)

    new_session = ClassSession(
        course_id=course.id,
        session_date=now,
        active_token=token,
        token_generated_at=now,
        expires_at=expires_at,
        is_active=True
    )
    db.add(new_session)
    db.commit()
    db.refresh(new_session)

    # Register in token history
    add_token_to_history(new_session.id, token)

    return {
        "message": "Session started",
        "session_id": new_session.id,
        "course_code": course.course_code,
        "course_name": course.course_name
    }

@router.get("/{session_id}/live-qr", response_model=DynamicQRResponse)
def get_live_qr(
    session_id: int,
    current_user: User = Depends(require_teacher),
    db: Session = Depends(get_db)
):
    session = db.query(ClassSession).filter(ClassSession.id == session_id).first()
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    if session.course.teacher_id != current_user.id:
        raise HTTPException(status_code=403, detail="Unauthorized for this session")

    now = datetime.datetime.utcnow()

    # Check if session is closed
    if not session.is_active:
        raise HTTPException(status_code=400, detail="This session is closed")

    # Check if current token has expired (older than rotation interval)
    elapsed = (now - (session.token_generated_at or now)).total_seconds()
    if elapsed >= QR_ROTATION_INTERVAL_SECONDS or not session.active_token:
        # Rotate token
        new_token = secrets.token_urlsafe(16)
        session.active_token = new_token
        session.token_generated_at = now
        session.expires_at = now + datetime.timedelta(seconds=QR_ROTATION_INTERVAL_SECONDS)
        db.commit()
        db.refresh(session)
        add_token_to_history(session.id, new_token)
        elapsed = 0

    expires_in = max(1, int(QR_ROTATION_INTERVAL_SECONDS - elapsed))

    # Construct QR payload: JSON string { "s": session_id, "t": token }
    payload = json.dumps({"s": session.id, "t": session.active_token})
    qr_base64 = generate_qr_base64(payload)

    present_count = db.query(Attendance).filter(Attendance.session_id == session.id).count()

    return DynamicQRResponse(
        session_id=session.id,
        course_code=session.course.course_code,
        course_name=session.course.course_name,
        token=session.active_token,
        qr_image_base64=qr_base64,
        expires_in_seconds=expires_in,
        present_count=present_count,
        is_active=session.is_active
    )

@router.post("/{session_id}/end")
def end_session(
    session_id: int,
    current_user: User = Depends(require_teacher),
    db: Session = Depends(get_db)
):
    session = db.query(ClassSession).filter(ClassSession.id == session_id).first()
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    if session.course.teacher_id != current_user.id:
        raise HTTPException(status_code=403, detail="Unauthorized")

    session.is_active = False
    session.active_token = None
    db.commit()

    # Clear token cache for this session
    if session_id in SESSION_TOKEN_HISTORY:
        del SESSION_TOKEN_HISTORY[session_id]

    present_count = db.query(Attendance).filter(Attendance.session_id == session.id).count()
    return {
        "message": "Session ended successfully",
        "session_id": session.id,
        "total_present": present_count
    }

@router.get("/{session_id}/attendances")
def get_session_attendances(
    session_id: int,
    current_user: User = Depends(require_teacher),
    db: Session = Depends(get_db)
):
    session = db.query(ClassSession).filter(ClassSession.id == session_id).first()
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    if session.course.teacher_id != current_user.id:
        raise HTTPException(status_code=403, detail="Unauthorized")

    records = db.query(Attendance).filter(Attendance.session_id == session.id).order_by(Attendance.marked_at.desc()).all()
    
    return {
        "session_id": session.id,
        "course_code": session.course.course_code,
        "is_active": session.is_active,
        "total_present": len(records),
        "students": [
            {
                "id": rec.id,
                "student_id": rec.student.id,
                "full_name": rec.student.full_name,
                "roll_no": rec.student.roll_no,
                "marked_at": rec.marked_at.strftime("%I:%M:%S %p"),
                "status": rec.status
            }
            for rec in records
        ]
    }
