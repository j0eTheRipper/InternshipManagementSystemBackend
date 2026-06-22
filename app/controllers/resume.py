from fastapi import APIRouter, UploadFile

from ..models.Resume import Resume


router = APIRouter(prefix="/resume")


@router.post("/upload")
async def upload_resume(file: UploadFile):
    path_to_resume = Resume.upload_resume_in_storage("newResume.pdf", await file.read())
    Resume.save_resume_in_db("TP076844", str(path_to_resume))
    return {"new-file": path_to_resume}
