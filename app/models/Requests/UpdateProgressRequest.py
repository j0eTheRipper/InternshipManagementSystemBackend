from pydantic import BaseModel, Field


class UpdateProgressRequest(BaseModel):
    progress: str = Field(min_length=1)
