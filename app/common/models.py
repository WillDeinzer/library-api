from pydantic import BaseModel

class AccountCreate(BaseModel):
    username: str
    password: str
    email: str | None = None

class ISBNRequest(BaseModel):
    isbn: str

class WishlistRequest(BaseModel):
    account_id: int
    isbn: str