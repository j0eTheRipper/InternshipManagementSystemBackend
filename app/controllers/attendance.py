from typing import Annotated
from datetime import date, datetime, timedelta, timezone

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


@router.get("/history")
async def get_history(user: Annotated[User, Depends(require_student)]):
    student = Student.get_student(user)
    if student.progress != "accepted":
        raise HTTPException(400, "Can only view attendance during an active internship")
    if not student.internship_start_date or not student.internship_duration_weeks:
        return []

    records = Attendance.get_history(student.student_id)
    attended_map = {}
    for r in records:
        if r.checked_at:
            dt_utc = datetime.fromisoformat(r.checked_at[:19].replace(' ', 'T')).replace(tzinfo=timezone.utc)
            day = dt_utc.astimezone().strftime('%Y-%m-%d')
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
