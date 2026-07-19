from fastapi import FastAPI
from fastapi.responses import RedirectResponse
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv
import os

from app.controllers.login import router as login_router
from app.controllers.student import router as student_router
from app.controllers.resume import router as resume_router
from app.controllers.notification import router as notification_router
from app.controllers.headhunter import router as headhunter_router
from app.controllers.opportunity import router as opportunity_router
from app.controllers.application import router as application_router
from app.controllers.offer_letter import router as offer_letter_router
from app.controllers.attendance import router as attendance_router
from app.controllers.daily_task import router as daily_task_router
from app.controllers.admin import router as admin_router
from app.controllers.company_supervisor import router as company_supervisor_router
from app.controllers.indemnity_letter import router as indemnity_letter_router
from app.controllers.placement_agreement import router as placement_agreement_router

load_dotenv()

app = FastAPI()

origins = [
    origin.strip()
    for origin in os.getenv("ALLOWED_ORIGINS", "http://localhost:8080").split(",")
    if origin.strip()
]

app.include_router(login_router)
app.include_router(student_router)
app.include_router(resume_router)
app.include_router(notification_router)
app.include_router(headhunter_router)
app.include_router(opportunity_router)
app.include_router(application_router)
app.include_router(offer_letter_router)
app.include_router(attendance_router)
app.include_router(daily_task_router)
app.include_router(admin_router)
app.include_router(company_supervisor_router)
app.include_router(indemnity_letter_router)
app.include_router(placement_agreement_router)

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
async def root():
    return RedirectResponse("/login")
