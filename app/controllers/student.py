from typing import Annotated

from fastapi import APIRouter, Depends, Form, HTTPException

from app.dependencies.auth import get_current_user, require_mentor, require_student
from app.dependencies.dbExceptions import NotStudent
from app.dependencies import database_connector
from app.models.PartneredCompanies.Application import Application
from app.models.PartneredCompanies.ExternalApplication import ExternalApplication
from app.models.PartneredCompanies.Headhunter.Headhunter import Headhunter
from app.models.PartneredCompanies.JobOpportunity import JobOpportunity
from app.models.User import Student, User


router = APIRouter()


@router.get("/student")
async def get_student(user: Annotated[User, Depends(get_current_user)]):
    try:
        return Student.get_student(user)
    except NotStudent:
        return {"Error": "No such student"}


@router.get("/students")
async def get_mentor_students(user: Annotated[User, Depends(require_mentor)]):
    return Student.get_students_by_mentor(user.user_id)


@router.get("/student/accepted-company")
async def get_my_accepted_company(user: Annotated[User, Depends(get_current_user)]):
    student = Student.get_student(user)
    return await _lookup_accepted_company(student.student_id)


@router.get("/students/{student_id}/accepted-company")
async def get_student_accepted_company(
    student_id: str,
    user: Annotated[User, Depends(require_mentor)],
):
    student = Student.get_student_by_id(student_id)
    if not student:
        raise HTTPException(404, "Student not found")
    if student.university_mentor.user_id != user.user_id:
        raise HTTPException(403, "You can only view your supervisees")
    return await _lookup_accepted_company(student_id)


@router.get("/students/{student_id}/applications")
async def get_student_applications(
    student_id: str,
    user: Annotated[User, Depends(require_mentor)],
):
    student = Student.get_student_by_id(student_id)
    if not student:
        raise HTTPException(404, "Student not found")
    if student.university_mentor.user_id != user.user_id:
        raise HTTPException(403, "You can only view your supervisees")

    connection = database_connector.create_connection(False)
    rows = database_connector.execute_read(
        connection,
        f"SELECT a.application_id, a.student_id, a.opportunity_id, a.resume_id, a.status, "
        f"ea.application_id IS NOT NULL AS is_external, "
        f"ea.company_name, ea.job_title, ea.job_mode, ea.company_location, ea.application_screenshot "
        f"FROM application a "
        f"LEFT JOIN external_application ea ON a.application_id = ea.application_id "
        f"WHERE a.student_id = '{student_id}' "
        f"ORDER BY a.application_id DESC;",
    )
    return [
        {
            "application_id": r[0],
            "student_id": r[1],
            "opportunity_id": r[2],
            "resume_id": r[3],
            "status": r[4],
            "is_external": r[5],
            "company_name": r[6],
            "job_title": r[7],
            "job_mode": r[8],
            "company_location": r[9],
            "application_screenshot": r[10],
        }
        for r in rows
    ]


async def _lookup_accepted_company(student_id: str):
    applications = Application.get_by_student(student_id)
    accepted = [a for a in applications if a.status == "accepted"]
    if not accepted:
        return {"company": None}

    app = accepted[0]

    if app.opportunity_id is not None:
        opportunity = JobOpportunity.get_by_id(app.opportunity_id)
        if not opportunity:
            return {"company": None}
        headhunter = Headhunter.get_headhunter(User.getUserData(opportunity.headhunter_id))
        return {"company": headhunter.company.name}

    external = ExternalApplication.get_by_application_id(app.application_id)
    if external:
        return {"company": external.company_name}

    return {"company": None}


@router.patch("/student/internship-details")
async def update_internship_details(
    user: Annotated[User, Depends(require_student)],
    start_date: str = Form(...),
    duration_weeks: int = Form(...),
):
    student = Student.get_student(user)
    if student.progress not in ("accepted", "pending_documents"):
        raise HTTPException(400, "Can only set internship details after offer letter is approved")
    Student.update_internship_dates(student.student_id, start_date, duration_weeks)
    return {"message": "Internship details updated"}


@router.patch("/student/supervisor-details")
async def update_supervisor_details(
    user: Annotated[User, Depends(require_student)],
    name: str = Form(...),
    email: str = Form(...),
    phone: str = Form(...),
):
    student = Student.get_student(user)
    if student.progress != "pending_documents":
        raise HTTPException(400, "Can only submit supervisor details during pending documents phase")
    Student.update_supervisor_details(student.student_id, name, email, phone)
    return {"message": "Supervisor details updated"}
