from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException

from app.dependencies.auth import require_company_supervisor
from app.models.Attendance import Attendance
from app.models.DailyTask import DailyTask
from app.models.PartneredCompanies.CompanySupervisor.CompanySupervisor import CompanySupervisor
from app.models.User import Student, User

router = APIRouter(prefix="/company-supervisor")


@router.get("/profile")
async def get_profile(user: Annotated[User, Depends(require_company_supervisor)]):
    supervisor = CompanySupervisor.get_company_supervisor(user)
    return supervisor.model_dump(mode="json")


@router.get("/students")
async def get_students(user: Annotated[User, Depends(require_company_supervisor)]):
    supervisor = CompanySupervisor.get_company_supervisor(user)
    students = Student.get_students_by_company_supervisor(supervisor.user.user_id)

    result = []
    for student in students:
        attendance_records = Attendance.get_history(student.student_id)
        work_logs = DailyTask.get_history(student.student_id)

        total_attendance = len(attendance_records)
        verified_attendance = sum(1 for r in attendance_records if r.verified)
        total_work_logs = len(work_logs)
        verified_work_logs = sum(1 for r in work_logs if r.verified)

        student_data = student.model_dump(mode="json")
        student_data["attendance_summary"] = {
            "total": total_attendance,
            "verified": verified_attendance,
        }
        student_data["work_logs_summary"] = {
            "total": total_work_logs,
            "verified": verified_work_logs,
        }
        result.append(student_data)

    return result


@router.get("/students/{student_id}/attendance")
async def get_student_attendance(student_id: str, user: Annotated[User, Depends(require_company_supervisor)]):
    supervisor = CompanySupervisor.get_company_supervisor(user)
    student = Student.get_student_by_id(student_id)

    assigned_students = Student.get_students_by_company_supervisor(supervisor.user.user_id)
    assigned_ids = [s.student_id for s in assigned_students]
    if student_id not in assigned_ids:
        raise HTTPException(403, "This student is not assigned to you")

    records = Attendance.get_history(student_id)
    return [r.model_dump(mode="json") for r in records]


@router.get("/students/{student_id}/work-logs")
async def get_student_work_logs(student_id: str, user: Annotated[User, Depends(require_company_supervisor)]):
    supervisor = CompanySupervisor.get_company_supervisor(user)

    assigned_students = Student.get_students_by_company_supervisor(supervisor.user.user_id)
    assigned_ids = [s.student_id for s in assigned_students]
    if student_id not in assigned_ids:
        raise HTTPException(403, "This student is not assigned to you")

    records = DailyTask.get_history(student_id)
    return [r.model_dump(mode="json") for r in records]


@router.patch("/attendance/{attendance_id}/verify")
async def verify_attendance(attendance_id: int, user: Annotated[User, Depends(require_company_supervisor)]):
    supervisor = CompanySupervisor.get_company_supervisor(user)
    Attendance.verify(attendance_id, supervisor.user.user_id)
    return {"message": "Attendance verified"}


@router.patch("/attendance/{attendance_id}/unverify")
async def unverify_attendance(attendance_id: int, user: Annotated[User, Depends(require_company_supervisor)]):
    Attendance.unverify(attendance_id)
    return {"message": "Attendance unverified"}


@router.patch("/work-logs/{daily_task_id}/verify")
async def verify_work_log(daily_task_id: int, user: Annotated[User, Depends(require_company_supervisor)]):
    supervisor = CompanySupervisor.get_company_supervisor(user)
    DailyTask.verify(daily_task_id, supervisor.user.user_id)
    return {"message": "Work log verified"}


@router.patch("/work-logs/{daily_task_id}/unverify")
async def unverify_work_log(daily_task_id: int, user: Annotated[User, Depends(require_company_supervisor)]):
    DailyTask.unverify(daily_task_id)
    return {"message": "Work log unverified"}
