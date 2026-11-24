import datetime
from sqlalchemy import Column, Integer, String, Boolean, DateTime, ForeignKey, UniqueConstraint
from sqlalchemy.orm import relationship
from backend.database import Base

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    full_name = Column(String(120), nullable=False)
    email = Column(String(120), unique=True, index=True, nullable=True)
    roll_no = Column(String(60), unique=True, index=True, nullable=True)
    password_hash = Column(String(255), nullable=False)
    role = Column(String(20), nullable=False)  # "teacher" or "student"
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

    # Relationships
    taught_courses = relationship("Course", back_populates="teacher")
    enrollments = relationship("Enrollment", back_populates="student")
    attendances = relationship("Attendance", back_populates="student")

class Course(Base):
    __tablename__ = "courses"

    id = Column(Integer, primary_key=True, index=True)
    course_code = Column(String(30), unique=True, index=True, nullable=False)
    course_name = Column(String(150), nullable=False)
    teacher_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

    # Relationships
    teacher = relationship("User", back_populates="taught_courses")
    enrollments = relationship("Enrollment", back_populates="course")
    sessions = relationship("Session", back_populates="course")

class Enrollment(Base):
    __tablename__ = "enrollments"

    id = Column(Integer, primary_key=True, index=True)
    course_id = Column(Integer, ForeignKey("courses.id"), nullable=False)
    student_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    enrolled_at = Column(DateTime, default=datetime.datetime.utcnow)

    __table_args__ = (
        UniqueConstraint("course_id", "student_id", name="uq_course_student"),
    )

    course = relationship("Course", back_populates="enrollments")
    student = relationship("User", back_populates="enrollments")

class Session(Base):
    __tablename__ = "sessions"

    id = Column(Integer, primary_key=True, index=True)
    course_id = Column(Integer, ForeignKey("courses.id"), nullable=False)
    session_date = Column(DateTime, default=datetime.datetime.utcnow)
    active_token = Column(String(255), nullable=True)
    token_generated_at = Column(DateTime, default=datetime.datetime.utcnow)
    expires_at = Column(DateTime, nullable=True)
    is_active = Column(Boolean, default=True)

    course = relationship("Course", back_populates="sessions")
    attendances = relationship("Attendance", back_populates="session", cascade="all, delete-orphan")

class Attendance(Base):
    __tablename__ = "attendance"

    id = Column(Integer, primary_key=True, index=True)
    session_id = Column(Integer, ForeignKey("sessions.id"), nullable=False)
    student_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    marked_at = Column(DateTime, default=datetime.datetime.utcnow)
    status = Column(String(20), default="present")  # "present", "manual_override"

    __table_args__ = (
        UniqueConstraint("session_id", "student_id", name="uq_session_student"),
    )

    session = relationship("Session", back_populates="attendances")
    student = relationship("User", back_populates="attendances")
