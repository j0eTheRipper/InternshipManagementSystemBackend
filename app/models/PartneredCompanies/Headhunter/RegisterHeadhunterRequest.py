from pydantic import BaseModel, Field


class RegisterHeadhunterRequest(BaseModel):
    fullname: str = Field(min_length=1)
    email: str = Field(min_length=1)
    password: str = Field(min_length=6)
    company_name: str = Field(min_length=1)
    company_email: str = Field(default="")
