from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException

from app.dependencies.auth import create_access_token, require_headhunter
from app.models.PartneredCompanies.Company import Company
from app.models.PartneredCompanies.Headhunter.Headhunter import Headhunter
from app.models.PartneredCompanies.Headhunter.RegisterHeadhunterRequest import RegisterHeadhunterRequest
from app.models.Role import Role
from app.models.User import User


router = APIRouter()


@router.post("/register/headhunter")
async def register_headhunter(body: RegisterHeadhunterRequest):
    if User.get_by_email(body.email):
        raise HTTPException(409, "Email already registered")

    company = Company.get_by_name(body.company_name)
    if not company:
        company = Company.create(body.company_name, body.company_email)

    user = User.create(body.fullname, body.email, body.password, Role.headhunter)
    Headhunter.create(user.user_id, company.company_id)

    headhunter = Headhunter.get_headhunter(user)
    token = create_access_token(user)
    return {
        "access_token": token,
        "token_type": "bearer",
        "user": headhunter.model_dump(mode="json"),
        "role": "headhunter",
    }


@router.get("/headhunter/profile")
async def get_headhunter_profile(user: Annotated[User, Depends(require_headhunter)]):
    return Headhunter.get_headhunter(user)
