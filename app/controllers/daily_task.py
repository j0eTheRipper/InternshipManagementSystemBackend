from typing import Annotated
from datetime import date, timedelta

from fastapi import APIRouter, Depends, Form, HTTPException

from app.dependencies.auth import require_student
from app.models.User import Student, User
from app.models.DailyTask import DailyTask

router = APIRouter(prefix="/daily-task")


@router.post("")
async def submit_daily_task(
    user: Annotated[User, Depends(require_student)],
    update_text: str = Form(...),
):
    student = Student.get_student(user)
    if student.progress != "accepted":
        raise HTTPException(
            400, "Can only submit daily tasks during an active internship"
        )
    if not update_text.strip():
        raise HTTPException(400, "Update text cannot be empty")

    today = date.today()
    start = date.fromisoformat(student.internship_start_date)
    week_number = ((today - start).days // 7) + 1
    week_start = start + timedelta(weeks=week_number - 1)
    week_end = week_start + timedelta(days=6)

    record = DailyTask.submit(
        student.student_id,
        update_text.strip(),
        today.isoformat(),
        week_start.isoformat(),
        week_end.isoformat(),
    )
    if not record:
        raise HTTPException(500, "Failed to submit daily task")

    return {"message": "Daily task submitted", "daily_task_id": record.daily_task_id}


@router.get("/today")
async def get_today_task(user: Annotated[User, Depends(require_student)]):
    student = Student.get_student(user)
    if student.progress != "accepted":
        raise HTTPException(
            400, "Can only view daily tasks during an active internship"
        )
    record = DailyTask.get_by_date(student.student_id, date.today().isoformat())
    if not record:
        return None
    return record.model_dump()


@router.get("/history")
async def get_daily_task_history(user: Annotated[User, Depends(require_student)]):
    student = Student.get_student(user)
    if student.progress != "accepted":
        raise HTTPException(
            400, "Can only view daily tasks during an active internship"
        )
    records = DailyTask.get_history(student.student_id)
    return [r.model_dump() for r in records]
