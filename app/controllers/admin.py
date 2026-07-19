from typing import Annotated
from datetime import date, timedelta

from fastapi import APIRouter, Depends, HTTPException

from app.dependencies.auth import require_admin
from app.models.Attendance import Attendance
from app.models.Mentor.Mentor import Mentor
from app.models.PartneredCompanies.CompanySupervisor.CompanySupervisor import CompanySupervisor
from app.models.Requests.AddAttendanceRequest import AddAttendanceRequest
from app.models.Requests.CreateCompanySupervisorRequest import CreateCompanySupervisorRequest, \
    AssignCompanySupervisorRequest
from app.models.Requests.CreateMentorRequest import CreateMentorRequest
from app.models.Requests.CreateStudentRequest import CreateStudentRequest
from app.models.Requests.UpdateMentorRequest import UpdateMentorRequest
from app.models.Requests.UpdateProgressRequest import UpdateProgressRequest
from app.models.Role import Role
from app.models.User import Student, User

router = APIRouter(prefix="/admin")


# ── Students ──────────────────────────────────────────────


@router.post("/students")
async def create_student(body: CreateStudentRequest, user: Annotated[User, Depends(require_admin)]):
    if User.get_by_email(body.email):
        raise HTTPException(409, "Email already registered")

    if Student.get_by_student_id(body.student_id):
        raise HTTPException(409, "Student ID already exists")

    mentor = User.getUserData(body.mentor_id)
    if mentor.role != Role.universityMentor:
        raise HTTPException(400, "Assigned mentor must be a university mentor")

    Student.create(
        fullname=body.fullname,
        email=body.email,
        password=body.password,
        student_id=body.student_id,
        year_of_study=body.year_of_study,
        field_of_study=body.field_of_study,
        mentor_id=body.mentor_id,
    )
    return {"message": "Student created"}


@router.get("/students")
async def list_students(user: Annotated[User, Depends(require_admin)]):
    return [s.model_dump(mode="json") for s in Student.get_all_students()]


@router.get("/students/{student_id}")
async def get_student(student_id: str, user: Annotated[User, Depends(require_admin)]):
    return Student.get_student_by_id(student_id).model_dump(mode="json")


@router.patch("/students/{student_id}/progress")
async def update_progress(student_id: str, body: UpdateProgressRequest, user: Annotated[User, Depends(require_admin)]):
    valid = {"none", "resume", "application", "offer_letter", "pending_documents", "accepted"}
    if body.progress not in valid:
        raise HTTPException(400, f"Progress must be one of: {', '.join(sorted(valid))}")
    Student.update_student_progress(student_id, body.progress)
    return {"message": "Progress updated"}


@router.patch("/students/{student_id}/mentor")
async def update_mentor(student_id: str, body: UpdateMentorRequest, user: Annotated[User, Depends(require_admin)]):
    mentor = User.getUserData(body.mentor_id)
    if mentor.role != Role.universityMentor:
        raise HTTPException(400, "Assigned mentor must be a university mentor")
    Student.update_mentor(student_id, body.mentor_id)
    return {"message": "Mentor updated"}


# ── Mentors ───────────────────────────────────────────────


@router.post("/mentors")
async def create_mentor(body: CreateMentorRequest, user: Annotated[User, Depends(require_admin)]):
    mentor = Mentor.create(
        fullname=body.fullname,
        email=body.email,
        password=body.password,
    )
    return {"message": "Mentor created", "mentor": mentor.user.model_dump(mode="json")}


@router.get("/mentors")
async def list_mentors(user: Annotated[User, Depends(require_admin)]):
    return [m.user.model_dump(mode="json") for m in Mentor.get_all()]


# ── Attendance ────────────────────────────────────────────


@router.post("/attendance")
async def add_attendance(body: AddAttendanceRequest, user: Annotated[User, Depends(require_admin)]):
    student = Student.get_student_by_id(body.student_id)
    record = Attendance.record_with_date(body.student_id, body.date)
    if not record:
        raise HTTPException(500, "Failed to add attendance record")
    return {"message": "Attendance added", "attendance": record.model_dump(mode="json")}


@router.delete("/attendance/{attendance_id}")
async def delete_attendance(attendance_id: int, user: Annotated[User, Depends(require_admin)]):
    Attendance.delete(attendance_id)
    return {"message": "Attendance deleted"}


@router.get("/attendance/{student_id}")
async def get_student_attendance(student_id: str, user: Annotated[User, Depends(require_admin)]):
    student = Student.get_student_by_id(student_id)

    if not student.internship_start_date or not student.internship_duration_weeks:
        return []

    records = Attendance.get_history(student_id)
    attended_map = {}
    for r in records:
        if r.checked_at:
            day = r.checked_at[:10]
            attended_map[day] = r

    start = date.fromisoformat(student.internship_start_date)
    end_of_internship = start + timedelta(weeks=student.internship_duration_weeks)
    today = date.today()
    range_end = min(end_of_internship, today)

    if start > today:
        return []

    result = []
    current = start
    while current <= range_end:
        if current.weekday() < 5:
            d_str = current.isoformat()
            if d_str in attended_map:
                r = attended_map[d_str]
                result.append({
                    "date": d_str,
                    "attended": True,
                    "pending": False,
                    "attendance_id": r.attendance_id,
                    "checked_at": r.checked_at,
                    "verified": r.verified,
                    "verified_at": r.verified_at,
                })
            elif current == today:
                result.append({
                    "date": d_str,
                    "attended": False,
                    "pending": True,
                    "attendance_id": None,
                    "checked_at": None,
                })
            else:
                result.append({
                    "date": d_str,
                    "attended": False,
                    "pending": False,
                    "attendance_id": None,
                    "checked_at": None,
                })
        current += timedelta(days=1)

    result.sort(key=lambda x: x["date"], reverse=True)
    return result


# ── Company Supervisors ──────────────────────────────────


@router.post("/company-supervisors")
async def create_company_supervisor(body: CreateCompanySupervisorRequest, user: Annotated[User, Depends(require_admin)]):
    if User.get_by_email(body.email):
        raise HTTPException(409, "Email already registered")

    from app.models.PartneredCompanies.Company import Company
    company = Company.get_by_id(body.company_id)
    if not company:
        raise HTTPException(400, "Company not found")

    created_user = User.create(body.fullname, body.email, body.password, Role.companySupervisor)
    CompanySupervisor.create(created_user.user_id, body.company_id)
    return {"message": "Company supervisor created"}


@router.get("/company-supervisors")
async def list_company_supervisors(user: Annotated[User, Depends(require_admin)]):
    supervisors = CompanySupervisor.get_all()
    return [s.model_dump(mode="json") for s in supervisors]


@router.delete("/company-supervisors/{supervisor_id}")
async def delete_company_supervisor(supervisor_id: int, user: Annotated[User, Depends(require_admin)]):
    CompanySupervisor.delete(supervisor_id)
    return {"message": "Company supervisor deleted"}


@router.patch("/students/{student_id}/company-supervisor")
async def assign_company_supervisor(student_id: str, body: AssignCompanySupervisorRequest, user: Annotated[User, Depends(require_admin)]):
    supervisor = CompanySupervisor.get_by_id(body.company_supervisor_id)
    if not supervisor:
        raise HTTPException(400, "Company supervisor not found")
    Student.update_company_supervisor(student_id, body.company_supervisor_id)
    return {"message": "Company supervisor assigned"}
