from passlib.context import CryptContext
from sqlalchemy import text

def get_password_hash(password: str) -> str:
    pwd_context = CryptContext(schemes=["argon2"], deprecated="auto")
    return pwd_context.hash(password)

def verify_login(username: str, password: str, db) -> bool:
    pwd_context = CryptContext(schemes=["argon2"], deprecated="auto")
    hashed_password = db.execute(
        text("SELECT password_hash FROM accounts WHERE username = :username"),
        {"username": username}
    )
    return pwd_context.verify(password, hashed_password.scalar()) if hashed_password else False