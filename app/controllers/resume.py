from typing import Annotated, Optional

from fastapi import APIRouter, Depends, HTTPException, UploadFile
from fastapi.responses import FileResponse

from app.dependencies.auth import get_current_user, require_mentor, require_student
from app.models.Document.Resume import Resume
from app.models.Notification import Notification
from app.models.Role import Role
from app.models.User import Student, User

router = APIRouter(prefix="/resume")


def __file_not_pdf(file):
    ext = file.filename.rsplit(".", 1)[-1].lower() if file.filename else ""
    if ext != "pdf":
        raise HTTPException(400, "only PDF files are accepted")


def __file_too_big(content, limit_mb=5):
    if len(content) > limit_mb * 1024 * 1024:
        raise HTTPException(413, "file exceeds 5MB limit")


def __file_wrong_type(file, type="pdf"):
    if file.content_type != "application/pdf":
        raise HTTPException(400, "only PDF files are accepted")


@router.post("/upload")
async def upload_resume(
    file: UploadFile,
    user: Annotated[User, Depends(require_student)],
):
    __file_wrong_type(file)
    __file_not_pdf(file)
    content = await file.read()
    __file_too_big(content)

    student = Student.get_student(user)
    path_to_resume = Resume.upload_in_storage(
        student.student_id, file.filename, content
    )
    resume_id = Resume.save_in_db(student.student_id, path_to_resume)

    mentor = student.university_mentor
    Notification.create_notification(
        user_id=mentor.user_id,
        message=f"Student {student.user.fullname} has uploaded their resume",
        type="resume_uploaded",
        related_id=resume_id,
    )

    return {"file_path": path_to_resume, "resume_id": resume_id}


@router.get("/")
async def get_resume(
    user: Annotated[User, Depends(get_current_user)],
    request_student_id: Optional[str] = None,
):
    student_id = None

    if user.role == Role.student:
        student = Student.get_student(user)
        student_id = student.student_id

        user_is_not_requested_student = student_id != request_student_id

        if request_student_id is not None and user_is_not_requested_student:
            raise HTTPException(403, "students cannot look up other students")
    elif user.role == Role.universityMentor:
        if not request_student_id:
            raise HTTPException(422, "student_id is required for mentors")
        student_id = request_student_id

    return Resume.get_by_student(student_id)


@router.get("/download/{resume_id}")
async def download_resume(
    resume_id: int,
    user: Annotated[User, Depends(get_current_user)],
):
    resume = Resume.get_by_id(resume_id)
    if not resume:
        raise HTTPException(404, "resume not found")

    if user.role == Role.student:
        student = Student.get_student(user)
        if student.student_id != resume.student_id:
            raise HTTPException(403, "you can only download your own resume")

    return FileResponse(
        resume.file,
        media_type="application/pdf",
        filename=f"resume_{resume_id}.pdf",
    )


@router.patch("/{resume_id}/approve")
async def approve_resume(
    resume_id: int,
    user: Annotated[User, Depends(require_mentor)],
):
    resume = Resume.get_by_id(resume_id)
    if not resume:
        raise HTTPException(404, "resume not found")
    Resume.approve(resume_id)

    student = Student.get_student_by_id(resume.student_id)
    student.update_student_progress(resume.student_id)
    Notification.create_notification(
        user_id=student.user.user_id,
        message=f"Your mentor {user.fullname} has approved your resume",
        type="resume_approved",
        related_id=resume_id,
    )

    return {"message": "Resume approved", "resume_id": resume_id}
