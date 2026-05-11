from pydantic.main import BaseModel


class Credentials(BaseModel):
    email: str
    password: str
