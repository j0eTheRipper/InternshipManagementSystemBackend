from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException

from app.dependencies.auth import get_current_user, require_student
from app.models.Attendance import Attendance
from app.models.User import Student, User

router = APIRouter(prefix="/attendance")


@router.get("/today")
async def get_today(user: Annotated[User, Depends(get_current_user)]):
    student = Student.get_student(user)
    if student.progress != "accepted":
        return {"checked_in": False}
    existing = Attendance.get_today(student.student_id)
    if existing:
        return {"checked_in": True, "checked_at": existing.checked_at}
    return {"checked_in": False}


@router.post("/check-in")
async def check_in(user: Annotated[User, Depends(require_student)]):
    student = Student.get_student(user)

    if student.progress != "accepted":
        raise HTTPException(400, "Can only check in during an active internship")

    existing = Attendance.get_today(student.student_id)
    if existing:
        return {"message": "Already checked in today", "checked_at": existing.checked_at}

    record = Attendance.record(student.student_id)
    if not record:
        raise HTTPException(500, "Failed to record attendance")

    return {"message": "Checked in", "checked_at": record.checked_at}
