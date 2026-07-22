from typing import Optional

from pydantic import BaseModel, model_validator


class UpdateProfileRequest(BaseModel):
    current_password: str
    new_email: Optional[str] = None
    new_password: Optional[str] = None

    @model_validator(mode="after")
    def check_at_least_one_field(self):
        if self.new_email is None and self.new_password is None:
            raise ValueError("At least one of new_email or new_password must be provided")
        return self
