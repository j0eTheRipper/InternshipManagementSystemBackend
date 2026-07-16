from pydantic import BaseModel, Field


class CreateStudentRequest(BaseModel):
    fullname: str = Field(min_length=1)
    email: str = Field(min_length=1)
    password: str = Field(min_length=6)
    student_id: str = Field(min_length=1)
    year_of_study: int = Field(ge=1, le=10)
    field_of_study: str = Field(min_length=1)
    mentor_id: int
