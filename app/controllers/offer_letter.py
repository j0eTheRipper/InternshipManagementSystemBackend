import os
from typing import Annotated

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile
from fastapi.responses import FileResponse

from app.dependencies.auth import get_current_user, require_mentor, require_student
from app.models.PartneredCompanies.Application import Application
from app.models.Document.OfferLetter import OfferLetter
from app.models.Notification import Notification
from app.models.Role import Role
from app.models.User import Student, User

router = APIRouter(prefix="/offer-letter")

ALLOWED_EXTENSIONS = {"pdf", "png", "jpg", "jpeg"}
MAX_FILE_SIZE = 5 * 1024 * 1024


def _validate_file(file: UploadFile, content: bytes):
    ext = file.filename.rsplit(".", 1)[-1].lower() if file.filename else ""
    if ext not in ALLOWED_EXTENSIONS:
        raise HTTPException(400, f"only {', '.join(sorted(ALLOWED_EXTENSIONS))} files are accepted")
    if len(content) > MAX_FILE_SIZE:
        raise HTTPException(413, "file exceeds 5MB limit")


@router.post("/upload")
async def upload_offer_letter(
    user: Annotated[User, Depends(require_student)],
    application_id: int = Form(...),
    file: UploadFile = File(...),
):
    content = await file.read()
    _validate_file(file, content)

    student = Student.get_student(user)

    application = Application.get_by_id(application_id)
    if not application:
        raise HTTPException(404, "Application not found")
    if application.student_id != student.student_id:
        raise HTTPException(403, "You can only upload offer letters for your own applications")
    if application.status != "pending":
        raise HTTPException(400, "Can only upload offer letter for pending applications")

    file_path = OfferLetter.upload_in_storage(student.student_id, file.filename, content)

    try:
        offer_letter_id = OfferLetter.save_in_db(application_id, student.student_id, file_path)

        Application.update_status(application_id, "uploaded")

        student.update_student_progress(student.student_id, "offer_letter")

        mentor = student.university_mentor
        Notification.create_notification(
            user_id=mentor.user_id,
            message=f"Student {student.user.fullname} has uploaded an offer letter for review",
            type="offer_letter_uploaded",
            related_id=offer_letter_id,
        )
    except Exception:
        os.remove(file_path)
        raise

    return {"offer_letter_id": offer_letter_id, "file_path": file_path}


@router.get("/download/{offer_letter_id}")
async def download_offer_letter(
    offer_letter_id: int,
    user: Annotated[User, Depends(get_current_user)],
):
    offer_letter = OfferLetter.get_by_id(offer_letter_id)
    if not offer_letter:
        raise HTTPException(404, "Offer letter not found")

    if user.role == Role.student:
        student = Student.get_student(user)
        if student.student_id != offer_letter.student_id:
            raise HTTPException(403, "You can only download your own offer letters")
    elif user.role == Role.universityMentor:
        student = Student.get_student_by_id(offer_letter.student_id)
        if student.university_mentor.user_id != user.user_id:
            raise HTTPException(403, "You can only download offer letters of your supervisees")

    return FileResponse(
        offer_letter.file,
        filename=f"offer_letter_{offer_letter_id}.pdf",
    )


@router.get("/by-application/{application_id}")
async def get_offer_letter_by_application(
    application_id: int,
    user: Annotated[User, Depends(get_current_user)],
):
    student = Student.get_student(user)
    application = Application.get_by_id(application_id)
    if not application or application.student_id != student.student_id:
        raise HTTPException(404, "Offer letter not found")
    docs = OfferLetter.get_by_student(student.student_id)
    for doc in docs:
        if doc.application_id == application_id:
            return doc
    raise HTTPException(404, "Offer letter not found")


@router.get("/pending")
async def get_pending_offer_letters(
    user: Annotated[User, Depends(require_mentor)],
):
    return OfferLetter.get_pending_by_mentor(user.user_id)


@router.patch("/{offer_letter_id}/approve")
async def approve_offer_letter(
    offer_letter_id: int,
    user: Annotated[User, Depends(require_mentor)],
):
    offer_letter = OfferLetter.get_by_id(offer_letter_id)
    if not offer_letter:
        raise HTTPException(404, "Offer letter not found")

    student = Student.get_student_by_id(offer_letter.student_id)
    if student.university_mentor.user_id != user.user_id:
        raise HTTPException(403, "You can only approve offer letters of your supervisees")

    OfferLetter.approve(offer_letter_id)

    application = Application.get_by_id(offer_letter.application_id)
    if application:
        Application.update_status(offer_letter.application_id, "accepted")

    student.update_student_progress(offer_letter.student_id, "accepted")

    Notification.create_notification(
        user_id=student.user.user_id,
        message=f"Your mentor {user.fullname} has approved your offer letter",
        type="offer_letter_approved",
        related_id=offer_letter_id,
    )

    return {"message": "Offer letter approved"}


@router.patch("/{offer_letter_id}/reject")
async def reject_offer_letter(
    offer_letter_id: int,
    user: Annotated[User, Depends(require_mentor)],
):
    offer_letter = OfferLetter.get_by_id(offer_letter_id)
    if not offer_letter:
        raise HTTPException(404, "Offer letter not found")

    student = Student.get_student_by_id(offer_letter.student_id)
    if student.university_mentor.user_id != user.user_id:
        raise HTTPException(403, "You can only reject offer letters of your supervisees")

    application = Application.get_by_id(offer_letter.application_id)
    if application:
        Application.update_status(offer_letter.application_id, "rejected")

    Notification.create_notification(
        user_id=student.user.user_id,
        message=f"Your mentor {user.fullname} has rejected your offer letter",
        type="offer_letter_rejected",
        related_id=offer_letter_id,
    )

    return {"message": "Offer letter rejected"}
