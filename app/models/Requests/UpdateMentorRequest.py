from pydantic import BaseModel


class UpdateMentorRequest(BaseModel):
    mentor_id: int
