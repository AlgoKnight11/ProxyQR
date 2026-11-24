import datetime
from backend.database import SessionLocal, engine, Base
from backend.models import User, Course, Enrollment, Session as ClassSession, Attendance
from backend.auth import hash_password

def seed_database():
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()

    # Check if already seeded
    if db.query(User).count() > 0:
        print("[*] Database already populated with users.")
        db.close()
        return

    print("[*] Seeding sample data...")

    # 1. Teachers
    teacher1 = User(
        full_name="Prof. Abhijeet Kushawah",
        email="abhijeet@college.edu",
        roll_no=None,
        password_hash=hash_password("Faculty@123"),
        role="teacher"
    )
    teacher2 = User(
        full_name="Dr. Priya Sharma",
        email="priya@college.edu",
        roll_no=None,
        password_hash=hash_password("Faculty@123"),
        role="teacher"
    )
    db.add_all([teacher1, teacher2])
    db.commit()
    db.refresh(teacher1)
    db.refresh(teacher2)

    # 2. Courses
    c1 = Course(
        course_code="CS301",
        course_name="Operating Systems",
        teacher_id=teacher1.id
    )
    c2 = Course(
        course_code="CS302",
        course_name="Database Management Systems",
        teacher_id=teacher1.id
    )
    c3 = Course(
        course_code="CS303",
        course_name="Computer Networks",
        teacher_id=teacher2.id
    )
    db.add_all([c1, c2, c3])
    db.commit()
    db.refresh(c1)
    db.refresh(c2)
    db.refresh(c3)

    # 3. Students (from synopsis and realistic peers)
    students_data = [
        {"name": "Rajpreet Singh", "roll": "251620101035", "email": "rajpreet@college.edu"},
        {"name": "Arvind Verma", "roll": "251620101008", "email": "arvind@college.edu"},
        {"name": "Sneha Kapoor", "roll": "251620101012", "email": "sneha@college.edu"},
        {"name": "Rohan Mehta", "roll": "251620101020", "email": "rohan@college.edu"},
        {"name": "Ananya Gupta", "roll": "251620101044", "email": "ananya@college.edu"},
    ]

    student_objs = []
    default_pw_hash = hash_password("Student@123")
    for s in students_data:
        student = User(
            full_name=s["name"],
            email=s["email"],
            roll_no=s["roll"],
            password_hash=default_pw_hash,
            role="student"
        )
        db.add(student)
        student_objs.append(student)

    db.commit()
    for s in student_objs:
        db.refresh(s)

    # 4. Enroll all students in CS301, CS302, CS303
    enrollments = []
    for course in [c1, c2, c3]:
        for student in student_objs:
            enrollments.append(Enrollment(course_id=course.id, student_id=student.id))
    db.add_all(enrollments)
    db.commit()

    # 5. Add a few historical sessions for CS301 to simulate existing attendance records
    now = datetime.datetime.utcnow()
    # Past session 1 (3 days ago)
    s1 = ClassSession(
        course_id=c1.id,
        session_date=now - datetime.timedelta(days=3),
        active_token=None,
        is_active=False
    )
    # Past session 2 (2 days ago)
    s2 = ClassSession(
        course_id=c1.id,
        session_date=now - datetime.timedelta(days=2),
        active_token=None,
        is_active=False
    )
    # Past session 3 (1 day ago)
    s3 = ClassSession(
        course_id=c1.id,
        session_date=now - datetime.timedelta(days=1),
        active_token=None,
        is_active=False
    )
    db.add_all([s1, s2, s3])
    db.commit()
    db.refresh(s1)
    db.refresh(s2)
    db.refresh(s3)

    # Mark attendance in past sessions:
    # Rajpreet was present in s1, s2, s3 (100%)
    # Arvind was present in s1, s2 (66.7% - defaulter demo!)
    # Sneha was present in s1, s3 (66.7%)
    # Rohan was present in s1, s2, s3 (100%)
    # Ananya was present in s2, s3 (66.7%)
    past_attendances = [
        Attendance(session_id=s1.id, student_id=student_objs[0].id, marked_at=s1.session_date + datetime.timedelta(minutes=2)),
        Attendance(session_id=s2.id, student_id=student_objs[0].id, marked_at=s2.session_date + datetime.timedelta(minutes=1)),
        Attendance(session_id=s3.id, student_id=student_objs[0].id, marked_at=s3.session_date + datetime.timedelta(minutes=3)),

        Attendance(session_id=s1.id, student_id=student_objs[1].id, marked_at=s1.session_date + datetime.timedelta(minutes=2)),
        Attendance(session_id=s2.id, student_id=student_objs[1].id, marked_at=s2.session_date + datetime.timedelta(minutes=4)),

        Attendance(session_id=s1.id, student_id=student_objs[2].id, marked_at=s1.session_date + datetime.timedelta(minutes=1)),
        Attendance(session_id=s3.id, student_id=student_objs[2].id, marked_at=s3.session_date + datetime.timedelta(minutes=5)),

        Attendance(session_id=s1.id, student_id=student_objs[3].id, marked_at=s1.session_date + datetime.timedelta(minutes=2)),
        Attendance(session_id=s2.id, student_id=student_objs[3].id, marked_at=s2.session_date + datetime.timedelta(minutes=2)),
        Attendance(session_id=s3.id, student_id=student_objs[3].id, marked_at=s3.session_date + datetime.timedelta(minutes=1)),

        Attendance(session_id=s2.id, student_id=student_objs[4].id, marked_at=s2.session_date + datetime.timedelta(minutes=3)),
        Attendance(session_id=s3.id, student_id=student_objs[4].id, marked_at=s3.session_date + datetime.timedelta(minutes=2)),
    ]
    db.add_all(past_attendances)
    db.commit()

    print("[+] Seeding complete! Created 2 faculty members, 3 courses, 5 students, and sample attendance history.")
    db.close()

if __name__ == "__main__":
    seed_database()
