from pydantic import BaseModel

class AccountCreate(BaseModel):
    username: str
    password: str
    email: str | None = None