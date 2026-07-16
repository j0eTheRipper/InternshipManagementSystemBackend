from pydantic import BaseModel, Field


class CreateMentorRequest(BaseModel):
    fullname: str = Field(min_length=1)
    email: str = Field(min_length=1)
    password: str = Field(min_length=6)
