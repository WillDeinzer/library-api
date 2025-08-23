from sqlalchemy import create_engine
from app.common.constants import DATABASE_PUBLIC_URL

engine = create_engine(DATABASE_PUBLIC_URL, echo=True, pool_size=2, max_overflow=1)

def get_db():
    with engine.connect() as conn:
        yield conn