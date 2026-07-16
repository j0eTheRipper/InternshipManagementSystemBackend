from pydantic import BaseModel, Field


class CreateCompanySupervisorRequest(BaseModel):
    fullname: str = Field(min_length=1)
    email: str = Field(min_length=1)
    password: str = Field(min_length=1)
    company_id: int = Field(gt=0)


class AssignCompanySupervisorRequest(BaseModel):
    company_supervisor_id: int = Field(gt=0)
