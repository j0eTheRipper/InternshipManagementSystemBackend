import os
from typing import Annotated
from uuid import uuid4

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile
from fastapi.responses import FileResponse

from app.dependencies import database_connector
from app.dependencies.auth import get_current_user, require_headhunter, require_student
from app.models.PartneredCompanies.Application import Application
from app.models.PartneredCompanies.ExternalApplication import ExternalApplication
from app.models.Document.Resume import Resume
from app.models.PartneredCompanies.JobOpportunity import JobOpportunity
from app.models.Notification import Notification
from app.models.User import Student, User

router = APIRouter(prefix="/applications")

ALLOWED_IMAGE_EXTENSIONS = {"png", "jpg", "jpeg", "gif", "webp", "bmp"}
MAX_SCREENSHOT_SIZE = 5 * 1024 * 1024


def _validate_screenshot(file: UploadFile, content: bytes):
    ext = file.filename.rsplit(".", 1)[-1].lower() if file.filename else ""
    if ext not in ALLOWED_IMAGE_EXTENSIONS:
        raise HTTPException(400, f"only image files ({', '.join(sorted(ALLOWED_IMAGE_EXTENSIONS))}) are accepted")
    if len(content) > MAX_SCREENSHOT_SIZE:
        raise HTTPException(413, "file exceeds 5MB limit")


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


@router.post("/external")
async def create_external_application(
    user: Annotated[User, Depends(require_student)],
    company_name: str = Form(...),
    job_title: str = Form(...),
    job_mode: str = Form(...),
    company_location: str = Form(...),
    resume_id: int = Form(...),
    screenshot: UploadFile = File(...),
):
    content = await screenshot.read()
    _validate_screenshot(screenshot, content)

    valid_modes = ["on-site", "remote", "hybrid"]
    if job_mode not in valid_modes:
        raise HTTPException(400, f"job_mode must be one of: {', '.join(valid_modes)}")

    student = Student.get_student(user)

    resume = Resume.get_by_id(resume_id)
    if not resume:
        raise HTTPException(404, "Resume not found")
    if resume.student_id != student.student_id:
        raise HTTPException(403, "You can only apply with your own resume")

    if ExternalApplication.exists(student.student_id, company_name, job_title):
        raise HTTPException(409, "You have already applied to this company for this role")

    ext = os.path.splitext(screenshot.filename)[1] if screenshot.filename else ".png"
    screenshot_filename = f"{student.student_id}_{uuid4().hex}{ext}"
    screenshot_dir = "uploads/applications/screenshots"
    os.makedirs(screenshot_dir, exist_ok=True)
    screenshot_path = os.path.join(screenshot_dir, screenshot_filename)
    with open(screenshot_path, "wb") as f:
        f.write(content)
    screenshot_abspath = os.path.abspath(screenshot_path)

    application = Application.create_external(student.student_id, resume_id)

    try:
        ExternalApplication.create(
            application_id=application.application_id,
            company_name=company_name,
            job_title=job_title,
            job_mode=job_mode,
            company_location=company_location,
            application_screenshot=screenshot_abspath,
        )
    except Exception:
        os.remove(screenshot_abspath)
        raise

    student.update_student_progress(student.student_id)

    mentor = student.university_mentor
    Notification.create_notification(
        user_id=mentor.user_id,
        message=f"Student {student.user.fullname} has recorded an external application at {company_name} for {job_title}",
        type="external_application",
        related_id=application.application_id,
    )

    return {
        "application_id": application.application_id,
        "student_id": application.student_id,
        "opportunity_id": None,
        "resume_id": application.resume_id,
        "status": application.status,
        "is_external": True,
        "company_name": company_name,
        "job_title": job_title,
        "job_mode": job_mode,
        "company_location": company_location,
        "application_screenshot": screenshot_abspath,
    }


@router.get("/my")
async def my_applications(user: Annotated[User, Depends(require_student)]):
    student = Student.get_student(user)
    connection = database_connector.create_connection(False)
    rows = database_connector.execute_read(
        connection,
        f"SELECT a.application_id, a.student_id, a.opportunity_id, a.resume_id, a.status, "
        f"ea.application_id IS NOT NULL AS is_external, "
        f"ea.company_name, ea.job_title, ea.job_mode, ea.company_location, ea.application_screenshot "
        f"FROM application a "
        f"LEFT JOIN external_application ea ON a.application_id = ea.application_id "
        f"WHERE a.student_id = '{student.student_id}' "
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


@router.get("/{application_id}")
async def get_application(
    application_id: int,
    user: Annotated[User, Depends(get_current_user)],
):
    application = Application.get_by_id(application_id)
    if not application:
        raise HTTPException(404, "Application not found")

    if user.role.name == "student":
        student = Student.get_student(user)
        if application.student_id != student.student_id:
            raise HTTPException(403, "You can only view your own applications")

    external = ExternalApplication.get_by_application_id(application_id)

    result = {
        "application_id": application.application_id,
        "student_id": application.student_id,
        "opportunity_id": application.opportunity_id,
        "resume_id": application.resume_id,
        "status": application.status,
        "is_external": external is not None,
    }

    if external:
        result.update({
            "company_name": external.company_name,
            "job_title": external.job_title,
            "job_mode": external.job_mode,
            "company_location": external.company_location,
            "application_screenshot": external.application_screenshot,
        })

    return result


@router.get("/{application_id}/screenshot")
async def download_screenshot(
    application_id: int,
    user: Annotated[User, Depends(get_current_user)],
):
    application = Application.get_by_id(application_id)
    if not application:
        raise HTTPException(404, "Application not found")

    if user.role.name == "student":
        student = Student.get_student(user)
        if application.student_id != student.student_id:
            raise HTTPException(403, "You can only download screenshots of your own applications")

    external = ExternalApplication.get_by_application_id(application_id)
    if not external:
        raise HTTPException(404, "Application is not an external application")

    ext = os.path.splitext(external.application_screenshot)[1] or ".png"
    return FileResponse(
        external.application_screenshot,
        filename=f"screenshot_{application_id}{ext}",
    )


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
