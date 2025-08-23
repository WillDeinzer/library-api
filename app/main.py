# from fastapi import FastAPI
# from app.common.constants import DATABASE_URL
# from contextlib import asynccontextmanager
# from fastapi.middleware.cors import CORSMiddleware
# from app.helpers.db_helper import engine

# from app.routes import accounts, books, reviews, chat

# @asynccontextmanager
# async def lifespan(app: FastAPI):
#     yield
#     engine.dispose()

# app = FastAPI(lifespan=lifespan)

# app.add_middleware(
#     CORSMiddleware,
#     allow_origins=["*"],  # Allow all origins
#     allow_credentials=True,
#     allow_methods=["*"],  # Allow all HTTP methods
#     allow_headers=["*"],  # Allow all headers
# )

# app.include_router(accounts.router)
# app.include_router(books.router)
# app.include_router(reviews.router)
# app.include_router(chat.router)

# @app.get("/")
# def root():
#     return {"message": "Hello, World!"}

from fastapi import FastAPI
app = FastAPI()

@app.get("/")
def root():
    return {"message": "Hello, World!"}