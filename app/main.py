from fastapi import Depends, FastAPI, HTTPException, status
from sqlalchemy import create_engine, text
from app.common.constants import DATABASE_URL
from contextlib import asynccontextmanager
from app.common.models import AccountCreate
from app.helpers.account_helper import get_password_hash, verify_login

engine = None

@asynccontextmanager
async def lifespan(app: FastAPI):
    global engine

    engine = create_engine(DATABASE_URL, echo=True, pool_size=2, max_overflow=1)

    yield

    if engine:
        engine.dispose()

app = FastAPI(lifespan=lifespan)


def get_db():
    with engine.connect() as conn:
        yield conn

@app.get("/")
def root():
    return {"message": "Hello, World!"}

@app.get("/get_all_books")
def get_all_books(db=Depends(get_db)):
    result = db.execute(text("SELECT * FROM books"))
    return [dict(row._mapping) for row in result.fetchall()]

@app.get("/get_all_reviews")
def get_all_reviews(db=Depends(get_db)):
    result = db.execute(text("SELECT * FROM reviews"))
    return [dict(row._mapping) for row in result.fetchall()]

@app.post("/create_account")
def create_account(account: AccountCreate, db=Depends(get_db)):
    try:
        # Check if username or email already exists
        user_exists = db.execute(
            text("SELECT 1 FROM accounts WHERE username=:username OR email=:email"),
            {"username": account.username, "email": account.email}
        ).first()
        if user_exists:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Username or email already exists."
            )

        hashed_password = get_password_hash(account.password)
        db.execute(
            text('''INSERT INTO accounts (username, password_hash, email, account_created, last_login, is_admin)
                    VALUES (:username, :passwordhash, :email, NOW(), NOW(), FALSE)'''),
            {"username": account.username, "passwordhash": hashed_password, "email": account.email}
        )
        db.commit()
        return {"message": "Account created successfully"}
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Account creation failed: {str(e)}"
        )


