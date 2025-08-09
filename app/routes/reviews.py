from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import text
from app.helpers.db_helper import get_db
from app.helpers.contest_helper import choose_winner

router = APIRouter()

@router.get("/get_all_reviews")
def get_all_reviews(db=Depends(get_db)):
    result = db.execute(text("SELECT * FROM reviews"))
    return [dict(row._mapping) for row in result.fetchall()]

@router.post("/submitReview")
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
    
@router.get("/get_reviews_by_book")
def get_reviews_by_book(book_isbn: str, db=Depends(get_db)):
    try:
        result = db.execute(
            text("SELECT * FROM reviews WHERE book_isbn = :book_isbn"),
            {"book_isbn": book_isbn}
        )
        return [dict(row._mapping) for row in result.fetchall()]
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to retrieve reviews: {str(e)}")
    
@router.get("/select_contest_winner")
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