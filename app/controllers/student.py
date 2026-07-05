from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException

from app.dependencies.auth import get_current_user, require_mentor
from app.dependencies.dbExceptions import NotStudent
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
