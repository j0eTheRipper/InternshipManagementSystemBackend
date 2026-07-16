from pydantic import BaseModel, Field


class AddAttendanceRequest(BaseModel):
    student_id: str = Field(min_length=1)
    date: str = Field(min_length=1, description="Date in YYYY-MM-DD format")
