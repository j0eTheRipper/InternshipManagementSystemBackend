from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException

from ..dependencies.auth import require_headhunter, require_student
from ..models.Application import Application
from ..models.JobOpportunity import JobOpportunity
from ..models.Notification import Notification
from app.models.Document.Resume import Resume
from ..models.User import Student, User


router = APIRouter(prefix="/applications")


@router.post("")
async def apply(
    body: dict,
    user: Annotated[User, Depends(require_student)],
):
    opportunity_id = body.get("opportunity_id")
    resume_id = body.get("resume_id")

    if not opportunity_id or not resume_id:
        raise HTTPException(400, "opportunity_id and resume_id are required")

    opportunity = JobOpportunity.get_by_id(opportunity_id)
    if not opportunity:
        raise HTTPException(404, "Opportunity not found")

    resume = Resume.get_by_id(resume_id)
    if not resume:
        raise HTTPException(404, "Resume not found")

    student = Student.get_student(user)
    if resume.student_id != student.student_id:
        raise HTTPException(403, "You can only apply with your own resume")

    application = Application.create(student.student_id, opportunity_id, resume_id)
    student.update_student_progress(student.student_id)

    Notification.create_notification(
        user_id=opportunity.headhunter_id,
        message=f"New application from {user.fullname} for {opportunity.title}",
        type="new_application",
        related_id=application.application_id,
    )

    return application


@router.get("/my")
async def my_applications(user: Annotated[User, Depends(require_student)]):
    student = Student.get_student(user)
    return Application.get_by_student(student.student_id)


@router.get("/opportunity/{opportunity_id}")
async def get_applicants(
    opportunity_id: int,
    user: Annotated[User, Depends(require_headhunter)],
):
    opportunity = JobOpportunity.get_by_id(opportunity_id)
    if not opportunity:
        raise HTTPException(404, "Opportunity not found")
    if opportunity.headhunter_id != user.user_id:
        raise HTTPException(
            403, "You can only view applicants for your own opportunities"
        )

    return Application.get_by_opportunity(opportunity_id)


@router.patch("/{application_id}/status")
async def update_application_status(
    application_id: int,
    body: dict,
    user: Annotated[User, Depends(require_headhunter)],
):
    application = Application.get_by_id(application_id)
    if not application:
        raise HTTPException(404, "Application not found")

    opportunity = JobOpportunity.get_by_id(application.opportunity_id)
    if opportunity.headhunter_id != user.user_id:
        raise HTTPException(
            403, "You can only update applications for your own opportunities"
        )

    new_status = body.get("status")
    valid_statuses = ["pending", "interview", "accepted", "rejected"]
    if new_status not in valid_statuses:
        raise HTTPException(400, f"status must be one of: {', '.join(valid_statuses)}")

    Application.update_status(application_id, new_status)

    Notification.create_notification(
        user_id=Student.get_student_by_id(application.student_id).user.user_id,
        message=f"Your application for {opportunity.title} has been {new_status}",
        type="application_status",
        related_id=application_id,
    )

    return {"message": f"Application {new_status}", "application_id": application_id}


@router.patch("/{application_id}/accept")
async def accept_application(
    application_id: int,
    user: Annotated[User, Depends(require_headhunter)],
):
    application = Application.get_by_id(application_id)
    if not application:
        raise HTTPException(404, "Application not found")

    opportunity = JobOpportunity.get_by_id(application.opportunity_id)
    if opportunity.headhunter_id != user.user_id:
        raise HTTPException(
            403, "You can only accept applications for your own opportunities"
        )

    if application.status not in ("pending", "interview"):
        raise HTTPException(400, "Can only accept pending or interview applications")

    Application.update_status(application_id, "accepted")

    student = Student.get_student_by_id(application.student_id)
    student.update_student_progress(student.student_id)

    Notification.create_notification(
        user_id=student.user.user_id,
        message=f"Congratulations! Your application for {opportunity.title} has been accepted!",
        type="application_accepted",
        related_id=application_id,
    )

    return {"message": "Application accepted", "application_id": application_id}
