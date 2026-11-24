from pydantic import BaseModel, EmailStr
from typing import Optional, List
from datetime import datetime

# Auth Schemas
class LoginRequest(BaseModel):
    identifier: str # Email or Roll Number
    password: str

class UserOut(BaseModel):
    id: int
    full_name: str
    email: Optional[str] = None
    roll_no: Optional[str] = None
    role: str

    class Config:
        from_attributes = True

class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserOut

# Course Schemas
class CourseOut(BaseModel):
    id: int
    course_code: str
    course_name: str
    teacher_id: int
    teacher_name: Optional[str] = None
    enrolled_count: Optional[int] = 0

    class Config:
        from_attributes = True

# Session Schemas
class SessionCreate(BaseModel):
    course_id: int

class SessionOut(BaseModel):
    id: int
    course_id: int
    course_code: str
    course_name: str
    session_date: datetime
    is_active: bool
    present_count: int

    class Config:
        from_attributes = True

class DynamicQRResponse(BaseModel):
    session_id: int
    course_code: str
    course_name: str
    token: str
    qr_image_base64: str
    expires_in_seconds: int
    present_count: int
    is_active: bool

# Attendance Schemas
class MarkAttendanceRequest(BaseModel):
    qr_payload: str # Contains "session_id:token" or signed token

class ManualAttendanceRequest(BaseModel):
    session_id: int
    student_id: int
    status: str = "manual_override"

class AttendanceRecordOut(BaseModel):
    id: int
    student_id: int
    student_name: str
    roll_no: str
    marked_at: datetime
    status: str

    class Config:
        from_attributes = True

class StudentAttendanceStats(BaseModel):
    course_id: int
    course_code: str
    course_name: str
    teacher_name: str
    total_classes: int
    attended_classes: int
    percentage: float
    is_low_attendance: bool # True if < 75%

class AttendanceHistoryItem(BaseModel):
    session_id: int
    course_code: str
    course_name: str
    session_date: datetime
    status: str # "Present", "Absent"
