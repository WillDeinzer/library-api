from fastapi import Depends, FastAPI
from sqlalchemy import create_engine, text
from app.common.constants import DATABASE_URL
from contextlib import asynccontextmanager

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

