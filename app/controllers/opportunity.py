from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query

from app.dependencies.auth import get_current_user, require_headhunter
from app.models.PartneredCompanies.Headhunter.Headhunter import Headhunter
from app.models.PartneredCompanies.JobOpportunity import JobOpportunity
from app.models.User import User


router = APIRouter(prefix="/opportunities")


@router.post("")
async def create_opportunity(
    body: dict,
    user: Annotated[User, Depends(require_headhunter)],
):
    title = body.get("title")
    job_role = body.get("job_role")
    description = body.get("description")
    location = body.get("location")
    status = body.get("status", "remote")
    field_of_study = body.get("field_of_study")

    if not all([title, job_role, description, location]):
        raise HTTPException(400, "title, job_role, description, and location are required")

    if not field_of_study:
        raise HTTPException(400, "field_of_study is required")

    valid_statuses = ["remote", "hybrid", "on-site"]
    if status not in valid_statuses:
        raise HTTPException(400, f"status must be one of: {', '.join(valid_statuses)}")

    opportunity = JobOpportunity.create(title, job_role, description, location, status, field_of_study, user.user_id)
    headhunter = Headhunter.get_headhunter(user)
    return opportunity.model_dump_with_company(headhunter.company.name)


@router.get("")
async def list_opportunities(
    user: Annotated[User, Depends(get_current_user)],
    field_of_study: str | None = Query(None),
    limit: int = Query(10, ge=1, le=100),
    offset: int = Query(0, ge=0),
    other_fields: bool = Query(False),
):
    if field_of_study and other_fields:
        opportunities = JobOpportunity.get_paginated_others(field_of_study, limit, offset)
    elif field_of_study:
        opportunities = JobOpportunity.get_paginated(field_of_study, limit, offset)
    else:
        opportunities = JobOpportunity.get_all()

    result = []
    for opp in opportunities:
        headhunter = Headhunter.get_headhunter(User.getUserData(opp.headhunter_id))
        result.append(opp.model_dump_with_company(headhunter.company.name))
    return result


@router.get("/my")
async def my_opportunities(user: Annotated[User, Depends(require_headhunter)]):
    opportunities = JobOpportunity.get_by_headhunter(user.user_id)
    headhunter = Headhunter.get_headhunter(user)
    return [opp.model_dump_with_company(headhunter.company.name) for opp in opportunities]


@router.get("/{opportunity_id}")
async def get_opportunity(
    opportunity_id: int,
    user: Annotated[User, Depends(get_current_user)],
):
    opportunity = JobOpportunity.get_by_id(opportunity_id)
    if not opportunity:
        raise HTTPException(404, "Opportunity not found")
    headhunter = Headhunter.get_headhunter(User.getUserData(opportunity.headhunter_id))
    return opportunity.model_dump_with_company(headhunter.company.name)


@router.patch("/{opportunity_id}")
async def update_opportunity(
    opportunity_id: int,
    body: dict,
    user: Annotated[User, Depends(require_headhunter)],
):
    opportunity = JobOpportunity.get_by_id(opportunity_id)
    if not opportunity:
        raise HTTPException(404, "Opportunity not found")
    if opportunity.headhunter_id != user.user_id:
        raise HTTPException(403, "You can only update your own opportunities")

    title = body.get("title", opportunity.title)
    job_role = body.get("job_role", opportunity.job_role)
    description = body.get("description", opportunity.description)
    location = body.get("location", opportunity.location)
    status = body.get("status", opportunity.status)

    JobOpportunity.update(opportunity_id, title, job_role, description, location, status)
    return {"message": "Opportunity updated"}


@router.delete("/{opportunity_id}")
async def delete_opportunity(
    opportunity_id: int,
    user: Annotated[User, Depends(require_headhunter)],
):
    opportunity = JobOpportunity.get_by_id(opportunity_id)
    if not opportunity:
        raise HTTPException(404, "Opportunity not found")
    if opportunity.headhunter_id != user.user_id:
        raise HTTPException(403, "You can only delete your own opportunities")

    JobOpportunity.delete(opportunity_id)
    return {"message": "Opportunity deleted"}
