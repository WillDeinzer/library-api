from fastapi import APIRouter, Depends
from sqlalchemy import text
from app.helpers.db_helper import get_db
from app.common.models import AccountCreate
from app.helpers.account_helper import get_password_hash, verify_login

router = APIRouter()

@router.post("/create_account")
def create_account(account: AccountCreate, db=Depends(get_db)):
    try:
        user_exists = db.execute(
            text("SELECT 1 FROM accounts WHERE username=:username"),
            {"username": account.username}
        ).first()
        if user_exists:
            return {"error": "Username or already exists"}

        hashed_password = get_password_hash(account.password)
        db.execute(
            text('''INSERT INTO accounts (username, password_hash, email, account_created, last_login, is_admin)
                    VALUES (:username, :passwordhash, :email, NOW(), NOW(), FALSE)'''),
            {"username": account.username, "passwordhash": hashed_password, "email": account.email}
        )
        db.commit()
        return login(account, db)
    except Exception as e:
        db.rollback()
        return {"error": f"Account creation failed: {str(e)}"}

@router.post("/login")
def login(account: AccountCreate, db=Depends(get_db)):
    try:
        existing_account = db.execute(
            text("SELECT * FROM accounts WHERE username=:username"),
            {"username": account.username}
        ).mappings().first()

        if not existing_account:
            return {"error": "Account does not exist"}

        if not verify_login(account.username, account.password, db):
            return {"error": "Incorrect password"}

        account_id = existing_account["account_id"]
        is_admin = existing_account["is_admin"]

        db.execute(
            text("UPDATE accounts SET last_login=NOW() WHERE username=:username"),
            {"username": account.username}
        )
        db.commit()

        return {"message": "Login successful", "username": account.username, "account_id": account_id, "is_admin": is_admin}
    except Exception as e:
        db.rollback()
        return {"error": f"Login failed: {str(e)}"}