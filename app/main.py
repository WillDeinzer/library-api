from fastapi import Depends, FastAPI, HTTPException
from sqlalchemy import create_engine, text
from app.common.constants import DATABASE_URL
from contextlib import asynccontextmanager
from app.common.models import AccountCreate
from app.helpers.account_helper import get_password_hash, verify_login
from fastapi.middleware.cors import CORSMiddleware

import httpx

from app.helpers.contest_helper import choose_winner

engine = None

@asynccontextmanager
async def lifespan(app: FastAPI):
    global engine
    engine = create_engine(DATABASE_URL, echo=True, pool_size=2, max_overflow=1)
    yield
    if engine:
        engine.dispose()

app = FastAPI(lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allow all origins
    allow_credentials=True,
    allow_methods=["*"],  # Allow all HTTP methods
    allow_headers=["*"],  # Allow all headers
)


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

# Account creation and login endpoints

@app.post("/create_account")
def create_account(account: AccountCreate, db=Depends(get_db)):
    try:
        # Check if username or email already exists
        user_exists = db.execute(
            text("SELECT 1 FROM accounts WHERE username=:username OR email=:email"),
            {"username": account.username, "email": account.email}
        ).first()
        if user_exists:
            return {"error": "Username or email already exists"}

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
    
@app.post("/login")
def login(account: AccountCreate, db=Depends(get_db)):
    try:
        # Check if account exists
        existing_account = db.execute(
            text("SELECT * FROM accounts WHERE username=:username"),
            {"username": account.username}
        ).first()
        if not existing_account:
            return {"error": "Account does not exist"}
        
        if not verify_login(account.username, account.password, db):
            return {"error": "Incorrect password"}
        
        account_id = existing_account["id"]
        
        db.execute(
            text("UPDATE accounts SET last_login=NOW() WHERE username=:username"),
            {"username": account.username}
        )
        db.commit()

        return {"message": "Login successful", "username": account.username, "account_id": account_id}
    except Exception as e:
        db.rollback()
        return {"error": f"Login failed: {str(e)}"}
    
# Admin endpoint for adding a new book to the database
    
@app.post("/addBookFromISBN")
def add_book_from_isbn(isbn: str, db=Depends(get_db)):
    url = f"https://openlibrary.org/api/books?bibkeys=ISBN:{isbn}&format=json&jscmd=data"
    try:
        with httpx.Client() as client:
            response = client.get(url)
            response.raise_for_status()
            data = response.json()
    except httpx.HTTPStatusError as e:
        raise HTTPException(status_code=502, detail=f"Upstream HTTP error: {e.response.status_code}")
    except httpx.RequestError:
        raise HTTPException(status_code=503, detail="Failed to reach upstream")
    
    book_data = data.get(f"ISBN:{isbn}", {})
    if not book_data:
        raise HTTPException(status_code=404, detail="Book not found")
    
    title = book_data.get("title")
    authors = [author.get("name") for author in book_data.get("authors", [])]
    publishers = [publisher.get("name") for publisher in book_data.get("publishers", [])]
    publication_date = book_data.get("publish_date")
    genres = [subject.get("name") for subject in book_data.get("subjects", [])]
    pages = book_data.get("number_of_pages")
    image = book_data.get("cover", {}).get("medium")

    try:
        db.execute(
            text('''INSERT INTO books(isbn, title, authors, publishers, publication_date, genres, pages, image)
                    VALUES (:isbn, :title, :authors, :publishers, :publication_date, :genres, :pages, :image)'''),
                {"isbn": isbn, "title": title, "authors": authors, "publishers": publishers,
                 "publication_date": publication_date, "genres": genres, "pages": int(pages), "image": image}
        )
        db.commit()
        return {"message": "Book added successfully"}
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Failed to add book: {str(e)}")
    
# Reviews endpoints
    
@app.post("/submitReview")
def submit_review(request: dict, db=Depends(get_db)):
    account_id = request.get("account_id")
    review_text = request.get("review_text")
    rating = request.get("rating")
    book_isbn = request.get("book_isbn")

    try:
        db.execute(
            text('''INSERT INTO reviews (account_id, review_text, rating, review_date, book_isbn)
                    VALUES (:account_id, :review_text, :rating, NOW(), :book_isbn)'''),
                {"account_id": account_id, "review_text": review_text, "rating": rating, "book_isbn": book_isbn}
        )
        db.commit()
        return {"message": "Review submitted successfully"}
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Failed to submit review: {str(e)}")
    
@app.get("/get_reviews_by_book")
def get_reviews_by_book(book_isbn: str, db=Depends(get_db)):
    try:
        result = db.execute(
            text("SELECT * FROM reviews WHERE book_isbn = :book_isbn"),
            {"book_isbn": book_isbn}
        )
        return [dict(row._mapping) for row in result.fetchall()]
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to retrieve reviews: {str(e)}")
    
@app.get("/select_contest_winner")
def select_contest_winner(db=Depends(get_db)):
    try:
        rows = db.execute(
            text('''SELECT a.username, COUNT(*) as review_count FROM accounts a JOIN reviews r
                    ON a.account_id = r.account_id GROUP BY a.username HAVING COUNT(*) > 0''')
        ).mappings().all()
        
        accounts_and_counts = [(row['username'], row['review_count']) for row in rows]

        if not accounts_and_counts:
            return {"message": "No reviews found to select a winner."}
        
        return {"winner": choose_winner(accounts_and_counts)}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to retrieve reviews: {str(e)}")

    






