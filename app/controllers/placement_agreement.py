import os
from typing import Annotated

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile
from fastapi.responses import FileResponse

from app.dependencies.auth import get_current_user, require_mentor, require_student
from app.models.Document.IndemnityLetter import IndemnityLetter
from app.models.Document.PlacementAgreement import PlacementAgreement
from app.models.Notification import Notification
from app.models.Role import Role
from app.models.User import Student, User

router = APIRouter(prefix="/placement-agreement")

ALLOWED_EXTENSIONS = {"pdf"}
MAX_FILE_SIZE = 5 * 1024 * 1024


def _validate_file(file: UploadFile, content: bytes):
    ext = file.filename.rsplit(".", 1)[-1].lower() if file.filename else ""
    if ext not in ALLOWED_EXTENSIONS:
        raise HTTPException(400, "only PDF files are accepted")
    if file.content_type != "application/pdf":
        raise HTTPException(400, "only PDF files are accepted")
    if len(content) > MAX_FILE_SIZE:
        raise HTTPException(413, "file exceeds 5MB limit")


def _check_and_transition(student_id: str):
    indemnity = IndemnityLetter.get_by_student(student_id)
    placement = PlacementAgreement.get_by_student(student_id)
    if not (indemnity and indemnity[0].verified and placement and placement[0].verified):
        return

    student = Student.get_student_by_id(student_id)
    if not student.company_supervisor_email:
        return

    supervisor_user = User.get_by_email(student.company_supervisor_email)
    if not supervisor_user:
        return

    Student.update_student_progress(student_id, "accepted")


@router.post("/upload")
async def upload_placement_agreement(
    user: Annotated[User, Depends(require_student)],
    file: UploadFile = File(...),
):
    content = await file.read()
    _validate_file(file, content)

    student = Student.get_student(user)

    PlacementAgreement.delete_by_student(student.student_id)

    file_path = PlacementAgreement.upload_in_storage(student.student_id, file.filename, content)

    try:
        placement_agreement_id = PlacementAgreement.save_in_db(student.student_id, file_path)

        mentor = student.university_mentor
        Notification.create_notification(
            user_id=mentor.user_id,
            message=f"Student {student.user.fullname} has uploaded a placement agreement for review",
            type="placement_agreement_uploaded",
            related_id=placement_agreement_id,
        )
    except Exception:
        os.remove(file_path)
        raise

    return {"placement_agreement_id": placement_agreement_id, "file_path": file_path}


@router.get("/download/{placement_agreement_id}")
async def download_placement_agreement(
    placement_agreement_id: int,
    user: Annotated[User, Depends(get_current_user)],
):
    doc = PlacementAgreement.get_by_id(placement_agreement_id)
    if not doc:
        raise HTTPException(404, "Placement agreement not found")

    if user.role == Role.student:
        student = Student.get_student(user)
        if student.student_id != doc.student_id:
            raise HTTPException(403, "You can only download your own documents")
    elif user.role == Role.universityMentor:
        student = Student.get_student_by_id(doc.student_id)
        if student.university_mentor.user_id != user.user_id:
            raise HTTPException(403, "You can only download documents of your supervisees")

    if not os.path.exists(doc.file):
        raise HTTPException(404, "File not found on disk")

    return FileResponse(
        doc.file,
        media_type="application/pdf",
        filename=f"placement_agreement_{placement_agreement_id}.pdf",
    )


@router.get("/student/{student_id}")
async def get_student_placement_agreement(
    student_id: str,
    user: Annotated[User, Depends(get_current_user)],
):
    if user.role == Role.student:
        student = Student.get_student(user)
        if student.student_id != student_id:
            raise HTTPException(403, "You can only view your own documents")
    elif user.role == Role.universityMentor:
        student = Student.get_student_by_id(student_id)
        if student.university_mentor.user_id != user.user_id:
            raise HTTPException(403, "You can only view documents of your supervisees")

    docs = PlacementAgreement.get_by_student(student_id)
    return docs[0] if docs else None


@router.get("/pending")
async def get_pending_placement_agreements(
    user: Annotated[User, Depends(require_mentor)],
):
    return PlacementAgreement.get_pending_by_mentor(user.user_id)


@router.patch("/{placement_agreement_id}/approve")
async def approve_placement_agreement(
    placement_agreement_id: int,
    user: Annotated[User, Depends(require_mentor)],
):
    doc = PlacementAgreement.get_by_id(placement_agreement_id)
    if not doc:
        raise HTTPException(404, "Placement agreement not found")

    student = Student.get_student_by_id(doc.student_id)
    if student.university_mentor.user_id != user.user_id:
        raise HTTPException(403, "You can only approve documents of your supervisees")

    PlacementAgreement.approve(placement_agreement_id)

    _check_and_transition(doc.student_id)

    Notification.create_notification(
        user_id=student.user.user_id,
        message=f"Your mentor {user.fullname} has approved your placement agreement",
        type="placement_agreement_approved",
        related_id=placement_agreement_id,
    )

    return {"message": "Placement agreement approved"}
